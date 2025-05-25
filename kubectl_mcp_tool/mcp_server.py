#!/usr/bin/env python3
"""
MCP server implementation for kubectl-mcp-tool.
"""

import json
import sys
import logging
import asyncio
import os
from typing import Dict, Any, List, Optional, Callable, Awaitable

import warnings
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    message=r".*found in sys.modules after import of package.*"
)

try:
    # Import the official MCP SDK with FastMCP
    from mcp.server.fastmcp import FastMCP
except ImportError:
    logging.error("MCP SDK not found. Installing...")
    import subprocess
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "mcp>=1.5.0"
        ])
        from mcp.server.fastmcp import FastMCP
    except Exception as e:
        logging.error(f"Failed to install MCP SDK: {e}")
        raise

from .natural_language import process_query

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-server")

class MCPServer:
    """MCP server implementation."""

    def __init__(self, name: str):
        """Initialize the MCP server."""
        self.name = name
        # Create a new server instance using the FastMCP API
        self.server = FastMCP(name=name)
        # Check for required dependencies
        self.dependencies_available = self._check_dependencies()
        if not self.dependencies_available:
            logger.warning("Some dependencies are missing. Certain operations may not work correctly.")
        # Register tools using the new FastMCP API
        self.setup_tools()
    
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
                            "status": node.status.conditions[-1].type if node.status.conditions else None,
                            "addresses": [addr.address for addr in node.status.addresses]
                        } for node in nodes.items
                    ]
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
            # Use shutil.which for more reliable cross-platform checking
            if shutil.which(tool) is None:
                return False
            # Also verify it runs correctly
            if tool == "kubectl":
                subprocess.check_output([tool, "version", "--client"], stderr=subprocess.PIPE)
            elif tool == "helm":
                subprocess.check_output([tool, "version"], stderr=subprocess.PIPE)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_kubectl_availability(self) -> bool:
        """Check if kubectl is available."""
        return self._check_tool_availability("kubectl")
    
    def _check_helm_availability(self) -> bool:
        """Check if helm is available."""
        return self._check_tool_availability("helm")
    
    async def serve_stdio(self):
        """Serve the MCP server over stdio transport."""
        # Add detailed logging for debugging Cursor integration
        logger.info("Starting MCP server with stdio transport")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"Python version: {sys.version}")
        
        # Log Kubernetes configuration
        kube_config = os.environ.get('KUBECONFIG', '~/.kube/config')
        expanded_path = os.path.expanduser(kube_config)
        logger.info(f"KUBECONFIG: {kube_config} (expanded: {expanded_path})")
        if os.path.exists(expanded_path):
            logger.info(f"Kubernetes config file exists at {expanded_path}")
        else:
            logger.warning(f"Kubernetes config file does not exist at {expanded_path}")
        
        # Log dependency check results
        logger.info(f"Dependencies check result: {'All available' if self.dependencies_available else 'Some missing'}")
        
        # Continue with normal server startup
        await self.server.run_stdio_async()
    
    async def serve_sse(self, port: int):
        """Serve the MCP server over SSE transport."""
        logger.info(f"Starting MCP server with SSE transport on port {port}")
        await self.server.run_sse_async(port=port)
        
if __name__ == "__main__":
    import asyncio
    import argparse
    # Ensure that logging, os, sys, FastMCP, MCPServer, and the logger instance
    # are imported or defined earlier in the file as needed.
    # Based on our previous views, most of these should already be in place.

    parser = argparse.ArgumentParser(description="Run the Kubectl MCP Server.")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default="stdio",
        help="Communication transport to use (stdio or sse). Default: stdio.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to use for SSE transport. Default: 8080.",
    )
    args = parser.parse_args()

    server_name = "kubectl_mcp_server"
    # Ensure MCPServer class is defined above this block
    mcp_server = MCPServer(name=server_name) 
    # Ensure logger is defined at the module level
    # logger = logging.getLogger(__name__) # Or however it's set up

    loop = asyncio.get_event_loop()
    try:
        if args.transport == "stdio":
            logger.info(f"Starting {server_name} with stdio transport.")
            loop.run_until_complete(mcp_server.serve_stdio())
        elif args.transport == "sse":
            logger.info(f"Starting {server_name} with SSE transport on port {args.port}.")
            loop.run_until_complete(mcp_server.serve_sse(port=args.port))
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user.")
    except Exception as e:
        logger.error(f"Server exited with error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down server.")