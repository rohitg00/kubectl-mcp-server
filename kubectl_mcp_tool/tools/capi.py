"""Cluster API (CAPI) toolset for kubectl-mcp-server."""

import subprocess
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


CLUSTER_CRD = "clusters.cluster.x-k8s.io"
MACHINE_CRD = "machines.cluster.x-k8s.io"
MACHINEDEPLOYMENT_CRD = "machinedeployments.cluster.x-k8s.io"
MACHINESET_CRD = "machinesets.cluster.x-k8s.io"
MACHINEPOOL_CRD = "machinepools.cluster.x-k8s.io"
MACHINEHEALTHCHECK_CRD = "machinehealthchecks.cluster.x-k8s.io"
CLUSTERCLASS_CRD = "clusterclasses.cluster.x-k8s.io"


def _clusterctl_available() -> bool:
    """Check if clusterctl CLI is available."""
    try:
        result = subprocess.run(["clusterctl", "version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def capi_clusters_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Cluster API managed clusters.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter clusters

    Returns:
        List of CAPI clusters with their status
    """
    if not crd_exists(CLUSTER_CRD, context):
        return {
            "success": False,
            "error": "Cluster API is not installed (clusters.cluster.x-k8s.io CRD not found)"
        }

    clusters = []
    for item in get_resources("clusters.cluster.x-k8s.io", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        conditions = status.get("conditions", [])
        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        infra_ready = next((c for c in conditions if c.get("type") == "InfrastructureReady"), {})
        cp_ready = next((c for c in conditions if c.get("type") == "ControlPlaneReady"), {})

        clusters.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "ready": ready_cond.get("status") == "True",
            "infrastructure_ready": infra_ready.get("status") == "True",
            "control_plane_ready": cp_ready.get("status") == "True",
            "control_plane_endpoint": spec.get("controlPlaneEndpoint", {}),
            "infrastructure_ref": spec.get("infrastructureRef", {}),
            "control_plane_ref": spec.get("controlPlaneRef", {}),
            "cluster_network": spec.get("clusterNetwork", {}),
            "paused": spec.get("paused", False),
            "observed_generation": status.get("observedGeneration"),
            "failure_reason": status.get("failureReason"),
            "failure_message": status.get("failureMessage"),
        })

    ready = sum(1 for c in clusters if c["ready"])
    provisioning = sum(1 for c in clusters if c["phase"] == "Provisioning")

    return {
        "context": context or "current",
        "total": len(clusters),
        "ready": ready,
        "provisioning": provisioning,
        "clusters": clusters,
    }


def capi_cluster_get(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a CAPI cluster.

    Args:
        name: Name of the cluster
        namespace: Namespace of the cluster
        context: Kubernetes context to use (optional)

    Returns:
        Detailed cluster information
    """
    if not crd_exists(CLUSTER_CRD, context):
        return {"success": False, "error": "Cluster API is not installed"}

    args = ["get", "clusters.cluster.x-k8s.io", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "cluster": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def capi_machines_list(
    namespace: str = "",
    cluster_name: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Cluster API machines.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        cluster_name: Filter by cluster name
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter machines

    Returns:
        List of machines with their status
    """
    if not crd_exists(MACHINE_CRD, context):
        return {
            "success": False,
            "error": "Cluster API is not installed (machines.cluster.x-k8s.io CRD not found)"
        }

    selector = label_selector
    if cluster_name:
        cluster_label = f"cluster.x-k8s.io/cluster-name={cluster_name}"
        selector = f"{selector},{cluster_label}" if selector else cluster_label

    machines = []
    for item in get_resources("machines.cluster.x-k8s.io", namespace, context, selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        infra_ready = next((c for c in conditions if c.get("type") == "InfrastructureReady"), {})

        machines.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "cluster": spec.get("clusterName", ""),
            "phase": status.get("phase", "Unknown"),
            "ready": ready_cond.get("status") == "True",
            "infrastructure_ready": infra_ready.get("status") == "True",
            "provider_id": spec.get("providerID", ""),
            "version": spec.get("version", ""),
            "bootstrap_ref": spec.get("bootstrap", {}).get("configRef", {}),
            "infrastructure_ref": spec.get("infrastructureRef", {}),
            "node_ref": status.get("nodeRef", {}),
            "addresses": status.get("addresses", []),
            "failure_reason": status.get("failureReason"),
            "failure_message": status.get("failureMessage"),
        })

    ready = sum(1 for m in machines if m["ready"])
    running = sum(1 for m in machines if m["phase"] == "Running")

    return {
        "context": context or "current",
        "total": len(machines),
        "ready": ready,
        "running": running,
        "machines": machines,
    }


def capi_machine_get(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a CAPI machine.

    Args:
        name: Name of the machine
        namespace: Namespace of the machine
        context: Kubernetes context to use (optional)

    Returns:
        Detailed machine information
    """
    if not crd_exists(MACHINE_CRD, context):
        return {"success": False, "error": "Cluster API is not installed"}

    args = ["get", "machines.cluster.x-k8s.io", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "machine": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def capi_machinedeployments_list(
    namespace: str = "",
    cluster_name: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Cluster API MachineDeployments.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        cluster_name: Filter by cluster name
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of MachineDeployments with their status
    """
    if not crd_exists(MACHINEDEPLOYMENT_CRD, context):
        return {
            "success": False,
            "error": "MachineDeployments CRD not found"
        }

    selector = label_selector
    if cluster_name:
        cluster_label = f"cluster.x-k8s.io/cluster-name={cluster_name}"
        selector = f"{selector},{cluster_label}" if selector else cluster_label

    deployments = []
    for item in get_resources("machinedeployments.cluster.x-k8s.io", namespace, context, selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        available_cond = next((c for c in conditions if c.get("type") == "Available"), {})

        deployments.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "cluster": spec.get("clusterName", ""),
            "phase": status.get("phase", "Unknown"),
            "ready": ready_cond.get("status") == "True",
            "available": available_cond.get("status") == "True",
            "replicas": spec.get("replicas", 0),
            "ready_replicas": status.get("readyReplicas", 0),
            "available_replicas": status.get("availableReplicas", 0),
            "updated_replicas": status.get("updatedReplicas", 0),
            "unavailable_replicas": status.get("unavailableReplicas", 0),
            "version": spec.get("template", {}).get("spec", {}).get("version", ""),
            "strategy": spec.get("strategy", {}),
            "observed_generation": status.get("observedGeneration"),
        })

    return {
        "context": context or "current",
        "total": len(deployments),
        "deployments": deployments,
    }


def capi_machinedeployment_scale(
    name: str,
    namespace: str,
    replicas: int,
    context: str = ""
) -> Dict[str, Any]:
    """Scale a MachineDeployment.

    Args:
        name: Name of the MachineDeployment
        namespace: Namespace of the MachineDeployment
        replicas: Desired number of replicas
        context: Kubernetes context to use (optional)

    Returns:
        Scale result
    """
    if not crd_exists(MACHINEDEPLOYMENT_CRD, context):
        return {"success": False, "error": "Cluster API is not installed"}

    if replicas < 0:
        return {"success": False, "error": "Replicas must be >= 0"}

    args = [
        "scale", "machinedeployments.cluster.x-k8s.io", name,
        "-n", namespace,
        f"--replicas={replicas}"
    ]
    result = run_kubectl(args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Scaled MachineDeployment {name} to {replicas} replicas",
        }

    return {"success": False, "error": result.get("error", "Failed to scale")}


def capi_machinesets_list(
    namespace: str = "",
    cluster_name: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Cluster API MachineSets.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        cluster_name: Filter by cluster name
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of MachineSets with their status
    """
    if not crd_exists(MACHINESET_CRD, context):
        return {
            "success": False,
            "error": "MachineSets CRD not found"
        }

    selector = label_selector
    if cluster_name:
        cluster_label = f"cluster.x-k8s.io/cluster-name={cluster_name}"
        selector = f"{selector},{cluster_label}" if selector else cluster_label

    machinesets = []
    for item in get_resources("machinesets.cluster.x-k8s.io", namespace, context, selector):
        status = item.get("status", {})
        spec = item.get("spec", {})

        machinesets.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "cluster": spec.get("clusterName", ""),
            "replicas": spec.get("replicas", 0),
            "ready_replicas": status.get("readyReplicas", 0),
            "available_replicas": status.get("availableReplicas", 0),
            "fully_labeled_replicas": status.get("fullyLabeledReplicas", 0),
            "version": spec.get("template", {}).get("spec", {}).get("version", ""),
            "selector": spec.get("selector", {}),
            "observed_generation": status.get("observedGeneration"),
            "failure_reason": status.get("failureReason"),
            "failure_message": status.get("failureMessage"),
        })

    return {
        "context": context or "current",
        "total": len(machinesets),
        "machinesets": machinesets,
    }


def capi_machinehealthchecks_list(
    namespace: str = "",
    cluster_name: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Cluster API MachineHealthChecks.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        cluster_name: Filter by cluster name
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of MachineHealthChecks with their status
    """
    if not crd_exists(MACHINEHEALTHCHECK_CRD, context):
        return {
            "success": False,
            "error": "MachineHealthChecks CRD not found"
        }

    selector = label_selector
    if cluster_name:
        cluster_label = f"cluster.x-k8s.io/cluster-name={cluster_name}"
        selector = f"{selector},{cluster_label}" if selector else cluster_label

    healthchecks = []
    for item in get_resources("machinehealthchecks.cluster.x-k8s.io", namespace, context, selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        conditions = status.get("conditions", [])

        remediation_allowed = next((c for c in conditions if c.get("type") == "RemediationAllowed"), {})

        healthchecks.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "cluster": spec.get("clusterName", ""),
            "expected_machines": status.get("expectedMachines", 0),
            "current_healthy": status.get("currentHealthy", 0),
            "remediation_allowed": remediation_allowed.get("status") == "True",
            "unhealthy_conditions": spec.get("unhealthyConditions", []),
            "max_unhealthy": spec.get("maxUnhealthy"),
            "node_startup_timeout": spec.get("nodeStartupTimeout"),
            "targets": status.get("targets", []),
        })

    return {
        "context": context or "current",
        "total": len(healthchecks),
        "healthchecks": healthchecks,
    }


def capi_clusterclasses_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Cluster API ClusterClasses.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of ClusterClasses
    """
    if not crd_exists(CLUSTERCLASS_CRD, context):
        return {
            "success": False,
            "error": "ClusterClasses CRD not found"
        }

    classes = []
    for item in get_resources("clusterclasses.cluster.x-k8s.io", namespace, context, label_selector):
        spec = item.get("spec", {})
        status = item.get("status", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        variables_ready = next((c for c in conditions if c.get("type") == "VariablesReady"), {})

        workers = spec.get("workers", {})
        machine_deployments = workers.get("machineDeployments", [])
        machine_pools = workers.get("machinePools", [])

        classes.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "ready": ready_cond.get("status") == "True",
            "variables_ready": variables_ready.get("status") == "True",
            "infrastructure_ref": spec.get("infrastructure", {}).get("ref", {}),
            "control_plane_ref": spec.get("controlPlane", {}).get("ref", {}),
            "machinedeployment_classes": len(machine_deployments),
            "machinepool_classes": len(machine_pools),
            "variables_count": len(spec.get("variables", [])),
            "observed_generation": status.get("observedGeneration"),
        })

    return {
        "context": context or "current",
        "total": len(classes),
        "clusterclasses": classes,
    }


def capi_cluster_kubeconfig(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get kubeconfig for a CAPI cluster.

    Args:
        name: Name of the cluster
        namespace: Namespace of the cluster
        context: Kubernetes context to use (optional)

    Returns:
        Kubeconfig secret information
    """
    if not crd_exists(CLUSTER_CRD, context):
        return {"success": False, "error": "Cluster API is not installed"}

    # CAPI stores kubeconfig in a secret named <cluster-name>-kubeconfig
    secret_name = f"{name}-kubeconfig"
    args = ["get", "secret", secret_name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            # Don't expose actual kubeconfig data, just metadata
            return {
                "success": True,
                "context": context or "current",
                "secret_name": secret_name,
                "namespace": namespace,
                "exists": True,
                "data_keys": list(data.get("data", {}).keys()),
                "note": "Use 'clusterctl get kubeconfig' or 'kubectl get secret -o jsonpath' to retrieve actual kubeconfig",
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    # Check if this is a NotFound error vs other failures
    error_output = result.get("output", "") + result.get("error", "")
    if "NotFound" in error_output or "not found" in error_output.lower():
        return {
            "success": True,
            "context": context or "current",
            "secret_name": secret_name,
            "namespace": namespace,
            "exists": False,
            "note": "Kubeconfig secret not found - cluster may still be provisioning",
        }

    # For other kubectl failures, return the actual error
    return {
        "success": False,
        "error": error_output.strip() or "Failed to get kubeconfig secret",
    }


def capi_detect(context: str = "") -> Dict[str, Any]:
    """Detect if Cluster API is installed and its components.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for Cluster API
    """
    return {
        "context": context or "current",
        "installed": crd_exists(CLUSTER_CRD, context),
        "cli_available": _clusterctl_available(),
        "crds": {
            "clusters": crd_exists(CLUSTER_CRD, context),
            "machines": crd_exists(MACHINE_CRD, context),
            "machinedeployments": crd_exists(MACHINEDEPLOYMENT_CRD, context),
            "machinesets": crd_exists(MACHINESET_CRD, context),
            "machinepools": crd_exists(MACHINEPOOL_CRD, context),
            "machinehealthchecks": crd_exists(MACHINEHEALTHCHECK_CRD, context),
            "clusterclasses": crd_exists(CLUSTERCLASS_CRD, context),
        },
    }


def register_capi_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register Cluster API tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_clusters_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Cluster API managed clusters."""
        return json.dumps(capi_clusters_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_cluster_get_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get detailed information about a CAPI cluster."""
        return json.dumps(capi_cluster_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_machines_list_tool(
        namespace: str = "",
        cluster_name: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Cluster API machines."""
        return json.dumps(capi_machines_list(namespace, cluster_name, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_machine_get_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get detailed information about a CAPI machine."""
        return json.dumps(capi_machine_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_machinedeployments_list_tool(
        namespace: str = "",
        cluster_name: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Cluster API MachineDeployments."""
        return json.dumps(capi_machinedeployments_list(namespace, cluster_name, context, label_selector), indent=2)

    @mcp.tool()
    def capi_machinedeployment_scale_tool(
        name: str,
        namespace: str,
        replicas: int,
        context: str = ""
    ) -> str:
        """Scale a CAPI MachineDeployment."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(capi_machinedeployment_scale(name, namespace, replicas, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_machinesets_list_tool(
        namespace: str = "",
        cluster_name: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Cluster API MachineSets."""
        return json.dumps(capi_machinesets_list(namespace, cluster_name, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_machinehealthchecks_list_tool(
        namespace: str = "",
        cluster_name: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Cluster API MachineHealthChecks."""
        return json.dumps(capi_machinehealthchecks_list(namespace, cluster_name, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_clusterclasses_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Cluster API ClusterClasses."""
        return json.dumps(capi_clusterclasses_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_cluster_kubeconfig_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get kubeconfig secret info for a CAPI cluster."""
        return json.dumps(capi_cluster_kubeconfig(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def capi_detect_tool(context: str = "") -> str:
        """Detect if Cluster API is installed and its components."""
        return json.dumps(capi_detect(context), indent=2)
