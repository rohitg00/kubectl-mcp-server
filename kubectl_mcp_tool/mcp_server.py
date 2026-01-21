#!/usr/bin/env python3
"""
MCP server implementation for kubectl-mcp-tool.

Compatible with:
- Claude Desktop
- Cursor AI
- Windsurf
- Docker MCP Toolkit (https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)
"""

import json
import sys
import logging
import asyncio
import os
import platform
from typing import Dict, Any, List, Optional, Callable, Awaitable

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import warnings
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    message=r".*found in sys.modules after import of package.*"
)

_log_file = os.environ.get("MCP_LOG_FILE")
_log_level = logging.DEBUG if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true") else logging.INFO

_handlers: List[logging.Handler] = []
if _log_file:
    try:
        os.makedirs(os.path.dirname(_log_file), exist_ok=True)
        _handlers.append(logging.FileHandler(_log_file))
    except (OSError, ValueError):
        _handlers.append(logging.StreamHandler(sys.stderr))
else:
    _handlers.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(
    level=_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=_handlers
)
logger = logging.getLogger("mcp-server")

for handler in logging.root.handlers[:]:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        logging.root.removeHandler(handler)

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations
except ImportError:
    logger.error("MCP SDK not found. Installing...")
    import subprocess
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "mcp>=1.8.0"],
            stdout=subprocess.DEVNULL,  # Don't pollute stdout
            stderr=subprocess.DEVNULL
        )
        from mcp.server.fastmcp import FastMCP
        from mcp.types import ToolAnnotations
    except Exception as e:
        logger.error(f"Failed to install MCP SDK: {e}")
        raise

from .natural_language import process_query

class MCPServer:
    """MCP server implementation."""

    def __init__(self, name: str, non_destructive: bool = False):
        """Initialize the MCP server."""
        self.name = name
        self.non_destructive = non_destructive
        self.server = FastMCP(name=name)
        self._dependencies_checked = False
        self._dependencies_available = None
        self.setup_tools()
        self.setup_prompts()
    
    @property
    def dependencies_available(self) -> bool:
        """Lazy check for dependencies (only runs once, on first access)."""
        if not self._dependencies_checked:
            self._dependencies_available = self._check_dependencies()
            self._dependencies_checked = True
            if not self._dependencies_available:
                logger.warning("Some dependencies are missing. Certain operations may not work correctly.")
        return self._dependencies_available
    
    def setup_tools(self):
        """Set up the tools for the MCP server."""
        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Pods",
                readOnlyHint=True,
            ),
        )
        def get_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get all pods in the specified namespace."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                
                if namespace:
                    pods = v1.list_namespaced_pod(namespace)
                else:
                    pods = v1.list_pod_for_all_namespaces()
                
                return {
                    "success": True,
                    "pods": [
                        {
                            "name": pod.metadata.name,
                            "namespace": pod.metadata.namespace,
                            "status": pod.status.phase,
                            "ip": pod.status.pod_ip
                        }
                        for pod in pods.items
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting pods: {e}")
                return {"success": False, "error": str(e)}
        
        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Namespaces",
                readOnlyHint=True,
            ),
        )
        def get_namespaces() -> Dict[str, Any]:
            """Get all Kubernetes namespaces."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                namespaces = v1.list_namespace()
                return {
                    "success": True,
                    "namespaces": [ns.metadata.name for ns in namespaces.items]
                }
            except Exception as e:
                logger.error(f"Error getting namespaces: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Services",
                readOnlyHint=True,
            ),
        )
        def get_services(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get all services in the specified namespace."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                if namespace:
                    services = v1.list_namespaced_service(namespace)
                else:
                    services = v1.list_service_for_all_namespaces()
                return {
                    "success": True,
                    "services": [
                        {
                            "name": svc.metadata.name,
                            "namespace": svc.metadata.namespace,
                            "type": svc.spec.type,
                            "cluster_ip": svc.spec.cluster_ip
                        } for svc in services.items
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting services: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Nodes",
                readOnlyHint=True,
            ),
        )
        def get_nodes() -> Dict[str, Any]:
            """Get all nodes in the cluster."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                nodes = v1.list_node()
                return {
                    "success": True,
                    "nodes": [
                        {
                            "name": node.metadata.name,
                            "status": (
                                "Ready"
                                if any(
                                    cond.type == "Ready" and cond.status == "True"
                                    for cond in node.status.conditions
                                )
                                else "NotReady"
                            ),
                            "addresses": [
                                addr.address for addr in node.status.addresses
                            ],
                        }
                        for node in nodes.items
                    ],
                }
            except Exception as e:
                logger.error(f"Error getting nodes: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get ConfigMaps",
                readOnlyHint=True,
            ),
        )
        def get_configmaps(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get all ConfigMaps in the specified namespace."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                if namespace:
                    cms = v1.list_namespaced_config_map(namespace)
                else:
                    cms = v1.list_config_map_for_all_namespaces()
                return {
                    "success": True,
                    "configmaps": [
                        {
                            "name": cm.metadata.name,
                            "namespace": cm.metadata.namespace,
                            "data": cm.data
                        } for cm in cms.items
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting ConfigMaps: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Secrets",
                readOnlyHint=True,
            ),
        )
        def get_secrets(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get all Secrets in the specified namespace."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                if namespace:
                    secrets = v1.list_namespaced_secret(namespace)
                else:
                    secrets = v1.list_secret_for_all_namespaces()
                return {
                    "success": True,
                    "secrets": [
                        {
                            "name": secret.metadata.name,
                            "namespace": secret.metadata.namespace,
                            "type": secret.type
                        } for secret in secrets.items
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting Secrets: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Install Helm Chart",
                destructiveHint=True,
            ),
        )
        def install_helm_chart(name: str, chart: str, namespace: str, repo: Optional[str] = None, values: Optional[dict] = None) -> Dict[str, Any]:
            """Install a Helm chart."""
            if self.non_destructive:
                return {"success": False, "error": "Blocked: non-destructive mode"}
            if not self._check_helm_availability():
                return {"success": False, "error": "Helm is not available on this system"}
            
            try:
                import subprocess, tempfile, yaml, os
                
                # Handle repo addition as a separate step if provided
                if repo:
                    try:
                        # Add the repository (assumed format: "repo_name=repo_url")
                        repo_parts = repo.split('=')
                        if len(repo_parts) != 2:
                            return {"success": False, "error": "Repository format should be 'repo_name=repo_url'"}
                        
                        repo_name, repo_url = repo_parts
                        repo_add_cmd = ["helm", "repo", "add", repo_name, repo_url]
                        logger.debug(f"Running command: {' '.join(repo_add_cmd)}")
                        subprocess.check_output(repo_add_cmd, stderr=subprocess.PIPE, text=True)
                        
                        # Update repositories
                        repo_update_cmd = ["helm", "repo", "update"]
                        logger.debug(f"Running command: {' '.join(repo_update_cmd)}")
                        subprocess.check_output(repo_update_cmd, stderr=subprocess.PIPE, text=True)
                        
                        # Use the chart with repo prefix if needed
                        if '/' not in chart:
                            chart = f"{repo_name}/{chart}"
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Error adding Helm repo: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                        return {"success": False, "error": f"Failed to add Helm repo: {e.stderr if hasattr(e, 'stderr') else str(e)}"}
                
                # Prepare the install command
                cmd = ["helm", "install", name, chart, "-n", namespace]
                
                # Create namespace if it doesn't exist
                try:
                    ns_cmd = ["kubectl", "get", "namespace", namespace]
                    subprocess.check_output(ns_cmd, stderr=subprocess.PIPE, text=True)
                except subprocess.CalledProcessError:
                    logger.info(f"Namespace {namespace} not found, creating it")
                    create_ns_cmd = ["kubectl", "create", "namespace", namespace]
                    try:
                        subprocess.check_output(create_ns_cmd, stderr=subprocess.PIPE, text=True)
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Error creating namespace: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                        return {"success": False, "error": f"Failed to create namespace: {e.stderr if hasattr(e, 'stderr') else str(e)}"}
                
                # Handle values file if provided
                values_file = None
                try:
                    if values:
                        with tempfile.NamedTemporaryFile("w", delete=False) as f:
                            yaml.dump(values, f)
                            values_file = f.name
                        cmd += ["-f", values_file]
                    
                    # Execute the install command
                    logger.debug(f"Running command: {' '.join(cmd)}")
                    result = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)
                    
                    return {
                        "success": True, 
                        "message": f"Helm chart {chart} installed as {name} in {namespace}",
                        "details": result
                    }
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                    logger.error(f"Error installing Helm chart: {error_msg}")
                    return {"success": False, "error": f"Failed to install Helm chart: {error_msg}"}
                finally:
                    # Clean up the temporary values file
                    if values_file and os.path.exists(values_file):
                        os.unlink(values_file)
            except Exception as e:
                logger.error(f"Unexpected error installing Helm chart: {str(e)}")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Upgrade Helm Chart",
                destructiveHint=True,
            ),
        )
        def upgrade_helm_chart(name: str, chart: str, namespace: str, repo: Optional[str] = None, values: Optional[dict] = None) -> Dict[str, Any]:
            """Upgrade a Helm release."""
            if self.non_destructive:
                return {"success": False, "error": "Blocked: non-destructive mode"}
            if not self._check_helm_availability():
                return {"success": False, "error": "Helm is not available on this system"}
            
            try:
                import subprocess, tempfile, yaml, os
                
                # Handle repo addition as a separate step if provided
                if repo:
                    try:
                        # Add the repository (assumed format: "repo_name=repo_url")
                        repo_parts = repo.split('=')
                        if len(repo_parts) != 2:
                            return {"success": False, "error": "Repository format should be 'repo_name=repo_url'"}
                        
                        repo_name, repo_url = repo_parts
                        repo_add_cmd = ["helm", "repo", "add", repo_name, repo_url]
                        logger.debug(f"Running command: {' '.join(repo_add_cmd)}")
                        subprocess.check_output(repo_add_cmd, stderr=subprocess.PIPE, text=True)
                        
                        # Update repositories
                        repo_update_cmd = ["helm", "repo", "update"]
                        logger.debug(f"Running command: {' '.join(repo_update_cmd)}")
                        subprocess.check_output(repo_update_cmd, stderr=subprocess.PIPE, text=True)
                        
                        # Use the chart with repo prefix if needed
                        if '/' not in chart:
                            chart = f"{repo_name}/{chart}"
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Error adding Helm repo: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                        return {"success": False, "error": f"Failed to add Helm repo: {e.stderr if hasattr(e, 'stderr') else str(e)}"}
                
                # Prepare the upgrade command
                cmd = ["helm", "upgrade", name, chart, "-n", namespace]
                
                # Handle values file if provided
                values_file = None
                try:
                    if values:
                        with tempfile.NamedTemporaryFile("w", delete=False) as f:
                            yaml.dump(values, f)
                            values_file = f.name
                        cmd += ["-f", values_file]
                    
                    # Execute the upgrade command
                    logger.debug(f"Running command: {' '.join(cmd)}")
                    result = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)
                    
                    return {
                        "success": True, 
                        "message": f"Helm release {name} upgraded with chart {chart} in {namespace}",
                        "details": result
                    }
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                    logger.error(f"Error upgrading Helm chart: {error_msg}")
                    return {"success": False, "error": f"Failed to upgrade Helm chart: {error_msg}"}
                finally:
                    # Clean up the temporary values file
                    if values_file and os.path.exists(values_file):
                        os.unlink(values_file)
            except Exception as e:
                logger.error(f"Unexpected error upgrading Helm chart: {str(e)}")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Uninstall Helm Chart",
                destructiveHint=True,
            ),
        )
        def uninstall_helm_chart(name: str, namespace: str) -> Dict[str, Any]:
            """Uninstall a Helm release."""
            if self.non_destructive:
                return {"success": False, "error": "Blocked: non-destructive mode"}
            if not self._check_helm_availability():
                return {"success": False, "error": "Helm is not available on this system"}
                
            try:
                import subprocess
                cmd = ["helm", "uninstall", name, "-n", namespace]
                logger.debug(f"Running command: {' '.join(cmd)}")
                
                try:
                    result = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)
                    return {
                        "success": True, 
                        "message": f"Helm release {name} uninstalled from {namespace}",
                        "details": result
                    }
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                    logger.error(f"Error uninstalling Helm chart: {error_msg}")
                    return {"success": False, "error": f"Failed to uninstall Helm chart: {error_msg}"}
            except Exception as e:
                logger.error(f"Unexpected error uninstalling Helm chart: {str(e)}")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get RBAC Roles",
                readOnlyHint=True,
            ),
        )
        def get_rbac_roles(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get all RBAC roles in the specified namespace."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                rbac = client.RbacAuthorizationV1Api()
                if namespace:
                    roles = rbac.list_namespaced_role(namespace)
                else:
                    roles = rbac.list_role_for_all_namespaces()
                return {
                    "success": True,
                    "roles": [role.metadata.name for role in roles.items]
                }
            except Exception as e:
                logger.error(f"Error getting RBAC roles: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Cluster Roles",
                readOnlyHint=True,
            ),
        )
        def get_cluster_roles() -> Dict[str, Any]:
            """Get all cluster-wide RBAC roles."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                rbac = client.RbacAuthorizationV1Api()
                roles = rbac.list_cluster_role()
                return {
                    "success": True,
                    "cluster_roles": [role.metadata.name for role in roles.items]
                }
            except Exception as e:
                logger.error(f"Error getting cluster roles: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Events",
                readOnlyHint=True,
            ),
        )
        def get_events(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get all events in the specified namespace."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                if namespace:
                    events = v1.list_namespaced_event(namespace)
                else:
                    events = v1.list_event_for_all_namespaces()
                return {
                    "success": True,
                    "events": [
                        {
                            "name": event.metadata.name,
                            "namespace": event.metadata.namespace,
                            "type": event.type,
                            "reason": event.reason,
                            "message": event.message
                        } for event in events.items
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting events: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Resource Usage",
                readOnlyHint=True,
            ),
        )
        def get_resource_usage(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get resource usage statistics via kubectl top."""
            if not self._check_kubectl_availability():
                return {"success": False, "error": "kubectl is not available on this system"}
                
            try:
                import subprocess
                import json
                
                # Get pod resource usage
                pod_cmd = ["kubectl", "top", "pods", "--no-headers"]
                if namespace:
                    pod_cmd += ["-n", namespace]
                else:
                    pod_cmd += ["--all-namespaces"]
                
                pod_cmd += ["-o", "json"]
                
                # If the cluster doesn't support JSON output format for top command,
                # fall back to parsing text output
                try:
                    pod_output = subprocess.check_output(pod_cmd, stderr=subprocess.PIPE, text=True)
                    pod_data = json.loads(pod_output)
                except (subprocess.CalledProcessError, json.JSONDecodeError):
                    # Fall back to text output and manual parsing
                    pod_cmd = ["kubectl", "top", "pods"]
                    if namespace:
                        pod_cmd += ["-n", namespace]
                    else:
                        pod_cmd += ["--all-namespaces"]
                    
                    pod_output = subprocess.check_output(pod_cmd, stderr=subprocess.PIPE, text=True)
                    pod_data = {"text_output": pod_output}
                
                # Get node resource usage
                try:
                    node_cmd = ["kubectl", "top", "nodes", "--no-headers", "-o", "json"]
                    node_output = subprocess.check_output(node_cmd, stderr=subprocess.PIPE, text=True)
                    node_data = json.loads(node_output)
                except (subprocess.CalledProcessError, json.JSONDecodeError):
                    # Fall back to text output
                    node_cmd = ["kubectl", "top", "nodes"]
                    node_output = subprocess.check_output(node_cmd, stderr=subprocess.PIPE, text=True)
                    node_data = {"text_output": node_output}
                
                return {
                    "success": True, 
                    "pod_usage": pod_data,
                    "node_usage": node_data
                }
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
                logger.error(f"Error getting resource usage: {error_msg}")
                return {"success": False, "error": f"Failed to get resource usage: {error_msg}"}
            except Exception as e:
                logger.error(f"Unexpected error getting resource usage: {str(e)}")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Switch Context",
                destructiveHint=True,
            ),
        )
        def switch_context(context_name: str) -> Dict[str, Any]:
            """Switch current kubeconfig context."""
            try:
                import subprocess
                cmd = ["kubectl", "config", "use-context", context_name]
                subprocess.check_output(cmd)
                return {"success": True, "message": f"Switched context to {context_name}"}
            except Exception as e:
                logger.error(f"Error switching context: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Current Context",
                readOnlyHint=True,
            ),
        )
        def get_current_context() -> Dict[str, Any]:
            """Get current kubeconfig context."""
            try:
                import subprocess
                cmd = ["kubectl", "config", "current-context"]
                output = subprocess.check_output(cmd, text=True).strip()
                return {"success": True, "context": output}
            except Exception as e:
                logger.error(f"Error getting current context: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="List Contexts",
                readOnlyHint=True,
            ),
        )
        def list_contexts() -> Dict[str, Any]:
            """List all available kubeconfig contexts for multi-cluster support."""
            try:
                import subprocess
                cmd = ["kubectl", "config", "get-contexts", "-o", "name"]
                output = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
                contexts = [ctx.strip() for ctx in output.strip().split('\n') if ctx.strip()]
                
                # Get current context
                current_cmd = ["kubectl", "config", "current-context"]
                try:
                    current = subprocess.check_output(current_cmd, text=True, stderr=subprocess.PIPE).strip()
                except subprocess.CalledProcessError:
                    current = None
                
                return {
                    "success": True,
                    "contexts": contexts,
                    "current_context": current,
                    "total": len(contexts)
                }
            except Exception as e:
                logger.error(f"Error listing contexts: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Context Details",
                readOnlyHint=True,
            ),
        )
        def get_context_details(context_name: str) -> Dict[str, Any]:
            """Get detailed information about a specific kubeconfig context."""
            try:
                import subprocess
                import json as json_module
                
                # Get the context info using kubectl config view
                cmd = ["kubectl", "config", "view", "-o", "json"]
                output = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
                config_data = json_module.loads(output)
                
                # Find the specific context
                context_info = None
                for ctx in config_data.get("contexts", []):
                    if ctx.get("name") == context_name:
                        context_info = ctx
                        break
                
                if not context_info:
                    return {"success": False, "error": f"Context '{context_name}' not found"}
                
                # Get cluster info
                cluster_name = context_info.get("context", {}).get("cluster")
                cluster_info = None
                for cluster in config_data.get("clusters", []):
                    if cluster.get("name") == cluster_name:
                        cluster_info = cluster
                        break
                
                # Get user info (without sensitive data)
                user_name = context_info.get("context", {}).get("user")
                
                return {
                    "success": True,
                    "context_name": context_name,
                    "cluster_name": cluster_name,
                    "cluster_server": cluster_info.get("cluster", {}).get("server") if cluster_info else None,
                    "namespace": context_info.get("context", {}).get("namespace", "default"),
                    "user": user_name
                }
            except Exception as e:
                logger.error(f"Error getting context details: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Set Namespace for Context",
                destructiveHint=True,
            ),
        )
        def set_namespace_for_context(namespace: str, context_name: Optional[str] = None) -> Dict[str, Any]:
            """Set the default namespace for a context. If no context specified, uses current context."""
            try:
                import subprocess
                
                # If no context specified, use current context
                if not context_name:
                    current_cmd = ["kubectl", "config", "current-context"]
                    context_name = subprocess.check_output(current_cmd, text=True, stderr=subprocess.PIPE).strip()
                
                cmd = ["kubectl", "config", "set-context", context_name, "--namespace", namespace]
                subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
                
                return {
                    "success": True,
                    "message": f"Set namespace to '{namespace}' for context '{context_name}'"
                }
            except Exception as e:
                logger.error(f"Error setting namespace: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Cluster Info",
                readOnlyHint=True,
            ),
        )
        def get_cluster_info() -> Dict[str, Any]:
            """Get detailed cluster information for the current context."""
            try:
                import subprocess
                cmd = ["kubectl", "cluster-info"]
                output = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
                
                # Get version info
                version_cmd = ["kubectl", "version", "-o", "json"]
                try:
                    version_output = subprocess.check_output(version_cmd, text=True, stderr=subprocess.PIPE)
                    import json as json_module
                    version_data = json_module.loads(version_output)
                except (subprocess.CalledProcessError, json.JSONDecodeError):
                    version_data = None
                
                return {
                    "success": True,
                    "cluster_info": output,
                    "version": version_data
                }
            except Exception as e:
                logger.error(f"Error getting cluster info: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Kubectl Explain",
                readOnlyHint=True,
            ),
        )
        def kubectl_explain(resource: str) -> Dict[str, Any]:
            """Explain a Kubernetes resource using kubectl explain."""
            try:
                import subprocess
                cmd = ["kubectl", "explain", resource]
                output = subprocess.check_output(cmd, text=True)
                return {"success": True, "explanation": output}
            except Exception as e:
                logger.error(f"Error explaining resource: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get API Resources",
                readOnlyHint=True,
            ),
        )
        def get_api_resources() -> Dict[str, Any]:
            """List Kubernetes API resources."""
            try:
                import subprocess
                cmd = ["kubectl", "api-resources"]
                output = subprocess.check_output(cmd, text=True)
                return {"success": True, "resources": output}
            except Exception as e:
                logger.error(f"Error getting api-resources: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Health Check",
                readOnlyHint=True,
            ),
        )
        def health_check() -> Dict[str, Any]:
            """Check cluster health by pinging the API server."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                v1.get_api_resources()
                return {"success": True, "message": "Cluster API is reachable"}
            except Exception as e:
                logger.error(f"Cluster health check failed: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Pod Events",
                readOnlyHint=True,
            ),
        )
        def get_pod_events(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
            """Get events for a specific pod."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                field_selector = f"involvedObject.name={pod_name}"
                events = v1.list_namespaced_event(namespace, field_selector=field_selector)
                return {
                    "success": True,
                    "events": [
                        {
                            "name": event.metadata.name,
                            "type": event.type,
                            "reason": event.reason,
                            "message": event.message,
                            "timestamp": event.last_timestamp.isoformat() if event.last_timestamp else None
                        } for event in events.items
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting pod events: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Check Pod Health",
                readOnlyHint=True,
            ),
        )
        def check_pod_health(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
            """Check the health status of a pod."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                pod = v1.read_namespaced_pod(pod_name, namespace)
                status = pod.status
                return {
                    "success": True,
                    "phase": status.phase,
                    "conditions": [c.type for c in status.conditions] if status.conditions else []
                }
            except Exception as e:
                logger.error(f"Error checking pod health: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Deployments",
                readOnlyHint=True,
            ),
        )
        def get_deployments(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get all deployments in the specified namespace."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                apps_v1 = client.AppsV1Api()
                if namespace:
                    deployments = apps_v1.list_namespaced_deployment(namespace)
                else:
                    deployments = apps_v1.list_deployment_for_all_namespaces()
                return {
                    "success": True,
                    "deployments": [
                        {
                            "name": d.metadata.name,
                            "namespace": d.metadata.namespace,
                            "replicas": d.status.replicas
                        } for d in deployments.items
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting deployments: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Create Deployment",
                destructiveHint=True,
            ),
        )
        def create_deployment(name: str, image: str, replicas: int, namespace: Optional[str] = "default") -> Dict[str, Any]:
            """Create a new deployment."""
            if self.non_destructive:
                return {"success": False, "error": "Blocked: non-destructive mode"}
            try:
                from kubernetes import client, config
                config.load_kube_config()
                apps_v1 = client.AppsV1Api()
                
                deployment = client.V1Deployment(
                    metadata=client.V1ObjectMeta(name=name),
                    spec=client.V1DeploymentSpec(
                        replicas=replicas,
                        selector=client.V1LabelSelector(
                            match_labels={"app": name}
                        ),
                        template=client.V1PodTemplateSpec(
                            metadata=client.V1ObjectMeta(
                                labels={"app": name}
                            ),
                            spec=client.V1PodSpec(
                                containers=[
                                    client.V1Container(
                                        name=name,
                                        image=image
                                    )
                                ]
                            )
                        )
                    )
                )
                
                apps_v1.create_namespaced_deployment(
                    body=deployment,
                    namespace=namespace
                )
                
                return {
                    "success": True,
                    "message": f"Deployment {name} created successfully"
                }
            except Exception as e:
                logger.error(f"Error creating deployment: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Delete Resource",
                destructiveHint=True,
            ),
        )
        def delete_resource(resource_type: str, name: str, namespace: Optional[str] = "default") -> Dict[str, Any]:
            """Delete a Kubernetes resource."""
            if self.non_destructive:
                return {"success": False, "error": "Blocked: non-destructive mode"}
            try:
                from kubernetes import client, config
                config.load_kube_config()
                
                if resource_type == "pod":
                    v1 = client.CoreV1Api()
                    v1.delete_namespaced_pod(name=name, namespace=namespace)
                elif resource_type == "deployment":
                    apps_v1 = client.AppsV1Api()
                    apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
                elif resource_type == "service":
                    v1 = client.CoreV1Api()
                    v1.delete_namespaced_service(name=name, namespace=namespace)
                else:
                    return {"success": False, "error": f"Unsupported resource type: {resource_type}"}
                
                return {
                    "success": True,
                    "message": f"{resource_type} {name} deleted successfully"
                }
            except Exception as e:
                logger.error(f"Error deleting resource: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Logs",
                readOnlyHint=True,
            ),
        )
        def get_logs(pod_name: str, namespace: Optional[str] = "default", container: Optional[str] = None, tail: Optional[int] = None) -> Dict[str, Any]:
            """Get logs from a pod."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                
                logs = v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=namespace,
                    container=container,
                    tail_lines=tail
                )
                
                return {
                    "success": True,
                    "logs": logs
                }
            except Exception as e:
                logger.error(f"Error getting logs: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Port Forward",
                destructiveHint=True,
            ),
        )
        def port_forward(pod_name: str, local_port: int, pod_port: int, namespace: Optional[str] = "default") -> Dict[str, Any]:
            """Forward local port to pod port."""
            try:
                import subprocess
                
                cmd = [
                    "kubectl", "port-forward",
                    f"pod/{pod_name}",
                    f"{local_port}:{pod_port}",
                    "-n", namespace
                ]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                return {
                    "success": True,
                    "message": f"Port forwarding started: localhost:{local_port} -> {pod_name}:{pod_port}",
                    "process_pid": process.pid
                }
            except Exception as e:
                logger.error(f"Error setting up port forward: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Scale Deployment",
                destructiveHint=True,
            ),
        )
        def scale_deployment(name: str, replicas: int, namespace: Optional[str] = "default") -> Dict[str, Any]:
            """Scale a deployment."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                apps_v1 = client.AppsV1Api()
                
                # Get the deployment
                deployment = apps_v1.read_namespaced_deployment(
                    name=name,
                    namespace=namespace
                )
                
                # Update replicas
                deployment.spec.replicas = replicas
                
                # Apply the update
                apps_v1.patch_namespaced_deployment(
                    name=name,
                    namespace=namespace,
                    body=deployment
                )
                
                return {
                    "success": True,
                    "message": f"Deployment {name} scaled to {replicas} replicas"
                }
            except Exception as e:
                logger.error(f"Error scaling deployment: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Kubectl Apply",
                destructiveHint=True,
            ),
        )
        def kubectl_apply(manifest: str, namespace: Optional[str] = "default") -> Dict[str, Any]:
            """Apply a YAML manifest to the cluster."""
            if self.non_destructive:
                return {"success": False, "error": "Blocked: non-destructive mode"}
            try:
                import subprocess
                import tempfile
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                    f.write(manifest)
                    temp_path = f.name
                
                cmd = ["kubectl", "apply", "-f", temp_path, "-n", namespace]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                import os
                os.unlink(temp_path)
                
                if result.returncode == 0:
                    return {"success": True, "output": result.stdout.strip()}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error applying manifest: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Kubectl Describe",
                readOnlyHint=True,
            ),
        )
        def kubectl_describe(resource_type: str, name: str, namespace: Optional[str] = "default") -> Dict[str, Any]:
            """Describe a Kubernetes resource in detail."""
            try:
                import subprocess
                cmd = ["kubectl", "describe", resource_type, name, "-n", namespace]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return {"success": True, "description": result.stdout}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error describing resource: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Kubectl Generic",
                readOnlyHint=True,
            ),
        )
        def kubectl_generic(command: str) -> Dict[str, Any]:
            """Execute any kubectl command. Use with caution."""
            try:
                import subprocess
                import shlex
                
                # Security: validate command starts with allowed operations
                allowed_prefixes = [
                    "get", "describe", "logs", "top", "explain", "api-resources",
                    "config", "version", "cluster-info", "auth"
                ]
                cmd_parts = shlex.split(command)
                if not cmd_parts:
                    return {"success": False, "error": "Empty command"}
                
                # Remove 'kubectl' prefix if present
                if cmd_parts[0] == "kubectl":
                    cmd_parts = cmd_parts[1:]
                
                if not cmd_parts or cmd_parts[0] not in allowed_prefixes:
                    return {
                        "success": False, 
                        "error": f"Command not allowed. Allowed: {', '.join(allowed_prefixes)}"
                    }
                
                full_cmd = ["kubectl"] + cmd_parts
                result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
                
                output = self._mask_secrets(result.stdout) if "secret" in command.lower() else result.stdout
                
                return {
                    "success": result.returncode == 0,
                    "output": output,
                    "error": result.stderr if result.returncode != 0 else None
                }
            except Exception as e:
                logger.error(f"Error running kubectl command: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Kubectl Patch",
                destructiveHint=True,
            ),
        )
        def kubectl_patch(resource_type: str, name: str, patch: str, patch_type: str = "strategic", namespace: Optional[str] = "default") -> Dict[str, Any]:
            """Patch a Kubernetes resource."""
            try:
                import subprocess
                
                type_flag = {
                    "strategic": "strategic",
                    "merge": "merge",
                    "json": "json"
                }.get(patch_type, "strategic")
                
                cmd = [
                    "kubectl", "patch", resource_type, name,
                    "-n", namespace,
                    "--type", type_flag,
                    "-p", patch
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    return {"success": True, "output": result.stdout.strip()}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error patching resource: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Kubectl Rollout",
                destructiveHint=True,
            ),
        )
        def kubectl_rollout(action: str, resource_type: str, name: str, namespace: Optional[str] = "default") -> Dict[str, Any]:
            """Manage rollouts (restart, status, history, undo, pause, resume)."""
            try:
                import subprocess
                
                allowed_actions = ["status", "history", "restart", "undo", "pause", "resume"]
                if action not in allowed_actions:
                    return {"success": False, "error": f"Invalid action. Allowed: {', '.join(allowed_actions)}"}
                
                cmd = ["kubectl", "rollout", action, f"{resource_type}/{name}", "-n", namespace]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    return {"success": True, "output": result.stdout.strip()}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error managing rollout: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Exec in Pod",
                destructiveHint=True,
            ),
        )
        def exec_in_pod(pod_name: str, command: str, namespace: Optional[str] = "default", container: Optional[str] = None) -> Dict[str, Any]:
            """Execute a command inside a pod."""
            try:
                import subprocess
                import shlex
                
                cmd = ["kubectl", "exec", pod_name, "-n", namespace]
                if container:
                    cmd.extend(["-c", container])
                cmd.append("--")
                cmd.extend(shlex.split(command))
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode
                }
            except Exception as e:
                logger.error(f"Error executing in pod: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Cleanup Pods",
                destructiveHint=True,
            ),
        )
        def cleanup_pods(namespace: Optional[str] = None, states: Optional[List[str]] = None) -> Dict[str, Any]:
            """Clean up pods in problematic states (Evicted, Error, Completed, etc.)."""
            try:
                import subprocess
                
                if states is None:
                    states = ["Evicted", "Error", "Completed", "ContainerStatusUnknown"]
                
                ns_flag = ["-n", namespace] if namespace else ["--all-namespaces"]
                
                deleted_pods = []
                for state in states:
                    # Get pods in this state
                    cmd = ["kubectl", "get", "pods"] + ns_flag + [
                        "--field-selector", f"status.phase={state}" if state not in ["Evicted", "ContainerStatusUnknown"] else "",
                        "-o", "jsonpath={.items[*].metadata.name}"
                    ]
                    
                    if state == "Evicted":
                        cmd = ["kubectl", "get", "pods"] + ns_flag + [
                            "-o", "json"
                        ]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            import json
                            try:
                                pods = json.loads(result.stdout)
                                for pod in pods.get("items", []):
                                    if pod.get("status", {}).get("reason") == "Evicted":
                                        pod_name = pod["metadata"]["name"]
                                        pod_ns = pod["metadata"]["namespace"]
                                        del_cmd = ["kubectl", "delete", "pod", pod_name, "-n", pod_ns]
                                        subprocess.run(del_cmd, capture_output=True, timeout=10)
                                        deleted_pods.append(f"{pod_ns}/{pod_name}")
                            except json.JSONDecodeError:
                                pass
                
                return {
                    "success": True,
                    "deleted_count": len(deleted_pods),
                    "deleted_pods": deleted_pods[:20]  # Limit output
                }
            except Exception as e:
                logger.error(f"Error cleaning up pods: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Node Management",
                destructiveHint=True,
            ),
        )
        def node_management(action: str, node_name: str, force: bool = False) -> Dict[str, Any]:
            """Manage nodes: cordon, uncordon, or drain."""
            try:
                import subprocess
                
                allowed_actions = ["cordon", "uncordon", "drain"]
                if action not in allowed_actions:
                    return {"success": False, "error": f"Invalid action. Allowed: {', '.join(allowed_actions)}"}
                
                cmd = ["kubectl", action, node_name]
                if action == "drain":
                    cmd.extend(["--ignore-daemonsets", "--delete-emptydir-data"])
                    if force:
                        cmd.append("--force")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    return {"success": True, "output": result.stdout.strip()}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error managing node: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Kubectl Create",
                destructiveHint=True,
            ),
        )
        def kubectl_create(resource_type: str, name: str, namespace: Optional[str] = "default", image: Optional[str] = None, **kwargs) -> Dict[str, Any]:
            """Create a Kubernetes resource."""
            if self.non_destructive:
                return {"success": False, "error": "Operation blocked: non-destructive mode enabled"}
            try:
                import subprocess
                cmd = ["kubectl", "create", resource_type, name, "-n", namespace]
                if image and resource_type in ["deployment", "pod"]:
                    cmd.extend(["--image", image])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    return {"success": True, "output": result.stdout.strip()}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error creating resource: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Helm Template",
                readOnlyHint=True,
            ),
        )
        def helm_template(chart: str, name: str, namespace: str = "default", repo: Optional[str] = None, values: Optional[str] = None) -> Dict[str, Any]:
            """Render Helm chart templates locally without installing."""
            try:
                import subprocess
                cmd = ["helm", "template", name, chart, "-n", namespace]
                if repo:
                    cmd.extend(["--repo", repo])
                if values:
                    cmd.extend(["--set", values])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    return {"success": True, "manifest": result.stdout}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error templating chart: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Helm Template Apply",
                destructiveHint=True,
            ),
        )
        def helm_template_apply(chart: str, name: str, namespace: str = "default", repo: Optional[str] = None, values: Optional[str] = None) -> Dict[str, Any]:
            """Render and apply Helm chart (bypasses Tiller/auth issues)."""
            if self.non_destructive:
                return {"success": False, "error": "Operation blocked: non-destructive mode enabled"}
            try:
                import subprocess
                cmd = ["helm", "template", name, chart, "-n", namespace]
                if repo:
                    cmd.extend(["--repo", repo])
                if values:
                    cmd.extend(["--set", values])
                template_result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if template_result.returncode != 0:
                    return {"success": False, "error": template_result.stderr.strip()}
                apply_cmd = ["kubectl", "apply", "-f", "-", "-n", namespace]
                apply_result = subprocess.run(apply_cmd, input=template_result.stdout, capture_output=True, text=True, timeout=60)
                if apply_result.returncode == 0:
                    return {"success": True, "output": apply_result.stdout.strip()}
                else:
                    return {"success": False, "error": apply_result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error applying template: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Kubectl Copy",
                destructiveHint=True,
            ),
        )
        def kubectl_cp(source: str, destination: str, namespace: str = "default", container: Optional[str] = None) -> Dict[str, Any]:
            """Copy files between local filesystem and pods.
            
            Use pod:path format for pod paths, e.g.:
            - Local to pod: kubectl_cp("/tmp/file.txt", "mypod:/tmp/file.txt")
            - Pod to local: kubectl_cp("mypod:/tmp/file.txt", "/tmp/file.txt")
            """
            try:
                import subprocess
                cmd = ["kubectl", "cp", source, destination, "-n", namespace]
                if container:
                    cmd.extend(["-c", container])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    return {"success": True, "message": f"Copied {source} to {destination}"}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error copying files: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="List Kubeconfig Contexts",
                readOnlyHint=True,
            ),
        )
        def list_kubeconfig_contexts() -> Dict[str, Any]:
            """List all contexts from KUBECONFIG (supports multiple files)."""
            try:
                import subprocess
                import os
                kubeconfig = os.environ.get("KUBECONFIG", os.path.expanduser("~/.kube/config"))
                result = subprocess.run(
                    ["kubectl", "config", "get-contexts", "-o", "name"],
                    capture_output=True, text=True, timeout=10,
                    env={**os.environ, "KUBECONFIG": kubeconfig}
                )
                if result.returncode == 0:
                    contexts = [c for c in result.stdout.strip().split("\n") if c]
                    return {"success": True, "contexts": contexts, "kubeconfig": kubeconfig}
                else:
                    return {"success": False, "error": result.stderr.strip()}
            except Exception as e:
                logger.error(f"Error listing contexts: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Analyze Pod Security",
                readOnlyHint=True,
            ),
        )
        def analyze_pod_security(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Analyze pod security configurations and identify risks."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                
                if namespace:
                    pods = v1.list_namespaced_pod(namespace)
                else:
                    pods = v1.list_pod_for_all_namespaces()
                
                issues = []
                for pod in pods.items:
                    pod_name = pod.metadata.name
                    pod_ns = pod.metadata.namespace
                    
                    for container in pod.spec.containers:
                        sc = container.security_context or pod.spec.security_context
                        if sc:
                            if getattr(sc, 'privileged', False):
                                issues.append({"pod": pod_name, "namespace": pod_ns, "container": container.name, "issue": "privileged", "severity": "critical"})
                            if getattr(sc, 'run_as_root', True) and not getattr(sc, 'run_as_non_root', False):
                                issues.append({"pod": pod_name, "namespace": pod_ns, "container": container.name, "issue": "may_run_as_root", "severity": "warning"})
                            if getattr(sc, 'allow_privilege_escalation', True):
                                issues.append({"pod": pod_name, "namespace": pod_ns, "container": container.name, "issue": "privilege_escalation_allowed", "severity": "warning"})
                        
                        if not container.resources or not container.resources.limits:
                            issues.append({"pod": pod_name, "namespace": pod_ns, "container": container.name, "issue": "no_resource_limits", "severity": "warning"})
                
                critical = len([i for i in issues if i["severity"] == "critical"])
                warnings = len([i for i in issues if i["severity"] == "warning"])
                
                return {
                    "success": True,
                    "summary": {"critical": critical, "warnings": warnings, "total_pods": len(pods.items)},
                    "issues": issues[:50]
                }
            except Exception as e:
                logger.error(f"Error analyzing pod security: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Analyze Network Policies",
                readOnlyHint=True,
            ),
        )
        def analyze_network_policies(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Analyze network policies and identify pods without policies."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                networking = client.NetworkingV1Api()
                
                if namespace:
                    pods = v1.list_namespaced_pod(namespace)
                    policies = networking.list_namespaced_network_policy(namespace)
                else:
                    pods = v1.list_pod_for_all_namespaces()
                    policies = networking.list_network_policy_for_all_namespaces()
                
                policy_map = {}
                for policy in policies.items:
                    ns = policy.metadata.namespace
                    if ns not in policy_map:
                        policy_map[ns] = []
                    policy_map[ns].append({
                        "name": policy.metadata.name,
                        "pod_selector": policy.spec.pod_selector.match_labels if policy.spec.pod_selector else {},
                        "ingress_rules": len(policy.spec.ingress or []),
                        "egress_rules": len(policy.spec.egress or [])
                    })
                
                unprotected_pods = []
                for pod in pods.items:
                    ns = pod.metadata.namespace
                    if ns not in policy_map:
                        unprotected_pods.append({"name": pod.metadata.name, "namespace": ns, "reason": "no_policies_in_namespace"})
                
                return {
                    "success": True,
                    "summary": {
                        "total_policies": len(policies.items),
                        "namespaces_with_policies": len(policy_map),
                        "unprotected_pods": len(unprotected_pods)
                    },
                    "policies": policy_map,
                    "unprotected_pods": unprotected_pods[:20]
                }
            except Exception as e:
                logger.error(f"Error analyzing network policies: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Audit RBAC Permissions",
                readOnlyHint=True,
            ),
        )
        def audit_rbac_permissions(namespace: Optional[str] = None, subject: Optional[str] = None) -> Dict[str, Any]:
            """Audit RBAC permissions for service accounts and users."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                rbac = client.RbacAuthorizationV1Api()
                
                if namespace:
                    role_bindings = rbac.list_namespaced_role_binding(namespace)
                else:
                    role_bindings = rbac.list_role_binding_for_all_namespaces()
                
                cluster_role_bindings = rbac.list_cluster_role_binding()
                
                bindings = []
                high_privilege = []
                
                for rb in role_bindings.items:
                    for subj in (rb.subjects or []):
                        if subject and subject not in subj.name:
                            continue
                        binding = {
                            "type": "RoleBinding",
                            "name": rb.metadata.name,
                            "namespace": rb.metadata.namespace,
                            "role": rb.role_ref.name,
                            "subject_kind": subj.kind,
                            "subject_name": subj.name
                        }
                        bindings.append(binding)
                
                for crb in cluster_role_bindings.items:
                    role_name = crb.role_ref.name
                    for subj in (crb.subjects or []):
                        if subject and subject not in subj.name:
                            continue
                        binding = {
                            "type": "ClusterRoleBinding",
                            "name": crb.metadata.name,
                            "role": role_name,
                            "subject_kind": subj.kind,
                            "subject_name": subj.name
                        }
                        bindings.append(binding)
                        if role_name in ["cluster-admin", "admin", "edit"]:
                            high_privilege.append(binding)
                
                return {
                    "success": True,
                    "summary": {
                        "total_bindings": len(bindings),
                        "high_privilege_bindings": len(high_privilege)
                    },
                    "high_privilege": high_privilege,
                    "all_bindings": bindings[:50]
                }
            except Exception as e:
                logger.error(f"Error auditing RBAC: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Check Secrets Security",
                readOnlyHint=True,
            ),
        )
        def check_secrets_security(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Check secrets for security best practices."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()
                
                if namespace:
                    secrets = v1.list_namespaced_secret(namespace)
                else:
                    secrets = v1.list_secret_for_all_namespaces()
                
                findings = []
                for secret in secrets.items:
                    name = secret.metadata.name
                    ns = secret.metadata.namespace
                    secret_type = secret.type
                    
                    if secret_type == "Opaque" and secret.data:
                        for key in secret.data.keys():
                            if any(x in key.lower() for x in ["password", "token", "key", "secret"]):
                                findings.append({
                                    "secret": name,
                                    "namespace": ns,
                                    "finding": f"Sensitive key '{key}' in Opaque secret",
                                    "severity": "info"
                                })
                    
                    if not secret.metadata.annotations or "sealed-secrets" not in str(secret.metadata.annotations):
                        if secret_type not in ["kubernetes.io/service-account-token", "kubernetes.io/dockerconfigjson"]:
                            findings.append({
                                "secret": name,
                                "namespace": ns,
                                "finding": "Secret not encrypted at rest (consider SealedSecrets or external secrets)",
                                "severity": "warning"
                            })
                
                return {
                    "success": True,
                    "summary": {
                        "total_secrets": len(secrets.items),
                        "findings": len(findings)
                    },
                    "findings": findings[:30]
                }
            except Exception as e:
                logger.error(f"Error checking secrets: {e}")
                return {"success": False, "error": str(e)}

        # ============================================================
        # PHASE 1: Quick Win Features
        # ============================================================

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Ingress Resources",
                readOnlyHint=True,
            ),
        )
        def get_ingress(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List Ingress resources with their hosts, paths, and backends."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                networking = client.NetworkingV1Api()

                if namespace:
                    ingresses = networking.list_namespaced_ingress(namespace)
                else:
                    ingresses = networking.list_ingress_for_all_namespaces()

                ingress_list = []
                for ing in ingresses.items:
                    rules = []
                    if ing.spec.rules:
                        for rule in ing.spec.rules:
                            paths = []
                            if rule.http and rule.http.paths:
                                for path in rule.http.paths:
                                    backend = {}
                                    if path.backend.service:
                                        backend = {
                                            "service": path.backend.service.name,
                                            "port": path.backend.service.port.number if path.backend.service.port else None
                                        }
                                    paths.append({
                                        "path": path.path or "/",
                                        "pathType": path.path_type,
                                        "backend": backend
                                    })
                            rules.append({
                                "host": rule.host or "*",
                                "paths": paths
                            })

                    tls = []
                    if ing.spec.tls:
                        for t in ing.spec.tls:
                            tls.append({
                                "hosts": t.hosts or [],
                                "secretName": t.secret_name
                            })

                    ingress_list.append({
                        "name": ing.metadata.name,
                        "namespace": ing.metadata.namespace,
                        "className": ing.spec.ingress_class_name,
                        "rules": rules,
                        "tls": tls,
                        "loadBalancer": [lb.ip or lb.hostname for lb in (ing.status.load_balancer.ingress or [])] if ing.status.load_balancer else []
                    })

                return {
                    "success": True,
                    "count": len(ingress_list),
                    "ingresses": ingress_list
                }
            except Exception as e:
                logger.error(f"Error getting ingresses: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get StatefulSets",
                readOnlyHint=True,
            ),
        )
        def get_statefulsets(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List StatefulSets with their status and replica counts."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                apps = client.AppsV1Api()

                if namespace:
                    statefulsets = apps.list_namespaced_stateful_set(namespace)
                else:
                    statefulsets = apps.list_stateful_set_for_all_namespaces()

                sts_list = []
                for sts in statefulsets.items:
                    sts_list.append({
                        "name": sts.metadata.name,
                        "namespace": sts.metadata.namespace,
                        "replicas": sts.spec.replicas,
                        "readyReplicas": sts.status.ready_replicas or 0,
                        "currentReplicas": sts.status.current_replicas or 0,
                        "updatedReplicas": sts.status.updated_replicas or 0,
                        "serviceName": sts.spec.service_name,
                        "podManagementPolicy": sts.spec.pod_management_policy,
                        "updateStrategy": sts.spec.update_strategy.type if sts.spec.update_strategy else None,
                        "volumeClaimTemplates": [
                            {
                                "name": pvc.metadata.name,
                                "storageClass": pvc.spec.storage_class_name,
                                "accessModes": pvc.spec.access_modes,
                                "storage": pvc.spec.resources.requests.get("storage") if pvc.spec.resources and pvc.spec.resources.requests else None
                            }
                            for pvc in (sts.spec.volume_claim_templates or [])
                        ],
                        "selector": sts.spec.selector.match_labels if sts.spec.selector else {},
                        "age": str(sts.metadata.creation_timestamp)
                    })

                return {
                    "success": True,
                    "count": len(sts_list),
                    "statefulsets": sts_list
                }
            except Exception as e:
                logger.error(f"Error getting statefulsets: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get DaemonSets",
                readOnlyHint=True,
            ),
        )
        def get_daemonsets(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List DaemonSets with their status and node coverage."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                apps = client.AppsV1Api()

                if namespace:
                    daemonsets = apps.list_namespaced_daemon_set(namespace)
                else:
                    daemonsets = apps.list_daemon_set_for_all_namespaces()

                ds_list = []
                for ds in daemonsets.items:
                    ds_list.append({
                        "name": ds.metadata.name,
                        "namespace": ds.metadata.namespace,
                        "desiredNumberScheduled": ds.status.desired_number_scheduled,
                        "currentNumberScheduled": ds.status.current_number_scheduled,
                        "numberReady": ds.status.number_ready or 0,
                        "numberAvailable": ds.status.number_available or 0,
                        "numberUnavailable": ds.status.number_unavailable or 0,
                        "numberMisscheduled": ds.status.number_misscheduled or 0,
                        "updatedNumberScheduled": ds.status.updated_number_scheduled or 0,
                        "updateStrategy": ds.spec.update_strategy.type if ds.spec.update_strategy else None,
                        "selector": ds.spec.selector.match_labels if ds.spec.selector else {},
                        "nodeSelector": ds.spec.template.spec.node_selector if ds.spec.template.spec.node_selector else {},
                        "tolerations": [
                            {"key": t.key, "operator": t.operator, "effect": t.effect}
                            for t in (ds.spec.template.spec.tolerations or [])
                        ],
                        "age": str(ds.metadata.creation_timestamp)
                    })

                return {
                    "success": True,
                    "count": len(ds_list),
                    "daemonsets": ds_list
                }
            except Exception as e:
                logger.error(f"Error getting daemonsets: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Jobs and CronJobs",
                readOnlyHint=True,
            ),
        )
        def get_jobs(namespace: Optional[str] = None, include_cronjobs: bool = True) -> Dict[str, Any]:
            """List Jobs and CronJobs with their status and completion info."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                batch = client.BatchV1Api()

                # Get Jobs
                if namespace:
                    jobs = batch.list_namespaced_job(namespace)
                else:
                    jobs = batch.list_job_for_all_namespaces()

                job_list = []
                for job in jobs.items:
                    conditions = []
                    if job.status.conditions:
                        for c in job.status.conditions:
                            conditions.append({
                                "type": c.type,
                                "status": c.status,
                                "reason": c.reason,
                                "message": c.message
                            })

                    job_list.append({
                        "name": job.metadata.name,
                        "namespace": job.metadata.namespace,
                        "completions": job.spec.completions,
                        "parallelism": job.spec.parallelism,
                        "succeeded": job.status.succeeded or 0,
                        "failed": job.status.failed or 0,
                        "active": job.status.active or 0,
                        "startTime": str(job.status.start_time) if job.status.start_time else None,
                        "completionTime": str(job.status.completion_time) if job.status.completion_time else None,
                        "backoffLimit": job.spec.backoff_limit,
                        "conditions": conditions,
                        "ownerReferences": [
                            {"kind": ref.kind, "name": ref.name}
                            for ref in (job.metadata.owner_references or [])
                        ]
                    })

                result = {
                    "success": True,
                    "jobs": {
                        "count": len(job_list),
                        "items": job_list
                    }
                }

                # Get CronJobs
                if include_cronjobs:
                    if namespace:
                        cronjobs = batch.list_namespaced_cron_job(namespace)
                    else:
                        cronjobs = batch.list_cron_job_for_all_namespaces()

                    cronjob_list = []
                    for cj in cronjobs.items:
                        cronjob_list.append({
                            "name": cj.metadata.name,
                            "namespace": cj.metadata.namespace,
                            "schedule": cj.spec.schedule,
                            "suspend": cj.spec.suspend,
                            "concurrencyPolicy": cj.spec.concurrency_policy,
                            "successfulJobsHistoryLimit": cj.spec.successful_jobs_history_limit,
                            "failedJobsHistoryLimit": cj.spec.failed_jobs_history_limit,
                            "lastScheduleTime": str(cj.status.last_schedule_time) if cj.status.last_schedule_time else None,
                            "lastSuccessfulTime": str(cj.status.last_successful_time) if cj.status.last_successful_time else None,
                            "activeJobs": len(cj.status.active or [])
                        })

                    result["cronjobs"] = {
                        "count": len(cronjob_list),
                        "items": cronjob_list
                    }

                return result
            except Exception as e:
                logger.error(f"Error getting jobs: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Diagnose Pod Crash",
                readOnlyHint=True,
            ),
        )
        def diagnose_pod_crash(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
            """Automated diagnosis of pod crash loops and failures."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                # Get pod details
                pod = v1.read_namespaced_pod(pod_name, namespace)

                diagnosis = {
                    "pod": pod_name,
                    "namespace": namespace,
                    "phase": pod.status.phase,
                    "issues": [],
                    "recommendations": [],
                    "containerStatuses": [],
                    "events": []
                }

                # Analyze container statuses
                for cs in (pod.status.container_statuses or []):
                    container_info = {
                        "name": cs.name,
                        "ready": cs.ready,
                        "restartCount": cs.restart_count,
                        "state": None,
                        "lastState": None
                    }

                    # Current state
                    if cs.state:
                        if cs.state.waiting:
                            container_info["state"] = {
                                "status": "waiting",
                                "reason": cs.state.waiting.reason,
                                "message": cs.state.waiting.message
                            }
                            # Diagnose waiting states
                            if cs.state.waiting.reason == "CrashLoopBackOff":
                                diagnosis["issues"].append({
                                    "container": cs.name,
                                    "issue": "CrashLoopBackOff",
                                    "severity": "critical",
                                    "description": "Container is crashing repeatedly"
                                })
                                diagnosis["recommendations"].append("Check container logs for error messages")
                                diagnosis["recommendations"].append("Verify the container command and args are correct")
                            elif cs.state.waiting.reason == "ImagePullBackOff":
                                diagnosis["issues"].append({
                                    "container": cs.name,
                                    "issue": "ImagePullBackOff",
                                    "severity": "critical",
                                    "description": "Unable to pull container image"
                                })
                                diagnosis["recommendations"].append("Verify the image name and tag exist")
                                diagnosis["recommendations"].append("Check imagePullSecrets if using private registry")
                            elif cs.state.waiting.reason == "CreateContainerConfigError":
                                diagnosis["issues"].append({
                                    "container": cs.name,
                                    "issue": "CreateContainerConfigError",
                                    "severity": "critical",
                                    "description": "Container configuration error"
                                })
                                diagnosis["recommendations"].append("Check ConfigMaps and Secrets referenced by the container")
                        elif cs.state.running:
                            container_info["state"] = {"status": "running", "startedAt": str(cs.state.running.started_at)}
                        elif cs.state.terminated:
                            container_info["state"] = {
                                "status": "terminated",
                                "exitCode": cs.state.terminated.exit_code,
                                "reason": cs.state.terminated.reason,
                                "message": cs.state.terminated.message
                            }
                            if cs.state.terminated.exit_code != 0:
                                diagnosis["issues"].append({
                                    "container": cs.name,
                                    "issue": f"Exited with code {cs.state.terminated.exit_code}",
                                    "severity": "error",
                                    "reason": cs.state.terminated.reason
                                })
                                if cs.state.terminated.reason == "OOMKilled":
                                    diagnosis["recommendations"].append(f"Increase memory limit for container '{cs.name}'")
                                elif cs.state.terminated.reason == "Error":
                                    diagnosis["recommendations"].append(f"Check logs for container '{cs.name}' to identify the error")

                    # Last state (for crash analysis)
                    if cs.last_state and cs.last_state.terminated:
                        container_info["lastState"] = {
                            "status": "terminated",
                            "exitCode": cs.last_state.terminated.exit_code,
                            "reason": cs.last_state.terminated.reason,
                            "finishedAt": str(cs.last_state.terminated.finished_at)
                        }

                    # High restart count warning
                    if cs.restart_count > 5:
                        diagnosis["issues"].append({
                            "container": cs.name,
                            "issue": f"High restart count: {cs.restart_count}",
                            "severity": "warning",
                            "description": "Container has restarted multiple times"
                        })

                    diagnosis["containerStatuses"].append(container_info)

                # Get recent events
                events = v1.list_namespaced_event(
                    namespace,
                    field_selector=f"involvedObject.name={pod_name}"
                )
                for event in events.items:
                    diagnosis["events"].append({
                        "type": event.type,
                        "reason": event.reason,
                        "message": event.message,
                        "count": event.count,
                        "lastTimestamp": str(event.last_timestamp) if event.last_timestamp else None
                    })
                    # Add issues from events
                    if event.type == "Warning":
                        if event.reason == "FailedScheduling":
                            diagnosis["issues"].append({
                                "issue": "FailedScheduling",
                                "severity": "critical",
                                "description": event.message
                            })
                        elif event.reason == "FailedMount":
                            diagnosis["issues"].append({
                                "issue": "FailedMount",
                                "severity": "critical",
                                "description": event.message
                            })
                            diagnosis["recommendations"].append("Check PVC status and storage class")
                        elif event.reason == "Unhealthy":
                            diagnosis["issues"].append({
                                "issue": "Unhealthy",
                                "severity": "warning",
                                "description": event.message
                            })
                            diagnosis["recommendations"].append("Review liveness/readiness probe configuration")

                # Check pod conditions
                for condition in (pod.status.conditions or []):
                    if condition.status == "False":
                        diagnosis["issues"].append({
                            "issue": f"Condition {condition.type} is False",
                            "severity": "warning",
                            "reason": condition.reason,
                            "message": condition.message
                        })

                # Summary
                diagnosis["summary"] = {
                    "totalIssues": len(diagnosis["issues"]),
                    "criticalIssues": len([i for i in diagnosis["issues"] if i.get("severity") == "critical"]),
                    "totalRecommendations": len(set(diagnosis["recommendations"]))
                }
                diagnosis["recommendations"] = list(set(diagnosis["recommendations"]))

                return {"success": True, "diagnosis": diagnosis}
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    return {"success": False, "error": f"Pod '{pod_name}' not found in namespace '{namespace}'"}
                return {"success": False, "error": str(e)}
            except Exception as e:
                logger.error(f"Error diagnosing pod: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Detect Pending Pods",
                readOnlyHint=True,
            ),
        )
        def detect_pending_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Find pending pods and explain why they are not scheduled."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if namespace:
                    pods = v1.list_namespaced_pod(namespace, field_selector="status.phase=Pending")
                else:
                    pods = v1.list_pod_for_all_namespaces(field_selector="status.phase=Pending")

                pending_pods = []
                for pod in pods.items:
                    pod_info = {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "createdAt": str(pod.metadata.creation_timestamp),
                        "reasons": [],
                        "events": []
                    }

                    # Check conditions for scheduling issues
                    for condition in (pod.status.conditions or []):
                        if condition.type == "PodScheduled" and condition.status == "False":
                            pod_info["reasons"].append({
                                "type": "SchedulingFailed",
                                "reason": condition.reason,
                                "message": condition.message
                            })

                    # Get events for more details
                    events = v1.list_namespaced_event(
                        pod.metadata.namespace,
                        field_selector=f"involvedObject.name={pod.metadata.name}"
                    )
                    for event in events.items:
                        if event.reason in ["FailedScheduling", "FailedAttachVolume", "FailedMount"]:
                            pod_info["events"].append({
                                "reason": event.reason,
                                "message": event.message,
                                "count": event.count
                            })
                            # Parse common scheduling failures
                            msg = event.message or ""
                            if "Insufficient cpu" in msg:
                                pod_info["reasons"].append({
                                    "type": "InsufficientCPU",
                                    "message": "Not enough CPU available on any node"
                                })
                            elif "Insufficient memory" in msg:
                                pod_info["reasons"].append({
                                    "type": "InsufficientMemory",
                                    "message": "Not enough memory available on any node"
                                })
                            elif "node(s) had taint" in msg:
                                pod_info["reasons"].append({
                                    "type": "NodeTaints",
                                    "message": "Pod doesn't tolerate node taints"
                                })
                            elif "node(s) didn't match Pod's node affinity" in msg:
                                pod_info["reasons"].append({
                                    "type": "NodeAffinity",
                                    "message": "No nodes match the pod's node affinity rules"
                                })
                            elif "persistentvolumeclaim" in msg.lower():
                                pod_info["reasons"].append({
                                    "type": "PVCIssue",
                                    "message": "PersistentVolumeClaim not bound or not found"
                                })

                    # Check resource requests
                    total_cpu = 0
                    total_memory = 0
                    for container in pod.spec.containers:
                        if container.resources and container.resources.requests:
                            cpu_req = container.resources.requests.get("cpu", "0")
                            mem_req = container.resources.requests.get("memory", "0")
                            pod_info["resourceRequests"] = {
                                "cpu": cpu_req,
                                "memory": mem_req
                            }

                    pending_pods.append(pod_info)

                # Categorize by reason
                by_reason = {}
                for pod in pending_pods:
                    for reason in pod["reasons"]:
                        reason_type = reason.get("type", "Unknown")
                        if reason_type not in by_reason:
                            by_reason[reason_type] = []
                        by_reason[reason_type].append(pod["name"])

                return {
                    "success": True,
                    "summary": {
                        "totalPending": len(pending_pods),
                        "byReason": {k: len(v) for k, v in by_reason.items()}
                    },
                    "pendingPods": pending_pods,
                    "recommendations": self._get_pending_recommendations(by_reason)
                }
            except Exception as e:
                logger.error(f"Error detecting pending pods: {e}")
                return {"success": False, "error": str(e)}

        def _get_pending_recommendations(reason_map: dict) -> List[str]:
            """Generate recommendations based on pending reasons."""
            recommendations = []
            if "InsufficientCPU" in reason_map:
                recommendations.append("Consider scaling up nodes or reducing CPU requests")
            if "InsufficientMemory" in reason_map:
                recommendations.append("Consider scaling up nodes or reducing memory requests")
            if "NodeTaints" in reason_map:
                recommendations.append("Add appropriate tolerations to pod spec or remove taints from nodes")
            if "NodeAffinity" in reason_map:
                recommendations.append("Review node affinity rules or add labels to nodes")
            if "PVCIssue" in reason_map:
                recommendations.append("Check PVC status and ensure storage class can provision volumes")
            return recommendations

        # Store helper as instance method
        self._get_pending_recommendations = _get_pending_recommendations

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get ReplicaSets",
                readOnlyHint=True,
            ),
        )
        def get_replicasets(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List ReplicaSets with their status and owner references."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                apps = client.AppsV1Api()

                if namespace:
                    replicasets = apps.list_namespaced_replica_set(namespace)
                else:
                    replicasets = apps.list_replica_set_for_all_namespaces()

                rs_list = []
                for rs in replicasets.items:
                    rs_list.append({
                        "name": rs.metadata.name,
                        "namespace": rs.metadata.namespace,
                        "replicas": rs.spec.replicas,
                        "readyReplicas": rs.status.ready_replicas or 0,
                        "availableReplicas": rs.status.available_replicas or 0,
                        "selector": rs.spec.selector.match_labels if rs.spec.selector else {},
                        "ownerReferences": [
                            {"kind": ref.kind, "name": ref.name}
                            for ref in (rs.metadata.owner_references or [])
                        ],
                        "age": str(rs.metadata.creation_timestamp)
                    })

                return {
                    "success": True,
                    "count": len(rs_list),
                    "replicasets": rs_list
                }
            except Exception as e:
                logger.error(f"Error getting replicasets: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Endpoints",
                readOnlyHint=True,
            ),
        )
        def get_endpoints(namespace: Optional[str] = None, service_name: Optional[str] = None) -> Dict[str, Any]:
            """List Endpoints for services to debug connectivity."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if service_name and namespace:
                    endpoints = [v1.read_namespaced_endpoints(service_name, namespace)]
                elif namespace:
                    endpoints = v1.list_namespaced_endpoints(namespace).items
                else:
                    endpoints = v1.list_endpoints_for_all_namespaces().items

                ep_list = []
                for ep in endpoints:
                    subsets = []
                    for subset in (ep.subsets or []):
                        addresses = []
                        for addr in (subset.addresses or []):
                            addresses.append({
                                "ip": addr.ip,
                                "hostname": addr.hostname,
                                "nodeName": addr.node_name,
                                "targetRef": {
                                    "kind": addr.target_ref.kind,
                                    "name": addr.target_ref.name,
                                    "namespace": addr.target_ref.namespace
                                } if addr.target_ref else None
                            })
                        not_ready = []
                        for addr in (subset.not_ready_addresses or []):
                            not_ready.append({
                                "ip": addr.ip,
                                "targetRef": {
                                    "kind": addr.target_ref.kind,
                                    "name": addr.target_ref.name
                                } if addr.target_ref else None
                            })
                        ports = [{"name": p.name, "port": p.port, "protocol": p.protocol} for p in (subset.ports or [])]
                        subsets.append({
                            "addresses": addresses,
                            "notReadyAddresses": not_ready,
                            "ports": ports
                        })

                    ep_list.append({
                        "name": ep.metadata.name,
                        "namespace": ep.metadata.namespace,
                        "subsets": subsets,
                        "totalReady": sum(len(s.get("addresses", [])) for s in subsets),
                        "totalNotReady": sum(len(s.get("notReadyAddresses", [])) for s in subsets)
                    })

                return {
                    "success": True,
                    "count": len(ep_list),
                    "endpoints": ep_list
                }
            except Exception as e:
                logger.error(f"Error getting endpoints: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get HorizontalPodAutoscalers",
                readOnlyHint=True,
            ),
        )
        def get_hpa(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List HorizontalPodAutoscalers with their current and target metrics."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                autoscaling = client.AutoscalingV2Api()

                if namespace:
                    hpas = autoscaling.list_namespaced_horizontal_pod_autoscaler(namespace)
                else:
                    hpas = autoscaling.list_horizontal_pod_autoscaler_for_all_namespaces()

                hpa_list = []
                for hpa in hpas.items:
                    metrics = []
                    for metric in (hpa.spec.metrics or []):
                        metric_info = {"type": metric.type}
                        if metric.type == "Resource" and metric.resource:
                            metric_info["resource"] = {
                                "name": metric.resource.name,
                                "targetType": metric.resource.target.type if metric.resource.target else None,
                                "targetValue": metric.resource.target.average_utilization if metric.resource.target else None
                            }
                        elif metric.type == "Pods" and metric.pods:
                            metric_info["pods"] = {
                                "metricName": metric.pods.metric.name if metric.pods.metric else None
                            }
                        metrics.append(metric_info)

                    current_metrics = []
                    for cm in (hpa.status.current_metrics or []):
                        cm_info = {"type": cm.type}
                        if cm.type == "Resource" and cm.resource:
                            cm_info["resource"] = {
                                "name": cm.resource.name,
                                "currentValue": cm.resource.current.average_utilization if cm.resource.current else None
                            }
                        current_metrics.append(cm_info)

                    hpa_list.append({
                        "name": hpa.metadata.name,
                        "namespace": hpa.metadata.namespace,
                        "scaleTargetRef": {
                            "kind": hpa.spec.scale_target_ref.kind,
                            "name": hpa.spec.scale_target_ref.name
                        },
                        "minReplicas": hpa.spec.min_replicas,
                        "maxReplicas": hpa.spec.max_replicas,
                        "currentReplicas": hpa.status.current_replicas,
                        "desiredReplicas": hpa.status.desired_replicas,
                        "metrics": metrics,
                        "currentMetrics": current_metrics,
                        "conditions": [
                            {"type": c.type, "status": c.status, "reason": c.reason}
                            for c in (hpa.status.conditions or [])
                        ]
                    })

                return {
                    "success": True,
                    "count": len(hpa_list),
                    "hpas": hpa_list
                }
            except Exception as e:
                logger.error(f"Error getting HPAs: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get PodDisruptionBudgets",
                readOnlyHint=True,
            ),
        )
        def get_pdb(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List PodDisruptionBudgets with their status."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                policy = client.PolicyV1Api()

                if namespace:
                    pdbs = policy.list_namespaced_pod_disruption_budget(namespace)
                else:
                    pdbs = policy.list_pod_disruption_budget_for_all_namespaces()

                pdb_list = []
                for pdb in pdbs.items:
                    pdb_list.append({
                        "name": pdb.metadata.name,
                        "namespace": pdb.metadata.namespace,
                        "minAvailable": str(pdb.spec.min_available) if pdb.spec.min_available else None,
                        "maxUnavailable": str(pdb.spec.max_unavailable) if pdb.spec.max_unavailable else None,
                        "selector": pdb.spec.selector.match_labels if pdb.spec.selector else {},
                        "currentHealthy": pdb.status.current_healthy,
                        "desiredHealthy": pdb.status.desired_healthy,
                        "disruptionsAllowed": pdb.status.disruptions_allowed,
                        "expectedPods": pdb.status.expected_pods
                    })

                return {
                    "success": True,
                    "count": len(pdb_list),
                    "pdbs": pdb_list
                }
            except Exception as e:
                logger.error(f"Error getting PDBs: {e}")
                return {"success": False, "error": str(e)}

        # ============================================================
        # PHASE 2: Kubernetes v1.35 Features & More Resource Types
        # ============================================================

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Persistent Volumes",
                readOnlyHint=True,
            ),
        )
        def get_persistent_volumes(name: Optional[str] = None) -> Dict[str, Any]:
            """List PersistentVolumes with their status, capacity, and node affinity (v1.35 mutable support)."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if name:
                    pvs = [v1.read_persistent_volume(name)]
                else:
                    pvs = v1.list_persistent_volume().items

                pv_list = []
                for pv in pvs:
                    # Extract node affinity (mutable in K8s v1.35)
                    node_affinity = None
                    if pv.spec.node_affinity and pv.spec.node_affinity.required:
                        terms = []
                        for term in (pv.spec.node_affinity.required.node_selector_terms or []):
                            expressions = []
                            for expr in (term.match_expressions or []):
                                expressions.append({
                                    "key": expr.key,
                                    "operator": expr.operator,
                                    "values": expr.values
                                })
                            terms.append({"matchExpressions": expressions})
                        node_affinity = {"required": {"nodeSelectorTerms": terms}}

                    pv_list.append({
                        "name": pv.metadata.name,
                        "capacity": pv.spec.capacity.get("storage") if pv.spec.capacity else None,
                        "accessModes": pv.spec.access_modes,
                        "reclaimPolicy": pv.spec.persistent_volume_reclaim_policy,
                        "storageClassName": pv.spec.storage_class_name,
                        "status": pv.status.phase,
                        "claim": {
                            "name": pv.spec.claim_ref.name,
                            "namespace": pv.spec.claim_ref.namespace
                        } if pv.spec.claim_ref else None,
                        "volumeMode": pv.spec.volume_mode,
                        "nodeAffinity": node_affinity,
                        "mountOptions": pv.spec.mount_options,
                        "source": self._get_pv_source(pv.spec),
                        "age": str(pv.metadata.creation_timestamp)
                    })

                return {
                    "success": True,
                    "count": len(pv_list),
                    "persistentVolumes": pv_list
                }
            except Exception as e:
                logger.error(f"Error getting PVs: {e}")
                return {"success": False, "error": str(e)}

        def _get_pv_source(spec) -> Dict[str, Any]:
            """Extract PV source type and details."""
            if spec.host_path:
                return {"type": "hostPath", "path": spec.host_path.path}
            elif spec.nfs:
                return {"type": "nfs", "server": spec.nfs.server, "path": spec.nfs.path}
            elif spec.csi:
                return {"type": "csi", "driver": spec.csi.driver, "volumeHandle": spec.csi.volume_handle}
            elif spec.aws_elastic_block_store:
                return {"type": "awsEBS", "volumeID": spec.aws_elastic_block_store.volume_id}
            elif spec.gce_persistent_disk:
                return {"type": "gcePD", "pdName": spec.gce_persistent_disk.pd_name}
            elif spec.azure_disk:
                return {"type": "azureDisk", "diskName": spec.azure_disk.disk_name}
            elif spec.local:
                return {"type": "local", "path": spec.local.path}
            return {"type": "unknown"}

        self._get_pv_source = _get_pv_source

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Persistent Volume Claims",
                readOnlyHint=True,
            ),
        )
        def get_pvcs(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List PersistentVolumeClaims with their status and bound volumes."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if namespace:
                    pvcs = v1.list_namespaced_persistent_volume_claim(namespace)
                else:
                    pvcs = v1.list_persistent_volume_claim_for_all_namespaces()

                pvc_list = []
                for pvc in pvcs.items:
                    pvc_list.append({
                        "name": pvc.metadata.name,
                        "namespace": pvc.metadata.namespace,
                        "status": pvc.status.phase,
                        "volume": pvc.spec.volume_name,
                        "capacity": pvc.status.capacity.get("storage") if pvc.status.capacity else None,
                        "requestedCapacity": pvc.spec.resources.requests.get("storage") if pvc.spec.resources and pvc.spec.resources.requests else None,
                        "accessModes": pvc.spec.access_modes,
                        "storageClassName": pvc.spec.storage_class_name,
                        "volumeMode": pvc.spec.volume_mode,
                        "conditions": [
                            {"type": c.type, "status": c.status, "reason": c.reason}
                            for c in (pvc.status.conditions or [])
                        ],
                        "age": str(pvc.metadata.creation_timestamp)
                    })

                return {
                    "success": True,
                    "count": len(pvc_list),
                    "pvcs": pvc_list
                }
            except Exception as e:
                logger.error(f"Error getting PVCs: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Storage Classes",
                readOnlyHint=True,
            ),
        )
        def get_storage_classes() -> Dict[str, Any]:
            """List StorageClasses with their provisioners and parameters."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                storage = client.StorageV1Api()

                scs = storage.list_storage_class()

                sc_list = []
                for sc in scs.items:
                    sc_list.append({
                        "name": sc.metadata.name,
                        "provisioner": sc.provisioner,
                        "reclaimPolicy": sc.reclaim_policy,
                        "volumeBindingMode": sc.volume_binding_mode,
                        "allowVolumeExpansion": sc.allow_volume_expansion,
                        "parameters": sc.parameters or {},
                        "isDefault": sc.metadata.annotations.get("storageclass.kubernetes.io/is-default-class") == "true" if sc.metadata.annotations else False,
                        "mountOptions": sc.mount_options
                    })

                return {
                    "success": True,
                    "count": len(sc_list),
                    "storageClasses": sc_list
                }
            except Exception as e:
                logger.error(f"Error getting storage classes: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Custom Resource Definitions",
                readOnlyHint=True,
            ),
        )
        def get_crds(group: Optional[str] = None) -> Dict[str, Any]:
            """List Custom Resource Definitions in the cluster."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                apiext = client.ApiextensionsV1Api()

                crds = apiext.list_custom_resource_definition()

                crd_list = []
                for crd in crds.items:
                    if group and crd.spec.group != group:
                        continue

                    versions = []
                    for v in (crd.spec.versions or []):
                        versions.append({
                            "name": v.name,
                            "served": v.served,
                            "storage": v.storage
                        })

                    crd_list.append({
                        "name": crd.metadata.name,
                        "group": crd.spec.group,
                        "kind": crd.spec.names.kind,
                        "plural": crd.spec.names.plural,
                        "singular": crd.spec.names.singular,
                        "scope": crd.spec.scope,
                        "versions": versions,
                        "established": any(
                            c.type == "Established" and c.status == "True"
                            for c in (crd.status.conditions or [])
                        ),
                        "age": str(crd.metadata.creation_timestamp)
                    })

                return {
                    "success": True,
                    "count": len(crd_list),
                    "crds": crd_list
                }
            except Exception as e:
                logger.error(f"Error getting CRDs: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Resource Quotas",
                readOnlyHint=True,
            ),
        )
        def get_resource_quotas(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List ResourceQuotas with their usage and limits."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if namespace:
                    quotas = v1.list_namespaced_resource_quota(namespace)
                else:
                    quotas = v1.list_resource_quota_for_all_namespaces()

                quota_list = []
                for quota in quotas.items:
                    hard = {}
                    used = {}
                    if quota.status.hard:
                        hard = {k: str(v) for k, v in quota.status.hard.items()}
                    if quota.status.used:
                        used = {k: str(v) for k, v in quota.status.used.items()}

                    quota_list.append({
                        "name": quota.metadata.name,
                        "namespace": quota.metadata.namespace,
                        "hard": hard,
                        "used": used,
                        "scopes": quota.spec.scopes if quota.spec.scopes else []
                    })

                return {
                    "success": True,
                    "count": len(quota_list),
                    "resourceQuotas": quota_list
                }
            except Exception as e:
                logger.error(f"Error getting resource quotas: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Limit Ranges",
                readOnlyHint=True,
            ),
        )
        def get_limit_ranges(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List LimitRanges with their constraints."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if namespace:
                    limits = v1.list_namespaced_limit_range(namespace)
                else:
                    limits = v1.list_limit_range_for_all_namespaces()

                limit_list = []
                for lr in limits.items:
                    ranges = []
                    for limit in (lr.spec.limits or []):
                        range_info = {"type": limit.type}
                        if limit.default:
                            range_info["default"] = {k: str(v) for k, v in limit.default.items()}
                        if limit.default_request:
                            range_info["defaultRequest"] = {k: str(v) for k, v in limit.default_request.items()}
                        if limit.max:
                            range_info["max"] = {k: str(v) for k, v in limit.max.items()}
                        if limit.min:
                            range_info["min"] = {k: str(v) for k, v in limit.min.items()}
                        if limit.max_limit_request_ratio:
                            range_info["maxLimitRequestRatio"] = {k: str(v) for k, v in limit.max_limit_request_ratio.items()}
                        ranges.append(range_info)

                    limit_list.append({
                        "name": lr.metadata.name,
                        "namespace": lr.metadata.namespace,
                        "limits": ranges
                    })

                return {
                    "success": True,
                    "count": len(limit_list),
                    "limitRanges": limit_list
                }
            except Exception as e:
                logger.error(f"Error getting limit ranges: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Service Accounts",
                readOnlyHint=True,
            ),
        )
        def get_service_accounts(namespace: Optional[str] = None) -> Dict[str, Any]:
            """List ServiceAccounts with their secrets and image pull secrets."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if namespace:
                    sas = v1.list_namespaced_service_account(namespace)
                else:
                    sas = v1.list_service_account_for_all_namespaces()

                sa_list = []
                for sa in sas.items:
                    sa_list.append({
                        "name": sa.metadata.name,
                        "namespace": sa.metadata.namespace,
                        "secrets": [s.name for s in (sa.secrets or [])],
                        "imagePullSecrets": [s.name for s in (sa.image_pull_secrets or [])],
                        "automountServiceAccountToken": sa.automount_service_account_token,
                        "age": str(sa.metadata.creation_timestamp)
                    })

                return {
                    "success": True,
                    "count": len(sa_list),
                    "serviceAccounts": sa_list
                }
            except Exception as e:
                logger.error(f"Error getting service accounts: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Restart Deployment",
                readOnlyHint=False,
            ),
        )
        def restart_deployment(name: str, namespace: str = "default") -> Dict[str, Any]:
            """Trigger a rolling restart of a deployment (similar to kubectl rollout restart)."""
            blocked = self._check_destructive()
            if blocked:
                return blocked

            try:
                from kubernetes import client, config
                from datetime import datetime, timezone
                config.load_kube_config()
                apps = client.AppsV1Api()

                # Patch the deployment to trigger a rolling restart
                now = datetime.now(timezone.utc).isoformat()
                body = {
                    "spec": {
                        "template": {
                            "metadata": {
                                "annotations": {
                                    "kubectl.kubernetes.io/restartedAt": now
                                }
                            }
                        }
                    }
                }

                apps.patch_namespaced_deployment(name, namespace, body)

                return {
                    "success": True,
                    "message": f"Deployment '{name}' in namespace '{namespace}' is being restarted",
                    "restartedAt": now
                }
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    return {"success": False, "error": f"Deployment '{name}' not found in namespace '{namespace}'"}
                return {"success": False, "error": str(e)}
            except Exception as e:
                logger.error(f"Error restarting deployment: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Pod Metrics",
                readOnlyHint=True,
            ),
        )
        def get_pod_metrics(namespace: Optional[str] = None, pod_name: Optional[str] = None) -> Dict[str, Any]:
            """Get CPU and memory metrics for pods (requires metrics-server)."""
            try:
                import subprocess
                cmd = ["kubectl", "top", "pods"]
                if namespace:
                    cmd.extend(["-n", namespace])
                else:
                    cmd.append("--all-namespaces")
                if pod_name:
                    cmd.append(pod_name)
                cmd.append("--no-headers")

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    if "metrics not available" in result.stderr.lower() or "metrics-server" in result.stderr.lower():
                        return {"success": False, "error": "Metrics server not available. Install metrics-server to use this feature."}
                    return {"success": False, "error": result.stderr.strip()}

                metrics = []
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split()
                    if namespace:
                        # Format: NAME CPU MEMORY
                        if len(parts) >= 3:
                            metrics.append({
                                "namespace": namespace,
                                "pod": parts[0],
                                "cpu": parts[1],
                                "memory": parts[2]
                            })
                    else:
                        # Format: NAMESPACE NAME CPU MEMORY
                        if len(parts) >= 4:
                            metrics.append({
                                "namespace": parts[0],
                                "pod": parts[1],
                                "cpu": parts[2],
                                "memory": parts[3]
                            })

                return {
                    "success": True,
                    "count": len(metrics),
                    "metrics": metrics
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Metrics request timed out"}
            except Exception as e:
                logger.error(f"Error getting pod metrics: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Node Metrics",
                readOnlyHint=True,
            ),
        )
        def get_node_metrics() -> Dict[str, Any]:
            """Get CPU and memory metrics for nodes (requires metrics-server)."""
            try:
                import subprocess
                result = subprocess.run(
                    ["kubectl", "top", "nodes", "--no-headers"],
                    capture_output=True, text=True, timeout=30
                )

                if result.returncode != 0:
                    if "metrics not available" in result.stderr.lower():
                        return {"success": False, "error": "Metrics server not available. Install metrics-server to use this feature."}
                    return {"success": False, "error": result.stderr.strip()}

                metrics = []
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split()
                    # Format: NAME CPU CPU% MEMORY MEMORY%
                    if len(parts) >= 5:
                        metrics.append({
                            "node": parts[0],
                            "cpu": parts[1],
                            "cpuPercent": parts[2],
                            "memory": parts[3],
                            "memoryPercent": parts[4]
                        })

                return {
                    "success": True,
                    "count": len(metrics),
                    "metrics": metrics
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Metrics request timed out"}
            except Exception as e:
                logger.error(f"Error getting node metrics: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Priority Classes",
                readOnlyHint=True,
            ),
        )
        def get_priority_classes() -> Dict[str, Any]:
            """List PriorityClasses for workload scheduling priority."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                scheduling = client.SchedulingV1Api()

                pcs = scheduling.list_priority_class()

                pc_list = []
                for pc in pcs.items:
                    pc_list.append({
                        "name": pc.metadata.name,
                        "value": pc.value,
                        "globalDefault": pc.global_default or False,
                        "preemptionPolicy": pc.preemption_policy,
                        "description": pc.description
                    })

                # Sort by value descending
                pc_list.sort(key=lambda x: x["value"], reverse=True)

                return {
                    "success": True,
                    "count": len(pc_list),
                    "priorityClasses": pc_list
                }
            except Exception as e:
                logger.error(f"Error getting priority classes: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Pod Security Policies (Deprecated) / Pod Security Standards",
                readOnlyHint=True,
            ),
        )
        def get_pod_security_info(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get Pod Security Standards enforcement info for namespaces."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if namespace:
                    namespaces = [v1.read_namespace(namespace)]
                else:
                    namespaces = v1.list_namespace().items

                ns_info = []
                for ns in namespaces:
                    labels = ns.metadata.labels or {}

                    # Check for Pod Security Standards labels
                    pss = {
                        "enforce": labels.get("pod-security.kubernetes.io/enforce"),
                        "enforceVersion": labels.get("pod-security.kubernetes.io/enforce-version"),
                        "audit": labels.get("pod-security.kubernetes.io/audit"),
                        "auditVersion": labels.get("pod-security.kubernetes.io/audit-version"),
                        "warn": labels.get("pod-security.kubernetes.io/warn"),
                        "warnVersion": labels.get("pod-security.kubernetes.io/warn-version")
                    }

                    # Remove None values
                    pss = {k: v for k, v in pss.items() if v is not None}

                    ns_info.append({
                        "namespace": ns.metadata.name,
                        "podSecurityStandards": pss if pss else None,
                        "hasNoSecurityPolicy": not pss
                    })

                # Summary
                unprotected = [n for n in ns_info if n["hasNoSecurityPolicy"]]

                return {
                    "success": True,
                    "summary": {
                        "totalNamespaces": len(ns_info),
                        "withPSS": len([n for n in ns_info if n["podSecurityStandards"]]),
                        "withoutPSS": len(unprotected)
                    },
                    "namespaces": ns_info,
                    "unprotectedNamespaces": [n["namespace"] for n in unprotected if n["namespace"] not in ["kube-system", "kube-public", "kube-node-lease"]]
                }
            except Exception as e:
                logger.error(f"Error getting pod security info: {e}")
                return {"success": False, "error": str(e)}

        # ============================================================
        # PHASE 3: Advanced Features - Network, Diagnostics, Security
        # ============================================================

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Diagnose Network Connectivity",
                readOnlyHint=True,
            ),
        )
        def diagnose_network_connectivity(
            source_pod: str,
            target: str,
            namespace: str = "default",
            port: Optional[int] = None
        ) -> Dict[str, Any]:
            """Test network connectivity from a pod to a target (service, pod IP, or external host)."""
            try:
                import subprocess

                diagnosis = {
                    "source": {"pod": source_pod, "namespace": namespace},
                    "target": target,
                    "port": port,
                    "tests": [],
                    "issues": [],
                    "recommendations": []
                }

                # DNS resolution test
                dns_cmd = ["kubectl", "exec", "-n", namespace, source_pod, "--", "nslookup", target.split(":")[0]]
                dns_result = subprocess.run(dns_cmd, capture_output=True, text=True, timeout=30)
                dns_success = dns_result.returncode == 0

                diagnosis["tests"].append({
                    "name": "DNS Resolution",
                    "success": dns_success,
                    "output": dns_result.stdout if dns_success else dns_result.stderr
                })

                if not dns_success:
                    diagnosis["issues"].append({
                        "type": "DNS",
                        "message": f"Failed to resolve {target}",
                        "details": dns_result.stderr
                    })
                    diagnosis["recommendations"].append("Check CoreDNS pods in kube-system namespace")
                    diagnosis["recommendations"].append("Verify the service/pod exists and is in the correct namespace")

                # Connectivity test (ping or nc)
                if port:
                    # TCP connectivity test
                    nc_cmd = ["kubectl", "exec", "-n", namespace, source_pod, "--", "nc", "-zv", "-w", "5", target.split(":")[0], str(port)]
                    nc_result = subprocess.run(nc_cmd, capture_output=True, text=True, timeout=30)
                    conn_success = nc_result.returncode == 0

                    diagnosis["tests"].append({
                        "name": f"TCP Connectivity (port {port})",
                        "success": conn_success,
                        "output": nc_result.stdout + nc_result.stderr
                    })

                    if not conn_success:
                        diagnosis["issues"].append({
                            "type": "TCP",
                            "message": f"Cannot connect to {target}:{port}",
                            "details": nc_result.stderr
                        })
                        diagnosis["recommendations"].append("Check if NetworkPolicy is blocking traffic")
                        diagnosis["recommendations"].append("Verify the target service/pod is running and listening on the port")
                else:
                    # Ping test
                    ping_cmd = ["kubectl", "exec", "-n", namespace, source_pod, "--", "ping", "-c", "3", "-W", "5", target.split(":")[0]]
                    ping_result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=30)
                    ping_success = ping_result.returncode == 0

                    diagnosis["tests"].append({
                        "name": "ICMP Ping",
                        "success": ping_success,
                        "output": ping_result.stdout if ping_success else ping_result.stderr
                    })

                # Curl test if HTTP/HTTPS target
                if target.startswith("http"):
                    curl_cmd = ["kubectl", "exec", "-n", namespace, source_pod, "--", "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-m", "10", target]
                    curl_result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)

                    http_code = curl_result.stdout.strip()
                    http_success = http_code.startswith("2") or http_code.startswith("3")

                    diagnosis["tests"].append({
                        "name": "HTTP Request",
                        "success": http_success,
                        "httpCode": http_code,
                        "output": f"HTTP {http_code}"
                    })

                # Summary
                all_passed = all(t["success"] for t in diagnosis["tests"])
                diagnosis["summary"] = {
                    "overallSuccess": all_passed,
                    "testsRun": len(diagnosis["tests"]),
                    "testsPassed": len([t for t in diagnosis["tests"] if t["success"]]),
                    "issuesFound": len(diagnosis["issues"])
                }

                return {"success": True, "diagnosis": diagnosis}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Network test timed out"}
            except Exception as e:
                logger.error(f"Error diagnosing network: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Check DNS Resolution",
                readOnlyHint=True,
            ),
        )
        def check_dns_resolution(hostname: str, namespace: str = "default", pod_name: Optional[str] = None) -> Dict[str, Any]:
            """Test DNS resolution from within the cluster."""
            try:
                import subprocess

                # If no pod specified, try to find a suitable pod
                if not pod_name:
                    # Look for a running pod in the namespace
                    find_cmd = ["kubectl", "get", "pods", "-n", namespace, "-o", "jsonpath={.items[0].metadata.name}", "--field-selector=status.phase=Running"]
                    find_result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=10)
                    if find_result.returncode != 0 or not find_result.stdout.strip():
                        return {"success": False, "error": f"No running pods found in namespace '{namespace}' to run DNS test from"}
                    pod_name = find_result.stdout.strip()

                results = {"hostname": hostname, "fromPod": pod_name, "namespace": namespace, "records": []}

                # nslookup
                nslookup_cmd = ["kubectl", "exec", "-n", namespace, pod_name, "--", "nslookup", hostname]
                nslookup_result = subprocess.run(nslookup_cmd, capture_output=True, text=True, timeout=30)

                results["nslookup"] = {
                    "success": nslookup_result.returncode == 0,
                    "output": nslookup_result.stdout if nslookup_result.returncode == 0 else nslookup_result.stderr
                }

                # Parse IPs from output
                if nslookup_result.returncode == 0:
                    import re
                    ips = re.findall(r'Address:\s*(\d+\.\d+\.\d+\.\d+)', nslookup_result.stdout)
                    # Filter out DNS server IPs (usually first one)
                    if len(ips) > 1:
                        results["resolvedIPs"] = ips[1:]
                    else:
                        results["resolvedIPs"] = ips

                # Check CoreDNS status
                coredns_cmd = ["kubectl", "get", "pods", "-n", "kube-system", "-l", "k8s-app=kube-dns", "-o", "jsonpath={.items[*].status.phase}"]
                coredns_result = subprocess.run(coredns_cmd, capture_output=True, text=True, timeout=10)
                results["coreDNSStatus"] = coredns_result.stdout.strip() if coredns_result.returncode == 0 else "unknown"

                return {"success": True, "results": results}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "DNS check timed out"}
            except Exception as e:
                logger.error(f"Error checking DNS: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Evicted Pods",
                readOnlyHint=True,
            ),
        )
        def get_evicted_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Find evicted pods with their eviction reasons."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                if namespace:
                    pods = v1.list_namespaced_pod(namespace)
                else:
                    pods = v1.list_pod_for_all_namespaces()

                evicted = []
                for pod in pods.items:
                    if pod.status.phase == "Failed" and pod.status.reason == "Evicted":
                        evicted.append({
                            "name": pod.metadata.name,
                            "namespace": pod.metadata.namespace,
                            "reason": pod.status.reason,
                            "message": pod.status.message,
                            "nodeName": pod.spec.node_name,
                            "evictedAt": str(pod.status.start_time) if pod.status.start_time else None
                        })

                # Group by reason
                by_reason = {}
                for pod in evicted:
                    msg = pod.get("message", "Unknown")
                    if "ephemeral-storage" in msg.lower():
                        reason = "DiskPressure"
                    elif "memory" in msg.lower():
                        reason = "MemoryPressure"
                    else:
                        reason = "Other"

                    if reason not in by_reason:
                        by_reason[reason] = []
                    by_reason[reason].append(pod["name"])

                return {
                    "success": True,
                    "summary": {
                        "totalEvicted": len(evicted),
                        "byReason": {k: len(v) for k, v in by_reason.items()}
                    },
                    "evictedPods": evicted,
                    "recommendations": [
                        "DiskPressure: Clean up disk space or increase ephemeral-storage limits" if "DiskPressure" in by_reason else None,
                        "MemoryPressure: Increase memory limits or add more nodes" if "MemoryPressure" in by_reason else None
                    ]
                }
            except Exception as e:
                logger.error(f"Error getting evicted pods: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Compare Resources Across Namespaces",
                readOnlyHint=True,
            ),
        )
        def compare_namespaces(namespace1: str, namespace2: str, resource_type: str = "deployment") -> Dict[str, Any]:
            """Compare resources between two namespaces (useful for staging vs prod comparison)."""
            try:
                import subprocess
                import json as json_module

                def get_resources(ns):
                    cmd = ["kubectl", "get", resource_type, "-n", ns, "-o", "json"]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode != 0:
                        return None, result.stderr
                    return json_module.loads(result.stdout), None

                ns1_resources, ns1_err = get_resources(namespace1)
                ns2_resources, ns2_err = get_resources(namespace2)

                if ns1_err:
                    return {"success": False, "error": f"Error getting resources from {namespace1}: {ns1_err}"}
                if ns2_err:
                    return {"success": False, "error": f"Error getting resources from {namespace2}: {ns2_err}"}

                ns1_names = {item["metadata"]["name"]: item for item in ns1_resources.get("items", [])}
                ns2_names = {item["metadata"]["name"]: item for item in ns2_resources.get("items", [])}

                comparison = {
                    "resourceType": resource_type,
                    "namespace1": namespace1,
                    "namespace2": namespace2,
                    "onlyInNs1": list(set(ns1_names.keys()) - set(ns2_names.keys())),
                    "onlyInNs2": list(set(ns2_names.keys()) - set(ns1_names.keys())),
                    "inBoth": list(set(ns1_names.keys()) & set(ns2_names.keys())),
                    "differences": []
                }

                # Compare common resources
                for name in comparison["inBoth"]:
                    r1 = ns1_names[name]
                    r2 = ns2_names[name]

                    diffs = []
                    # Compare replicas for deployments
                    if resource_type == "deployment":
                        r1_replicas = r1.get("spec", {}).get("replicas", 0)
                        r2_replicas = r2.get("spec", {}).get("replicas", 0)
                        if r1_replicas != r2_replicas:
                            diffs.append({"field": "replicas", "ns1": r1_replicas, "ns2": r2_replicas})

                        # Compare image
                        r1_containers = r1.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
                        r2_containers = r2.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
                        for i, (c1, c2) in enumerate(zip(r1_containers, r2_containers)):
                            if c1.get("image") != c2.get("image"):
                                diffs.append({
                                    "field": f"containers[{i}].image",
                                    "ns1": c1.get("image"),
                                    "ns2": c2.get("image")
                                })

                    if diffs:
                        comparison["differences"].append({"name": name, "diffs": diffs})

                comparison["summary"] = {
                    "totalInNs1": len(ns1_names),
                    "totalInNs2": len(ns2_names),
                    "onlyInNs1Count": len(comparison["onlyInNs1"]),
                    "onlyInNs2Count": len(comparison["onlyInNs2"]),
                    "commonCount": len(comparison["inBoth"]),
                    "withDifferences": len(comparison["differences"])
                }

                return {"success": True, "comparison": comparison}
            except Exception as e:
                logger.error(f"Error comparing namespaces: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Admission Webhooks",
                readOnlyHint=True,
            ),
        )
        def get_admission_webhooks() -> Dict[str, Any]:
            """List ValidatingWebhookConfigurations and MutatingWebhookConfigurations."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                admission = client.AdmissionregistrationV1Api()

                validating = admission.list_validating_webhook_configuration()
                mutating = admission.list_mutating_webhook_configuration()

                validating_list = []
                for vwc in validating.items:
                    webhooks = []
                    for wh in (vwc.webhooks or []):
                        webhooks.append({
                            "name": wh.name,
                            "failurePolicy": wh.failure_policy,
                            "matchPolicy": wh.match_policy,
                            "sideEffects": wh.side_effects,
                            "timeoutSeconds": wh.timeout_seconds,
                            "rules": [
                                {
                                    "apiGroups": r.api_groups,
                                    "apiVersions": r.api_versions,
                                    "operations": r.operations,
                                    "resources": r.resources
                                }
                                for r in (wh.rules or [])
                            ]
                        })
                    validating_list.append({
                        "name": vwc.metadata.name,
                        "webhooks": webhooks
                    })

                mutating_list = []
                for mwc in mutating.items:
                    webhooks = []
                    for wh in (mwc.webhooks or []):
                        webhooks.append({
                            "name": wh.name,
                            "failurePolicy": wh.failure_policy,
                            "matchPolicy": wh.match_policy,
                            "sideEffects": wh.side_effects,
                            "timeoutSeconds": wh.timeout_seconds,
                            "reinvocationPolicy": wh.reinvocation_policy
                        })
                    mutating_list.append({
                        "name": mwc.metadata.name,
                        "webhooks": webhooks
                    })

                return {
                    "success": True,
                    "validatingWebhooks": {
                        "count": len(validating_list),
                        "items": validating_list
                    },
                    "mutatingWebhooks": {
                        "count": len(mutating_list),
                        "items": mutating_list
                    }
                }
            except Exception as e:
                logger.error(f"Error getting admission webhooks: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Backup Resource as YAML",
                readOnlyHint=True,
            ),
        )
        def backup_resource(resource_type: str, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
            """Export a resource as YAML for backup or migration."""
            try:
                import subprocess

                cmd = ["kubectl", "get", resource_type, name, "-o", "yaml"]
                if namespace:
                    cmd.extend(["-n", namespace])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}

                # Remove cluster-specific fields for cleaner export
                yaml_content = result.stdout

                return {
                    "success": True,
                    "resource": {
                        "type": resource_type,
                        "name": name,
                        "namespace": namespace
                    },
                    "yaml": yaml_content,
                    "hint": "Save this YAML to a file and use 'kubectl apply -f' to restore"
                }
            except Exception as e:
                logger.error(f"Error backing up resource: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Label Resource",
                readOnlyHint=False,
            ),
        )
        def label_resource(
            resource_type: str,
            name: str,
            labels: Dict[str, str],
            namespace: Optional[str] = None,
            overwrite: bool = False
        ) -> Dict[str, Any]:
            """Add or update labels on a resource."""
            blocked = self._check_destructive()
            if blocked:
                return blocked

            try:
                import subprocess

                cmd = ["kubectl", "label", resource_type, name]
                if namespace:
                    cmd.extend(["-n", namespace])

                # Add labels
                for key, value in labels.items():
                    if value is None:
                        cmd.append(f"{key}-")  # Remove label
                    else:
                        cmd.append(f"{key}={value}")

                if overwrite:
                    cmd.append("--overwrite")

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}

                return {
                    "success": True,
                    "message": result.stdout.strip(),
                    "resource": {"type": resource_type, "name": name, "namespace": namespace},
                    "appliedLabels": labels
                }
            except Exception as e:
                logger.error(f"Error labeling resource: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Annotate Resource",
                readOnlyHint=False,
            ),
        )
        def annotate_resource(
            resource_type: str,
            name: str,
            annotations: Dict[str, str],
            namespace: Optional[str] = None,
            overwrite: bool = False
        ) -> Dict[str, Any]:
            """Add or update annotations on a resource."""
            blocked = self._check_destructive()
            if blocked:
                return blocked

            try:
                import subprocess

                cmd = ["kubectl", "annotate", resource_type, name]
                if namespace:
                    cmd.extend(["-n", namespace])

                for key, value in annotations.items():
                    if value is None:
                        cmd.append(f"{key}-")  # Remove annotation
                    else:
                        cmd.append(f"{key}={value}")

                if overwrite:
                    cmd.append("--overwrite")

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}

                return {
                    "success": True,
                    "message": result.stdout.strip(),
                    "resource": {"type": resource_type, "name": name, "namespace": namespace},
                    "appliedAnnotations": annotations
                }
            except Exception as e:
                logger.error(f"Error annotating resource: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Taint Node",
                readOnlyHint=False,
            ),
        )
        def taint_node(
            node_name: str,
            key: str,
            value: Optional[str] = None,
            effect: str = "NoSchedule",
            remove: bool = False
        ) -> Dict[str, Any]:
            """Add or remove taints on a node."""
            blocked = self._check_destructive()
            if blocked:
                return blocked

            try:
                import subprocess

                if effect not in ["NoSchedule", "PreferNoSchedule", "NoExecute"]:
                    return {"success": False, "error": f"Invalid effect: {effect}. Must be NoSchedule, PreferNoSchedule, or NoExecute"}

                cmd = ["kubectl", "taint", "nodes", node_name]

                if remove:
                    # Remove taint
                    taint_str = f"{key}:{effect}-"
                else:
                    # Add taint
                    if value:
                        taint_str = f"{key}={value}:{effect}"
                    else:
                        taint_str = f"{key}:{effect}"

                cmd.append(taint_str)

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    return {"success": False, "error": result.stderr.strip()}

                return {
                    "success": True,
                    "message": result.stdout.strip(),
                    "node": node_name,
                    "action": "removed" if remove else "added",
                    "taint": {"key": key, "value": value, "effect": effect}
                }
            except Exception as e:
                logger.error(f"Error tainting node: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Wait for Condition",
                readOnlyHint=True,
            ),
        )
        def wait_for_condition(
            resource_type: str,
            name: str,
            condition: str,
            namespace: Optional[str] = None,
            timeout: int = 60
        ) -> Dict[str, Any]:
            """Wait for a resource to reach a specific condition."""
            try:
                import subprocess

                cmd = ["kubectl", "wait", f"{resource_type}/{name}", f"--for={condition}", f"--timeout={timeout}s"]
                if namespace:
                    cmd.extend(["-n", namespace])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)

                if result.returncode != 0:
                    return {
                        "success": False,
                        "conditionMet": False,
                        "error": result.stderr.strip(),
                        "resource": {"type": resource_type, "name": name, "namespace": namespace},
                        "condition": condition
                    }

                return {
                    "success": True,
                    "conditionMet": True,
                    "message": result.stdout.strip(),
                    "resource": {"type": resource_type, "name": name, "namespace": namespace},
                    "condition": condition
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "conditionMet": False,
                    "error": f"Timeout waiting for condition '{condition}' after {timeout}s",
                    "resource": {"type": resource_type, "name": name, "namespace": namespace}
                }
            except Exception as e:
                logger.error(f"Error waiting for condition: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Pod Conditions Detailed",
                readOnlyHint=True,
            ),
        )
        def get_pod_conditions(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
            """Get detailed pod conditions breakdown."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                pod = v1.read_namespaced_pod(pod_name, namespace)

                conditions = []
                for c in (pod.status.conditions or []):
                    conditions.append({
                        "type": c.type,
                        "status": c.status,
                        "reason": c.reason,
                        "message": c.message,
                        "lastTransitionTime": str(c.last_transition_time) if c.last_transition_time else None,
                        "lastProbeTime": str(c.last_probe_time) if c.last_probe_time else None
                    })

                # Container readiness
                container_statuses = []
                for cs in (pod.status.container_statuses or []):
                    status = {
                        "name": cs.name,
                        "ready": cs.ready,
                        "started": cs.started,
                        "restartCount": cs.restart_count,
                        "image": cs.image,
                        "containerID": cs.container_id
                    }
                    if cs.state:
                        if cs.state.running:
                            status["state"] = "running"
                            status["startedAt"] = str(cs.state.running.started_at)
                        elif cs.state.waiting:
                            status["state"] = "waiting"
                            status["waitingReason"] = cs.state.waiting.reason
                        elif cs.state.terminated:
                            status["state"] = "terminated"
                            status["terminatedReason"] = cs.state.terminated.reason
                            status["exitCode"] = cs.state.terminated.exit_code
                    container_statuses.append(status)

                # Overall pod phase
                phase_analysis = {
                    "phase": pod.status.phase,
                    "reason": pod.status.reason,
                    "message": pod.status.message,
                    "hostIP": pod.status.host_ip,
                    "podIP": pod.status.pod_ip,
                    "startTime": str(pod.status.start_time) if pod.status.start_time else None,
                    "qosClass": pod.status.qos_class
                }

                return {
                    "success": True,
                    "pod": pod_name,
                    "namespace": namespace,
                    "phaseAnalysis": phase_analysis,
                    "conditions": conditions,
                    "containerStatuses": container_statuses
                }
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    return {"success": False, "error": f"Pod '{pod_name}' not found in namespace '{namespace}'"}
                return {"success": False, "error": str(e)}
            except Exception as e:
                logger.error(f"Error getting pod conditions: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Trace Service to Pods",
                readOnlyHint=True,
            ),
        )
        def trace_service_chain(service_name: str, namespace: str = "default") -> Dict[str, Any]:
            """Trace the connection chain from a service to its pods."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                v1 = client.CoreV1Api()

                # Get service
                service = v1.read_namespaced_service(service_name, namespace)

                chain = {
                    "service": {
                        "name": service.metadata.name,
                        "namespace": namespace,
                        "type": service.spec.type,
                        "clusterIP": service.spec.cluster_ip,
                        "ports": [
                            {"name": p.name, "port": p.port, "targetPort": str(p.target_port), "protocol": p.protocol}
                            for p in (service.spec.ports or [])
                        ],
                        "selector": service.spec.selector
                    },
                    "endpoints": [],
                    "pods": []
                }

                # Get endpoints
                try:
                    endpoints = v1.read_namespaced_endpoints(service_name, namespace)
                    for subset in (endpoints.subsets or []):
                        for addr in (subset.addresses or []):
                            chain["endpoints"].append({
                                "ip": addr.ip,
                                "nodeName": addr.node_name,
                                "targetRef": {
                                    "kind": addr.target_ref.kind,
                                    "name": addr.target_ref.name
                                } if addr.target_ref else None
                            })
                except:
                    pass

                # Get pods matching selector
                if service.spec.selector:
                    selector = ",".join([f"{k}={v}" for k, v in service.spec.selector.items()])
                    pods = v1.list_namespaced_pod(namespace, label_selector=selector)

                    for pod in pods.items:
                        chain["pods"].append({
                            "name": pod.metadata.name,
                            "ip": pod.status.pod_ip,
                            "phase": pod.status.phase,
                            "ready": all(c.ready for c in (pod.status.container_statuses or []) if c.ready is not None),
                            "nodeName": pod.spec.node_name,
                            "containers": [c.name for c in pod.spec.containers]
                        })

                # Analysis
                ready_pods = [p for p in chain["pods"] if p["ready"]]
                chain["analysis"] = {
                    "totalPods": len(chain["pods"]),
                    "readyPods": len(ready_pods),
                    "endpointCount": len(chain["endpoints"]),
                    "healthy": len(ready_pods) > 0 and len(chain["endpoints"]) > 0,
                    "issues": []
                }

                if not chain["pods"]:
                    chain["analysis"]["issues"].append("No pods match the service selector")
                elif len(ready_pods) == 0:
                    chain["analysis"]["issues"].append("No pods are ready")
                if not chain["endpoints"]:
                    chain["analysis"]["issues"].append("No endpoints found - service cannot route traffic")

                return {"success": True, "chain": chain}
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    return {"success": False, "error": f"Service '{service_name}' not found in namespace '{namespace}'"}
                return {"success": False, "error": str(e)}
            except Exception as e:
                logger.error(f"Error tracing service: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Cluster Version Info",
                readOnlyHint=True,
            ),
        )
        def get_cluster_version() -> Dict[str, Any]:
            """Get detailed cluster version information."""
            try:
                from kubernetes import client, config
                config.load_kube_config()
                version_api = client.VersionApi()

                version_info = version_api.get_code()

                return {
                    "success": True,
                    "version": {
                        "major": version_info.major,
                        "minor": version_info.minor,
                        "gitVersion": version_info.git_version,
                        "gitCommit": version_info.git_commit,
                        "gitTreeState": version_info.git_tree_state,
                        "buildDate": version_info.build_date,
                        "goVersion": version_info.go_version,
                        "compiler": version_info.compiler,
                        "platform": version_info.platform
                    }
                }
            except Exception as e:
                logger.error(f"Error getting cluster version: {e}")
                return {"success": False, "error": str(e)}

        @self.server.tool(
            annotations=ToolAnnotations(
                title="Get Container Logs Previous",
                readOnlyHint=True,
            ),
        )
        def get_previous_logs(
            pod_name: str,
            namespace: str = "default",
            container: Optional[str] = None,
            tail: int = 100
        ) -> Dict[str, Any]:
            """Get logs from the previous container instance (useful for crash debugging)."""
            try:
                import subprocess

                cmd = ["kubectl", "logs", pod_name, "-n", namespace, "--previous", f"--tail={tail}"]
                if container:
                    cmd.extend(["-c", container])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode != 0:
                    if "previous terminated container" in result.stderr.lower():
                        return {"success": False, "error": "No previous container instance found (container hasn't crashed)"}
                    return {"success": False, "error": result.stderr.strip()}

                return {
                    "success": True,
                    "pod": pod_name,
                    "namespace": namespace,
                    "container": container,
                    "logs": result.stdout,
                    "lineCount": len(result.stdout.split("\n"))
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Log retrieval timed out"}
            except Exception as e:
                logger.error(f"Error getting previous logs: {e}")
                return {"success": False, "error": str(e)}

    def _check_destructive(self) -> Optional[Dict[str, Any]]:
        """Check if destructive operations are allowed."""
        if self.non_destructive:
            return {"success": False, "error": "Operation blocked: non-destructive mode enabled"}
        return None

    def setup_prompts(self):
        """Set up MCP prompts."""
        @self.server.prompt()
        def troubleshoot_workload(workload: str, namespace: Optional[str] = None, resource_type: str = "pod") -> str:
            """Comprehensive troubleshooting guide for Kubernetes workloads."""
            ns_clause = f"-n {namespace}" if namespace else "--all-namespaces"
            ns_text = f"in namespace '{namespace}'" if namespace else "across all namespaces"
            return f"""# Kubernetes Troubleshooting: {workload}

Target: {resource_type}s matching '{workload}' {ns_text}

## Step 1: Discovery
First, identify all relevant resources:
- Use `get_pods` with namespace={namespace or 'None'} to list pods
- Filter results for pods containing '{workload}' in the name
- Note the status of each pod (Running, Pending, CrashLoopBackOff, etc.)

## Step 2: Status Analysis
For each pod found, check:
- **Phase**: Is it Running, Pending, Failed, or Unknown?
- **Ready**: Are all containers ready? (e.g., 1/1, 2/2)
- **Restarts**: High restart count indicates crashes
- **Age**: Recently created pods may still be starting

### Common Status Issues:
| Status | Likely Cause | First Check |
|--------|--------------|-------------|
| Pending | Scheduling issues | get_pod_events |
| CrashLoopBackOff | App crash on start | get_logs |
| ImagePullBackOff | Image not found | kubectl_describe |
| OOMKilled | Memory limit exceeded | kubectl_describe |
| CreateContainerError | Config issue | get_pod_events |

## Step 3: Deep Inspection
Use these tools in order:

1. **Events** - `get_pod_events(pod_name, namespace)`
   - Look for: FailedScheduling, FailedMount, Unhealthy
   - Check timestamps for recent issues

2. **Logs** - `get_logs(pod_name, namespace, tail=100)`
   - Look for: exceptions, errors, stack traces
   - If container crashed: use previous=true

3. **Describe** - `kubectl_describe("pod", pod_name, namespace)`
   - Check: resource requests/limits, node assignment
   - Look at: conditions, volumes, container states

## Step 4: Related Resources
Check parent resources:
- For Deployments: `kubectl_describe("deployment", name, namespace)`
- For StatefulSets: `kubectl_describe("statefulset", name, namespace)`
- For DaemonSets: `kubectl_describe("daemonset", name, namespace)`

Check dependencies:
- Services: `get_services(namespace)` 
- ConfigMaps/Secrets: referenced in pod spec
- PVCs: `kubectl_describe("pvc", name, namespace)` if storage issues

## Step 5: Resolution Checklist
For each issue, provide:

1. **Root Cause**: What is actually wrong
2. **Evidence**: Specific log line or event message
3. **Fix Command**: Exact kubectl command or manifest change
4. **Verification**: How to confirm the fix worked
5. **Prevention**: Configuration to prevent recurrence

## Common Fixes Reference:
- **OOMKilled**: Increase memory limits in deployment spec
- **CrashLoopBackOff**: Fix application error, check logs
- **Pending (no nodes)**: Check node capacity, add nodes
- **ImagePullBackOff**: Verify image name, check imagePullSecrets
- **Mount failures**: Check PVC status, storage class

Start the investigation now."""

    def _mask_secrets(self, text: str) -> str:
        """Mask sensitive data in output."""
        import re
        # Mask base64-encoded data that looks like secrets
        masked = re.sub(r'(data:\s*\n)(\s+\w+:\s*)([A-Za-z0-9+/=]{20,})', r'\1\2[MASKED]', text)
        # Mask password-like fields
        masked = re.sub(r'(password|secret|token|key|credential)(["\s:=]+)([^\s"\n]+)', r'\1\2[MASKED]', masked, flags=re.IGNORECASE)
        return masked
    
    def _check_dependencies(self) -> bool:
        """Check for required command-line tools."""
        all_available = True
        for tool in ["kubectl", "helm"]:
            if not self._check_tool_availability(tool):
                logger.warning(f"{tool} not found in PATH. Operations requiring {tool} will not work.")
                all_available = False
        return all_available
    
    def _check_tool_availability(self, tool: str) -> bool:
        """Check if a specific tool is available."""
        try:
            import subprocess, shutil
            if shutil.which(tool) is None:
                return False
            if tool == "kubectl":
                subprocess.check_output(
                    [tool, "version", "--client", "--output=json"],
                    stderr=subprocess.PIPE,
                    timeout=2
                )
            elif tool == "helm":
                subprocess.check_output(
                    [tool, "version", "--short"],
                    stderr=subprocess.PIPE,
                    timeout=2
                )
            return True
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_kubectl_availability(self) -> bool:
        """Check if kubectl is available."""
        return self._check_tool_availability("kubectl")
    
    def _check_helm_availability(self) -> bool:
        """Check if helm is available."""
        return self._check_tool_availability("helm")
    
    async def serve_stdio(self):
        """Serve the MCP server over stdio transport."""
        if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true"):
            logger.debug("Starting MCP server with stdio transport")
            logger.debug(f"Working directory: {os.getcwd()}")
            kube_config = os.environ.get('KUBECONFIG', '~/.kube/config')
            expanded_path = os.path.expanduser(kube_config)
            logger.debug(f"KUBECONFIG: {expanded_path}")
            logger.debug(f"Dependencies: {'available' if self.dependencies_available else 'missing'}")
        
        await self.server.run_stdio_async()
    
    async def serve_sse(self, host: str = "0.0.0.0", port: int = 8000):
        """Serve the MCP server over SSE transport."""
        logger.info(f"Starting MCP server with SSE transport on {host}:{port}")

        try:
            # Try newer FastMCP API with host and port
            await self.server.run_sse_async(host=host, port=port)
        except TypeError:
            try:
                # Try with just port parameter
                await self.server.run_sse_async(port=port)
            except TypeError:
                # Fall back to the legacy signature that takes no parameters
                logger.warning(
                    "FastMCP.run_sse_async() does not accept host/port parameters in this version. "
                    "Falling back to the default signature (using FastMCP's internal default port)."
                )
                await self.server.run_sse_async()
    
    async def serve_http(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Serve the MCP server over HTTP transport (streamable HTTP).
        This is an alternative to SSE that some clients prefer.
        """
        logger.info(f"Starting MCP server with HTTP transport on {host}:{port}")
        
        try:
            # Check if FastMCP supports streamable HTTP
            if hasattr(self.server, 'run_http_async'):
                await self.server.run_http_async(host=host, port=port)
            elif hasattr(self.server, 'run_streamable_http_async'):
                await self.server.run_streamable_http_async(host=host, port=port)
            else:
                # Fall back to implementing HTTP transport manually using ASGI
                logger.info("FastMCP does not have built-in HTTP support, using custom implementation")
                await self._serve_http_custom(host=host, port=port)
        except TypeError as e:
            logger.warning(f"HTTP transport parameter issue: {e}. Trying alternative signatures...")
            # Try without parameters
            if hasattr(self.server, 'run_http_async'):
                await self.server.run_http_async()
            elif hasattr(self.server, 'run_streamable_http_async'):
                await self.server.run_streamable_http_async()
            else:
                await self._serve_http_custom(host=host, port=port)
    
    async def _serve_http_custom(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Custom HTTP server implementation using uvicorn and Starlette.
        Provides HTTP/JSON-RPC transport for MCP.
        """
        try:
            from starlette.applications import Starlette
            from starlette.responses import JSONResponse
            from starlette.routing import Route
            import uvicorn
        except ImportError:
            logger.error("HTTP transport requires 'starlette' and 'uvicorn'. Install with: pip install starlette uvicorn")
            raise ImportError("Missing dependencies for HTTP transport. Run: pip install starlette uvicorn")
        
        async def handle_mcp_request(request):
            """Handle incoming MCP JSON-RPC requests."""
            try:
                body = await request.json()
                logger.debug(f"Received MCP request: {body}")
                
                # Get the method and params from the JSON-RPC request
                method = body.get("method", "")
                params = body.get("params", {})
                request_id = body.get("id")
                
                # Handle different MCP methods
                if method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"subscribe": False, "listChanged": True}
                        },
                        "serverInfo": {
                            "name": self.name,
                            "version": "1.2.0"
                        }
                    }
                elif method == "tools/list":
                    # Get list of tools from FastMCP
                    tools = []
                    if hasattr(self.server, '_tool_manager') and hasattr(self.server._tool_manager, 'tools'):
                        for name, tool in self.server._tool_manager.tools.items():
                            tools.append({
                                "name": name,
                                "description": tool.description if hasattr(tool, 'description') else "",
                                "inputSchema": tool.parameters if hasattr(tool, 'parameters') else {}
                            })
                    result = {"tools": tools}
                elif method == "tools/call":
                    tool_name = params.get("name", "")
                    tool_args = params.get("arguments", {})
                    
                    # Execute the tool
                    if hasattr(self.server, '_tool_manager'):
                        try:
                            tool_result = await self.server._tool_manager.call_tool(tool_name, tool_args)
                            result = {"content": [{"type": "text", "text": json.dumps(tool_result)}]}
                        except Exception as e:
                            result = {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
                    else:
                        result = {"content": [{"type": "text", "text": "Tool manager not available"}], "isError": True}
                elif method == "ping":
                    result = {}
                else:
                    result = {"error": f"Unknown method: {method}"}
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                return JSONResponse(response)
            except Exception as e:
                logger.error(f"Error handling MCP request: {e}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }, status_code=500)
        
        async def health_check(request):
            """Health check endpoint."""
            return JSONResponse({"status": "healthy", "server": self.name})
        
        app = Starlette(
            routes=[
                Route("/", handle_mcp_request, methods=["POST"]),
                Route("/mcp", handle_mcp_request, methods=["POST"]),
                Route("/health", health_check, methods=["GET"]),
            ]
        )
        
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
        
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Kubectl MCP Server.")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "http", "streamable-http"],
        default="stdio",
        help="Communication transport to use (stdio, sse, http, or streamable-http). Default: stdio.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to use for SSE/HTTP transport. Default: 8000.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to for SSE/HTTP transport. Default: 0.0.0.0.",
    )
    args = parser.parse_args()

    server_name = "kubectl_mcp_server"
    mcp_server = MCPServer(name=server_name)

    import signal
    import os

    # Handle signals gracefully with immediate exit
    def signal_handler(sig, frame):
        print("\nShutting down server...", file=sys.stderr)
        os._exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if args.transport == "stdio":
            logger.info(f"Starting {server_name} with stdio transport.")
            asyncio.run(mcp_server.serve_stdio())
        elif args.transport == "sse":
            logger.info(f"Starting {server_name} with SSE transport on {args.host}:{args.port}.")
            asyncio.run(mcp_server.serve_sse(host=args.host, port=args.port))
        elif args.transport in ("http", "streamable-http"):
            logger.info(f"Starting {server_name} with HTTP transport on {args.host}:{args.port}.")
            asyncio.run(mcp_server.serve_http(host=args.host, port=args.port))
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
    except SystemExit:
        pass  # Clean exit
    except Exception as e:
        logger.error(f"Server exited with error: {e}", exc_info=True)