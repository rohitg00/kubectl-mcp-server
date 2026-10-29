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

    def _context_info():
        """Return (contexts, active) for the context/namespace resources.

        Follows the same selection rules as ``KubernetesProvider``
        (``MCP_K8S_PROVIDER``, ``MCP_K8S_KUBECONFIG``/``KUBECONFIG``,
        ``MCP_K8S_CONTEXT``), so resources describe the cluster the tools
        talk to. The kubeconfig is read on every call, so edits and errors
        (parse errors, missing current-context) are reported as they are.
        In-cluster is used for the ``in-cluster`` provider, or for the
        default provider only when the kubeconfig file does not exist.
        """
        import os
        from kubernetes import client, config
        from kubectl_mcp_tool.providers import ProviderConfig, ProviderType

        settings = ProviderConfig.from_env()
        path = settings.kubeconfig_path

        def _in_cluster():
            # Throwaway Configuration so the probe doesn't change the
            # global default client config.
            config.load_incluster_config(client_configuration=client.Configuration())
            ctx = {
                "name": "in-cluster",
                "cluster": "in-cluster",
                "user": "service-account",
                "namespace": "default",
            }
            return [ctx], ctx

        def _flatten(ctx):
            details = ctx.get("context", {})
            return {
                "name": ctx.get("name"),
                "cluster": details.get("cluster"),
                "user": details.get("user"),
                "namespace": details.get("namespace") or "default",
            }

        if settings.provider_type == ProviderType.IN_CLUSTER:
            return _in_cluster()

        if settings.provider_type == ProviderType.SINGLE:
            if not settings.context:
                raise ValueError("MCP_K8S_CONTEXT must be set for 'single' provider")
            contexts, _ = config.list_kube_config_contexts(config_file=path)
            for ctx in contexts:
                if ctx.get("name") == settings.context:
                    single = _flatten(ctx)
                    return [single], single
            raise ValueError(f"Context '{settings.context}' not found in kubeconfig '{path}'")

        if not any(os.path.exists(p) for p in path.split(os.pathsep) if p):
            try:
                return _in_cluster()
            except Exception as err:
                raise FileNotFoundError(
                    f"No Kubernetes configuration found: kubeconfig not found at "
                    f"'{path}' and in-cluster config is not available."
                ) from err

        contexts, active = config.list_kube_config_contexts(config_file=path)
        return [_flatten(ctx) for ctx in contexts], (_flatten(active) if active else None)

    @server.resource("kubeconfig://contexts")
    def get_kubeconfig_contexts() -> str:
        """List all available kubectl contexts."""
        try:
            contexts, active_context = _context_info()
            result = {
                "active_context": active_context.get("name") if active_context else None,
                "contexts": [
                    {
                        "name": ctx.get("name"),
                        "cluster": ctx.get("cluster"),
                        "user": ctx.get("user"),
                        "namespace": ctx.get("namespace") or "default"
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
            _, active_context = _context_info()
            if active_context:
                result = {
                    "name": active_context.get("name"),
                    "cluster": active_context.get("cluster"),
                    "user": active_context.get("user"),
                    "namespace": active_context.get("namespace") or "default"
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
            _, active_context = _context_info()
            namespace = "default"
            if active_context:
                namespace = active_context.get("namespace") or "default"
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

            from kubectl_mcp_tool.utils.helpers import redact_secrets
            secret = v1.read_namespaced_secret(name, namespace)
            manifest = client.ApiClient().sanitize_for_serialization(secret)
            manifest["kind"] = "Secret"
            return yaml.dump(redact_secrets(manifest), default_flow_style=False)
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
