"""KubeVirt VM lifecycle toolset for kubectl-mcp-server."""

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


VM_CRD = "virtualmachines.kubevirt.io"
VMI_CRD = "virtualmachineinstances.kubevirt.io"
VMIPRESET_CRD = "virtualmachineinstancepresets.kubevirt.io"
VMIRS_CRD = "virtualmachineinstancereplicasets.kubevirt.io"
VMPOOL_CRD = "virtualmachinepools.pool.kubevirt.io"
DATASOURCE_CRD = "datasources.cdi.kubevirt.io"
DATAVOLUME_CRD = "datavolumes.cdi.kubevirt.io"
VMCLONE_CRD = "virtualmachineclones.clone.kubevirt.io"
INSTANCETYPE_CRD = "virtualmachineinstancetypes.instancetype.kubevirt.io"
CLUSTERINSTANCETYPE_CRD = "virtualmachineclusterinstancetypes.instancetype.kubevirt.io"
PREFERENCE_CRD = "virtualmachinepreferences.instancetype.kubevirt.io"


def _virtctl_available() -> bool:
    """Check if virtctl CLI is available."""
    try:
        result = subprocess.run(["virtctl", "version", "--client"],
                                capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def _run_virtctl(args: List[str], context: str = "") -> Dict[str, Any]:
    """Run virtctl command if available."""
    if not _virtctl_available():
        return {"success": False, "error": "virtctl CLI not available"}

    cmd = ["virtctl"] + args
    if context:
        cmd.extend(["--context", context])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        return {"success": False, "error": result.stderr}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def kubevirt_vms_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List KubeVirt VirtualMachines.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter VMs

    Returns:
        List of VirtualMachines with their status
    """
    if not crd_exists(VM_CRD, context):
        return {
            "success": False,
            "error": "KubeVirt is not installed (virtualmachines.kubevirt.io CRD not found)"
        }

    vms = []
    for item in get_resources("virtualmachines.kubevirt.io", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        paused_cond = next((c for c in conditions if c.get("type") == "Paused"), {})

        # Get resource info from template
        template = spec.get("template", {}).get("spec", {})
        domain = template.get("domain", {})
        resources = domain.get("resources", {})
        cpu = domain.get("cpu", {})

        vms.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "running": spec.get("running", False),
            "run_strategy": spec.get("runStrategy"),
            "ready": ready_cond.get("status") == "True",
            "paused": paused_cond.get("status") == "True",
            "print_status": status.get("printableStatus", "Unknown"),
            "created": status.get("created", False),
            "cpu_cores": cpu.get("cores", 1),
            "cpu_sockets": cpu.get("sockets", 1),
            "cpu_threads": cpu.get("threads", 1),
            "memory": resources.get("requests", {}).get("memory", ""),
            "volume_count": len(template.get("volumes", [])),
            "network_count": len(template.get("networks", [])),
            "state_change_requests": status.get("stateChangeRequests", []),
        })

    # Summary
    running = sum(1 for v in vms if v["running"])
    ready = sum(1 for v in vms if v["ready"])

    return {
        "context": context or "current",
        "total": len(vms),
        "running": running,
        "ready": ready,
        "vms": vms,
    }


def kubevirt_vm_get(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a VirtualMachine.

    Args:
        name: Name of the VM
        namespace: Namespace of the VM
        context: Kubernetes context to use (optional)

    Returns:
        Detailed VM information
    """
    if not crd_exists(VM_CRD, context):
        return {"success": False, "error": "KubeVirt is not installed"}

    args = ["get", "virtualmachines.kubevirt.io", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "vm": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def kubevirt_vmis_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List KubeVirt VirtualMachineInstances (running VMs).

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter VMIs

    Returns:
        List of running VirtualMachineInstances
    """
    if not crd_exists(VMI_CRD, context):
        return {
            "success": False,
            "error": "KubeVirt is not installed"
        }

    vmis = []
    for item in get_resources("virtualmachineinstances.kubevirt.io", namespace, context, label_selector):
        status = item.get("status", {})
        spec = item.get("spec", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        live_migratable = next((c for c in conditions if c.get("type") == "LiveMigratable"), {})

        domain = spec.get("domain", {})
        resources = domain.get("resources", {})

        # Get guest info if available
        guest_info = status.get("guestOSInfo", {})

        vmis.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "ready": ready_cond.get("status") == "True",
            "live_migratable": live_migratable.get("status") == "True",
            "node": status.get("nodeName", ""),
            "ip_addresses": [iface.get("ipAddress") for iface in status.get("interfaces", []) if iface.get("ipAddress")],
            "memory": resources.get("requests", {}).get("memory", ""),
            "guest_os": guest_info.get("name", ""),
            "guest_os_version": guest_info.get("version", ""),
            "migration_state": status.get("migrationState"),
            "active_pods": status.get("activePods", {}),
        })

    # Summary
    running = sum(1 for v in vmis if v["phase"] == "Running")
    scheduled = sum(1 for v in vmis if v["phase"] == "Scheduled")

    return {
        "context": context or "current",
        "total": len(vmis),
        "running": running,
        "scheduled": scheduled,
        "vmis": vmis,
    }


def kubevirt_vm_start(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Start a VirtualMachine.

    Args:
        name: Name of the VM
        namespace: Namespace of the VM
        context: Kubernetes context to use (optional)

    Returns:
        Start result
    """
    if not crd_exists(VM_CRD, context):
        return {"success": False, "error": "KubeVirt is not installed"}

    # Try virtctl first
    if _virtctl_available():
        result = _run_virtctl(["start", name, "-n", namespace], context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Started VM {name}",
                "output": result.get("output", ""),
            }
        # Don't return error, fall through to patch

    # Fallback to patching
    patch = {"spec": {"running": True}}
    args = [
        "patch", "virtualmachines.kubevirt.io", name,
        "-n", namespace,
        "--type=merge",
        "-p", json.dumps(patch)
    ]
    result = run_kubectl(args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Started VM {name}",
        }

    return {"success": False, "error": result.get("error", "Failed to start VM")}


def kubevirt_vm_stop(
    name: str,
    namespace: str,
    force: bool = False,
    context: str = ""
) -> Dict[str, Any]:
    """Stop a VirtualMachine.

    Args:
        name: Name of the VM
        namespace: Namespace of the VM
        force: Force stop (like pulling the power)
        context: Kubernetes context to use (optional)

    Returns:
        Stop result
    """
    if not crd_exists(VM_CRD, context):
        return {"success": False, "error": "KubeVirt is not installed"}

    # Try virtctl first
    if _virtctl_available():
        cmd = ["stop", name, "-n", namespace]
        if force:
            cmd.append("--force")
        result = _run_virtctl(cmd, context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Stopped VM {name}" + (" (forced)" if force else ""),
                "output": result.get("output", ""),
            }

    # Fallback to patching
    patch = {"spec": {"running": False}}
    args = [
        "patch", "virtualmachines.kubevirt.io", name,
        "-n", namespace,
        "--type=merge",
        "-p", json.dumps(patch)
    ]
    result = run_kubectl(args, context)

    if result["success"]:
        return {
            "success": True,
            "context": context or "current",
            "message": f"Stopped VM {name}",
        }

    return {"success": False, "error": result.get("error", "Failed to stop VM")}


def kubevirt_vm_restart(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Restart a VirtualMachine.

    Args:
        name: Name of the VM
        namespace: Namespace of the VM
        context: Kubernetes context to use (optional)

    Returns:
        Restart result
    """
    if not crd_exists(VM_CRD, context):
        return {"success": False, "error": "KubeVirt is not installed"}

    if _virtctl_available():
        result = _run_virtctl(["restart", name, "-n", namespace], context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Restarted VM {name}",
                "output": result.get("output", ""),
            }
        return {"success": False, "error": result.get("error", "Failed to restart")}

    return {"success": False, "error": "virtctl CLI required for restart operation"}


def kubevirt_vm_pause(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Pause a VirtualMachine.

    Args:
        name: Name of the VM
        namespace: Namespace of the VM
        context: Kubernetes context to use (optional)

    Returns:
        Pause result
    """
    if not crd_exists(VM_CRD, context):
        return {"success": False, "error": "KubeVirt is not installed"}

    if _virtctl_available():
        result = _run_virtctl(["pause", "vm", name, "-n", namespace], context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Paused VM {name}",
                "output": result.get("output", ""),
            }
        return {"success": False, "error": result.get("error", "Failed to pause")}

    return {"success": False, "error": "virtctl CLI required for pause operation"}


def kubevirt_vm_unpause(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Unpause a VirtualMachine.

    Args:
        name: Name of the VM
        namespace: Namespace of the VM
        context: Kubernetes context to use (optional)

    Returns:
        Unpause result
    """
    if not crd_exists(VM_CRD, context):
        return {"success": False, "error": "KubeVirt is not installed"}

    if _virtctl_available():
        result = _run_virtctl(["unpause", "vm", name, "-n", namespace], context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Unpaused VM {name}",
                "output": result.get("output", ""),
            }
        return {"success": False, "error": result.get("error", "Failed to unpause")}

    return {"success": False, "error": "virtctl CLI required for unpause operation"}


def kubevirt_vm_migrate(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Trigger live migration of a VirtualMachineInstance.

    Args:
        name: Name of the VM
        namespace: Namespace of the VM
        context: Kubernetes context to use (optional)

    Returns:
        Migration result
    """
    if not crd_exists(VM_CRD, context):
        return {"success": False, "error": "KubeVirt is not installed"}

    if _virtctl_available():
        result = _run_virtctl(["migrate", name, "-n", namespace], context)
        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Triggered migration for VM {name}",
                "output": result.get("output", ""),
            }
        return {"success": False, "error": result.get("error", "Failed to migrate")}

    return {"success": False, "error": "virtctl CLI required for migration operation"}


def kubevirt_datasources_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List KubeVirt DataSources (for disk images).

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of DataSources
    """
    if not crd_exists(DATASOURCE_CRD, context):
        return {
            "success": False,
            "error": "CDI DataSources CRD not found"
        }

    datasources = []
    for item in get_resources("datasources.cdi.kubevirt.io", namespace, context, label_selector):
        spec = item.get("spec", {})
        status = item.get("status", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        source = spec.get("source", {})

        datasources.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "ready": ready_cond.get("status") == "True",
            "source_pvc": source.get("pvc", {}),
            "source_snapshot": source.get("snapshot", {}),
        })

    return {
        "context": context or "current",
        "total": len(datasources),
        "datasources": datasources,
    }


def kubevirt_instancetypes_list(
    namespace: str = "",
    context: str = "",
    include_cluster: bool = True
) -> Dict[str, Any]:
    """List KubeVirt InstanceTypes (VM sizing templates).

    Args:
        namespace: Filter by namespace (empty for all)
        context: Kubernetes context to use (optional)
        include_cluster: Include cluster-wide instance types

    Returns:
        List of InstanceTypes
    """
    instancetypes = []

    if crd_exists(INSTANCETYPE_CRD, context):
        for item in get_resources("virtualmachineinstancetypes.instancetype.kubevirt.io", namespace, context):
            spec = item.get("spec", {})
            cpu = spec.get("cpu", {})
            memory = spec.get("memory", {})

            instancetypes.append({
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "kind": "VirtualMachineInstancetype",
                "cpu_guest": cpu.get("guest", 1),
                "cpu_model": cpu.get("model"),
                "memory_guest": memory.get("guest", ""),
                "memory_hugepages": memory.get("hugepages", {}),
            })

    if include_cluster and crd_exists(CLUSTERINSTANCETYPE_CRD, context):
        for item in get_resources("virtualmachineclusterinstancetypes.instancetype.kubevirt.io", "", context):
            spec = item.get("spec", {})
            cpu = spec.get("cpu", {})
            memory = spec.get("memory", {})

            instancetypes.append({
                "name": item["metadata"]["name"],
                "namespace": "",
                "kind": "VirtualMachineClusterInstancetype",
                "cpu_guest": cpu.get("guest", 1),
                "cpu_model": cpu.get("model"),
                "memory_guest": memory.get("guest", ""),
                "memory_hugepages": memory.get("hugepages", {}),
            })

    return {
        "context": context or "current",
        "total": len(instancetypes),
        "instancetypes": instancetypes,
    }


def kubevirt_datavolumes_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List KubeVirt DataVolumes (disk images).

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of DataVolumes
    """
    if not crd_exists(DATAVOLUME_CRD, context):
        return {
            "success": False,
            "error": "CDI DataVolumes CRD not found"
        }

    datavolumes = []
    for item in get_resources("datavolumes.cdi.kubevirt.io", namespace, context, label_selector):
        spec = item.get("spec", {})
        status = item.get("status", {})
        conditions = status.get("conditions", [])

        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        bound_cond = next((c for c in conditions if c.get("type") == "Bound"), {})

        source = spec.get("source", {})
        source_type = list(source.keys())[0] if source else "unknown"

        datavolumes.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "phase": status.get("phase", "Unknown"),
            "ready": ready_cond.get("status") == "True",
            "bound": bound_cond.get("status") == "True",
            "progress": status.get("progress", "N/A"),
            "source_type": source_type,
            "storage_size": spec.get("pvc", {}).get("resources", {}).get("requests", {}).get("storage", ""),
            "storage_class": spec.get("pvc", {}).get("storageClassName", ""),
        })

    return {
        "context": context or "current",
        "total": len(datavolumes),
        "datavolumes": datavolumes,
    }


def kubevirt_detect(context: str = "") -> Dict[str, Any]:
    """Detect if KubeVirt is installed and its components.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for KubeVirt
    """
    return {
        "context": context or "current",
        "installed": crd_exists(VM_CRD, context),
        "cli_available": _virtctl_available(),
        "crds": {
            "virtualmachines": crd_exists(VM_CRD, context),
            "virtualmachineinstances": crd_exists(VMI_CRD, context),
            "virtualmachineinstancepresets": crd_exists(VMIPRESET_CRD, context),
            "virtualmachineinstancereplicasets": crd_exists(VMIRS_CRD, context),
            "datasources": crd_exists(DATASOURCE_CRD, context),
            "datavolumes": crd_exists(DATAVOLUME_CRD, context),
            "instancetypes": crd_exists(INSTANCETYPE_CRD, context),
            "clusterinstancetypes": crd_exists(CLUSTERINSTANCETYPE_CRD, context),
        },
    }


def register_kubevirt_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register KubeVirt tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kubevirt_vms_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List KubeVirt VirtualMachines."""
        return json.dumps(kubevirt_vms_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kubevirt_vm_get_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get detailed information about a VirtualMachine."""
        return json.dumps(kubevirt_vm_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kubevirt_vmis_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List running VirtualMachineInstances."""
        return json.dumps(kubevirt_vmis_list(namespace, context, label_selector), indent=2)

    @mcp.tool()
    def kubevirt_vm_start_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Start a VirtualMachine."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kubevirt_vm_start(name, namespace, context), indent=2)

    @mcp.tool()
    def kubevirt_vm_stop_tool(
        name: str,
        namespace: str,
        force: bool = False,
        context: str = ""
    ) -> str:
        """Stop a VirtualMachine."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kubevirt_vm_stop(name, namespace, force, context), indent=2)

    @mcp.tool()
    def kubevirt_vm_restart_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Restart a VirtualMachine."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kubevirt_vm_restart(name, namespace, context), indent=2)

    @mcp.tool()
    def kubevirt_vm_pause_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Pause a VirtualMachine."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kubevirt_vm_pause(name, namespace, context), indent=2)

    @mcp.tool()
    def kubevirt_vm_unpause_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Unpause a VirtualMachine."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kubevirt_vm_unpause(name, namespace, context), indent=2)

    @mcp.tool()
    def kubevirt_vm_migrate_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Trigger live migration of a VirtualMachine."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kubevirt_vm_migrate(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kubevirt_datasources_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List KubeVirt DataSources."""
        return json.dumps(kubevirt_datasources_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kubevirt_instancetypes_list_tool(
        namespace: str = "",
        context: str = "",
        include_cluster: bool = True
    ) -> str:
        """List KubeVirt InstanceTypes (VM sizing templates)."""
        return json.dumps(kubevirt_instancetypes_list(namespace, context, include_cluster), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kubevirt_datavolumes_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List KubeVirt DataVolumes (disk images)."""
        return json.dumps(kubevirt_datavolumes_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kubevirt_detect_tool(context: str = "") -> str:
        """Detect if KubeVirt is installed and its components."""
        return json.dumps(kubevirt_detect(context), indent=2)
