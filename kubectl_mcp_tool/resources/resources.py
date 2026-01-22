import json
import logging
import subprocess
from typing import Any

logger = logging.getLogger("mcp-server")


def register_resources(server):
    """Register all MCP resources for Kubernetes data exposure.

    Args:
        server: FastMCP server instance
    """

    @server.resource("kubeconfig://contexts")
    def get_kubeconfig_contexts() -> str:
        """List all available kubectl contexts."""
        try:
            from kubernetes import config
            contexts, active_context = config.list_kube_config_contexts()
            result = {
                "active_context": active_context.get("name") if active_context else None,
                "contexts": [
                    {
                        "name": ctx.get("name"),
                        "cluster": ctx.get("context", {}).get("cluster"),
                        "user": ctx.get("context", {}).get("user"),
                        "namespace": ctx.get("context", {}).get("namespace", "default")
                    }
                    for ctx in contexts
                ]
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.resource("kubeconfig://current-context")
    def get_current_context() -> str:
        """Get the current active kubectl context."""
        try:
            from kubernetes import config
            _, active_context = config.list_kube_config_contexts()
            if active_context:
                result = {
                    "name": active_context.get("name"),
                    "cluster": active_context.get("context", {}).get("cluster"),
                    "user": active_context.get("context", {}).get("user"),
                    "namespace": active_context.get("context", {}).get("namespace", "default")
                }
            else:
                result = {"error": "No active context found"}
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.resource("namespace://current")
    def get_current_namespace() -> str:
        """Get the current namespace from kubectl context."""
        try:
            from kubernetes import config
            _, active_context = config.list_kube_config_contexts()
            namespace = "default"
            if active_context:
                namespace = active_context.get("context", {}).get("namespace", "default")
            return json.dumps({"namespace": namespace}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.resource("namespace://list")
    def list_all_namespaces() -> str:
        """List all namespaces in the cluster."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            namespaces = v1.list_namespace()
            result = {
                "namespaces": [
                    {
                        "name": ns.metadata.name,
                        "status": ns.status.phase,
                        "created": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None,
                        "labels": ns.metadata.labels or {}
                    }
                    for ns in namespaces.items
                ]
            }
            return json.dumps(result, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.resource("cluster://info")
    def get_cluster_info() -> str:
        """Get cluster information including version and nodes."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            version_api = client.VersionApi()

            version_info = version_api.get_code()
            nodes = v1.list_node()

            result = {
                "version": {
                    "git_version": version_info.git_version,
                    "platform": version_info.platform,
                    "go_version": version_info.go_version
                },
                "nodes": {
                    "count": len(nodes.items),
                    "ready": sum(1 for n in nodes.items if any(
                        c.type == "Ready" and c.status == "True"
                        for c in n.status.conditions
                    ))
                }
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.resource("cluster://nodes")
    def get_cluster_nodes() -> str:
        """Get detailed information about all cluster nodes."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            nodes = v1.list_node()

            result = {
                "nodes": [
                    {
                        "name": node.metadata.name,
                        "status": next(
                            (c.status for c in node.status.conditions if c.type == "Ready"),
                            "Unknown"
                        ),
                        "roles": [
                            k.replace("node-role.kubernetes.io/", "")
                            for k in (node.metadata.labels or {}).keys()
                            if k.startswith("node-role.kubernetes.io/")
                        ] or ["worker"],
                        "kubernetes_version": node.status.node_info.kubelet_version,
                        "os": node.status.node_info.os_image,
                        "architecture": node.status.node_info.architecture,
                        "capacity": {
                            "cpu": node.status.capacity.get("cpu"),
                            "memory": node.status.capacity.get("memory"),
                            "pods": node.status.capacity.get("pods")
                        },
                        "allocatable": {
                            "cpu": node.status.allocatable.get("cpu"),
                            "memory": node.status.allocatable.get("memory"),
                            "pods": node.status.allocatable.get("pods")
                        }
                    }
                    for node in nodes.items
                ]
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.resource("cluster://version")
    def get_cluster_version() -> str:
        """Get Kubernetes cluster version."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            version_api = client.VersionApi()
            version_info = version_api.get_code()

            result = {
                "git_version": version_info.git_version,
                "major": version_info.major,
                "minor": version_info.minor,
                "platform": version_info.platform,
                "build_date": version_info.build_date,
                "go_version": version_info.go_version,
                "compiler": version_info.compiler
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.resource("cluster://api-resources")
    def get_api_resources() -> str:
        """Get available API resources in the cluster."""
        try:
            result = subprocess.run(
                ["kubectl", "api-resources", "--output=wide"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    resources = []
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 4:
                            resources.append({
                                "name": parts[0],
                                "shortnames": parts[1] if len(parts) > 4 else "",
                                "apigroup": parts[-4] if len(parts) > 4 else "",
                                "namespaced": parts[-3] if len(parts) > 4 else parts[-2],
                                "kind": parts[-2] if len(parts) > 4 else parts[-1]
                            })
                    return json.dumps({"resources": resources}, indent=2)
            return json.dumps({"error": result.stderr or "Failed to get API resources"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @server.resource("manifest://deployments/{namespace}/{name}")
    def get_deployment_manifest(namespace: str, name: str) -> str:
        """Get YAML manifest for a specific deployment."""
        try:
            from kubernetes import client, config
            import yaml
            config.load_kube_config()
            apps_v1 = client.AppsV1Api()

            deployment = apps_v1.read_namespaced_deployment(name, namespace)
            manifest = client.ApiClient().sanitize_for_serialization(deployment)
            return yaml.dump(manifest, default_flow_style=False)
        except Exception as e:
            return f"# Error: {str(e)}"

    @server.resource("manifest://services/{namespace}/{name}")
    def get_service_manifest(namespace: str, name: str) -> str:
        """Get YAML manifest for a specific service."""
        try:
            from kubernetes import client, config
            import yaml
            config.load_kube_config()
            v1 = client.CoreV1Api()

            service = v1.read_namespaced_service(name, namespace)
            manifest = client.ApiClient().sanitize_for_serialization(service)
            return yaml.dump(manifest, default_flow_style=False)
        except Exception as e:
            return f"# Error: {str(e)}"

    @server.resource("manifest://configmaps/{namespace}/{name}")
    def get_configmap_manifest(namespace: str, name: str) -> str:
        """Get YAML manifest for a specific ConfigMap."""
        try:
            from kubernetes import client, config
            import yaml
            config.load_kube_config()
            v1 = client.CoreV1Api()

            configmap = v1.read_namespaced_config_map(name, namespace)
            manifest = client.ApiClient().sanitize_for_serialization(configmap)
            return yaml.dump(manifest, default_flow_style=False)
        except Exception as e:
            return f"# Error: {str(e)}"

    @server.resource("manifest://pods/{namespace}/{name}")
    def get_pod_manifest(namespace: str, name: str) -> str:
        """Get YAML manifest for a specific pod."""
        try:
            from kubernetes import client, config
            import yaml
            config.load_kube_config()
            v1 = client.CoreV1Api()

            pod = v1.read_namespaced_pod(name, namespace)
            manifest = client.ApiClient().sanitize_for_serialization(pod)
            return yaml.dump(manifest, default_flow_style=False)
        except Exception as e:
            return f"# Error: {str(e)}"

    @server.resource("manifest://secrets/{namespace}/{name}")
    def get_secret_manifest(namespace: str, name: str) -> str:
        """Get YAML manifest for a specific secret (data masked)."""
        try:
            from kubernetes import client, config
            import yaml
            config.load_kube_config()
            v1 = client.CoreV1Api()

            secret = v1.read_namespaced_secret(name, namespace)
            manifest = client.ApiClient().sanitize_for_serialization(secret)
            if "data" in manifest and manifest["data"]:
                manifest["data"] = {k: "[MASKED]" for k in manifest["data"].keys()}
            return yaml.dump(manifest, default_flow_style=False)
        except Exception as e:
            return f"# Error: {str(e)}"

    @server.resource("manifest://ingresses/{namespace}/{name}")
    def get_ingress_manifest(namespace: str, name: str) -> str:
        """Get YAML manifest for a specific ingress."""
        try:
            from kubernetes import client, config
            import yaml
            config.load_kube_config()
            networking_v1 = client.NetworkingV1Api()

            ingress = networking_v1.read_namespaced_ingress(name, namespace)
            manifest = client.ApiClient().sanitize_for_serialization(ingress)
            return yaml.dump(manifest, default_flow_style=False)
        except Exception as e:
            return f"# Error: {str(e)}"
