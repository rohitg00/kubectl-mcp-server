import logging
import subprocess
from typing import Any, Dict, Optional

from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")


def register_cluster_tools(server, non_destructive: bool):
    """Register cluster and context management tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Switch Context",
            destructiveHint=True,
        ),
    )
    def switch_context(context_name: str) -> Dict[str, Any]:
        """Switch to a different kubectl context."""
        try:
            result = subprocess.run(
                ["kubectl", "config", "use-context", context_name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return {"success": True, "message": f"Switched to context: {context_name}"}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error switching context: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Current Context",
            readOnlyHint=True,
        ),
    )
    def get_current_context() -> Dict[str, Any]:
        """Get the current kubectl context."""
        try:
            result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return {"success": True, "context": result.stdout.strip()}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error getting current context: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="List Contexts",
            readOnlyHint=True,
        ),
    )
    def list_contexts() -> Dict[str, Any]:
        """List all available kubectl contexts."""
        try:
            from kubernetes import config
            contexts, active_context = config.list_kube_config_contexts()
            return {
                "success": True,
                "contexts": [
                    {
                        "name": ctx.get("name"),
                        "cluster": ctx.get("context", {}).get("cluster"),
                        "user": ctx.get("context", {}).get("user"),
                        "namespace": ctx.get("context", {}).get("namespace", "default"),
                        "active": ctx.get("name") == (active_context.get("name") if active_context else None)
                    }
                    for ctx in contexts
                ],
                "active_context": active_context.get("name") if active_context else None
            }
        except Exception as e:
            logger.error(f"Error listing contexts: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Context Details",
            readOnlyHint=True,
        ),
    )
    def get_context_details(context_name: str) -> Dict[str, Any]:
        """Get details about a specific context."""
        try:
            from kubernetes import config
            contexts, _ = config.list_kube_config_contexts()

            for ctx in contexts:
                if ctx.get("name") == context_name:
                    return {
                        "success": True,
                        "context": {
                            "name": ctx.get("name"),
                            "cluster": ctx.get("context", {}).get("cluster"),
                            "user": ctx.get("context", {}).get("user"),
                            "namespace": ctx.get("context", {}).get("namespace", "default")
                        }
                    }

            return {"success": False, "error": f"Context '{context_name}' not found"}
        except Exception as e:
            logger.error(f"Error getting context details: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Set Namespace for Context",
            destructiveHint=True,
        ),
    )
    def set_namespace_for_context(namespace: str, context_name: Optional[str] = None) -> Dict[str, Any]:
        """Set the default namespace for a context."""
        try:
            cmd = ["kubectl", "config", "set-context"]
            if context_name:
                cmd.append(context_name)
            else:
                cmd.append("--current")
            cmd.extend(["--namespace", namespace])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {"success": True, "message": f"Namespace set to: {namespace}"}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error setting namespace: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="List Kubeconfig Contexts",
            readOnlyHint=True,
        ),
    )
    def list_kubeconfig_contexts() -> Dict[str, Any]:
        """List all contexts from kubeconfig with detailed info."""
        try:
            result = subprocess.run(
                ["kubectl", "config", "get-contexts", "-o", "name"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                contexts = [c.strip() for c in result.stdout.strip().split("\n") if c.strip()]
                return {"success": True, "contexts": contexts}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error listing kubeconfig contexts: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Cluster Info",
            readOnlyHint=True,
        ),
    )
    def get_cluster_info() -> Dict[str, Any]:
        """Get cluster information."""
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return {"success": True, "info": result.stdout}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Explain",
            readOnlyHint=True,
        ),
    )
    def kubectl_explain(resource: str) -> Dict[str, Any]:
        """Explain a Kubernetes resource."""
        try:
            result = subprocess.run(
                ["kubectl", "explain", resource],
                capture_output=True, text=True, timeout=30
            )
            return {"success": result.returncode == 0, "output": result.stdout or result.stderr}
        except Exception as e:
            logger.error(f"Error explaining resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get API Resources",
            readOnlyHint=True,
        ),
    )
    def get_api_resources() -> Dict[str, Any]:
        """Get available API resources."""
        try:
            result = subprocess.run(
                ["kubectl", "api-resources"],
                capture_output=True, text=True, timeout=30
            )
            return {"success": result.returncode == 0, "output": result.stdout or result.stderr}
        except Exception as e:
            logger.error(f"Error getting API resources: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Health Check",
            readOnlyHint=True,
        ),
    )
    def health_check() -> Dict[str, Any]:
        """Perform a cluster health check."""
        try:
            result = subprocess.run(
                ["kubectl", "get", "componentstatuses", "-o", "json"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                return {"success": True, "components": data.get("items", [])}
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Cluster Version Info",
            readOnlyHint=True,
        ),
    )
    def get_cluster_version() -> Dict[str, Any]:
        """Get Kubernetes cluster version information."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            version_api = client.VersionApi()
            version_info = version_api.get_code()

            return {
                "success": True,
                "version": {
                    "gitVersion": version_info.git_version,
                    "major": version_info.major,
                    "minor": version_info.minor,
                    "platform": version_info.platform,
                    "buildDate": version_info.build_date,
                    "goVersion": version_info.go_version,
                    "compiler": version_info.compiler
                }
            }
        except Exception as e:
            logger.error(f"Error getting cluster version: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Admission Webhooks",
            readOnlyHint=True,
        ),
    )
    def get_admission_webhooks() -> Dict[str, Any]:
        """Get admission webhooks configured in the cluster."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            api = client.AdmissionregistrationV1Api()

            validating = api.list_validating_webhook_configuration()
            mutating = api.list_mutating_webhook_configuration()

            return {
                "success": True,
                "validatingWebhooks": [
                    {
                        "name": w.metadata.name,
                        "webhooks": [
                            {
                                "name": wh.name,
                                "failurePolicy": wh.failure_policy,
                                "matchPolicy": wh.match_policy,
                                "sideEffects": wh.side_effects
                            }
                            for wh in (w.webhooks or [])
                        ]
                    }
                    for w in validating.items
                ],
                "mutatingWebhooks": [
                    {
                        "name": w.metadata.name,
                        "webhooks": [
                            {
                                "name": wh.name,
                                "failurePolicy": wh.failure_policy,
                                "matchPolicy": wh.match_policy,
                                "sideEffects": wh.side_effects
                            }
                            for wh in (w.webhooks or [])
                        ]
                    }
                    for w in mutating.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting admission webhooks: {e}")
            return {"success": False, "error": str(e)}
