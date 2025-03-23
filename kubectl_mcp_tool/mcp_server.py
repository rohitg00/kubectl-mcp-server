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

try:
    # Import the official MCP SDK
    from mcp.server import Server
    from mcp.server import stdio, sse
    import mcp.types as types
    from mcp.server.models import InitializationOptions
except ImportError:
    logging.error("MCP SDK not found. Installing...")
    import subprocess
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "git+https://github.com/modelcontextprotocol/python-sdk.git"
        ])
        from mcp.server import Server
        from mcp.server import stdio, sse
        import mcp.types as types
        from mcp.server.models import InitializationOptions
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
        # Create a new server instance using the MCP SDK
        self.server = Server(name=name, version="0.1.0")
        
        # Register tools using the correct API
        self.setup_tools()
    
    def setup_tools(self):
        """Set up the tools for the MCP server."""
        # Define tools
        tools = [
            {
                "name": "process_natural_language",
                "description": "Process natural language query for kubectl",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The natural language query to process"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_pods",
                "description": "Get all pods in the specified namespace",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "The Kubernetes namespace (optional)"
                        }
                    }
                }
            },
            {
                "name": "get_namespaces",
                "description": "Get all Kubernetes namespaces",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "create_deployment",
                "description": "Create a new deployment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the deployment"
                        },
                        "image": {
                            "type": "string",
                            "description": "Container image to use"
                        },
                        "replicas": {
                            "type": "integer",
                            "description": "Number of replicas"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Target namespace"
                        }
                    },
                    "required": ["name", "image", "replicas"]
                }
            },
            {
                "name": "delete_resource",
                "description": "Delete a Kubernetes resource",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource_type": {
                            "type": "string",
                            "description": "Type of resource (pod, deployment, service, etc.)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Name of the resource"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Resource namespace"
                        }
                    },
                    "required": ["resource_type", "name"]
                }
            },
            {
                "name": "get_logs",
                "description": "Get logs from a pod",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pod_name": {
                            "type": "string",
                            "description": "Name of the pod"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Pod namespace"
                        },
                        "container": {
                            "type": "string",
                            "description": "Container name (if pod has multiple containers)"
                        },
                        "tail": {
                            "type": "integer",
                            "description": "Number of lines to tail"
                        }
                    },
                    "required": ["pod_name"]
                }
            },
            {
                "name": "port_forward",
                "description": "Forward local port to pod port",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pod_name": {
                            "type": "string",
                            "description": "Name of the pod"
                        },
                        "local_port": {
                            "type": "integer",
                            "description": "Local port to forward from"
                        },
                        "pod_port": {
                            "type": "integer",
                            "description": "Pod port to forward to"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Pod namespace"
                        }
                    },
                    "required": ["pod_name", "local_port", "pod_port"]
                }
            },
            {
                "name": "scale_deployment",
                "description": "Scale a deployment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the deployment"
                        },
                        "replicas": {
                            "type": "integer",
                            "description": "Number of desired replicas"
                        },
                        "namespace": {
                            "type": "string",
                            "description": "Deployment namespace"
                        }
                    },
                    "required": ["name", "replicas"]
                }
            }
        ]
        
        # Register tools with the server
        for tool in tools:
            self.server.tools.append(tool)
        
        # Register tool handlers
        @self.server.on_tool_call("process_natural_language")
        async def process_natural_language(query: str) -> Dict[str, Any]:
            """Process natural language query for kubectl."""
            try:
                result = process_query(query)
                return {"success": True, "result": result}
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                return {"success": False, "error": str(e)}
        
        @self.server.on_tool_call("get_pods")
        async def get_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
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
        
        @self.server.on_tool_call("get_namespaces")
        async def get_namespaces() -> Dict[str, Any]:
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
        
        @self.server.on_tool_call("create_deployment")
        async def create_deployment(name: str, image: str, replicas: int, namespace: Optional[str] = "default") -> Dict[str, Any]:
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
        
        @self.server.on_tool_call("delete_resource")
        async def delete_resource(resource_type: str, name: str, namespace: Optional[str] = "default") -> Dict[str, Any]:
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
        
        @self.server.on_tool_call("get_logs")
        async def get_logs(pod_name: str, namespace: Optional[str] = "default", container: Optional[str] = None, tail: Optional[int] = None) -> Dict[str, Any]:
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
        
        @self.server.on_tool_call("port_forward")
        async def port_forward(pod_name: str, local_port: int, pod_port: int, namespace: Optional[str] = "default") -> Dict[str, Any]:
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
        
        @self.server.on_tool_call("scale_deployment")
        async def scale_deployment(name: str, replicas: int, namespace: Optional[str] = "default") -> Dict[str, Any]:
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
    
    async def serve_stdio(self):
        """Serve the MCP server over stdio transport."""
        logger.info("Serving MCP server over stdio")
        await stdio.serve(self.server)
    
    async def serve_sse(self, port: int):
        """Serve the MCP server over SSE transport."""
        logger.info(f"Serving MCP server over SSE on port {port}")
        await sse.serve(self.server, port=port)
