"""vind (vCluster in Docker) toolset for kubectl-mcp-server.

vind enables running Kubernetes clusters directly as Docker containers,
combining vCluster with Docker's simplicity. Uses the standard vCluster CLI.
"""

import subprocess
import json
import re
from typing import Dict, Any, List, Optional

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations


def _vcluster_available() -> bool:
    """Check if vcluster CLI is available."""
    try:
        result = subprocess.run(
            ["vcluster", "version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def _get_vcluster_version() -> Optional[str]:
    """Get vcluster CLI version."""
    try:
        result = subprocess.run(
            ["vcluster", "version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            match = re.search(r'v?\d+\.\d+\.\d+', output)
            if match:
                return match.group(0)
            return output
        return None
    except Exception:
        return None


def _run_vcluster(
    args: List[str],
    timeout: int = 120,
    json_output: bool = False
) -> Dict[str, Any]:
    """Run vcluster command and return result.

    Args:
        args: Command arguments (without 'vcluster' prefix)
        timeout: Command timeout in seconds
        json_output: Whether to add --output json flag

    Returns:
        Result dict with success status and output/error
    """
    if not _vcluster_available():
        return {
            "success": False,
            "error": "vcluster CLI not available. Install from: https://www.vcluster.com/docs/getting-started/setup"
        }

    cmd = ["vcluster"] + args
    if json_output and "--output" not in args:
        cmd.extend(["--output", "json"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if json_output and output:
                try:
                    return {"success": True, "data": json.loads(output)}
                except json.JSONDecodeError:
                    return {"success": True, "output": output}
            return {"success": True, "output": output}
        return {
            "success": False,
            "error": result.stderr.strip() or f"Command failed with exit code {result.returncode}"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout} seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def vind_detect() -> Dict[str, Any]:
    """Detect if vCluster CLI is installed and get version info.

    Returns:
        Detection results including CLI availability and version
    """
    available = _vcluster_available()
    version = _get_vcluster_version() if available else None

    return {
        "installed": available,
        "cli_available": available,
        "version": version,
        "install_instructions": "https://www.vcluster.com/docs/getting-started/setup" if not available else None
    }


def vind_list_clusters() -> Dict[str, Any]:
    """List all vCluster instances.

    Returns:
        List of vCluster instances with their status
    """
    result = _run_vcluster(["list"], json_output=True, timeout=30)

    if not result["success"]:
        return result

    clusters = []
    data = result.get("data") or result.get("output", "")

    if isinstance(data, str) and data:
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    if isinstance(data, list):
        for cluster in data:
            clusters.append({
                "name": cluster.get("Name", cluster.get("name", "")),
                "namespace": cluster.get("Namespace", cluster.get("namespace", "")),
                "status": cluster.get("Status", cluster.get("status", "")),
                "version": cluster.get("Version", cluster.get("version", "")),
                "connected": cluster.get("Connected", cluster.get("connected", False)),
                "created": cluster.get("Created", cluster.get("created", "")),
                "age": cluster.get("Age", cluster.get("age", "")),
            })
    elif isinstance(data, str) and data:
        return {"success": True, "output": data, "clusters": []}

    return {
        "success": True,
        "total": len(clusters),
        "clusters": clusters
    }


def vind_status(name: str, namespace: str = "vcluster") -> Dict[str, Any]:
    """Get detailed status of a vCluster instance.

    Args:
        name: Name of the vCluster instance
        namespace: Namespace where vCluster is running (default: vcluster)

    Returns:
        Detailed status information
    """
    result = _run_vcluster(
        ["list"],
        timeout=30,
        json_output=True,
    )

    if not result["success"]:
        return result

    data = result.get("data") or []
    if isinstance(data, list):
        for cluster in data:
            cluster_name = cluster.get("Name", cluster.get("name", ""))
            cluster_ns = cluster.get("Namespace", cluster.get("namespace", ""))
            if cluster_name == name and (not namespace or cluster_ns == namespace):
                return {
                    "success": True,
                    "cluster": {
                        "name": cluster_name,
                        "namespace": cluster_ns,
                        "status": cluster.get("Status", cluster.get("status", "")),
                        "version": cluster.get("Version", cluster.get("version", "")),
                        "connected": cluster.get("Connected", cluster.get("connected", False)),
                        "created": cluster.get("Created", cluster.get("created", "")),
                        "age": cluster.get("Age", cluster.get("age", "")),
                        "pro": cluster.get("Pro", cluster.get("pro", False)),
                    }
                }

    return {
        "success": False,
        "error": f"vCluster '{name}' not found in namespace '{namespace}'"
    }


def vind_get_kubeconfig(
    name: str,
    namespace: str = "vcluster",
    print_only: bool = True
) -> Dict[str, Any]:
    """Get kubeconfig for a vCluster instance.

    Args:
        name: Name of the vCluster instance
        namespace: Namespace where vCluster is running
        print_only: Only print kubeconfig without modifying local config

    Returns:
        Kubeconfig content or path
    """
    args = ["connect", name, "--namespace", namespace]
    if print_only:
        args.append("--print")

    result = _run_vcluster(args, timeout=60)

    if result["success"] and print_only:
        return {
            "success": True,
            "kubeconfig": result.get("output", ""),
            "message": f"Kubeconfig for vCluster '{name}'"
        }

    return result


def vind_logs(
    name: str,
    namespace: str = "vcluster",
    follow: bool = False,
    tail: int = 100
) -> Dict[str, Any]:
    """Get logs from a vCluster instance.

    Args:
        name: Name of the vCluster instance
        namespace: Namespace where vCluster is running
        follow: Follow log output (not recommended for API use)
        tail: Number of lines to show

    Returns:
        Log output
    """
    args = ["logs", name, "--namespace", namespace]
    if tail:
        args.extend(["--tail", str(tail)])

    result = _run_vcluster(args, timeout=60)
    return result


def vind_create_cluster(
    name: str,
    namespace: str = "",
    kubernetes_version: str = "",
    values_file: str = "",
    set_values: List[str] = None,
    connect: bool = True,
    upgrade: bool = False
) -> Dict[str, Any]:
    """Create a new vCluster instance.

    Args:
        name: Name for the new vCluster
        namespace: Namespace to create vCluster in (default: vcluster-<name>)
        kubernetes_version: Kubernetes version (e.g., "v1.29.0")
        values_file: Path to values.yaml file
        set_values: List of Helm-style value overrides (e.g., ["key=value"])
        connect: Update kubeconfig and switch context after creation
        upgrade: Upgrade existing vCluster instead of failing

    Returns:
        Creation result
    """
    args = ["create", name]

    if namespace:
        args.extend(["--namespace", namespace])

    if kubernetes_version:
        args.extend(["--kubernetes-version", kubernetes_version])

    if values_file:
        args.extend(["--values", values_file])

    if set_values:
        for val in set_values:
            args.extend(["--set", val])

    if connect:
        args.append("--connect")
    else:
        args.append("--connect=false")

    if upgrade:
        args.append("--upgrade")

    result = _run_vcluster(args, timeout=300)

    if result["success"]:
        return {
            "success": True,
            "message": f"vCluster '{name}' created successfully",
            "output": result.get("output", ""),
            "connected": connect
        }

    return result


def vind_delete_cluster(
    name: str,
    namespace: str = "",
    delete_namespace: bool = False,
    force: bool = False
) -> Dict[str, Any]:
    """Delete a vCluster instance.

    Args:
        name: Name of the vCluster to delete
        namespace: Namespace of the vCluster
        delete_namespace: Also delete the namespace
        force: Force deletion

    Returns:
        Deletion result
    """
    args = ["delete", name]

    if namespace:
        args.extend(["--namespace", namespace])

    if delete_namespace:
        args.append("--delete-namespace")

    if force:
        args.append("--force")

    result = _run_vcluster(args, timeout=120)

    if result["success"]:
        return {
            "success": True,
            "message": f"vCluster '{name}' deleted successfully",
            "output": result.get("output", "")
        }

    return result


def vind_pause(name: str, namespace: str = "") -> Dict[str, Any]:
    """Pause/sleep a vCluster instance to save resources.

    Args:
        name: Name of the vCluster to pause
        namespace: Namespace of the vCluster

    Returns:
        Pause result
    """
    args = ["pause", name]

    if namespace:
        args.extend(["--namespace", namespace])

    result = _run_vcluster(args, timeout=120)

    if result["success"]:
        return {
            "success": True,
            "message": f"vCluster '{name}' paused successfully",
            "output": result.get("output", "")
        }

    return result


def vind_resume(name: str, namespace: str = "") -> Dict[str, Any]:
    """Resume/wake a sleeping vCluster instance.

    Args:
        name: Name of the vCluster to resume
        namespace: Namespace of the vCluster

    Returns:
        Resume result
    """
    args = ["resume", name]

    if namespace:
        args.extend(["--namespace", namespace])

    result = _run_vcluster(args, timeout=120)

    if result["success"]:
        return {
            "success": True,
            "message": f"vCluster '{name}' resumed successfully",
            "output": result.get("output", "")
        }

    return result


def vind_connect(
    name: str,
    namespace: str = "",
    update_current: bool = True,
    kube_config: str = "",
    background_proxy: bool = True
) -> Dict[str, Any]:
    """Connect kubectl to a vCluster instance.

    Args:
        name: Name of the vCluster
        namespace: Namespace of the vCluster
        update_current: Update current kubeconfig context
        kube_config: Path to kubeconfig file to update
        background_proxy: Use background proxy to avoid blocking (default: True)

    Returns:
        Connection result
    """
    args = ["connect", name]

    if namespace:
        args.extend(["--namespace", namespace])

    if not update_current:
        args.append("--update-current=false")

    if kube_config:
        args.extend(["--kube-config", kube_config])

    if background_proxy:
        args.append("--background-proxy")

    result = _run_vcluster(args, timeout=60)

    if result["success"]:
        return {
            "success": True,
            "message": f"Connected to vCluster '{name}'",
            "output": result.get("output", "")
        }

    return result


def vind_disconnect(name: str, namespace: str = "") -> Dict[str, Any]:
    """Disconnect from a vCluster instance.

    Args:
        name: Name of the vCluster
        namespace: Namespace of the vCluster

    Returns:
        Disconnection result
    """
    args = ["disconnect"]

    result = _run_vcluster(args, timeout=30)

    if result["success"]:
        return {
            "success": True,
            "message": "Disconnected from vCluster",
            "output": result.get("output", "")
        }

    return result


def vind_upgrade(
    name: str,
    namespace: str = "",
    kubernetes_version: str = "",
    values_file: str = "",
    set_values: List[str] = None
) -> Dict[str, Any]:
    """Upgrade a vCluster instance.

    Args:
        name: Name of the vCluster to upgrade
        namespace: Namespace of the vCluster
        kubernetes_version: New Kubernetes version
        values_file: Path to values.yaml file
        set_values: List of Helm-style value overrides

    Returns:
        Upgrade result
    """
    args = ["create", name, "--upgrade"]

    if namespace:
        args.extend(["--namespace", namespace])

    if kubernetes_version:
        args.extend(["--kubernetes-version", kubernetes_version])

    if values_file:
        args.extend(["--values", values_file])

    if set_values:
        for val in set_values:
            args.extend(["--set", val])

    result = _run_vcluster(args, timeout=300)

    if result["success"]:
        return {
            "success": True,
            "message": f"vCluster '{name}' upgraded successfully",
            "output": result.get("output", "")
        }

    return result


def vind_describe(name: str, namespace: str = "") -> Dict[str, Any]:
    """Describe a vCluster instance with detailed information.

    Args:
        name: Name of the vCluster
        namespace: Namespace of the vCluster

    Returns:
        Detailed cluster information
    """
    args = ["describe", name]

    if namespace:
        args.extend(["--namespace", namespace])

    result = _run_vcluster(args, timeout=60)
    return result


def vind_platform_start(
    host: str = "",
    port: int = 0,
    no_port_forwarding: bool = True
) -> Dict[str, Any]:
    """Start the vCluster Platform UI.

    Args:
        host: Host to bind to (default: localhost)
        port: Port to bind to (default: 9898)
        no_port_forwarding: Don't start port-forwarding (install only, default: True)

    Returns:
        Platform start result
    """
    args = ["platform", "start"]

    if host:
        args.extend(["--host", host])

    if port:
        args.extend(["--port", str(port)])

    if no_port_forwarding:
        args.append("--no-port-forwarding")

    result = _run_vcluster(args, timeout=60)

    if result["success"]:
        return {
            "success": True,
            "message": "vCluster Platform started",
            "output": result.get("output", "")
        }

    return result


def register_vind_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register vind (vCluster in Docker) tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def vind_detect_tool() -> str:
        """Detect if vCluster CLI is installed and get version info."""
        return json.dumps(vind_detect(), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def vind_list_clusters_tool() -> str:
        """List all vCluster instances."""
        return json.dumps(vind_list_clusters(), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def vind_status_tool(
        name: str,
        namespace: str = "vcluster"
    ) -> str:
        """Get detailed status of a vCluster instance."""
        return json.dumps(vind_status(name, namespace), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def vind_get_kubeconfig_tool(
        name: str,
        namespace: str = "vcluster"
    ) -> str:
        """Get kubeconfig for a vCluster instance."""
        return json.dumps(vind_get_kubeconfig(name, namespace, print_only=True), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def vind_logs_tool(
        name: str,
        namespace: str = "vcluster",
        tail: int = 100
    ) -> str:
        """Get logs from a vCluster instance."""
        return json.dumps(vind_logs(name, namespace, follow=False, tail=tail), indent=2)

    @mcp.tool()
    def vind_create_cluster_tool(
        name: str,
        namespace: str = "",
        kubernetes_version: str = "",
        values_file: str = "",
        set_values: str = "",
        connect: bool = True,
        upgrade: bool = False
    ) -> str:
        """Create a new vCluster instance.

        Args:
            name: Name for the new vCluster
            namespace: Namespace to create vCluster in
            kubernetes_version: Kubernetes version (e.g., "v1.29.0")
            values_file: Path to values.yaml file
            set_values: Comma-separated Helm-style value overrides
            connect: Update kubeconfig after creation
            upgrade: Upgrade existing vCluster instead of failing
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})

        values_list = [v.strip() for v in set_values.split(",") if v.strip()] if set_values else None
        return json.dumps(
            vind_create_cluster(name, namespace, kubernetes_version, values_file, values_list, connect, upgrade),
            indent=2
        )

    @mcp.tool()
    def vind_delete_cluster_tool(
        name: str,
        namespace: str = "",
        delete_namespace: bool = False,
        force: bool = False
    ) -> str:
        """Delete a vCluster instance."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(vind_delete_cluster(name, namespace, delete_namespace, force), indent=2)

    @mcp.tool()
    def vind_pause_tool(
        name: str,
        namespace: str = ""
    ) -> str:
        """Pause/sleep a vCluster instance to save resources."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(vind_pause(name, namespace), indent=2)

    @mcp.tool()
    def vind_resume_tool(
        name: str,
        namespace: str = ""
    ) -> str:
        """Resume/wake a sleeping vCluster instance."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(vind_resume(name, namespace), indent=2)

    @mcp.tool()
    def vind_connect_tool(
        name: str,
        namespace: str = "",
        kube_config: str = ""
    ) -> str:
        """Connect kubectl to a vCluster instance."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(vind_connect(name, namespace, True, kube_config), indent=2)

    @mcp.tool()
    def vind_disconnect_tool() -> str:
        """Disconnect from a vCluster instance."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(vind_disconnect("", ""), indent=2)

    @mcp.tool()
    def vind_upgrade_tool(
        name: str,
        namespace: str = "",
        kubernetes_version: str = "",
        values_file: str = "",
        set_values: str = ""
    ) -> str:
        """Upgrade a vCluster instance.

        Args:
            name: Name of the vCluster to upgrade
            namespace: Namespace of the vCluster
            kubernetes_version: New Kubernetes version
            values_file: Path to values.yaml file
            set_values: Comma-separated Helm-style value overrides
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})

        values_list = [v.strip() for v in set_values.split(",") if v.strip()] if set_values else None
        return json.dumps(vind_upgrade(name, namespace, kubernetes_version, values_file, values_list), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def vind_describe_tool(
        name: str,
        namespace: str = ""
    ) -> str:
        """Describe a vCluster instance with detailed information."""
        return json.dumps(vind_describe(name, namespace), indent=2)

    @mcp.tool()
    def vind_platform_start_tool(
        host: str = "",
        port: int = 0
    ) -> str:
        """Start the vCluster Platform UI."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(vind_platform_start(host, port), indent=2)
