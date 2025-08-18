#!/usr/bin/env python3
"""
Simple Kubernetes MCP Server with enhanced features.
"""

import json
import sys
import logging
import threading
import time
from typing import Dict, Any, Optional
from kubectl_mcp_tool.core.kubernetes_ops import KubernetesOperations
from kubectl_mcp_tool.security.security_ops import KubernetesSecurityOps
from kubectl_mcp_tool.monitoring.diagnostics import KubernetesDiagnostics
from kubernetes import client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

class SimpleKubectlMcpServer:
    """Simple MCP server for Kubernetes operations."""

    def __init__(self, input_stream=sys.stdin, output_stream=sys.stdout):
        """Initialize the server."""
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.k8s_ops = KubernetesOperations()
        self.security_ops = KubernetesSecurityOps()
        self.diagnostics = KubernetesDiagnostics()
        self.current_namespace = "default"  # Store the current namespace
        self.heartbeat_interval = 5
        self.running = True
        self.heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def send_heartbeat(self):
        """Send periodic heartbeat messages."""
        while self.running:
            try:
                self.write_message({
                    "jsonrpc": "2.0", 
                    "method": "heartbeat", 
                    "params": {}
                })
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logging.error(f"Error sending heartbeat: {str(e)}")

    def set_current_namespace(self, namespace: str) -> Dict[str, Any]:
        """Set the current namespace for future operations."""
        old_namespace = self.current_namespace
        self.current_namespace = namespace
        
        return {
            "status": "success",
            "message": f"Namespace changed from '{old_namespace}' to '{namespace}'",
            "current_namespace": namespace
        }

    def handle_init(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request."""
        try:
            return {
                "name": "kubectl-mcp-server-simple",
                "version": "0.1.0",
                "capabilities": ["tools/list", "tools/call"]
            }
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return {
                "error": str(e)
            }

    def handle_tools_list(self) -> Dict[str, Any]:
        """List all the available tools."""
        return {
            "tools": [
                {
                    "name": "init",
                    "description": "Initialize the server with a config file.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "config_path": {"type": "string", "description": "Path to the config file."},
                        },
                        "required": ["config_path"]
                    }
                },
                # Pod Management
                {
                    "name": "create_pod",
                    "description": "Create a new pod in the Kubernetes cluster.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "pod_name": {"type": "string", "description": "Name for the pod."},
                            "namespace": {"type": "string", "description": "Namespace to create the pod in."},
                            "image": {"type": "string", "description": "Container image to use for the pod."},
                            "command": {"type": "array", "items": {"type": "string"}, "description": "Command to run in the container."},
                            "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments for the command."},
                            "env_vars": {"type": "object", "description": "Environment variables to set in the container."},
                            "ports": {"type": "array", "items": {"type": "integer"}, "description": "Ports to expose from the container."},
                            "volume_mounts": {"type": "array", "items": {"type": "object"}, "description": "Volumes to mount in the container."},
                        },
                        "required": ["pod_name", "namespace", "image"]
                    }
                },
                {
                    "name": "delete_pod",
                    "description": "Delete a pod",
                    "inputSchema": {
                        "type": "object",
                        "required": ["pod_name"],
                        "properties": {
                            "pod_name": {"type": "string"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                # Deployment Management
                {
                    "name": "create_deployment",
                    "description": "Create a new deployment",
                    "inputSchema": {
                        "type": "object",
                        "required": ["deployment_spec"],
                        "properties": {
                            "deployment_spec": {"type": "object"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                {
                    "name": "scale_deployment",
                    "description": "Scale a deployment",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name", "replicas"],
                        "properties": {
                            "name": {"type": "string"},
                            "replicas": {"type": "integer"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                {
                    "name": "rollback_deployment",
                    "description": "Rollback a deployment",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "revision": {"type": "integer"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                # Service Management
                {
                    "name": "create_service",
                    "description": "Create a new service",
                    "inputSchema": {
                        "type": "object",
                        "required": ["service_spec"],
                        "properties": {
                            "service_spec": {"type": "object"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                {
                    "name": "delete_service",
                    "description": "Delete a service",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                # Configuration Management
                {
                    "name": "create_config_map",
                    "description": "Create a ConfigMap",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name", "data"],
                        "properties": {
                            "name": {"type": "string"},
                            "data": {"type": "object"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                {
                    "name": "create_secret",
                    "description": "Create a Secret",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name", "data"],
                        "properties": {
                            "name": {"type": "string"},
                            "data": {"type": "object"},
                            "secret_type": {"type": "string", "default": "Opaque"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                # Network Operations
                {
                    "name": "create_network_policy",
                    "description": "Create a NetworkPolicy",
                    "inputSchema": {
                        "type": "object",
                        "required": ["policy_spec"],
                        "properties": {
                            "policy_spec": {"type": "object"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                {
                    "name": "create_ingress",
                    "description": "Create an Ingress",
                    "inputSchema": {
                        "type": "object",
                        "required": ["ingress_spec"],
                        "properties": {
                            "ingress_spec": {"type": "object"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                # Security Operations
                {
                    "name": "create_role",
                    "description": "Create a Role",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name", "rules"],
                        "properties": {
                            "name": {"type": "string"},
                            "rules": {"type": "array"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                {
                    "name": "create_cluster_role",
                    "description": "Create a ClusterRole",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name", "rules"],
                        "properties": {
                            "name": {"type": "string"},
                            "rules": {"type": "array"}
                        }
                    }
                },
                {
                    "name": "create_service_account",
                    "description": "Create a ServiceAccount",
                    "inputSchema": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string"},
                            "namespace": {"type": "string", "default": "default"},
                            "annotations": {"type": "object"}
                        }
                    }
                },
                {
                    "name": "audit_rbac",
                    "description": "Audit RBAC permissions",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string"},
                            "audit_type": {"type": "string"}
                        }
                    }
                },
                # Monitoring and Diagnostics
                {
                    "name": "get_pod_logs",
                    "description": "Get logs from a pod",
                    "inputSchema": {
                        "type": "object",
                        "required": ["pod_name"],
                        "properties": {
                            "pod_name": {"type": "string"},
                            "namespace": {"type": "string", "default": "default"},
                            "container": {"type": "string"},
                            "tail_lines": {"type": "integer", "default": 100},
                            "since_seconds": {"type": "integer"}
                        }
                    }
                },
                {
                    "name": "analyze_pod_logs",
                    "description": "Analyze pod logs for patterns and issues",
                    "inputSchema": {
                        "type": "object",
                        "required": ["pod_name"],
                        "properties": {
                            "pod_name": {"type": "string"},
                            "namespace": {"type": "string", "default": "default"},
                            "container": {"type": "string"},
                            "tail_lines": {"type": "integer", "default": 1000}
                        }
                    }
                },
                {
                    "name": "get_pod_events",
                    "description": "Get events related to a pod",
                    "inputSchema": {
                        "type": "object",
                        "required": ["pod_name"],
                        "properties": {
                            "pod_name": {"type": "string"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                {
                    "name": "check_pod_health",
                    "description": "Check the health status of a pod",
                    "inputSchema": {
                        "type": "object",
                        "required": ["pod_name"],
                        "properties": {
                            "pod_name": {"type": "string"},
                            "namespace": {"type": "string", "default": "default"}
                        }
                    }
                },
                {
                    "name": "get_resource_usage",
                    "description": "Get resource usage metrics for pods",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "validate_resources",
                    "description": "Validate resource configurations and usage",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "analyze_network_policies",
                    "description": "Analyze NetworkPolicies for security gaps",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "check_pod_security",
                    "description": "Check pod security context for best practices",
                    "inputSchema": {
                        "type": "object",
                        "required": ["pod_spec"],
                        "properties": {
                            "pod_spec": {"type": "object"}
                        }
                    }
                },
                # Context Management
                {
                    "name": "get_contexts",
                    "description": "Get available contexts",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "switch_context",
                    "description": "Switch to a different context",
                    "inputSchema": {
                        "type": "object",
                        "required": ["context_name"],
                        "properties": {
                            "context_name": {"type": "string"}
                        }
                    }
                },
                # Resource Listing Tools
                {
                    "name": "list_pods",
                    "description": "List pods in a namespace with filtering options.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "Namespace to list pods from."},
                            "label_selector": {"type": "string", "description": "Label selector to filter pods (e.g. 'app=nginx')."},
                            "field_selector": {"type": "string", "description": "Field selector to filter pods (e.g. 'status.phase=Running')."}
                        },
                        "required": []
                    }
                },
                {
                    "name": "list_deployments",
                    "description": "List deployments in a namespace with filtering options.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "Namespace to list deployments from."},
                            "label_selector": {"type": "string", "description": "Label selector to filter deployments (e.g. 'app=nginx')."}
                        },
                        "required": []
                    }
                },
                {
                    "name": "list_services",
                    "description": "List services in a namespace with filtering options.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "Namespace to list services from."},
                            "label_selector": {"type": "string", "description": "Label selector to filter services (e.g. 'app=nginx')."}
                        },
                        "required": []
                    }
                },
                {
                    "name": "list_nodes",
                    "description": "List all nodes in the Kubernetes cluster.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "label_selector": {"type": "string", "description": "Label selector to filter nodes."}
                        },
                        "required": []
                    }
                },
                {
                    "name": "list_namespaces",
                    "description": "List all namespaces in the Kubernetes cluster.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "label_selector": {"type": "string", "description": "Label selector to filter namespaces."}
                        },
                        "required": []
                    }
                },
                # Helm Chart Support
                {
                    "name": "install_helm_chart",
                    "description": "Install a Helm chart in the Kubernetes cluster.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Release name for the chart installation."},
                            "chart": {"type": "string", "description": "Chart name or path (e.g., 'stable/nginx' or 'nginx')."},
                            "namespace": {"type": "string", "description": "Namespace to install the chart in."},
                            "repo": {"type": "string", "description": "Chart repository URL (optional)."},
                            "values": {"type": "object", "description": "Values to override in the chart (optional)."}
                        },
                        "required": ["name", "chart", "namespace"]
                    }
                },
                {
                    "name": "upgrade_helm_chart",
                    "description": "Upgrade an existing Helm release.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name of the Helm release to upgrade."},
                            "chart": {"type": "string", "description": "Chart name or path to upgrade to."},
                            "namespace": {"type": "string", "description": "Namespace of the release."},
                            "repo": {"type": "string", "description": "Chart repository URL (optional)."},
                            "values": {"type": "object", "description": "Values to override in the chart (optional)."}
                        },
                        "required": ["name", "chart", "namespace"]
                    }
                },
                {
                    "name": "uninstall_helm_chart",
                    "description": "Uninstall a Helm release.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Name of the Helm release to uninstall."},
                            "namespace": {"type": "string", "description": "Namespace of the release."}
                        },
                        "required": ["name", "namespace"]
                    }
                },
                # Kubectl Utilities
                {
                    "name": "explain_resource",
                    "description": "Get documentation for a Kubernetes resource from the API server.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "resource": {"type": "string", "description": "Resource to explain (e.g., 'pods', 'deployments.v1.apps')."},
                            "api_version": {"type": "string", "description": "API version of the resource (optional)."},
                            "recursive": {"type": "boolean", "description": "Whether to show all fields recursively."}
                        },
                        "required": ["resource"]
                    }
                },
                {
                    "name": "list_api_resources",
                    "description": "List API resources available in the Kubernetes cluster.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "api_group": {"type": "string", "description": "API group to filter by (e.g., 'apps', 'networking.k8s.io')."},
                            "namespaced": {"type": "boolean", "description": "Whether to show only namespaced resources."},
                            "verbs": {"type": "array", "items": {"type": "string"}, "description": "Filter by verbs (e.g., ['get', 'list', 'watch'])."}
                        },
                        "required": []
                    }
                },
                {
                    "name": "describe_pod",
                    "description": "Get detailed information about a pod.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "pod_name": {"type": "string", "description": "Name of the pod to describe."},
                            "namespace": {"type": "string", "description": "Namespace of the pod."}
                        },
                        "required": ["pod_name"]
                    }
                },
                # Context and Namespace Management
                {
                    "name": "set_namespace",
                    "description": "Set the default namespace for subsequent commands.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "namespace": {"type": "string", "description": "The namespace to set as default."}
                        },
                        "required": ["namespace"]
                    }
                }
            ]
        }

    def handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request."""
        name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        try:
            # Pod Management
            if name == "create_pod":
                return self.k8s_ops.create_pod(**arguments)
            elif name == "delete_pod":
                return self.k8s_ops.delete_pod(**arguments)
            elif name == "check_pod_health":
                return self.k8s_ops.check_pod_health(**arguments)
            elif name == "get_pod_logs":
                return self.k8s_ops.get_pod_logs(**arguments)
            
            # Deployment Management
            elif name == "create_deployment":
                return self.k8s_ops.create_deployment(**arguments)
            elif name == "delete_deployment":
                return self.k8s_ops.delete_deployment(**arguments)
            elif name == "scale_deployment":
                return self.k8s_ops.scale_deployment(**arguments)
            
            # Service Management
            elif name == "create_service":
                return self.k8s_ops.create_service(**arguments)
            elif name == "delete_service":
                return self.k8s_ops.delete_service(**arguments)
                
            # Resource Listing Tools
            elif name == "list_pods":
                return self.k8s_ops.list_pods(**arguments)
            elif name == "list_deployments":
                return self.k8s_ops.list_deployments(**arguments)
            elif name == "list_services":
                return self.k8s_ops.list_services(**arguments)
            elif name == "list_nodes":
                return self.k8s_ops.list_nodes(**arguments)
            elif name == "list_namespaces":
                return self.k8s_ops.list_namespaces(**arguments)
                
            # Helm Chart Support
            elif name == "install_helm_chart":
                return self.k8s_ops.install_helm_chart(**arguments)
            elif name == "upgrade_helm_chart":
                return self.k8s_ops.upgrade_helm_chart(**arguments)
            elif name == "uninstall_helm_chart":
                return self.k8s_ops.uninstall_helm_chart(**arguments)
                
            # Kubectl Utilities
            elif name == "explain_resource":
                return self.k8s_ops.explain_resource(**arguments)
            elif name == "list_api_resources":
                return self.k8s_ops.list_api_resources(**arguments)
            elif name == "describe_pod":
                return self.k8s_ops.describe_pod(**arguments)
                
            # Security Operations
            elif name == "audit_rbac":
                return self.handle_audit_rbac(
                    arguments.get("namespace", "default"),
                    arguments.get("type", "all"),
                    arguments.get("chunk_number", 0),
                    arguments.get("chunks_total", 5),
                    arguments.get("minimal_mode", False)
                )
            elif name == "create_role":
                return self.k8s_ops.create_role(**arguments)
            elif name == "create_cluster_role":
                return self.k8s_ops.create_cluster_role(**arguments)
            elif name == "create_service_account":
                return self.k8s_ops.create_service_account(**arguments)
            
            # Context Operations
            elif name == "list_contexts":
                return self.k8s_ops.list_contexts()
            elif name == "get_current_context":
                return self.k8s_ops.get_current_context()
            elif name == "switch_context":
                return self.k8s_ops.switch_context(**arguments)
            
            # Miscellaneous Operations
            elif name == "get_pod_events":
                return self.k8s_ops.get_pod_events(**arguments)
            elif name == "analyze_pod_logs":
                return self.k8s_ops.analyze_pod_logs(**arguments)
            
            # Namespace Management
            elif name == "set_namespace":
                return self.set_current_namespace(arguments.get("namespace", "default"))
            
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            logging.error(f"Error handling tool call {name}: {str(e)}")
            return {"error": f"Error handling tool call {name}: {str(e)}"}

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming JSON-RPC request."""
        try:
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            logger.debug(f"Handling request: method={method}, id={request_id}")
            
            # Skip heartbeat messages in response
            if method == "heartbeat":
                return None
            
            result = None
            if method == "initialize":
                result = self.handle_init(params)
            elif method == "tools/list":
                result = self.handle_tools_list()
            elif method == "tools/call":
                result = self.handle_tool_call(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            if result is None:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": "Internal error: null result"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    def run(self):
        """Run the server."""
        logger.info("Starting simplified kubectl MCP server...")
        
        while self.running:
            try:
                line = self.input_stream.readline()
                if not line:
                    break

                request = json.loads(line)
                response = self.handle_request(request)
                
                if response:
                    self.output_stream.write(json.dumps(response) + "\n")
                    self.output_stream.flush()

            except Exception as e:
                logger.error(f"Error processing request: {e}")
                continue

        self.running = False
        logger.info("Server stopped.")

def main():
    """Main entry point."""
    server = SimpleKubectlMcpServer()
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    finally:
        server.running = False

if __name__ == "__main__":
    main() 