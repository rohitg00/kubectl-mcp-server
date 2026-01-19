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
except ImportError:
    logger.error("MCP SDK not found. Installing...")
    import subprocess
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "mcp>=1.5.0"],
            stdout=subprocess.DEVNULL,  # Don't pollute stdout
            stderr=subprocess.DEVNULL
        )
        from mcp.server.fastmcp import FastMCP
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
        @self.server.tool()
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
        
        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

        @self.server.tool()
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

    loop = asyncio.get_event_loop()
    try:
        if args.transport == "stdio":
            logger.info(f"Starting {server_name} with stdio transport.")
            loop.run_until_complete(mcp_server.serve_stdio())
        elif args.transport == "sse":
            logger.info(f"Starting {server_name} with SSE transport on {args.host}:{args.port}.")
            loop.run_until_complete(mcp_server.serve_sse(host=args.host, port=args.port))
        elif args.transport in ("http", "streamable-http"):
            logger.info(f"Starting {server_name} with HTTP transport on {args.host}:{args.port}.")
            loop.run_until_complete(mcp_server.serve_http(host=args.host, port=args.port))
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user.")
    except Exception as e:
        logger.error(f"Server exited with error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down server.")