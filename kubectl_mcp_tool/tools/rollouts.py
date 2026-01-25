"""Argo Rollouts and Flagger progressive delivery toolset for kubectl-mcp-server."""

import subprocess
import json
from typing import Dict, Any, List
from datetime import datetime

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ..crd_detector import crd_exists
from .utils import run_kubectl, get_resources


ARGO_ROLLOUT_CRD = "rollouts.argoproj.io"
ARGO_ANALYSIS_TEMPLATE_CRD = "analysistemplates.argoproj.io"
ARGO_CLUSTER_ANALYSIS_TEMPLATE_CRD = "clusteranalysistemplates.argoproj.io"
ARGO_ANALYSIS_RUN_CRD = "analysisruns.argoproj.io"
ARGO_EXPERIMENT_CRD = "experiments.argoproj.io"
FLAGGER_CANARY_CRD = "canaries.flagger.app"
FLAGGER_METRIC_TEMPLATE_CRD = "metrictemplates.flagger.app"
FLAGGER_ALERT_PROVIDER_CRD = "alertproviders.flagger.app"


def _argo_rollouts_cli_available() -> bool:
    """Check if kubectl-argo-rollouts plugin is available."""
    try:
        result = subprocess.run(["kubectl", "argo", "rollouts", "version"],
                                capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def rollouts_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Argo Rollouts with their status.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter rollouts

    Returns:
        List of Argo Rollouts with their status
    """
    if not crd_exists(ARGO_ROLLOUT_CRD, context):
        return {
            "success": False,
            "error": "Argo Rollouts is not installed (rollouts.argoproj.io CRD not found)"
        }

    rollouts = []
    for item in get_resources("rollouts.argoproj.io", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        strategy_spec = spec.get("strategy", {})
        if "canary" in strategy_spec:
            strategy = "canary"
            strategy_details = strategy_spec.get("canary", {})
        elif "blueGreen" in strategy_spec:
            strategy = "blueGreen"
            strategy_details = strategy_spec.get("blueGreen", {})
        else:
            strategy = "unknown"
            strategy_details = {}

        conditions = status.get("conditions", [])
        available_cond = next((c for c in conditions if c.get("type") == "Available"), {})
        progressing_cond = next((c for c in conditions if c.get("type") == "Progressing"), {})

        rollouts.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "strategy": strategy,
            "phase": status.get("phase", "Unknown"),
            "message": status.get("message", ""),
            "replicas": spec.get("replicas", 1),
            "ready_replicas": status.get("readyReplicas", 0),
            "available_replicas": status.get("availableReplicas", 0),
            "current_step": status.get("currentStepIndex"),
            "total_steps": len(strategy_details.get("steps", [])) if strategy == "canary" else None,
            "stable_rs": status.get("stableRS", ""),
            "canary_rs": status.get("canaryRS", "") if strategy == "canary" else None,
            "active_rs": status.get("blueGreen", {}).get("activeSelector", "") if strategy == "blueGreen" else None,
            "preview_rs": status.get("blueGreen", {}).get("previewSelector", "") if strategy == "blueGreen" else None,
            "available": available_cond.get("status") == "True",
            "progressing": progressing_cond.get("status") == "True",
            "paused": status.get("pauseConditions") is not None,
            "aborted": status.get("abort", False),
        })

    healthy = sum(1 for r in rollouts if r["phase"] == "Healthy")
    progressing = sum(1 for r in rollouts if r["phase"] == "Progressing")
    paused = sum(1 for r in rollouts if r["paused"])

    return {
        "context": context or "current",
        "total": len(rollouts),
        "healthy": healthy,
        "progressing": progressing,
        "paused": paused,
        "rollouts": rollouts,
    }


def rollout_get(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about an Argo Rollout.

    Args:
        name: Name of the Rollout
        namespace: Namespace of the Rollout
        context: Kubernetes context to use (optional)

    Returns:
        Detailed Rollout information
    """
    if not crd_exists(ARGO_ROLLOUT_CRD, context):
        return {"success": False, "error": "Argo Rollouts is not installed"}

    args = ["get", "rollouts.argoproj.io", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "rollout": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def rollout_status(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get current status of an Argo Rollout with step details.

    Args:
        name: Name of the Rollout
        namespace: Namespace of the Rollout
        context: Kubernetes context to use (optional)

    Returns:
        Rollout status with step information
    """
    result = rollout_get(name, namespace, context)
    if not result.get("success"):
        return result

    rollout = result["rollout"]
    status = rollout.get("status", {})
    spec = rollout.get("spec", {})
    strategy_spec = spec.get("strategy", {})

    if "canary" in strategy_spec:
        strategy = "canary"
        steps = strategy_spec.get("canary", {}).get("steps", [])
    elif "blueGreen" in strategy_spec:
        strategy = "blueGreen"
        steps = []
    else:
        strategy = "unknown"
        steps = []

    current_step = status.get("currentStepIndex", 0)
    step_info = []
    for i, step in enumerate(steps):
        step_type = list(step.keys())[0] if step else "unknown"
        step_value = step.get(step_type)

        step_info.append({
            "index": i,
            "type": step_type,
            "value": step_value,
            "current": i == current_step,
            "completed": i < current_step,
        })

    return {
        "success": True,
        "context": context or "current",
        "name": name,
        "namespace": namespace,
        "strategy": strategy,
        "phase": status.get("phase", "Unknown"),
        "message": status.get("message", ""),
        "current_step": current_step,
        "total_steps": len(steps),
        "steps": step_info,
        "paused": status.get("pauseConditions") is not None,
        "pause_reasons": [p.get("reason") for p in (status.get("pauseConditions") or [])],
        "canary_weight": status.get("canary", {}).get("weight", 0) if strategy == "canary" else None,
        "stable_revision": status.get("stableRS", ""),
        "canary_revision": status.get("canaryRS", ""),
    }


def rollout_promote(
    name: str,
    namespace: str,
    full: bool = False,
    context: str = ""
) -> Dict[str, Any]:
    """Promote a paused Argo Rollout.

    Args:
        name: Name of the Rollout
        namespace: Namespace of the Rollout
        full: Promote to full healthy state (skip remaining steps)
        context: Kubernetes context to use (optional)

    Returns:
        Promotion result
    """
    if not crd_exists(ARGO_ROLLOUT_CRD, context):
        return {"success": False, "error": "Argo Rollouts is not installed"}

    # Use kubectl plugin if available
    if _argo_rollouts_cli_available():
        cmd = ["kubectl", "argo", "rollouts", "promote", name, "-n", namespace]
        if full:
            cmd.append("--full")
        if context:
            cmd.extend(["--context", context])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Promoted rollout {name}" + (" (full)" if full else ""),
                    "output": result.stdout,
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Fallback to patching
    patch = {"status": {"pauseConditions": None}}
    if full:
        patch["status"]["promoteFull"] = True  # Full promotion to end

    args = [
        "patch", "rollouts.argoproj.io", name,
        "-n", namespace,
        "--type=merge",
        "-p", json.dumps(patch)
    ]
    result = run_kubectl(args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Promoted rollout {name}",
        }

    return {"success": False, "error": result.get("error", "Failed to promote")}


def rollout_abort(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Abort an Argo Rollout.

    Args:
        name: Name of the Rollout
        namespace: Namespace of the Rollout
        context: Kubernetes context to use (optional)

    Returns:
        Abort result
    """
    if not crd_exists(ARGO_ROLLOUT_CRD, context):
        return {"success": False, "error": "Argo Rollouts is not installed"}

    if _argo_rollouts_cli_available():
        cmd = ["kubectl", "argo", "rollouts", "abort", name, "-n", namespace]
        if context:
            cmd.extend(["--context", context])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Aborted rollout {name}",
                    "output": result.stdout,
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Fallback to patching
    patch = {"status": {"abort": True}}
    args = [
        "patch", "rollouts.argoproj.io", name,
        "-n", namespace,
        "--type=merge",
        "-p", json.dumps(patch)
    ]
    result = run_kubectl(args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Aborted rollout {name}",
        }

    return {"success": False, "error": result.get("error", "Failed to abort")}


def rollout_retry(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Retry an aborted Argo Rollout.

    Args:
        name: Name of the Rollout
        namespace: Namespace of the Rollout
        context: Kubernetes context to use (optional)

    Returns:
        Retry result
    """
    if not crd_exists(ARGO_ROLLOUT_CRD, context):
        return {"success": False, "error": "Argo Rollouts is not installed"}

    if _argo_rollouts_cli_available():
        cmd = ["kubectl", "argo", "rollouts", "retry", name, "-n", namespace]
        if context:
            cmd.extend(["--context", context])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Retried rollout {name}",
                    "output": result.stdout,
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Fallback to patching (clear abort status)
    patch = {"status": {"abort": False}}
    args = [
        "patch", "rollouts.argoproj.io", name,
        "-n", namespace,
        "--type=merge",
        "-p", json.dumps(patch)
    ]
    result = run_kubectl(args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Retried rollout {name}",
        }

    return {"success": False, "error": result.get("error", "Failed to retry")}


def rollout_restart(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Restart an Argo Rollout.

    Args:
        name: Name of the Rollout
        namespace: Namespace of the Rollout
        context: Kubernetes context to use (optional)

    Returns:
        Restart result
    """
    if not crd_exists(ARGO_ROLLOUT_CRD, context):
        return {"success": False, "error": "Argo Rollouts is not installed"}

    if _argo_rollouts_cli_available():
        cmd = ["kubectl", "argo", "rollouts", "restart", name, "-n", namespace]
        if context:
            cmd.extend(["--context", context])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "message": f"Restarted rollout {name}",
                    "output": result.stdout,
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Fallback: patch the template to trigger restart
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    patch = {
        "spec": {
            "restartAt": timestamp
        }
    }
    args = [
        "patch", "rollouts.argoproj.io", name,
        "-n", namespace,
        "--type=merge",
        "-p", json.dumps(patch)
    ]
    result = run_kubectl(args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Restarted rollout {name}",
        }

    return {"success": False, "error": result.get("error", "Failed to restart")}


def analysis_runs_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Argo Rollouts AnalysisRuns.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of AnalysisRuns with their status
    """
    if not crd_exists(ARGO_ANALYSIS_RUN_CRD, context):
        return {
            "success": False,
            "error": "AnalysisRuns CRD not found"
        }

    runs = []
    for item in get_resources("analysisruns.argoproj.io", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})

        runs.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "message": status.get("message", ""),
            "metrics_count": len(spec.get("metrics", [])),
            "started_at": status.get("startedAt", ""),
            "metric_results": [
                {
                    "name": m.get("name"),
                    "phase": m.get("phase"),
                    "count": m.get("count", 0),
                    "successful": m.get("successful", 0),
                    "failed": m.get("failed", 0),
                }
                for m in status.get("metricResults", [])
            ],
        })

    return {
        "context": context or "current",
        "total": len(runs),
        "analysis_runs": runs,
    }


def flagger_canaries_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Flagger Canary resources.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of Flagger Canaries with their status
    """
    if not crd_exists(FLAGGER_CANARY_CRD, context):
        return {
            "success": False,
            "error": "Flagger is not installed (canaries.flagger.app CRD not found)"
        }

    canaries = []
    for item in get_resources("canaries.flagger.app", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        analysis = spec.get("analysis", {})

        canaries.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "canary_weight": status.get("canaryWeight", 0),
            "failed_checks": status.get("failedChecks", 0),
            "iterations": status.get("iterations", 0),
            "target_ref": spec.get("targetRef", {}),
            "service": spec.get("service", {}),
            "max_weight": analysis.get("maxWeight", 50),
            "step_weight": analysis.get("stepWeight", 5),
            "threshold": analysis.get("threshold", 5),
            "interval": analysis.get("interval", "1m"),
            "metrics_count": len(analysis.get("metrics", [])),
            "last_transition_time": status.get("lastTransitionTime", ""),
        })

    progressing = sum(1 for c in canaries if c["phase"] == "Progressing")
    succeeded = sum(1 for c in canaries if c["phase"] == "Succeeded")
    failed = sum(1 for c in canaries if c["phase"] == "Failed")

    return {
        "context": context or "current",
        "total": len(canaries),
        "progressing": progressing,
        "succeeded": succeeded,
        "failed": failed,
        "canaries": canaries,
    }


def flagger_canary_get(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a Flagger Canary.

    Args:
        name: Name of the Canary
        namespace: Namespace of the Canary
        context: Kubernetes context to use (optional)

    Returns:
        Detailed Canary information
    """
    if not crd_exists(FLAGGER_CANARY_CRD, context):
        return {"success": False, "error": "Flagger is not installed"}

    args = ["get", "canaries.flagger.app", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "canary": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def rollouts_detect(context: str = "") -> Dict[str, Any]:
    """Detect which progressive delivery tools are installed.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for Argo Rollouts and Flagger
    """
    return {
        "context": context or "current",
        "argo_rollouts": {
            "installed": crd_exists(ARGO_ROLLOUT_CRD, context),
            "cli_available": _argo_rollouts_cli_available(),
            "crds": {
                "rollouts": crd_exists(ARGO_ROLLOUT_CRD, context),
                "analysistemplates": crd_exists(ARGO_ANALYSIS_TEMPLATE_CRD, context),
                "clusteranalysistemplates": crd_exists(ARGO_CLUSTER_ANALYSIS_TEMPLATE_CRD, context),
                "analysisruns": crd_exists(ARGO_ANALYSIS_RUN_CRD, context),
                "experiments": crd_exists(ARGO_EXPERIMENT_CRD, context),
            },
        },
        "flagger": {
            "installed": crd_exists(FLAGGER_CANARY_CRD, context),
            "crds": {
                "canaries": crd_exists(FLAGGER_CANARY_CRD, context),
                "metrictemplates": crd_exists(FLAGGER_METRIC_TEMPLATE_CRD, context),
                "alertproviders": crd_exists(FLAGGER_ALERT_PROVIDER_CRD, context),
            },
        },
    }


def register_rollouts_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register progressive delivery tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def rollouts_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Argo Rollouts with their status."""
        return json.dumps(rollouts_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def rollout_get_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get detailed information about an Argo Rollout."""
        return json.dumps(rollout_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def rollout_status_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get current status of an Argo Rollout with step details."""
        return json.dumps(rollout_status(name, namespace, context), indent=2)

    @mcp.tool()
    def rollout_promote_tool(
        name: str,
        namespace: str,
        full: bool = False,
        context: str = ""
    ) -> str:
        """Promote a paused Argo Rollout to the next step or full."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(rollout_promote(name, namespace, full, context), indent=2)

    @mcp.tool()
    def rollout_abort_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Abort an Argo Rollout."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(rollout_abort(name, namespace, context), indent=2)

    @mcp.tool()
    def rollout_retry_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Retry an aborted Argo Rollout."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(rollout_retry(name, namespace, context), indent=2)

    @mcp.tool()
    def rollout_restart_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Restart an Argo Rollout."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(rollout_restart(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def analysis_runs_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Argo Rollouts AnalysisRuns."""
        return json.dumps(analysis_runs_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def flagger_canaries_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Flagger Canary resources."""
        return json.dumps(flagger_canaries_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def flagger_canary_get_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get detailed information about a Flagger Canary."""
        return json.dumps(flagger_canary_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def rollouts_detect_tool(context: str = "") -> str:
        """Detect which progressive delivery tools are installed."""
        return json.dumps(rollouts_detect(context), indent=2)
