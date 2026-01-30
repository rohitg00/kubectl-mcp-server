"""kind (Kubernetes IN Docker) toolset for kubectl-mcp-server.

kind enables running local Kubernetes clusters using Docker container "nodes".
It's a tool from Kubernetes SIG for local development and CI testing.
"""

import subprocess
import json
import re
import os
import tempfile
import yaml
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


def _run_docker(
    args: List[str],
    timeout: int = 60,
    capture_output: bool = True
) -> Dict[str, Any]:
    """Run docker command and return result.

    Args:
        args: Command arguments (without 'docker' prefix)
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr

    Returns:
        Result dict with success status and output/error
    """
    cmd = ["docker"] + args

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
    except FileNotFoundError:
        return {"success": False, "error": "Docker CLI not available"}
    except Exception as e:
        return {"success": False, "error": str(e)}


KNOWN_KIND_IMAGES = [
    "kindest/node:v1.32.0",
    "kindest/node:v1.31.0",
    "kindest/node:v1.30.0",
    "kindest/node:v1.29.0",
    "kindest/node:v1.28.0",
    "kindest/node:v1.27.0",
    "kindest/node:v1.26.0",
    "kindest/node:v1.25.0",
]


def kind_config_validate(config_path: str) -> Dict[str, Any]:
    """Validate kind configuration file.

    Args:
        config_path: Path to kind config YAML file

    Returns:
        Validation results
    """
    if not os.path.exists(config_path):
        return {"success": False, "error": f"Config file not found: {config_path}"}

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return {"success": False, "error": f"Invalid YAML: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to read config: {e}"}

    errors = []
    warnings = []

    if config.get("kind") != "Cluster":
        errors.append("kind must be 'Cluster'")

    api_version = config.get("apiVersion", "")
    if not api_version.startswith("kind.x-k8s.io/"):
        errors.append("apiVersion should be 'kind.x-k8s.io/v1alpha4'")

    nodes = config.get("nodes", [])
    if not nodes:
        warnings.append("No nodes defined, will create single control-plane")

    control_planes = [n for n in nodes if n.get("role") == "control-plane"]
    workers = [n for n in nodes if n.get("role") == "worker"]

    if len(control_planes) == 0 and nodes:
        warnings.append("No control-plane node defined")
    elif len(control_planes) > 1:
        warnings.append(f"HA setup with {len(control_planes)} control-planes")

    return {
        "success": len(errors) == 0,
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "config_summary": {
            "control_planes": len(control_planes),
            "workers": len(workers),
            "total_nodes": len(nodes) if nodes else 1,
            "api_version": api_version
        }
    }


def kind_config_generate(
    name: str = "kind",
    workers: int = 0,
    control_planes: int = 1,
    registry: bool = False,
    ingress: bool = False,
    port_mappings: List[Dict] = None
) -> Dict[str, Any]:
    """Generate kind config YAML for common scenarios.

    Args:
        name: Cluster name (for reference)
        workers: Number of worker nodes
        control_planes: Number of control-plane nodes (1 for single, 3 for HA)
        registry: Add local registry configuration
        ingress: Add port mappings for ingress (80, 443)
        port_mappings: Custom port mappings list

    Returns:
        Generated config YAML
    """
    config = {
        "kind": "Cluster",
        "apiVersion": "kind.x-k8s.io/v1alpha4",
        "nodes": []
    }

    for i in range(control_planes):
        node = {"role": "control-plane"}
        if ingress and i == 0:
            node["kubeadmConfigPatches"] = [
                "kind: InitConfiguration\nnodeRegistration:\n  kubeletExtraArgs:\n    node-labels: \"ingress-ready=true\""
            ]
            node["extraPortMappings"] = [
                {"containerPort": 80, "hostPort": 80, "protocol": "TCP"},
                {"containerPort": 443, "hostPort": 443, "protocol": "TCP"},
            ]
        if port_mappings and i == 0:
            node["extraPortMappings"] = node.get("extraPortMappings", []) + port_mappings
        config["nodes"].append(node)

    for _ in range(workers):
        config["nodes"].append({"role": "worker"})

    if registry:
        config["containerdConfigPatches"] = [
            "[plugins.\"io.containerd.grpc.v1.cri\".registry.mirrors.\"localhost:5001\"]\n  endpoint = [\"http://kind-registry:5001\"]"
        ]

    config_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False)

    return {
        "success": True,
        "config": config_yaml,
        "summary": {
            "name": name,
            "control_planes": control_planes,
            "workers": workers,
            "total_nodes": control_planes + workers,
            "features": {
                "registry": registry,
                "ingress": ingress,
                "custom_ports": bool(port_mappings)
            }
        }
    }


def kind_config_show(name: str = "kind") -> Dict[str, Any]:
    """Show effective config for a running cluster.

    Args:
        name: Name of the kind cluster

    Returns:
        Cluster configuration details
    """
    nodes_result = kind_get_nodes(name)
    if not nodes_result["success"]:
        return nodes_result

    nodes = nodes_result.get("nodes", [])
    if not nodes:
        return {"success": False, "error": f"No nodes found for cluster '{name}'"}

    node_configs = []
    for node in nodes:
        inspect_result = _run_docker(
            ["inspect", "--format", '{{json .}}', node],
            timeout=30
        )
        if inspect_result["success"]:
            try:
                node_info = json.loads(inspect_result["output"])
                labels = node_info.get("Config", {}).get("Labels", {})
                ports = node_info.get("HostConfig", {}).get("PortBindings", {})
                node_configs.append({
                    "name": node,
                    "role": labels.get("io.x-k8s.kind.role", "unknown"),
                    "cluster": labels.get("io.x-k8s.kind.cluster", name),
                    "port_mappings": ports
                })
            except json.JSONDecodeError:
                node_configs.append({"name": node, "error": "Failed to parse"})

    return {
        "success": True,
        "cluster": name,
        "nodes": node_configs,
        "total_nodes": len(node_configs)
    }


def kind_available_images() -> Dict[str, Any]:
    """List available kindest/node images (K8s versions).

    Returns:
        List of available node images
    """
    return {
        "success": True,
        "images": KNOWN_KIND_IMAGES,
        "latest": KNOWN_KIND_IMAGES[0] if KNOWN_KIND_IMAGES else None,
        "note": "Use image parameter with kind_create_cluster_tool to specify K8s version"
    }


def kind_registry_create(
    name: str = "kind-registry",
    port: int = 5001
) -> Dict[str, Any]:
    """Create local Docker registry for kind clusters.

    Args:
        name: Name for the registry container
        port: Host port to expose registry on

    Returns:
        Creation result
    """
    check_result = _run_docker(["ps", "-q", "-f", f"name={name}"], timeout=30)
    if check_result["success"] and check_result.get("output"):
        return {
            "success": True,
            "message": f"Registry '{name}' already exists",
            "name": name,
            "port": port
        }

    result = _run_docker([
        "run", "-d",
        "--restart=always",
        "-p", f"127.0.0.1:{port}:5000",
        "--name", name,
        "--network", "bridge",
        "registry:2"
    ], timeout=120)

    if not result["success"]:
        return result

    network_result = _run_docker(["network", "ls", "-q", "-f", "name=kind"], timeout=30)
    if network_result["success"] and network_result.get("output"):
        _run_docker(["network", "connect", "kind", name], timeout=30)

    return {
        "success": True,
        "message": f"Registry '{name}' created successfully",
        "name": name,
        "port": port,
        "endpoint": f"localhost:{port}"
    }


def kind_registry_connect(
    cluster_name: str = "kind",
    registry_name: str = "kind-registry"
) -> Dict[str, Any]:
    """Connect kind cluster to local registry.

    Args:
        cluster_name: Name of the kind cluster
        registry_name: Name of the registry container

    Returns:
        Connection result
    """
    network_result = _run_docker(
        ["network", "connect", "kind", registry_name],
        timeout=30
    )

    if not network_result["success"] and "already exists" not in network_result.get("error", ""):
        return network_result

    nodes_result = kind_get_nodes(cluster_name)
    if not nodes_result["success"]:
        return nodes_result

    return {
        "success": True,
        "message": f"Registry '{registry_name}' connected to cluster '{cluster_name}'",
        "cluster": cluster_name,
        "registry": registry_name,
        "usage": f"Tag images as localhost:5001/image:tag and push to registry"
    }


def kind_registry_status(name: str = "kind-registry") -> Dict[str, Any]:
    """Check local registry status.

    Args:
        name: Name of the registry container

    Returns:
        Registry status information
    """
    result = _run_docker(
        ["inspect", "--format", '{{json .}}', name],
        timeout=30
    )

    if not result["success"]:
        return {
            "success": False,
            "error": f"Registry '{name}' not found",
            "installed": False
        }

    try:
        info = json.loads(result["output"])
        state = info.get("State", {})
        network_settings = info.get("NetworkSettings", {})
        ports = network_settings.get("Ports", {})

        host_port = None
        for port_binding in ports.get("5000/tcp", []) or []:
            host_port = port_binding.get("HostPort")
            break

        networks = list(network_settings.get("Networks", {}).keys())

        return {
            "success": True,
            "name": name,
            "running": state.get("Running", False),
            "status": state.get("Status", "unknown"),
            "port": host_port,
            "networks": networks,
            "connected_to_kind": "kind" in networks
        }
    except json.JSONDecodeError:
        return {"success": False, "error": "Failed to parse registry info"}


def kind_node_exec(
    node: str,
    command: str,
    cluster: str = "kind"
) -> Dict[str, Any]:
    """Execute command on kind node container.

    Args:
        node: Node name (e.g., kind-control-plane)
        command: Command to execute
        cluster: Cluster name (for validation)

    Returns:
        Command execution result
    """
    if not node:
        return {"success": False, "error": "Node name is required"}
    if not command:
        return {"success": False, "error": "Command is required"}

    nodes_result = kind_get_nodes(cluster)
    if nodes_result["success"] and node not in nodes_result.get("nodes", []):
        return {
            "success": False,
            "error": f"Node '{node}' not found in cluster '{cluster}'",
            "available_nodes": nodes_result.get("nodes", [])
        }

    result = _run_docker(
        ["exec", node] + command.split(),
        timeout=120
    )

    if result["success"]:
        return {
            "success": True,
            "node": node,
            "command": command,
            "output": result.get("output", "")
        }

    return result


def kind_node_logs(
    node: str,
    tail: int = 100
) -> Dict[str, Any]:
    """Get logs from kind node container.

    Args:
        node: Node name
        tail: Number of lines to return

    Returns:
        Node container logs
    """
    if not node:
        return {"success": False, "error": "Node name is required"}

    result = _run_docker(
        ["logs", "--tail", str(tail), node],
        timeout=60
    )

    if result["success"]:
        return {
            "success": True,
            "node": node,
            "logs": result.get("output", "")
        }

    return result


def kind_node_inspect(node: str) -> Dict[str, Any]:
    """Inspect kind node container details.

    Args:
        node: Node name

    Returns:
        Node container details
    """
    if not node:
        return {"success": False, "error": "Node name is required"}

    result = _run_docker(
        ["inspect", "--format", '{{json .}}', node],
        timeout=30
    )

    if not result["success"]:
        return result

    try:
        info = json.loads(result["output"])
        state = info.get("State", {})
        config = info.get("Config", {})
        network_settings = info.get("NetworkSettings", {})
        host_config = info.get("HostConfig", {})

        return {
            "success": True,
            "node": node,
            "state": {
                "running": state.get("Running", False),
                "status": state.get("Status", "unknown"),
                "started_at": state.get("StartedAt"),
                "pid": state.get("Pid")
            },
            "image": config.get("Image"),
            "labels": config.get("Labels", {}),
            "ip_address": network_settings.get("IPAddress", ""),
            "networks": list(network_settings.get("Networks", {}).keys()),
            "port_bindings": host_config.get("PortBindings", {}),
            "mounts": [
                {"source": m.get("Source"), "destination": m.get("Destination")}
                for m in info.get("Mounts", [])
            ]
        }
    except json.JSONDecodeError:
        return {"success": False, "error": "Failed to parse node info"}


def kind_node_restart(node: str) -> Dict[str, Any]:
    """Restart kind node container.

    Args:
        node: Node name to restart

    Returns:
        Restart result
    """
    if not node:
        return {"success": False, "error": "Node name is required"}

    result = _run_docker(["restart", node], timeout=120)

    if result["success"]:
        return {
            "success": True,
            "message": f"Node '{node}' restarted successfully",
            "node": node
        }

    return result


def kind_network_inspect(cluster: str = "kind") -> Dict[str, Any]:
    """Inspect kind Docker network.

    Args:
        cluster: Cluster name (kind network is shared)

    Returns:
        Network details
    """
    result = _run_docker(
        ["network", "inspect", "kind"],
        timeout=30
    )

    if not result["success"]:
        return {"success": False, "error": "kind network not found. Is any cluster running?"}

    try:
        info = json.loads(result["output"])
        if isinstance(info, list) and len(info) > 0:
            info = info[0]

        ipam = info.get("IPAM", {}).get("Config", [{}])[0]
        containers = {}
        for container_id, container_info in info.get("Containers", {}).items():
            containers[container_info.get("Name", container_id[:12])] = {
                "ip": container_info.get("IPv4Address", "").split("/")[0],
                "mac": container_info.get("MacAddress")
            }

        return {
            "success": True,
            "name": info.get("Name", "kind"),
            "driver": info.get("Driver"),
            "scope": info.get("Scope"),
            "subnet": ipam.get("Subnet"),
            "gateway": ipam.get("Gateway"),
            "containers": containers,
            "container_count": len(containers)
        }
    except (json.JSONDecodeError, IndexError):
        return {"success": False, "error": "Failed to parse network info"}


def kind_port_mappings(cluster: str = "kind") -> Dict[str, Any]:
    """List all port mappings for cluster.

    Args:
        cluster: Cluster name

    Returns:
        Port mappings for all nodes
    """
    nodes_result = kind_get_nodes(cluster)
    if not nodes_result["success"]:
        return nodes_result

    mappings = {}
    for node in nodes_result.get("nodes", []):
        inspect_result = _run_docker(
            ["inspect", "--format", '{{json .HostConfig.PortBindings}}', node],
            timeout=30
        )
        if inspect_result["success"]:
            try:
                ports = json.loads(inspect_result["output"]) or {}
                node_ports = []
                for container_port, bindings in ports.items():
                    for binding in bindings or []:
                        node_ports.append({
                            "container_port": container_port,
                            "host_ip": binding.get("HostIp", "0.0.0.0"),
                            "host_port": binding.get("HostPort")
                        })
                if node_ports:
                    mappings[node] = node_ports
            except json.JSONDecodeError:
                pass

    return {
        "success": True,
        "cluster": cluster,
        "port_mappings": mappings,
        "has_mappings": len(mappings) > 0
    }


def kind_ingress_setup(
    cluster: str = "kind",
    ingress_type: str = "nginx"
) -> Dict[str, Any]:
    """Setup ingress controller on kind cluster.

    Args:
        cluster: Cluster name
        ingress_type: Type of ingress (nginx, contour)

    Returns:
        Setup result
    """
    if ingress_type not in ["nginx", "contour"]:
        return {"success": False, "error": f"Unsupported ingress type: {ingress_type}"}

    clusters_result = kind_list_clusters()
    if not clusters_result["success"]:
        return clusters_result
    if cluster not in clusters_result.get("clusters", []):
        return {"success": False, "error": f"Cluster '{cluster}' not found"}

    if ingress_type == "nginx":
        manifest_url = "https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml"
    else:
        manifest_url = "https://projectcontour.io/quickstart/contour.yaml"

    try:
        result = subprocess.run(
            ["kubectl", "apply", "-f", manifest_url, "--context", f"kind-{cluster}"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return {
                "success": True,
                "message": f"{ingress_type.title()} ingress controller installed on '{cluster}'",
                "cluster": cluster,
                "ingress_type": ingress_type,
                "manifest": manifest_url,
                "next_steps": [
                    "Wait for ingress controller pods to be ready",
                    "Create Ingress resources to expose services",
                    f"Access via localhost (ports 80/443 if configured)"
                ]
            }
        return {"success": False, "error": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "kubectl apply timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "kubectl not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def kind_cluster_status(name: str = "kind") -> Dict[str, Any]:
    """Get detailed cluster health status.

    Args:
        name: Cluster name

    Returns:
        Comprehensive cluster status
    """
    clusters_result = kind_list_clusters()
    if not clusters_result["success"]:
        return clusters_result
    if name not in clusters_result.get("clusters", []):
        return {
            "success": False,
            "error": f"Cluster '{name}' not found",
            "available_clusters": clusters_result.get("clusters", [])
        }

    nodes_result = kind_get_nodes(name)
    node_statuses = []

    for node in nodes_result.get("nodes", []):
        inspect_result = _run_docker(
            ["inspect", "--format", '{{json .State}}', node],
            timeout=30
        )
        if inspect_result["success"]:
            try:
                state = json.loads(inspect_result["output"])
                node_statuses.append({
                    "name": node,
                    "running": state.get("Running", False),
                    "status": state.get("Status", "unknown")
                })
            except json.JSONDecodeError:
                node_statuses.append({"name": node, "running": False, "status": "unknown"})

    all_running = all(n.get("running", False) for n in node_statuses)

    try:
        kubectl_result = subprocess.run(
            ["kubectl", "get", "nodes", "-o", "json", "--context", f"kind-{name}"],
            capture_output=True,
            text=True,
            timeout=30
        )
        k8s_nodes = []
        if kubectl_result.returncode == 0:
            nodes_data = json.loads(kubectl_result.stdout)
            for item in nodes_data.get("items", []):
                conditions = {c["type"]: c["status"] for c in item.get("status", {}).get("conditions", [])}
                k8s_nodes.append({
                    "name": item.get("metadata", {}).get("name"),
                    "ready": conditions.get("Ready") == "True",
                    "conditions": conditions
                })
    except Exception:
        k8s_nodes = []

    return {
        "success": True,
        "cluster": name,
        "healthy": all_running,
        "container_nodes": node_statuses,
        "kubernetes_nodes": k8s_nodes,
        "summary": {
            "total_nodes": len(node_statuses),
            "running_containers": sum(1 for n in node_statuses if n.get("running")),
            "ready_k8s_nodes": sum(1 for n in k8s_nodes if n.get("ready"))
        }
    }


def kind_images_list(
    cluster: str = "kind",
    node: str = ""
) -> Dict[str, Any]:
    """List images on cluster nodes.

    Args:
        cluster: Cluster name
        node: Specific node (optional, defaults to first control-plane)

    Returns:
        List of images on the node
    """
    if not node:
        nodes_result = kind_get_nodes(cluster)
        if not nodes_result["success"]:
            return nodes_result
        nodes = nodes_result.get("nodes", [])
        node = next((n for n in nodes if "control-plane" in n), nodes[0] if nodes else None)
        if not node:
            return {"success": False, "error": f"No nodes found in cluster '{cluster}'"}

    result = _run_docker(
        ["exec", node, "crictl", "images", "-o", "json"],
        timeout=60
    )

    if not result["success"]:
        result = _run_docker(
            ["exec", node, "crictl", "images"],
            timeout=60
        )
        if result["success"]:
            return {
                "success": True,
                "node": node,
                "cluster": cluster,
                "images_raw": result.get("output", "")
            }
        return result

    try:
        images_data = json.loads(result["output"])
        images = []
        for img in images_data.get("images", []):
            tags = img.get("repoTags", [])
            images.append({
                "id": img.get("id", "")[:12],
                "tags": tags,
                "size": img.get("size")
            })
        return {
            "success": True,
            "node": node,
            "cluster": cluster,
            "images": images,
            "total": len(images)
        }
    except json.JSONDecodeError:
        return {"success": True, "node": node, "images_raw": result.get("output", "")}


def kind_provider_info() -> Dict[str, Any]:
    """Get container runtime provider info.

    Returns:
        Provider (Docker/Podman) details
    """
    provider = os.environ.get("KIND_EXPERIMENTAL_PROVIDER", "docker")

    version_result = _run_docker(["version", "--format", "{{json .}}"], timeout=30)

    if not version_result["success"]:
        return {
            "success": False,
            "error": "Failed to get provider info",
            "provider": provider
        }

    try:
        version_info = json.loads(version_result["output"])
        client = version_info.get("Client", {})
        server = version_info.get("Server", {})

        return {
            "success": True,
            "provider": provider,
            "client_version": client.get("Version"),
            "server_version": server.get("Version"),
            "api_version": client.get("ApiVersion"),
            "os": client.get("Os"),
            "arch": client.get("Arch"),
            "experimental": os.environ.get("KIND_EXPERIMENTAL_PROVIDER") is not None
        }
    except json.JSONDecodeError:
        return {
            "success": True,
            "provider": provider,
            "raw_output": version_result.get("output", "")
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

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_config_validate_tool(config_path: str) -> str:
        """Validate kind configuration file before cluster creation.

        Args:
            config_path: Path to kind config YAML file
        """
        return json.dumps(kind_config_validate(config_path), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_config_generate_tool(
        name: str = "kind",
        workers: int = 0,
        control_planes: int = 1,
        registry: bool = False,
        ingress: bool = False
    ) -> str:
        """Generate kind config YAML for common scenarios.

        Args:
            name: Cluster name (for reference)
            workers: Number of worker nodes (default: 0)
            control_planes: Number of control-plane nodes (1 for single, 3 for HA)
            registry: Add local registry configuration
            ingress: Add port mappings for ingress (80, 443)
        """
        return json.dumps(kind_config_generate(
            name, workers, control_planes, registry, ingress
        ), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_config_show_tool(name: str = "kind") -> str:
        """Show effective config for a running cluster.

        Args:
            name: Name of the kind cluster
        """
        return json.dumps(kind_config_show(name), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_available_images_tool() -> str:
        """List available kindest/node images (K8s versions)."""
        return json.dumps(kind_available_images(), indent=2)

    @mcp.tool()
    def kind_registry_create_tool(
        name: str = "kind-registry",
        port: int = 5001
    ) -> str:
        """Create local Docker registry for kind clusters.

        Args:
            name: Name for the registry container
            port: Host port to expose registry on
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_registry_create(name, port), indent=2)

    @mcp.tool()
    def kind_registry_connect_tool(
        cluster_name: str = "kind",
        registry_name: str = "kind-registry"
    ) -> str:
        """Connect kind cluster to local registry.

        Args:
            cluster_name: Name of the kind cluster
            registry_name: Name of the registry container
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_registry_connect(cluster_name, registry_name), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_registry_status_tool(name: str = "kind-registry") -> str:
        """Check local registry status.

        Args:
            name: Name of the registry container
        """
        return json.dumps(kind_registry_status(name), indent=2)

    @mcp.tool()
    def kind_node_exec_tool(
        node: str,
        command: str,
        cluster: str = "kind"
    ) -> str:
        """Execute command on kind node container.

        Useful for debugging with crictl, journalctl, systemctl.

        Args:
            node: Node name (e.g., kind-control-plane)
            command: Command to execute
            cluster: Cluster name (for validation)
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_node_exec(node, command, cluster), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_node_logs_tool(node: str, tail: int = 100) -> str:
        """Get logs from kind node container.

        Args:
            node: Node name
            tail: Number of lines to return
        """
        return json.dumps(kind_node_logs(node, tail), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_node_inspect_tool(node: str) -> str:
        """Inspect kind node container details.

        Args:
            node: Node name
        """
        return json.dumps(kind_node_inspect(node), indent=2)

    @mcp.tool()
    def kind_node_restart_tool(node: str) -> str:
        """Restart kind node container.

        Args:
            node: Node name to restart
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_node_restart(node), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_network_inspect_tool(cluster: str = "kind") -> str:
        """Inspect kind Docker network.

        Args:
            cluster: Cluster name (kind network is shared)
        """
        return json.dumps(kind_network_inspect(cluster), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_port_mappings_tool(cluster: str = "kind") -> str:
        """List all port mappings for cluster.

        Args:
            cluster: Cluster name
        """
        return json.dumps(kind_port_mappings(cluster), indent=2)

    @mcp.tool()
    def kind_ingress_setup_tool(
        cluster: str = "kind",
        ingress_type: str = "nginx"
    ) -> str:
        """Setup ingress controller on kind cluster.

        Args:
            cluster: Cluster name
            ingress_type: Type of ingress (nginx or contour)
        """
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(kind_ingress_setup(cluster, ingress_type), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_cluster_status_tool(name: str = "kind") -> str:
        """Get detailed cluster health status.

        Args:
            name: Cluster name
        """
        return json.dumps(kind_cluster_status(name), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_images_list_tool(cluster: str = "kind", node: str = "") -> str:
        """List images on cluster nodes.

        Args:
            cluster: Cluster name
            node: Specific node (optional, defaults to control-plane)
        """
        return json.dumps(kind_images_list(cluster, node), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def kind_provider_info_tool() -> str:
        """Get container runtime provider info (Docker/Podman)."""
        return json.dumps(kind_provider_info(), indent=2)
