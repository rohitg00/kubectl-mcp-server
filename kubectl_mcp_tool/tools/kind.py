"""kind (Kubernetes IN Docker) toolset for kubectl-mcp-server.

kind enables running local Kubernetes clusters using Docker container "nodes".
It's a tool from Kubernetes SIG for local development and CI testing.
"""

import subprocess
import json
import re
import os
import tempfile
from typing import Dict, Any, List, Optional

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations


def _kind_available() -> bool:
    """Check if kind CLI is available."""
    try:
        result = subprocess.run(
            ["kind", "version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def _get_kind_version() -> Optional[str]:
    """Get kind CLI version."""
    try:
        result = subprocess.run(
            ["kind", "version"],
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


def _run_kind(
    args: List[str],
    timeout: int = 300,
    capture_output: bool = True
) -> Dict[str, Any]:
    """Run kind command and return result.

    Args:
        args: Command arguments (without 'kind' prefix)
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        Result dict with success status and output/error
    """
    if not _kind_available():
        return {
            "success": False,
            "error": "kind CLI not available. Install from: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
        }

    cmd = ["kind"] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            output = result.stdout.strip() if capture_output else ""
            return {"success": True, "output": output}
        return {
            "success": False,
            "error": result.stderr.strip() if capture_output else f"Command failed with exit code {result.returncode}"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout} seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def kind_detect() -> Dict[str, Any]:
    """Detect if kind CLI is installed and get version info.

    Returns:
        Detection results including CLI availability and version
    """
    available = _kind_available()
    version = _get_kind_version() if available else None

    return {
        "installed": available,
        "cli_available": available,
        "version": version,
        "install_instructions": "https://kind.sigs.k8s.io/docs/user/quick-start/#installation" if not available else None
    }


def kind_version() -> Dict[str, Any]:
    """Get kind CLI version information.

    Returns:
        Version information
    """
    result = _run_kind(["version"], timeout=10)
    if result["success"]:
        return {
            "success": True,
            "version": result.get("output", ""),
        }
    return result


def kind_list_clusters() -> Dict[str, Any]:
    """List all kind clusters.

    Returns:
        List of kind cluster names
    """
    result = _run_kind(["get", "clusters"], timeout=30)

    if not result["success"]:
        return result

    output = result.get("output", "")
    clusters = [name.strip() for name in output.split("\n") if name.strip()]

    return {
        "success": True,
        "total": len(clusters),
        "clusters": clusters
    }


def kind_get_nodes(name: str = "kind") -> Dict[str, Any]:
    """List nodes in a kind cluster.

    Args:
        name: Name of the kind cluster (default: kind)

    Returns:
        List of node container names
    """
    result = _run_kind(["get", "nodes", "--name", name], timeout=30)

    if not result["success"]:
        return result

    output = result.get("output", "")
    nodes = [node.strip() for node in output.split("\n") if node.strip()]

    return {
        "success": True,
        "cluster": name,
        "total": len(nodes),
        "nodes": nodes
    }


def kind_get_kubeconfig(name: str = "kind", internal: bool = False) -> Dict[str, Any]:
    """Get kubeconfig for a kind cluster.

    Args:
        name: Name of the kind cluster
        internal: Return internal (container) kubeconfig instead of external

    Returns:
        Kubeconfig content
    """
    args = ["get", "kubeconfig", "--name", name]
    if internal:
        args.append("--internal")

    result = _run_kind(args, timeout=30)

    if result["success"]:
        return {
            "success": True,
            "kubeconfig": result.get("output", ""),
            "message": f"Kubeconfig for kind cluster '{name}'"
        }

    return result


def kind_export_logs(
    name: str = "kind",
    output_dir: str = ""
) -> Dict[str, Any]:
    """Export cluster logs for debugging.

    Args:
        name: Name of the kind cluster
        output_dir: Directory to export logs to (default: temp directory)

    Returns:
        Export result with log location
    """
    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix=f"kind-logs-{name}-")

    args = ["export", "logs", output_dir, "--name", name]
    result = _run_kind(args, timeout=120)

    if result["success"]:
        return {
            "success": True,
            "message": f"Logs exported for cluster '{name}'",
            "log_directory": output_dir,
            "output": result.get("output", "")
        }

    return result


def kind_create_cluster(
    name: str = "kind",
    image: str = "",
    config: str = "",
    wait: str = "5m",
    retain: bool = False,
    kubeconfig: str = ""
) -> Dict[str, Any]:
    """Create a new kind cluster.

    Args:
        name: Name for the new cluster (default: kind)
        image: Node image (determines K8s version, e.g., kindest/node:v1.29.0)
        config: Path to kind config YAML file for multi-node or custom setup
        wait: Wait timeout for control plane (default: 5m)
        retain: Retain nodes on creation failure for debugging
        kubeconfig: Path to kubeconfig file to update

    Returns:
        Creation result
    """
    args = ["create", "cluster", "--name", name]

    if image:
        args.extend(["--image", image])

    if config:
        args.extend(["--config", config])

    if wait:
        args.extend(["--wait", wait])

    if retain:
        args.append("--retain")

    if kubeconfig:
        args.extend(["--kubeconfig", kubeconfig])

    result = _run_kind(args, timeout=600)

    if result["success"]:
        return {
            "success": True,
            "message": f"kind cluster '{name}' created successfully",
            "output": result.get("output", ""),
            "cluster": name
        }

    return result


def kind_delete_cluster(name: str = "kind", kubeconfig: str = "") -> Dict[str, Any]:
    """Delete a kind cluster.

    Args:
        name: Name of the cluster to delete
        kubeconfig: Path to kubeconfig file to update

    Returns:
        Deletion result
    """
    args = ["delete", "cluster", "--name", name]

    if kubeconfig:
        args.extend(["--kubeconfig", kubeconfig])

    result = _run_kind(args, timeout=120)

    if result["success"]:
        return {
            "success": True,
            "message": f"kind cluster '{name}' deleted successfully",
            "output": result.get("output", "")
        }

    return result


def kind_delete_all_clusters(kubeconfig: str = "") -> Dict[str, Any]:
    """Delete all kind clusters.

    Args:
        kubeconfig: Path to kubeconfig file to update

    Returns:
        Deletion result
    """
    args = ["delete", "clusters", "--all"]

    if kubeconfig:
        args.extend(["--kubeconfig", kubeconfig])

    result = _run_kind(args, timeout=300)

    if result["success"]:
        return {
            "success": True,
            "message": "All kind clusters deleted successfully",
            "output": result.get("output", "")
        }

    return result


def kind_load_image(
    images: List[str],
    name: str = "kind",
    nodes: List[str] = None
) -> Dict[str, Any]:
    """Load Docker images into kind cluster nodes.

    This is a key feature for local development - load locally built
    images directly into the cluster without pushing to a registry.

    Args:
        images: List of Docker image names to load
        name: Name of the kind cluster
        nodes: Specific nodes to load images to (default: all nodes)

    Returns:
        Load result
    """
    if not images:
        return {"success": False, "error": "No images specified to load"}

    args = ["load", "docker-image", "--name", name] + images

    if nodes:
        for node in nodes:
            args.extend(["--nodes", node])

    result = _run_kind(args, timeout=300)

    if result["success"]:
        return {
            "success": True,
            "message": f"Loaded {len(images)} image(s) into cluster '{name}'",
            "images": images,
            "output": result.get("output", "")
        }

    return result


def kind_load_image_archive(
    archive: str,
    name: str = "kind",
    nodes: List[str] = None
) -> Dict[str, Any]:
    """Load Docker images from tar archive into kind cluster.

    Args:
        archive: Path to image archive (tar file)
        name: Name of the kind cluster
        nodes: Specific nodes to load images to (default: all nodes)

    Returns:
        Load result
    """
    if not os.path.exists(archive):
        return {"success": False, "error": f"Archive file not found: {archive}"}

    args = ["load", "image-archive", archive, "--name", name]

    if nodes:
        for node in nodes:
            args.extend(["--nodes", node])

    result = _run_kind(args, timeout=300)

    if result["success"]:
        return {
            "success": True,
            "message": f"Loaded images from archive into cluster '{name}'",
            "archive": archive,
            "output": result.get("output", "")
        }

    return result


def kind_build_node_image(
    image: str = "",
    base_image: str = "",
    kube_root: str = ""
) -> Dict[str, Any]:
    """Build a kind node image from Kubernetes source.

    This is an advanced feature for testing custom Kubernetes builds.

    Args:
        image: Name for the resulting image (default: kindest/node:latest)
        base_image: Base image to use
        kube_root: Path to Kubernetes source root

    Returns:
        Build result
    """
    args = ["build", "node-image"]

    if image:
        args.extend(["--image", image])

    if base_image:
        args.extend(["--base-image", base_image])

    if kube_root:
        args.extend(["--kube-root", kube_root])

    result = _run_kind(args, timeout=1800)

    if result["success"]:
        return {
            "success": True,
            "message": "Node image built successfully",
            "image": image or "kindest/node:latest",
            "output": result.get("output", "")
        }

    return result


def kind_cluster_info(name: str = "kind") -> Dict[str, Any]:
    """Get cluster information including nodes and kubeconfig.

    Args:
        name: Name of the kind cluster

    Returns:
        Cluster information
    """
    clusters_result = kind_list_clusters()
    if not clusters_result["success"]:
        return clusters_result

    if name not in clusters_result.get("clusters", []):
        return {
            "success": False,
            "error": f"Cluster '{name}' not found. Available clusters: {clusters_result.get('clusters', [])}"
        }

    nodes_result = kind_get_nodes(name)
    kubeconfig_result = kind_get_kubeconfig(name)

    return {
        "success": True,
        "cluster": name,
        "nodes": nodes_result.get("nodes", []) if nodes_result["success"] else [],
        "node_count": nodes_result.get("total", 0) if nodes_result["success"] else 0,
        "kubeconfig_available": kubeconfig_result["success"],
    }


def kind_node_labels(name: str = "kind") -> Dict[str, Any]:
    """Get node labels for kind cluster nodes.

    Args:
        name: Name of the kind cluster

    Returns:
        Node labels information
    """
    nodes_result = kind_get_nodes(name)
    if not nodes_result["success"]:
        return nodes_result

    node_labels = {}
    for node in nodes_result.get("nodes", []):
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format", '{{json .Config.Labels}}', node],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                labels = json.loads(result.stdout.strip())
                node_labels[node] = labels
            else:
                node_labels[node] = {"error": "Failed to get labels"}
        except Exception as e:
            node_labels[node] = {"error": str(e)}

    return {
        "success": True,
        "cluster": name,
        "node_labels": node_labels
    }


def register_kind_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register kind (Kubernetes IN Docker) tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_detect_tool() -> str:
        """Detect if kind CLI is installed and get version info."""
        return json.dumps(kind_detect(), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_version_tool() -> str:
        """Get kind CLI version information."""
        return json.dumps(kind_version(), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_list_clusters_tool() -> str:
        """List all kind clusters."""
        return json.dumps(kind_list_clusters(), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_get_nodes_tool(name: str = "kind") -> str:
        """List nodes in a kind cluster.

        Args:
            name: Name of the kind cluster (default: kind)
        """
        return json.dumps(kind_get_nodes(name), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_get_kubeconfig_tool(
        name: str = "kind",
        internal: bool = False
    ) -> str:
        """Get kubeconfig for a kind cluster.

        Args:
            name: Name of the kind cluster
            internal: Return internal (container) kubeconfig instead of external
        """
        return json.dumps(kind_get_kubeconfig(name, internal), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_export_logs_tool(
        name: str = "kind",
        output_dir: str = ""
    ) -> str:
        """Export cluster logs for debugging.

        Args:
            name: Name of the kind cluster
            output_dir: Directory to export logs to (default: temp directory)
        """
        return json.dumps(kind_export_logs(name, output_dir), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_cluster_info_tool(name: str = "kind") -> str:
        """Get cluster information including nodes and kubeconfig.

        Args:
            name: Name of the kind cluster
        """
        return json.dumps(kind_cluster_info(name), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_node_labels_tool(name: str = "kind") -> str:
        """Get node labels for kind cluster nodes.

        Args:
            name: Name of the kind cluster
        """
        return json.dumps(kind_node_labels(name), indent=2)

    @mcp.tool()
    def kind_create_cluster_tool(
        name: str = "kind",
        image: str = "",
        config: str = "",
        wait: str = "5m",
        retain: bool = False
    ) -> str:
        """Create a new kind cluster.

        Args:
            name: Name for the new cluster (default: kind)
            image: Node image (determines K8s version, e.g., kindest/node:v1.29.0)
            config: Path to kind config YAML file for multi-node or custom setup
            wait: Wait timeout for control plane (default: 5m)
            retain: Retain nodes on creation failure for debugging
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_create_cluster(name, image, config, wait, retain), indent=2)

    @mcp.tool()
    def kind_delete_cluster_tool(name: str = "kind") -> str:
        """Delete a kind cluster.

        Args:
            name: Name of the cluster to delete
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_delete_cluster(name), indent=2)

    @mcp.tool()
    def kind_delete_all_clusters_tool() -> str:
        """Delete all kind clusters."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_delete_all_clusters(), indent=2)

    @mcp.tool()
    def kind_load_image_tool(
        images: str,
        name: str = "kind"
    ) -> str:
        """Load Docker images into kind cluster nodes.

        This is a key feature for local development - load locally built
        images directly into the cluster without pushing to a registry.

        Args:
            images: Comma-separated list of Docker image names to load
            name: Name of the kind cluster
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        image_list = [img.strip() for img in images.split(",") if img.strip()]
        return json.dumps(kind_load_image(image_list, name), indent=2)

    @mcp.tool()
    def kind_load_image_archive_tool(
        archive: str,
        name: str = "kind"
    ) -> str:
        """Load Docker images from tar archive into kind cluster.

        Args:
            archive: Path to image archive (tar file)
            name: Name of the kind cluster
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_load_image_archive(archive, name), indent=2)

    @mcp.tool()
    def kind_build_node_image_tool(
        image: str = "",
        base_image: str = "",
        kube_root: str = ""
    ) -> str:
        """Build a kind node image from Kubernetes source.

        This is an advanced feature for testing custom Kubernetes builds.

        Args:
            image: Name for the resulting image (default: kindest/node:latest)
            base_image: Base image to use
            kube_root: Path to Kubernetes source root
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_build_node_image(image, base_image, kube_root), indent=2)

    @mcp.tool()
    def kind_set_kubeconfig_tool(name: str = "kind") -> str:
        """Export kubeconfig and set as current context.

        This updates your KUBECONFIG to add the kind cluster context.

        Args:
            name: Name of the kind cluster
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        result = _run_kind(["export", "kubeconfig", "--name", name], timeout=30)
        if result["success"]:
            return json.dumps({
                "success": True,
                "message": f"Kubeconfig exported and context set for cluster '{name}'",
                "output": result.get("output", "")
            }, indent=2)
        return json.dumps(result, indent=2)
