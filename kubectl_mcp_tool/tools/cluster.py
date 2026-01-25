"""
Cluster and context management tools for kubectl-mcp-server.

All tools support multi-cluster operations via the optional 'context' parameter.
"""

import json
import logging
import os
import re
import subprocess
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from kubectl_mcp_tool.k8s_config import (
    get_k8s_client,
    get_version_client,
    get_admissionregistration_client,
    list_contexts,
    get_active_context,
    enable_kubeconfig_watch,
    disable_kubeconfig_watch,
    is_stateless_mode,
    set_stateless_mode,
)

logger = logging.getLogger("mcp-server")


def _get_kubectl_context_args(context: str = "") -> List[str]:
    """Get kubectl context arguments."""
    if context:
        return ["--context", context]
    return []


# DNS-1123 subdomain regex for node name validation
_DNS_1123_PATTERN = re.compile(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$')


def _validate_node_name(name: str) -> tuple:
    """Validate that a node name follows DNS-1123 subdomain rules.

    Args:
        name: Node name to validate

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    if not name:
        return False, "Node name cannot be empty"
    if len(name) > 253:
        return False, f"Node name too long: {len(name)} chars (max 253)"
    if not _DNS_1123_PATTERN.match(name):
        return False, (
            f"Invalid node name '{name}': must be a valid DNS-1123 subdomain "
            "(lowercase alphanumeric, '-' or '.', must start/end with alphanumeric)"
        )
    return True, None


def register_cluster_tools(server, non_destructive: bool):
    """Register cluster and context management tools."""

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

                for condition in (node.status.conditions or []):
                    if condition.type == "Ready":
                        node_info["status"] = "Ready" if condition.status == "True" else "NotReady"
                        if condition.status == "True":
                            summary["ready"] += 1
                        else:
                            summary["notReady"] += 1

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

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Server Config Status",
            readOnlyHint=True,
        ),
    )
    def get_server_config_status() -> Dict[str, Any]:
        """Get current server configuration status.

        Returns information about:
        - Stateless mode (whether API clients are cached)
        - Kubeconfig watching (whether auto-reload is enabled)
        - Available contexts
        - Current active context
        """
        try:
            from kubectl_mcp_tool.k8s_config import _kubeconfig_watcher

            contexts = list_contexts()
            active = get_active_context()

            return {
                "success": True,
                "config": {
                    "statelessMode": is_stateless_mode(),
                    "kubeconfigWatching": _kubeconfig_watcher is not None,
                },
                "contexts": {
                    "active": active,
                    "available": [c.get("name") for c in contexts],
                    "total": len(contexts)
                }
            }
        except Exception as e:
            logger.error(f"Error getting config status: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Enable Kubeconfig Watching",
            destructiveHint=True,
        ),
    )
    def enable_kubeconfig_watching(
        check_interval: float = 5.0
    ) -> Dict[str, Any]:
        """Enable automatic kubeconfig file watching.

        When enabled, the server will automatically detect changes to kubeconfig
        files and reload the configuration. This is useful when:
        - Cloud provider CLIs update credentials (aws, gcloud, az)
        - Users switch contexts using external tools
        - Kubeconfig files are mounted dynamically

        Args:
            check_interval: How often to check for changes (seconds). Default: 5.0

        Returns:
            Status of the kubeconfig watcher.

        Raises:
            TypeError: If check_interval is not a number (int or float).
            ValueError: If check_interval is not positive.
        """
        if not isinstance(check_interval, (int, float)):
            raise TypeError(f"check_interval must be a number (int or float), got {type(check_interval).__name__}")
        if check_interval <= 0:
            raise ValueError(f"check_interval must be positive, got {check_interval}")

        try:
            enable_kubeconfig_watch(check_interval=check_interval)
            return {
                "success": True,
                "message": f"Kubeconfig watching enabled (interval: {check_interval}s)",
                "checkInterval": check_interval
            }
        except Exception as e:
            logger.error(f"Error enabling kubeconfig watch: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Disable Kubeconfig Watching",
            destructiveHint=True,
        ),
    )
    def disable_kubeconfig_watching() -> Dict[str, Any]:
        """Disable automatic kubeconfig file watching.

        Stops monitoring kubeconfig files for changes.
        """
        try:
            disable_kubeconfig_watch()
            return {
                "success": True,
                "message": "Kubeconfig watching disabled"
            }
        except Exception as e:
            logger.error(f"Error disabling kubeconfig watch: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Set Stateless Mode",
            destructiveHint=True,
        ),
    )
    def set_server_stateless_mode(
        enabled: bool
    ) -> Dict[str, Any]:
        """Enable or disable stateless mode.

        In stateless mode:
        - API clients are not cached
        - Configuration is reloaded on each request
        - Useful for serverless/Lambda environments
        - Useful when credentials may change frequently

        Args:
            enabled: True to enable stateless mode, False to disable

        Returns:
            New stateless mode status.
        """
        try:
            set_stateless_mode(enabled)
            return {
                "success": True,
                "statelessMode": enabled,
                "message": f"Stateless mode {'enabled' if enabled else 'disabled'}"
            }
        except Exception as e:
            logger.error(f"Error setting stateless mode: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Node Logs",
            readOnlyHint=True,
        ),
    )
    def node_logs_tool(
        name: str,
        query: str = "kubelet",
        tail_lines: int = 100,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get logs from a Kubernetes node via kubelet API proxy.

        This tool retrieves logs from a node's kubelet service or system log files.
        Common service names: kubelet, kube-proxy, containerd, docker.
        For file paths, use the full path like /var/log/syslog or /var/log/messages.

        Args:
            name: Node name
            query: Service name (kubelet, kube-proxy) or log file path (/var/log/syslog)
            tail_lines: Number of lines from end (0 = all lines)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            # Validate node name
            is_valid, error_msg = _validate_node_name(name)
            if not is_valid:
                return {"success": False, "error": error_msg}

            ctx_args = _get_kubectl_context_args(context)

            # Build the proxy URL path
            log_path = query.lstrip("/") if query.startswith("/var/log") else query

            # Use kubectl proxy to access kubelet logs
            cmd = ["kubectl"] + ctx_args + [
                "get", "--raw",
                f"/api/v1/nodes/{name}/proxy/logs/{log_path}"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "not found" in error_msg.lower():
                    return {
                        "success": False,
                        "error": f"Node '{name}' not found or log path '{query}' is invalid",
                        "hint": "Try: kubelet, kube-proxy, or /var/log/syslog"
                    }
                return {"success": False, "error": error_msg}

            # Handle empty or None output
            logs = result.stdout or ""
            if not logs.strip():
                lines = []
                total_lines = 0
            else:
                lines = logs.splitlines()
                total_lines = len(lines)

            # Apply tail_lines if specified
            if tail_lines > 0 and len(lines) > tail_lines:
                lines = lines[-tail_lines:]
                truncated = True
            else:
                truncated = False

            return {
                "success": True,
                "context": context or "current",
                "node": name,
                "query": query,
                "tailLines": tail_lines,
                "truncated": truncated,
                "totalLines": total_lines,
                "returnedLines": len(lines),
                "logs": "\n".join(lines)
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Log retrieval timed out after 60 seconds"}
        except Exception as e:
            logger.error(f"Error getting node logs: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Node Stats Summary",
            readOnlyHint=True,
        ),
    )
    def node_stats_summary_tool(
        name: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get resource usage statistics from node via kubelet Summary API.

        Returns CPU, memory, filesystem, and network usage at node, pod, and
        container levels. On systems with cgroup v2 and kernel 4.20+, may include
        PSI (Pressure Stall Information) metrics.

        This provides more detailed metrics than 'kubectl top nodes' including:
        - Node-level: CPU, memory, filesystem, network, runtime stats
        - Pod-level: CPU, memory, network, volume stats for each pod
        - Container-level: CPU, memory, rootfs, logs usage for each container

        Args:
            name: Node name
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            # Validate node name
            is_valid, error_msg = _validate_node_name(name)
            if not is_valid:
                return {"success": False, "error": error_msg}

            ctx_args = _get_kubectl_context_args(context)

            cmd = ["kubectl"] + ctx_args + [
                "get", "--raw",
                f"/api/v1/nodes/{name}/proxy/stats/summary"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "not found" in error_msg.lower():
                    return {"success": False, "error": f"Node '{name}' not found"}
                return {"success": False, "error": error_msg}

            stats = json.loads(result.stdout)
            node_stats = stats.get("node", {})
            pods_stats = stats.get("pods", [])

            formatted_node = {
                "nodeName": node_stats.get("nodeName"),
                "startTime": node_stats.get("startTime"),
                "cpu": _format_cpu_stats(node_stats.get("cpu", {})),
                "memory": _format_memory_stats(node_stats.get("memory", {})),
                "network": _format_network_stats(node_stats.get("network", {})),
                "fs": _format_fs_stats(node_stats.get("fs", {})),
                "runtime": _format_runtime_stats(node_stats.get("runtime", {})),
                "rlimit": node_stats.get("rlimit", {}),
            }

            # Truncation limits
            pod_limit = 50
            container_limit = 5

            formatted_pods = []
            for pod in pods_stats[:pod_limit]:
                containers = pod.get("containers", [])
                pod_summary = {
                    "podRef": pod.get("podRef", {}),
                    "startTime": pod.get("startTime"),
                    "cpu": _format_cpu_stats(pod.get("cpu", {})),
                    "memory": _format_memory_stats(pod.get("memory", {})),
                    "network": _format_network_stats(pod.get("network", {})),
                    "containers": [],
                    "containersTruncated": len(containers) > container_limit
                }

                for container in containers[:container_limit]:
                    pod_summary["containers"].append({
                        "name": container.get("name"),
                        "cpu": _format_cpu_stats(container.get("cpu", {})),
                        "memory": _format_memory_stats(container.get("memory", {})),
                        "rootfs": _format_fs_stats(container.get("rootfs", {})),
                    })

                formatted_pods.append(pod_summary)

            return {
                "success": True,
                "context": context or "current",
                "nodeName": name,
                "nodeStats": formatted_node,
                "podCount": len(pods_stats),
                "pods": formatted_pods,
                "podLimit": pod_limit,
                "containerLimit": container_limit,
                "podsTruncated": len(pods_stats) > pod_limit,
                "rawStatsAvailable": True
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Failed to parse stats: {e}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Stats retrieval timed out after 120 seconds"}
        except Exception as e:
            logger.error(f"Error getting node stats summary: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Node Top",
            readOnlyHint=True,
        ),
    )
    def node_top_tool(
        name: str = "",
        label_selector: str = "",
        context: str = ""
    ) -> Dict[str, Any]:
        """Get resource consumption (CPU, memory) for nodes from Metrics Server.

        Similar to 'kubectl top nodes' command. Requires metrics-server to be
        installed in the cluster.

        Args:
            name: Specific node name (optional, all nodes if empty)
            label_selector: Label selector to filter nodes (e.g., 'node-role.kubernetes.io/control-plane')
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            ctx_args = _get_kubectl_context_args(context)
            cmd = ["kubectl"] + ctx_args + ["top", "nodes", "--no-headers"]

            if label_selector:
                cmd.extend(["-l", label_selector])

            if name:
                cmd.append(name)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "metrics" in error_msg.lower() or "not available" in error_msg.lower():
                    return {
                        "success": False,
                        "error": "Metrics server not available or not ready",
                        "hint": "Install metrics-server: kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
                    }
                if "not found" in error_msg.lower() and name:
                    return {"success": False, "error": f"Node '{name}' not found"}
                return {"success": False, "error": error_msg}

            metrics = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 5:
                    node_metric = {
                        "node": parts[0],
                        "cpuCores": parts[1],
                        "cpuPercent": parts[2].rstrip("%"),
                        "memoryBytes": parts[3],
                        "memoryPercent": parts[4].rstrip("%"),
                    }
                    metrics.append(node_metric)

            # Use separate counters for valid samples to avoid skewing average
            total_cpu_percent = 0.0
            total_memory_percent = 0.0
            cpu_samples = 0
            memory_samples = 0
            for m in metrics:
                try:
                    total_cpu_percent += float(m["cpuPercent"])
                    cpu_samples += 1
                except (ValueError, TypeError):
                    pass
                try:
                    total_memory_percent += float(m["memoryPercent"])
                    memory_samples += 1
                except (ValueError, TypeError):
                    pass

            return {
                "success": True,
                "context": context or "current",
                "filter": {
                    "name": name or None,
                    "labelSelector": label_selector or None
                },
                "nodeCount": len(metrics),
                "nodes": metrics,
                "clusterAverage": {
                    "cpuPercent": round(total_cpu_percent / cpu_samples, 1) if cpu_samples else None,
                    "memoryPercent": round(total_memory_percent / memory_samples, 1) if memory_samples else None
                } if cpu_samples > 1 or memory_samples > 1 else None
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Metrics retrieval timed out after 60 seconds"}
        except Exception as e:
            logger.error(f"Error getting node top metrics: {e}")
            return {"success": False, "error": str(e)}


def _format_cpu_stats(cpu: Dict) -> Dict[str, Any]:
    """Format CPU statistics from kubelet stats."""
    if not cpu:
        return {}
    return {
        "time": cpu.get("time"),
        "usageNanoCores": cpu.get("usageNanoCores"),
        "usageCoreNanoSeconds": cpu.get("usageCoreNanoSeconds"),
    }


def _format_memory_stats(memory: Dict) -> Dict[str, Any]:
    """Format memory statistics from kubelet stats."""
    if not memory:
        return {}
    return {
        "time": memory.get("time"),
        "availableBytes": memory.get("availableBytes"),
        "usageBytes": memory.get("usageBytes"),
        "workingSetBytes": memory.get("workingSetBytes"),
        "rssBytes": memory.get("rssBytes"),
        "pageFaults": memory.get("pageFaults"),
        "majorPageFaults": memory.get("majorPageFaults"),
    }


def _format_network_stats(network: Dict) -> Dict[str, Any]:
    """Format network statistics from kubelet stats."""
    if not network:
        return {}
    return {
        "time": network.get("time"),
        "rxBytes": network.get("rxBytes"),
        "rxErrors": network.get("rxErrors"),
        "txBytes": network.get("txBytes"),
        "txErrors": network.get("txErrors"),
    }


def _format_fs_stats(fs: Dict) -> Dict[str, Any]:
    """Format filesystem statistics from kubelet stats."""
    if not fs:
        return {}
    return {
        "time": fs.get("time"),
        "availableBytes": fs.get("availableBytes"),
        "capacityBytes": fs.get("capacityBytes"),
        "usedBytes": fs.get("usedBytes"),
        "inodesFree": fs.get("inodesFree"),
        "inodes": fs.get("inodes"),
        "inodesUsed": fs.get("inodesUsed"),
    }


def _format_runtime_stats(runtime: Dict) -> Dict[str, Any]:
    """Format runtime (container runtime) statistics from kubelet stats."""
    if not runtime:
        return {}
    return {
        "imageFs": _format_fs_stats(runtime.get("imageFs", {})),
    }


def register_multicluster_tools(server, non_destructive: bool):
    """Register multi-cluster simultaneous access tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Multi-Cluster Query",
            readOnlyHint=True,
        ),
    )
    def multi_cluster_query(
        contexts: List[str],
        resource: str = "pods",
        namespace: Optional[str] = None,
        label_selector: str = "",
        field_selector: str = ""
    ) -> Dict[str, Any]:
        """Query resources across multiple Kubernetes clusters simultaneously.

        This tool allows you to query the same resource type across multiple clusters
        in a single request, returning aggregated results from all clusters.

        Args:
            contexts: List of context names to query (e.g., ["prod-us", "prod-eu", "staging"])
            resource: Resource type to query (pods, deployments, services, nodes, namespaces)
            namespace: Namespace to query (optional, all namespaces if not specified)
            label_selector: Label selector to filter resources (e.g., "app=nginx")
            field_selector: Field selector to filter resources (e.g., "status.phase=Running")

        Returns:
            Aggregated results from all specified clusters with per-cluster breakdown.

        Examples:
            - Get all pods across prod clusters: multi_cluster_query(contexts=["prod-us", "prod-eu"], resource="pods")
            - Get nginx deployments: multi_cluster_query(contexts=["dev", "staging"], resource="deployments", label_selector="app=nginx")
        """
        import concurrent.futures

        if not contexts:
            return {"success": False, "error": "At least one context must be specified"}

        valid_resources = ["pods", "deployments", "services", "nodes", "namespaces",
                          "configmaps", "secrets", "ingresses", "statefulsets",
                          "daemonsets", "jobs", "cronjobs", "pvcs"]
        if resource not in valid_resources:
            return {
                "success": False,
                "error": f"Invalid resource '{resource}'. Must be one of: {valid_resources}"
            }

        def query_cluster(ctx: str) -> Dict[str, Any]:
            """Query a single cluster."""
            try:
                ctx_args = _get_kubectl_context_args(ctx)
                cmd = ["kubectl"] + ctx_args + ["get", resource, "-o", "json"]

                if namespace:
                    cmd.extend(["-n", namespace])
                else:
                    cmd.append("--all-namespaces")

                if label_selector:
                    cmd.extend(["-l", label_selector])

                if field_selector:
                    cmd.extend(["--field-selector", field_selector])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    return {
                        "context": ctx,
                        "success": False,
                        "error": result.stderr.strip()
                    }

                data = json.loads(result.stdout)
                items = data.get("items", [])

                # Extract summary info based on resource type
                summaries = []
                for item in items:
                    metadata = item.get("metadata", {})
                    summary = {
                        "name": metadata.get("name"),
                        "namespace": metadata.get("namespace"),
                    }

                    # Add resource-specific fields
                    if resource == "pods":
                        status = item.get("status", {})
                        summary["phase"] = status.get("phase")
                        summary["podIP"] = status.get("podIP")
                        summary["nodeName"] = item.get("spec", {}).get("nodeName")
                    elif resource == "deployments":
                        status = item.get("status", {})
                        summary["replicas"] = status.get("replicas", 0)
                        summary["readyReplicas"] = status.get("readyReplicas", 0)
                        summary["availableReplicas"] = status.get("availableReplicas", 0)
                    elif resource == "services":
                        spec = item.get("spec", {})
                        summary["type"] = spec.get("type")
                        summary["clusterIP"] = spec.get("clusterIP")
                        summary["ports"] = [
                            {"port": p.get("port"), "targetPort": p.get("targetPort")}
                            for p in spec.get("ports", [])[:5]  # Limit ports
                        ]
                    elif resource == "nodes":
                        summary["namespace"] = None  # Nodes are cluster-scoped
                        conditions = item.get("status", {}).get("conditions", [])
                        for c in conditions:
                            if c.get("type") == "Ready":
                                summary["ready"] = c.get("status") == "True"
                        node_info = item.get("status", {}).get("nodeInfo", {})
                        summary["kubeletVersion"] = node_info.get("kubeletVersion")
                    elif resource == "namespaces":
                        summary["namespace"] = None
                        summary["phase"] = item.get("status", {}).get("phase")

                    summaries.append(summary)

                return {
                    "context": ctx,
                    "success": True,
                    "count": len(items),
                    "items": summaries
                }
            except subprocess.TimeoutExpired:
                return {"context": ctx, "success": False, "error": "Query timed out"}
            except json.JSONDecodeError as e:
                return {"context": ctx, "success": False, "error": f"Invalid JSON: {e}"}
            except Exception as e:
                return {"context": ctx, "success": False, "error": str(e)}

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(contexts), 10)) as executor:
            future_to_ctx = {executor.submit(query_cluster, ctx): ctx for ctx in contexts}
            for future in concurrent.futures.as_completed(future_to_ctx):
                results.append(future.result())

        results.sort(key=lambda x: x.get("context", ""))
        total_items = sum(r.get("count", 0) for r in results if r.get("success"))
        successful_clusters = sum(1 for r in results if r.get("success"))
        failed_clusters = len(results) - successful_clusters

        return {
            "success": successful_clusters > 0,
            "query": {
                "resource": resource,
                "namespace": namespace or "all",
                "labelSelector": label_selector or None,
                "fieldSelector": field_selector or None,
            },
            "summary": {
                "totalClusters": len(contexts),
                "successfulClusters": successful_clusters,
                "failedClusters": failed_clusters,
                "totalItems": total_items
            },
            "clusters": results
        }

    @server.tool(
        annotations=ToolAnnotations(
            title="Multi-Cluster Health Check",
            readOnlyHint=True,
        ),
    )
    def multi_cluster_health(
        contexts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Check health status across multiple Kubernetes clusters.

        Performs connectivity and version checks across specified clusters or all
        available contexts if none specified.

        Args:
            contexts: List of context names to check (optional, uses all contexts if not specified)

        Returns:
            Health status for each cluster including version, node count, and connectivity.
        """
        import concurrent.futures

        if not contexts:
            try:
                all_contexts = list_contexts()
                contexts = [c.get("name") for c in all_contexts if c.get("name")]
            except Exception as e:
                return {"success": False, "error": f"Failed to list contexts: {e}"}

        if not contexts:
            return {"success": False, "error": "No contexts available"}

        def check_cluster(ctx: str) -> Dict[str, Any]:
            """Check health of a single cluster."""
            cluster_health = {
                "context": ctx,
                "reachable": False,
                "version": None,
                "nodeCount": None,
                "readyNodes": None,
                "error": None
            }

            try:
                # Check version (tests API connectivity)
                version_api = get_version_client(ctx)
                version_info = version_api.get_code()
                cluster_health["reachable"] = True
                cluster_health["version"] = version_info.git_version

                # Get node count
                v1 = get_k8s_client(ctx)
                nodes = v1.list_node()
                cluster_health["nodeCount"] = len(nodes.items)

                ready_count = 0
                for node in nodes.items:
                    for condition in (node.status.conditions or []):
                        if condition.type == "Ready" and condition.status == "True":
                            ready_count += 1
                            break
                cluster_health["readyNodes"] = ready_count

            except Exception as e:
                cluster_health["error"] = str(e)

            return cluster_health

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(contexts), 10)) as executor:
            future_to_ctx = {executor.submit(check_cluster, ctx): ctx for ctx in contexts}
            for future in concurrent.futures.as_completed(future_to_ctx):
                results.append(future.result())

        results.sort(key=lambda x: x.get("context", ""))
        reachable = sum(1 for r in results if r.get("reachable"))
        total_nodes = sum(r.get("nodeCount", 0) or 0 for r in results)
        ready_nodes = sum(r.get("readyNodes", 0) or 0 for r in results)

        return {
            "success": reachable > 0,
            "summary": {
                "totalClusters": len(contexts),
                "reachableClusters": reachable,
                "unreachableClusters": len(contexts) - reachable,
                "totalNodes": total_nodes,
                "readyNodes": ready_nodes
            },
            "clusters": results
        }

    @server.tool(
        annotations=ToolAnnotations(
            title="Multi-Cluster Pod Count",
            readOnlyHint=True,
        ),
    )
    def multi_cluster_pod_count(
        contexts: Optional[List[str]] = None,
        namespace: Optional[str] = None,
        group_by: str = "status"
    ) -> Dict[str, Any]:
        """Get pod counts across multiple clusters grouped by status or namespace.

        Quickly see pod distribution across your clusters without fetching full pod details.

        Args:
            contexts: List of context names (optional, uses all contexts if not specified)
            namespace: Filter by namespace (optional, all namespaces if not specified)
            group_by: How to group results: "status" (Running/Pending/etc) or "namespace"

        Returns:
            Pod counts per cluster with grouping breakdown.
        """
        import concurrent.futures

        if group_by not in ["status", "namespace"]:
            return {"success": False, "error": "group_by must be 'status' or 'namespace'"}

        if not contexts:
            try:
                all_contexts = list_contexts()
                contexts = [c.get("name") for c in all_contexts if c.get("name")]
            except Exception as e:
                return {"success": False, "error": f"Failed to list contexts: {e}"}

        if not contexts:
            return {"success": False, "error": "No contexts available"}

        def count_pods(ctx: str) -> Dict[str, Any]:
            """Count pods in a single cluster."""
            try:
                v1 = get_k8s_client(ctx)

                if namespace:
                    pods = v1.list_namespaced_pod(namespace)
                else:
                    pods = v1.list_pod_for_all_namespaces()

                counts = {}
                total = 0

                for pod in pods.items:
                    total += 1
                    if group_by == "status":
                        key = pod.status.phase or "Unknown"
                    else:  # namespace
                        key = pod.metadata.namespace

                    counts[key] = counts.get(key, 0) + 1

                return {
                    "context": ctx,
                    "success": True,
                    "total": total,
                    "breakdown": counts
                }
            except Exception as e:
                return {"context": ctx, "success": False, "error": str(e)}

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(contexts), 10)) as executor:
            future_to_ctx = {executor.submit(count_pods, ctx): ctx for ctx in contexts}
            for future in concurrent.futures.as_completed(future_to_ctx):
                results.append(future.result())

        results.sort(key=lambda x: x.get("context", ""))
        aggregate = {}
        total_pods = 0
        for r in results:
            if r.get("success"):
                total_pods += r.get("total", 0)
                for key, count in r.get("breakdown", {}).items():
                    aggregate[key] = aggregate.get(key, 0) + count

        return {
            "success": any(r.get("success") for r in results),
            "query": {
                "namespace": namespace or "all",
                "groupBy": group_by
            },
            "summary": {
                "totalClusters": len(contexts),
                "totalPods": total_pods,
                "aggregateBreakdown": aggregate
            },
            "clusters": results
        }
