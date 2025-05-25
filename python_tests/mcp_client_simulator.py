#!/usr/bin/env python3
"""
MCP Client Simulator for testing the kubectl-mcp-tool.

This module provides a client that can communicate with the MCP server
through stdio or HTTP transport, simulating an MCP client for testing purposes.
"""

import os
import json
import uuid
import time
import logging
import requests
import subprocess
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Check if we're running in mock mode
MOCK_MODE = os.environ.get("MCP_TEST_MOCK_MODE", "0") == "1"

class MCPClientSimulator:
    """
    Simulates an MCP client for testing purposes.
    Supports both HTTP and stdio transports.
    """
    
    def __init__(self, server_url: Optional[str] = None, 
                 stdio_cmd: Optional[List[str]] = None,
                 timeout: int = 30):
        """
        Initialize the MCP client simulator.
        
        Args:
            server_url: URL for HTTP transport (e.g., "http://localhost:8080")
            stdio_cmd: Command to start the MCP server for stdio transport
            timeout: Request timeout in seconds
        """
        self.server_url = server_url
        self.stdio_cmd = stdio_cmd
        self.timeout = timeout
        self.server_process = None
        
        if not server_url and not stdio_cmd and not MOCK_MODE:
            raise ValueError("Either server_url or stdio_cmd must be provided")
        
        # Start the server process if using stdio
        if stdio_cmd and not MOCK_MODE:
            self._start_server_process()
    
    def _start_server_process(self):
        """Start the server process for stdio transport."""
        import copy
        import sys
        import os
        import re

        # Always use sys.executable and -I for full isolation
        if self.stdio_cmd and self.stdio_cmd[0] == "python":
            self.stdio_cmd = [sys.executable, "-I"] + self.stdio_cmd[1:]
        
        # Handle the PYTHONPATH for module import
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        logger.info(f"Project root: {project_root}")
        
        logger.info(f"Starting MCP server process: {' '.join(self.stdio_cmd)}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Sanitize environment to avoid sys.modules import collision bug
        env = copy.deepcopy(os.environ)
        # Add project root to PYTHONPATH for the subprocess
        env["PYTHONPATH"] = project_root
        env["PYTHONNOUSERSITE"] = "1"
        
        logger.info(f"Environment: PYTHONPATH={env.get('PYTHONPATH')}, PYTHONNOUSERSITE={env.get('PYTHONNOUSERSITE')}")

        self.server_process = subprocess.Popen(
            self.stdio_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            env=env
        )
        
        # Wait a moment for the server to initialize
        import time
        time.sleep(1)
        
        if self.server_process.poll() is not None:
            stdout = self.server_process.stdout.read()
            stderr = self.server_process.stderr.read()
            msg = (
                f"Failed to start MCP server process!\n"
                f"Command: {' '.join(self.stdio_cmd)}\n"
                f"CWD: {os.getcwd()}\n"
                f"PYTHONPATH: {env.get('PYTHONPATH')}\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}\n"
            )
            raise RuntimeError(msg)
    
    def _send_stdio_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request through stdio and read response.
        
        Args:
            request: The request to send
            
        Returns:
            The parsed response
        """
        if not self.server_process:
            raise RuntimeError("Server process not started")
        
        # Verify the process is still running
        if self.server_process.poll() is not None:
            stderr = self.server_process.stderr.read()
            raise RuntimeError(f"MCP server process has terminated: {stderr}")
        
        # Send the request
        request_json = json.dumps(request) + "\n"
        self.server_process.stdin.write(request_json)
        self.server_process.stdin.flush()
        
        # Read the response
        response_line = self.server_process.stdout.readline()
        if not response_line:
            stderr = self.server_process.stderr.read()
            raise RuntimeError(f"No response from MCP server: {stderr}")
        
        return json.loads(response_line)
    
    def _send_http_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request through HTTP and handle response.
        
        Args:
            request: The request to send
            
        Returns:
            The parsed response
        """
        if not self.server_url:
            raise RuntimeError("Server URL not provided for HTTP transport")
        
        response = requests.post(
            self.server_url,
            json=request,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a request using the configured transport.
        
        Args:
            request: The request to send
            
        Returns:
            The parsed response
        """
        if MOCK_MODE:
            # In mock mode, generate a mock response
            return self._generate_mock_response(request)
        
        # Ensure the request has an id
        if "id" not in request:
            request["id"] = str(uuid.uuid4())
        
        # Use the appropriate transport
        if self.server_url:
            return self._send_http_request(request)
        else:
            return self._send_stdio_request(request)
    
    def _generate_mock_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a mock response for testing without a real MCP server.
        
        Args:
            request: The original request
            
        Returns:
            A mock response
        """
        logger.info(f"[MOCK] Generating mock response for request: {request.get('type')}")
        
        # Basic response structure
        response = {
            "id": request.get("id", str(uuid.uuid4())),
            "type": "tool_call",
            "result": {}
        }
        
        # Handle different request types
        if request.get("type") == "list_tools":
            response["type"] = "tools"
            response["result"] = {
                "tools": [
                    {"name": "get_pods", "description": "Get pods in a namespace"},
                    {"name": "get_namespaces", "description": "List all namespaces"},
                    {"name": "get_current_namespace", "description": "Get the current namespace"},
                    {"name": "set_namespace", "description": "Set the current namespace"},
                    {"name": "create_resource", "description": "Create a Kubernetes resource"},
                    {"name": "delete_resource", "description": "Delete a Kubernetes resource"},
                    {"name": "scale_deployment", "description": "Scale a deployment"},
                    {"name": "get_deployments", "description": "Get deployments in a namespace"},
                    {"name": "get_events", "description": "Get events in a namespace"},
                    {"name": "get_resource_usage", "description": "Get resource usage statistics"},
                    {"name": "check_pod_health", "description": "Check pod health status"},
                    {"name": "process_natural_language", "description": "Process natural language query"},
                    {"name": "audit_pod_security", "description": "Audit pod security settings"},
                    {"name": "validate_resource", "description": "Validate a Kubernetes resource"},
                    {"name": "explain_resource", "description": "Explain a Kubernetes resource"},
                    {"name": "get_api_resources", "description": "Get API resources"}
                ]
            }
        elif request.get("type") == "tool_call":
            tool_name = request.get("name", "")
            args = request.get("args", {})
            
            # Mock responses for different tools
            if tool_name == "get_pods":
                namespace = args.get("namespace", "default")
                pod_name = args.get("name", "")
                
                # If a specific pod is requested, return only that pod
                if pod_name:
                    response["result"] = {
                        "items": [
                            {
                                "metadata": {
                                    "name": pod_name,
                                    "namespace": namespace
                                },
                                "status": {
                                    "phase": "Running",
                                    "conditions": [
                                        {
                                            "type": "Ready",
                                            "status": "True"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                else:
                    response["result"] = {
                        "items": [
                            {
                                "metadata": {
                                    "name": "mock-pod-1",
                                    "namespace": namespace
                                },
                                "status": {
                                    "phase": "Running",
                                    "conditions": [
                                        {
                                            "type": "Ready",
                                            "status": "True"
                                        }
                                    ]
                                }
                            },
                            {
                                "metadata": {
                                    "name": "mock-pod-2",
                                    "namespace": namespace
                                },
                                "status": {
                                    "phase": "Running",
                                    "conditions": [
                                        {
                                            "type": "Ready",
                                            "status": "True"
                                        }
                                    ]
                                }
                            }
                        ]
                    }
            elif tool_name == "get_namespaces":
                response["result"] = {
                    "items": [
                        {
                            "metadata": {
                                "name": "default"
                            },
                            "status": {
                                "phase": "Active"
                            }
                        },
                        {
                            "metadata": {
                                "name": "kube-system"
                            },
                            "status": {
                                "phase": "Active"
                            }
                        }
                    ]
                }
            elif tool_name == "get_current_namespace":
                # Get the stored namespace from the client's state
                current_namespace = self.__dict__.get("_current_namespace", "default")
                response["result"] = {
                    "namespace": current_namespace
                }
            elif tool_name == "set_namespace":
                namespace = args.get("namespace", "default")
                # Store the current namespace in the client's state
                self.__dict__["_current_namespace"] = namespace
                response["result"] = {
                    "success": True,
                    "namespace": namespace
                }
            elif tool_name == "create_resource":
                response["result"] = {
                    "success": True,
                    "resource": {
                        "kind": "Pod",
                        "name": "mock-resource",
                        "namespace": "default"
                    }
                }
            elif tool_name == "get_deployments":
                namespace = args.get("namespace", "default")
                name = args.get("name", "")
                
                if name:
                    response["result"] = {
                        "items": [
                            {
                                "metadata": {
                                    "name": name,
                                    "namespace": namespace
                                },
                                "spec": {
                                    "replicas": 2
                                },
                                "status": {
                                    "readyReplicas": 2,
                                    "availableReplicas": 2
                                }
                            }
                        ]
                    }
                else:
                    response["result"] = {
                        "items": [
                            {
                                "metadata": {
                                    "name": "mock-deployment-1",
                                    "namespace": namespace
                                },
                                "spec": {
                                    "replicas": 2
                                },
                                "status": {
                                    "readyReplicas": 2,
                                    "availableReplicas": 2
                                }
                            }
                        ]
                    }
            elif tool_name == "scale_deployment":
                response["result"] = {
                    "success": True,
                    "deployment": args.get("deployment", "mock-deployment"),
                    "namespace": args.get("namespace", "default"),
                    "replicas": args.get("replicas", 1)
                }
            elif tool_name == "get_events":
                response["result"] = {
                    "items": [
                        {"type": "Normal", "reason": "Created", "message": "Created container"},
                        {"type": "Normal", "reason": "Started", "message": "Started container"}
                    ]
                }
            elif tool_name == "get_resource_usage":
                response["result"] = {
                    "items": [
                        {"name": "mock-pod-1", "cpu": "10m", "memory": "20Mi"},
                        {"name": "mock-pod-2", "cpu": "15m", "memory": "30Mi"}
                    ]
                }
            elif tool_name == "get_node_health":
                response["result"] = {
                    "nodes": [
                        {
                            "name": "mock-node-1", 
                            "status": "Ready", 
                            "cpu": "20%", 
                            "memory": "30%",
                            "conditions": [
                                {"type": "Ready", "status": "True", "message": "kubelet is posting ready status"},
                                {"type": "DiskPressure", "status": "False", "message": "no disk pressure"}
                            ]
                        }
                    ],
                    "cluster_status": "Healthy"
                }
            elif tool_name == "check_pod_health":
                response["result"] = {
                    "status": "Healthy",
                    "pod": args.get("name", "mock-pod"),
                    "namespace": args.get("namespace", "default"),
                    "readiness": {
                        "status": "Passed",
                        "message": "Readiness probe succeeded"
                    },
                    "liveness": {
                        "status": "Passed",
                        "message": "Liveness probe succeeded"
                    },
                    "probes": {
                        "readiness": {
                            "configured": True,
                            "type": "httpGet"
                        },
                        "liveness": {
                            "configured": True,
                            "type": "httpGet"
                        },
                        "startup": {
                            "configured": False
                        }
                    },
                    "container_statuses": [
                        {
                            "name": "main-container",
                            "ready": True,
                            "started": True,
                            "restartCount": 0
                        }
                    ]
                }
            elif tool_name == "process_natural_language":
                query = args.get("query", "").lower()
                intent = "list pods"
                k8s_cmd = "kubectl get pods"
                
                # Track the current namespace context for the client
                # In a real client, this would be part of the state tracking
                current_namespace = self.__dict__.get("_current_namespace", "default")
                
                if "deployment" in query or "replicas" in query:
                    intent = "list deployments with condition"
                    k8s_cmd = "kubectl get deployments --field-selector spec.replicas>2"
                
                # Check if there's an explicit namespace mention
                if "namespace" in query:
                    if "kube-system" in query:
                        intent += " in kube-system"
                        k8s_cmd += " -n kube-system"
                # Otherwise use the current namespace context
                elif current_namespace != "default":
                    intent += f" in {current_namespace}"
                    k8s_cmd += f" -n {current_namespace}"
                
                if "explode" in query or "error" in query:
                    response["result"] = {
                        "intent": "invalid request",
                        "kubernetes_command": "N/A",
                        "response": "I cannot perform that operation",
                        "error": "Invalid or unsupported request",
                        "message": "Please provide a valid Kubernetes query"
                    }
                else:
                    response["result"] = {
                        "intent": intent,
                        "kubernetes_command": k8s_cmd,
                        "response": f"Mock response for query: {query} (context: namespace={current_namespace})",
                        "is_mock": True
                    }
            elif tool_name == "validate_resource":
                # Check if we should simulate an invalid resource
                if "invalid" in args.get("filepath", "").lower():
                    response["result"] = {
                        "valid": False,
                        "errors": [
                            "Container in pod 'invalid-pod' is missing required field 'name'"
                        ]
                    }
                else:
                    response["result"] = {
                        "valid": True,
                        "errors": []
                    }
            elif tool_name == "audit_pod_security":
                response["result"] = {
                    "findings": [
                        {"severity": "low", "message": "Pod uses the 'default' service account"}
                    ],
                    "pod": args.get("name", "mock-pod"),
                    "namespace": args.get("namespace", "default"),
                    "securityContext": {
                        "configured": True
                    },
                    "privileged": False,
                    "hostNetwork": False,
                    "hostPID": False,
                    "hostIPC": False
                }
            elif tool_name == "validate_probes":
                response["result"] = {
                    "readiness": {"status": "configured"},
                    "liveness": {"status": "configured"},
                    "issues": []
                }
            elif tool_name == "get_diagnostics":
                response["result"] = {
                    "cluster_info": {"name": "mock-cluster"},
                    "version": {"gitVersion": "v1.24.0"},
                    "nodes": [{"name": "mock-node", "status": "Ready"}],
                    "system_pods": [{"name": "mock-system-pod", "namespace": "kube-system"}]
                }
            elif tool_name == "explain_resource":
                resource = args.get("resource", "pod")
                response["result"] = {
                    "explanation": f"Mock explanation for {resource}. This would contain the structure and fields of the resource.",
                    "resource": resource,
                    "apiVersion": "v1" if resource in ["pod", "service"] else "apps/v1"
                }
            elif tool_name == "get_api_resources":
                response["result"] = {
                    "resources": [
                        {"name": "pods", "shortNames": ["po"], "kind": "Pod", "namespaced": True},
                        {"name": "services", "shortNames": ["svc"], "kind": "Service", "namespaced": True},
                        {"name": "deployments", "shortNames": ["deploy"], "kind": "Deployment", "namespaced": True},
                        {"name": "namespaces", "shortNames": ["ns"], "kind": "Namespace", "namespaced": False}
                    ],
                    "apiVersion": "v1"
                }
            elif tool_name == "can_i":
                response["result"] = {
                    "allowed": True
                }
            elif tool_name == "analyze_resource_issues":
                response["result"] = {
                    "issues": [
                        {"type": "warning", "description": "Mock issue for testing"}
                    ]
                }
            else:
                # Generic success response for other tools
                response["result"] = {
                    "success": True,
                    "message": f"Mock response for tool: {tool_name}"
                }
        
        return response
    
    def list_tools(self) -> Dict[str, Any]:
        """
        List available tools from the MCP server.
        
        Returns:
            Response containing list of available tools
        """
        request = {
            "type": "list_tools"
        }
        return self.send_request(request)
    
    def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific tool on the MCP server.
        
        Args:
            tool_name: The name of the tool to call
            args: Arguments for the tool
            
        Returns:
            The tool call response
        """
        request = {
            "type": "tool_call",
            "name": tool_name,
            "args": args
        }
        return self.send_request(request)
    
    def close(self):
        """Clean up resources."""
        if self.server_process:
            logger.info("Stopping MCP server process")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server process did not terminate gracefully, forcing")
                self.server_process.kill()
            
            self.server_process = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 