"""KEDA autoscaling toolset for kubectl-mcp-server."""

import json
from typing import Dict, Any, List

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ..crd_detector import crd_exists
from .utils import run_kubectl, get_resources


SCALEDOBJECT_CRD = "scaledobjects.keda.sh"
SCALEDJOB_CRD = "scaledjobs.keda.sh"
TRIGGERAUTH_CRD = "triggerauthentications.keda.sh"
CLUSTERTRIGGERAUTH_CRD = "clustertriggerauthentications.keda.sh"


def keda_scaledobjects_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List KEDA ScaledObjects with their status.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter resources

    Returns:
        List of ScaledObjects with their scaling status
    """
    if not crd_exists(SCALEDOBJECT_CRD, context):
        return {
            "success": False,
            "error": "KEDA is not installed (scaledobjects.keda.sh CRD not found)"
        }

    objects = []
    for item in get_resources("scaledobjects.keda.sh", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        active_cond = next((c for c in conditions if c.get("type") == "Active"), {})

        triggers = spec.get("triggers", [])
        trigger_types = [t.get("type", "unknown") for t in triggers]

        objects.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "ready": ready_cond.get("status") == "True",
            "active": active_cond.get("status") == "True",
            "status": ready_cond.get("reason", "Unknown"),
            "message": ready_cond.get("message", ""),
            "scale_target_ref": spec.get("scaleTargetRef", {}),
            "min_replicas": spec.get("minReplicaCount", 0),
            "max_replicas": spec.get("maxReplicaCount", 100),
            "current_replicas": status.get("scaleTargetKind", {}).get("replicas"),
            "trigger_types": trigger_types,
            "triggers_count": len(triggers),
            "paused_replicas": spec.get("pausedReplicaCount"),
            "cooldown_period": spec.get("cooldownPeriod", 300),
            "polling_interval": spec.get("pollingInterval", 30),
        })

    active_count = sum(1 for o in objects if o["active"])

    return {
        "context": context or "current",
        "total": len(objects),
        "active": active_count,
        "scaledobjects": objects,
    }


def keda_scaledobject_get(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a ScaledObject.

    Args:
        name: Name of the ScaledObject
        namespace: Namespace of the ScaledObject
        context: Kubernetes context to use (optional)

    Returns:
        Detailed ScaledObject information
    """
    if not crd_exists(SCALEDOBJECT_CRD, context):
        return {"success": False, "error": "KEDA is not installed"}

    args = ["get", "scaledobjects.keda.sh", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "scaledobject": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def keda_scaledjobs_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List KEDA ScaledJobs with their status.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter resources

    Returns:
        List of ScaledJobs with their scaling status
    """
    if not crd_exists(SCALEDJOB_CRD, context):
        return {
            "success": False,
            "error": "KEDA ScaledJobs CRD not found"
        }

    jobs = []
    for item in get_resources("scaledjobs.keda.sh", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})

        triggers = spec.get("triggers", [])
        trigger_types = [t.get("type", "unknown") for t in triggers]

        jobs.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "ready": ready_cond.get("status") == "True",
            "status": ready_cond.get("reason", "Unknown"),
            "message": ready_cond.get("message", ""),
            "job_target_ref": spec.get("jobTargetRef", {}),
            "min_replicas": spec.get("minReplicaCount", 0),
            "max_replicas": spec.get("maxReplicaCount", 100),
            "trigger_types": trigger_types,
            "triggers_count": len(triggers),
            "polling_interval": spec.get("pollingInterval", 30),
            "successful_jobs_history": spec.get("successfulJobsHistoryLimit", 100),
            "failed_jobs_history": spec.get("failedJobsHistoryLimit", 100),
        })

    return {
        "context": context or "current",
        "total": len(jobs),
        "scaledjobs": jobs,
    }


def keda_triggerauths_list(
    namespace: str = "",
    context: str = "",
    include_cluster: bool = True
) -> Dict[str, Any]:
    """List KEDA TriggerAuthentications and ClusterTriggerAuthentications.

    Args:
        namespace: Filter by namespace (empty for all)
        context: Kubernetes context to use (optional)
        include_cluster: Include ClusterTriggerAuthentications

    Returns:
        List of trigger authentications
    """
    auths = []

    if crd_exists(TRIGGERAUTH_CRD, context):
        for item in get_resources("triggerauthentications.keda.sh", namespace, context):
            spec = item.get("spec", {})
            secret_refs = spec.get("secretTargetRef", [])
            env_refs = spec.get("env", [])

            auths.append({
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "kind": "TriggerAuthentication",
                "secret_refs_count": len(secret_refs),
                "env_refs_count": len(env_refs),
                "has_pod_identity": "podIdentity" in spec,
                "has_azure_identity": "azureKeyVault" in spec,
                "has_hashicorp_vault": "hashiCorpVault" in spec,
            })

    if include_cluster and crd_exists(CLUSTERTRIGGERAUTH_CRD, context):
        for item in get_resources("clustertriggerauthentications.keda.sh", "", context):
            spec = item.get("spec", {})
            secret_refs = spec.get("secretTargetRef", [])
            env_refs = spec.get("env", [])

            auths.append({
                "name": item["metadata"]["name"],
                "namespace": "",
                "kind": "ClusterTriggerAuthentication",
                "secret_refs_count": len(secret_refs),
                "env_refs_count": len(env_refs),
                "has_pod_identity": "podIdentity" in spec,
                "has_azure_identity": "azureKeyVault" in spec,
                "has_hashicorp_vault": "hashiCorpVault" in spec,
            })

    return {
        "context": context or "current",
        "total": len(auths),
        "authentications": auths,
    }


def keda_triggerauth_get(
    name: str,
    namespace: str = "",
    kind: str = "TriggerAuthentication",
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a TriggerAuthentication.

    Args:
        name: Name of the TriggerAuthentication
        namespace: Namespace (only for TriggerAuthentication, not ClusterTriggerAuthentication)
        kind: TriggerAuthentication or ClusterTriggerAuthentication
        context: Kubernetes context to use (optional)

    Returns:
        Detailed TriggerAuthentication information
    """
    if kind.lower() == "clustertriggerauthentication":
        crd = "clustertriggerauthentications.keda.sh"
        args = ["get", crd, name, "-o", "json"]
    else:
        crd = "triggerauthentications.keda.sh"
        args = ["get", crd, name, "-n", namespace, "-o", "json"]

    if not crd_exists(crd, context):
        return {"success": False, "error": f"{crd} not found"}

    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "authentication": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def keda_hpa_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List HPAs managed by KEDA.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter resources

    Returns:
        List of KEDA-managed HPAs
    """
    # KEDA creates HPAs with specific labels
    keda_label = "scaledobject.keda.sh/name"
    selector = label_selector if label_selector else ""

    args = ["get", "hpa", "-o", "json"]
    if namespace:
        args.extend(["-n", namespace])
    else:
        args.append("-A")
    if selector:
        args.extend(["-l", selector])

    result = run_kubectl(args, context)
    if not result["success"]:
        return {"success": False, "error": result.get("error", "Failed to list HPAs")}

    try:
        data = json.loads(result["output"])
        items = data.get("items", [])
    except json.JSONDecodeError:
        return {"success": False, "error": "Failed to parse response"}

    hpas = []
    for item in items:
        labels = item.get("metadata", {}).get("labels", {})
        # Filter to KEDA-managed HPAs
        if keda_label not in labels and "app.kubernetes.io/managed-by" not in labels:
            continue
        if labels.get("app.kubernetes.io/managed-by") != "keda-operator":
            if keda_label not in labels:
                continue

        spec = item.get("spec", {})
        status = item.get("status", {})

        hpas.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "scaledobject": labels.get(keda_label, ""),
            "min_replicas": spec.get("minReplicas", 1),
            "max_replicas": spec.get("maxReplicas", 10),
            "current_replicas": status.get("currentReplicas", 0),
            "desired_replicas": status.get("desiredReplicas", 0),
            "current_metrics": status.get("currentMetrics", []),
            "conditions": status.get("conditions", []),
        })

    return {
        "context": context or "current",
        "total": len(hpas),
        "hpas": hpas,
    }


def keda_detect(context: str = "") -> Dict[str, Any]:
    """Detect if KEDA is installed and its components.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for KEDA
    """
    return {
        "context": context or "current",
        "installed": crd_exists(SCALEDOBJECT_CRD, context),
        "crds": {
            "scaledobjects": crd_exists(SCALEDOBJECT_CRD, context),
            "scaledjobs": crd_exists(SCALEDJOB_CRD, context),
            "triggerauthentications": crd_exists(TRIGGERAUTH_CRD, context),
            "clustertriggerauthentications": crd_exists(CLUSTERTRIGGERAUTH_CRD, context),
        },
    }


def register_keda_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register KEDA tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def keda_scaledobjects_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List KEDA ScaledObjects with their scaling status."""
        return json.dumps(keda_scaledobjects_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def keda_scaledobject_get_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get detailed information about a ScaledObject."""
        return json.dumps(keda_scaledobject_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def keda_scaledjobs_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List KEDA ScaledJobs with their status."""
        return json.dumps(keda_scaledjobs_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def keda_triggerauths_list_tool(
        namespace: str = "",
        context: str = "",
        include_cluster: bool = True
    ) -> str:
        """List KEDA TriggerAuthentications and ClusterTriggerAuthentications."""
        return json.dumps(keda_triggerauths_list(namespace, context, include_cluster), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def keda_triggerauth_get_tool(
        name: str,
        namespace: str = "",
        kind: str = "TriggerAuthentication",
        context: str = ""
    ) -> str:
        """Get detailed information about a TriggerAuthentication."""
        return json.dumps(keda_triggerauth_get(name, namespace, kind, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def keda_hpa_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List HPAs managed by KEDA."""
        return json.dumps(keda_hpa_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def keda_detect_tool(context: str = "") -> str:
        """Detect if KEDA is installed and its components."""
        return json.dumps(keda_detect(context), indent=2)
