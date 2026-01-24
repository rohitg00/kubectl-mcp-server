"""
Cluster and context management tools for kubectl-mcp-server.

All tools support multi-cluster operations via the optional 'context' parameter.
"""

import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from kubectl_mcp_tool.k8s_config import (
    get_k8s_client,
    get_version_client,
    get_admissionregistration_client,
    list_contexts,
    get_active_context,
)

logger = logging.getLogger("mcp-server")


def _get_kubectl_context_args(context: str = "") -> List[str]:
    """Get kubectl context arguments."""
    if context:
        return ["--context", context]
    return []


def register_cluster_tools(server, non_destructive: bool):
    """Register cluster and context management tools."""

    # ========== Config Toolset ==========

    @server.tool(
        annotations=ToolAnnotations(
            title="List Contexts",
            readOnlyHint=True,
        ),
    )
    def list_contexts_tool() -> Dict[str, Any]:
        """List all available kubectl contexts with detailed info.

        Returns all contexts from kubeconfig with cluster, user, namespace info.
        """
        try:
            contexts = list_contexts()
            active = get_active_context()

            return {
                "success": True,
                "contexts": contexts,
                "active_context": active,
                "total": len(contexts)
            }
        except Exception as e:
            logger.error(f"Error listing contexts: {e}")
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
            active = get_active_context()
            if active:
                return {"success": True, "context": active}
            return {"success": False, "error": "No active context found"}
        except Exception as e:
            logger.error(f"Error getting current context: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Context Details",
            readOnlyHint=True,
        ),
    )
    def get_context_details(context_name: str) -> Dict[str, Any]:
        """Get details about a specific context.

        Args:
            context_name: Name of the context to get details for
        """
        try:
            contexts = list_contexts()

            for ctx in contexts:
                if ctx.get("name") == context_name:
                    return {
                        "success": True,
                        "context": ctx
                    }

            return {"success": False, "error": f"Context '{context_name}' not found"}
        except Exception as e:
            logger.error(f"Error getting context details: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="View Kubeconfig",
            readOnlyHint=True,
        ),
    )
    def kubeconfig_view(minify: bool = True) -> Dict[str, Any]:
        """View kubeconfig file contents (sanitized - no secrets).

        Args:
            minify: If True, show only current context info. If False, show all.
        """
        try:
            cmd = ["kubectl", "config", "view"]
            if minify:
                cmd.append("--minify")
            cmd.extend(["--raw=false", "-o", "json"])  # raw=false strips sensitive data

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                try:
                    config_data = json.loads(result.stdout)
                    # Additional sanitization
                    for user in config_data.get("users", []):
                        if "user" in user:
                            user_data = user["user"]
                            for sensitive in ["client-certificate-data", "client-key-data", "token"]:
                                if sensitive in user_data:
                                    user_data[sensitive] = "[REDACTED]"

                    return {
                        "success": True,
                        "minified": minify,
                        "kubeconfig": config_data
                    }
                except json.JSONDecodeError:
                    return {"success": True, "kubeconfig": result.stdout}

            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error viewing kubeconfig: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Switch Context",
            destructiveHint=True,
        ),
    )
    def switch_context(context_name: str) -> Dict[str, Any]:
        """Switch to a different kubectl context (changes default context).

        Args:
            context_name: Name of the context to switch to

        Note: This changes the default context in kubeconfig. For multi-cluster
        operations without changing default, use the 'context' parameter on
        individual tools instead.
        """
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
            title="Set Namespace for Context",
            destructiveHint=True,
        ),
    )
    def set_namespace_for_context(
        namespace: str,
        context_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Set the default namespace for a context.

        Args:
            namespace: Namespace to set as default
            context_name: Context to modify (uses current context if not specified)
        """
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

    # ========== Cluster Info Tools ==========

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Cluster Info",
            readOnlyHint=True,
        ),
    )
    def get_cluster_info(context: str = "") -> Dict[str, Any]:
        """Get cluster information.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            ctx_args = _get_kubectl_context_args(context)
            result = subprocess.run(
                ["kubectl"] + ctx_args + ["cluster-info"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return {
                    "success": True,
                    "context": context or "current",
                    "info": result.stdout
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error getting cluster info: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Cluster Version Info",
            readOnlyHint=True,
        ),
    )
    def get_cluster_version(context: str = "") -> Dict[str, Any]:
        """Get Kubernetes cluster version information.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            version_api = get_version_client(context)
            version_info = version_api.get_code()

            return {
                "success": True,
                "context": context or "current",
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
            title="Health Check",
            readOnlyHint=True,
        ),
    )
    def health_check(context: str = "") -> Dict[str, Any]:
        """Perform a cluster health check.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            ctx_args = _get_kubectl_context_args(context)
            result = subprocess.run(
                ["kubectl"] + ctx_args + ["get", "componentstatuses", "-o", "json"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "success": True,
                    "context": context or "current",
                    "components": data.get("items", [])
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Kubectl Explain",
            readOnlyHint=True,
        ),
    )
    def kubectl_explain(
        resource: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """Explain a Kubernetes resource.

        Args:
            resource: Resource type to explain (e.g., pods, deployments.spec)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            ctx_args = _get_kubectl_context_args(context)
            result = subprocess.run(
                ["kubectl"] + ctx_args + ["explain", resource],
                capture_output=True, text=True, timeout=30
            )
            return {
                "success": result.returncode == 0,
                "context": context or "current",
                "output": result.stdout or result.stderr
            }
        except Exception as e:
            logger.error(f"Error explaining resource: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get API Resources",
            readOnlyHint=True,
        ),
    )
    def get_api_resources(context: str = "") -> Dict[str, Any]:
        """Get available API resources.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            ctx_args = _get_kubectl_context_args(context)
            result = subprocess.run(
                ["kubectl"] + ctx_args + ["api-resources"],
                capture_output=True, text=True, timeout=30
            )
            return {
                "success": result.returncode == 0,
                "context": context or "current",
                "output": result.stdout or result.stderr
            }
        except Exception as e:
            logger.error(f"Error getting API resources: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get API Versions",
            readOnlyHint=True,
        ),
    )
    def get_api_versions(context: str = "") -> Dict[str, Any]:
        """Get available API versions.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            ctx_args = _get_kubectl_context_args(context)
            result = subprocess.run(
                ["kubectl"] + ctx_args + ["api-versions"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                versions = [v.strip() for v in result.stdout.strip().split("\n") if v.strip()]
                return {
                    "success": True,
                    "context": context or "current",
                    "versions": versions,
                    "total": len(versions)
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error getting API versions: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Admission Webhooks",
            readOnlyHint=True,
        ),
    )
    def get_admission_webhooks(context: str = "") -> Dict[str, Any]:
        """Get admission webhooks configured in the cluster.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            api = get_admissionregistration_client(context)

            validating = api.list_validating_webhook_configuration()
            mutating = api.list_mutating_webhook_configuration()

            return {
                "success": True,
                "context": context or "current",
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

    @server.tool(
        annotations=ToolAnnotations(
            title="Check CRD Exists",
            readOnlyHint=True,
        ),
    )
    def check_crd_exists(
        crd_name: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """Check if a Custom Resource Definition exists in the cluster.

        Args:
            crd_name: Name of the CRD to check (e.g., certificates.cert-manager.io)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            ctx_args = _get_kubectl_context_args(context)
            result = subprocess.run(
                ["kubectl"] + ctx_args + ["get", "crd", crd_name, "-o", "name"],
                capture_output=True, text=True, timeout=10
            )

            exists = result.returncode == 0

            return {
                "success": True,
                "context": context or "current",
                "crd": crd_name,
                "exists": exists
            }
        except Exception as e:
            logger.error(f"Error checking CRD: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="List CRDs",
            readOnlyHint=True,
        ),
    )
    def list_crds(context: str = "") -> Dict[str, Any]:
        """List all Custom Resource Definitions in the cluster.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            ctx_args = _get_kubectl_context_args(context)
            result = subprocess.run(
                ["kubectl"] + ctx_args + ["get", "crd", "-o", "json"],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                crds = []
                for item in data.get("items", []):
                    crds.append({
                        "name": item.get("metadata", {}).get("name"),
                        "group": item.get("spec", {}).get("group"),
                        "scope": item.get("spec", {}).get("scope"),
                        "versions": [
                            v.get("name") for v in item.get("spec", {}).get("versions", [])
                        ]
                    })

                return {
                    "success": True,
                    "context": context or "current",
                    "crds": crds,
                    "total": len(crds)
                }
            return {"success": False, "error": result.stderr}
        except Exception as e:
            logger.error(f"Error listing CRDs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Nodes Summary",
            readOnlyHint=True,
        ),
    )
    def get_nodes_summary(context: str = "") -> Dict[str, Any]:
        """Get summary of all nodes in the cluster.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)
            nodes = v1.list_node()

            summary = {
                "total": len(nodes.items),
                "ready": 0,
                "notReady": 0,
                "nodes": []
            }

            for node in nodes.items:
                node_info = {
                    "name": node.metadata.name,
                    "status": "Unknown",
                    "roles": [],
                    "kubeletVersion": node.status.node_info.kubelet_version if node.status.node_info else None,
                    "os": node.status.node_info.os_image if node.status.node_info else None,
                    "capacity": {
                        "cpu": node.status.capacity.get("cpu") if node.status.capacity else None,
                        "memory": node.status.capacity.get("memory") if node.status.capacity else None,
                        "pods": node.status.capacity.get("pods") if node.status.capacity else None
                    }
                }

                # Get node status
                for condition in (node.status.conditions or []):
                    if condition.type == "Ready":
                        node_info["status"] = "Ready" if condition.status == "True" else "NotReady"
                        if condition.status == "True":
                            summary["ready"] += 1
                        else:
                            summary["notReady"] += 1

                # Get node roles
                for label, value in (node.metadata.labels or {}).items():
                    if label.startswith("node-role.kubernetes.io/"):
                        role = label.split("/")[1]
                        node_info["roles"].append(role)

                summary["nodes"].append(node_info)

            return {
                "success": True,
                "context": context or "current",
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error getting nodes summary: {e}")
            return {"success": False, "error": str(e)}
