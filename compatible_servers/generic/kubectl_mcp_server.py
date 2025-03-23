#!/usr/bin/env python3
"""
A simple MCP server for kubectl that follows the Model Context Protocol specification
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import uuid
import select
import time
from typing import Any, Dict, List, Optional, TextIO, Tuple, Union

# Set up logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("MCP_DEBUG") else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "kubectl_mcp_server.log")),
        logging.StreamHandler(sys.stderr),
    ],
)
logger = logging.getLogger("kubectl-mcp-server")

# Set default kubeconfig path
DEFAULT_KUBECONFIG = os.path.expanduser("~/.kube/config")
KUBECONFIG = os.environ.get("KUBECONFIG", DEFAULT_KUBECONFIG)

logger.info(f"Using kubeconfig from: {KUBECONFIG}")

class KubectlMcpServer:
    """
    A simple MCP server that executes kubectl commands based on natural language input.
    """

    def __init__(self):
        self.initialized = False
        self.request_id_counter = 0
        self.tools = [
            {
                "name": "get_pods",
                "description": "Get information about pods in the current namespace or all namespaces",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "The namespace to get pods from, or 'all' for all namespaces"
                        },
                        "label_selector": {
                            "type": "string",
                            "description": "Label selector to filter pods"
                        }
                    }
                }
            },
            {
                "name": "get_namespaces",
                "description": "Get available namespaces",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "describe",
                "description": "Describe a Kubernetes resource",
                "inputSchema": {
                    "type": "object",
                    "required": ["resource_type", "name"],
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
                            "description": "Namespace of the resource"
                        }
                    }
                }
            },
            {
                "name": "kubectl",
                "description": "Run a raw kubectl command",
                "inputSchema": {
                    "type": "object",
                    "required": ["command"],
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The kubectl command to run"
                        }
                    }
                }
            },
            {
                "name": "switch_namespace",
                "description": "Switch to a different namespace",
                "inputSchema": {
                    "type": "object",
                    "required": ["namespace"],
                    "properties": {
                        "namespace": {
                            "type": "string",
                            "description": "The namespace to switch to"
                        }
                    }
                }
            },
            {
                "name": "get_current_context",
                "description": "Get information about the current Kubernetes context and cluster",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "check_cluster_status",
                "description": "Check if the Kubernetes cluster is accessible and running",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        # Check cluster connection on startup
        asyncio.get_event_loop().create_task(self.check_cluster_connection())

    async def check_cluster_connection(self) -> None:
        """Check if we can connect to the Kubernetes cluster."""
        try:
            # First make sure kubectl is available
            try:
                version_cmd = ["kubectl", "version", "--client"]
                env = os.environ.copy()
                env["KUBECONFIG"] = KUBECONFIG
                
                result = subprocess.run(
                    version_cmd,
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                if result.returncode == 0:
                    logger.info(f"kubectl client version: {result.stdout.strip()}")
                else:
                    logger.warning(f"kubectl client check failed: {result.stderr}")
            except Exception as e:
                logger.error(f"Error checking kubectl client: {str(e)}")
            
            # Simple command to check if cluster is accessible
            max_retries = 3
            retry_count = 0
            connected = False
            
            while retry_count < max_retries and not connected:
                try:
                    result = await self.run_kubernetes_command(["kubectl", "cluster-info"])
                    if "Kubernetes control plane" in result and "Error" not in result:
                        logger.info("Successfully connected to Kubernetes cluster")
                        connected = True
                    else:
                        logger.warning(f"Cluster connection check returned: {result}")
                        retry_count += 1
                        await asyncio.sleep(2)  # Wait before retrying
                except Exception as e:
                    logger.error(f"Failed to connect to Kubernetes cluster (attempt {retry_count+1}): {str(e)}")
                    retry_count += 1
                    await asyncio.sleep(2)  # Wait before retrying
                    
            # Log cluster status
            if connected:
                logger.info("Kubernetes cluster is ready")
            else:
                logger.warning("Could not connect to Kubernetes cluster after multiple attempts")
                
        except Exception as e:
            logger.error(f"Unexpected error checking cluster connection: {str(e)}")

    async def run_kubernetes_command(self, cmd: List[str]) -> str:
        """Run a kubectl command and return the output."""
        logger.debug(f"Running kubectl command: {' '.join(cmd)}")
        try:
            env = os.environ.copy()
            env["KUBECONFIG"] = KUBECONFIG
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed with exit code {e.returncode}: {e.stderr}"
            logger.error(error_msg)
            
            # Provide more helpful error messages for common issues
            if "connection refused" in e.stderr.lower():
                return f"Error: Could not connect to the Kubernetes cluster. Please check if the cluster is running and accessible.\n\nDetails: {e.stderr}"
            elif "current-context is not set" in e.stderr.lower():
                return f"Error: No Kubernetes context is set. Please set a context using 'kubectl config use-context <context-name>'.\n\nDetails: {e.stderr}"
            elif "unauthorized" in e.stderr.lower():
                return f"Error: Unauthorized access to the Kubernetes API. Please check your credentials.\n\nDetails: {e.stderr}"
            else:
                return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Unexpected error running command: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    async def handle_get_pods(self, args: Dict[str, Any]) -> str:
        """Handle the get_pods tool call."""
        cmd = ["kubectl", "get", "pods"]
        
        namespace = args.get("namespace")
        if namespace:
            if namespace.lower() == "all":
                cmd.append("--all-namespaces")
            else:
                cmd.extend(["-n", namespace])
        
        label_selector = args.get("label_selector")
        if label_selector:
            cmd.extend(["-l", label_selector])
        
        return await self.run_kubernetes_command(cmd)

    async def handle_get_namespaces(self, args: Dict[str, Any]) -> str:
        """Handle the get_namespaces tool call."""
        cmd = ["kubectl", "get", "namespaces"]
        return await self.run_kubernetes_command(cmd)

    async def handle_describe(self, args: Dict[str, Any]) -> str:
        """Handle the describe tool call."""
        cmd = ["kubectl", "describe", args["resource_type"], args["name"]]
        
        namespace = args.get("namespace")
        if namespace:
            cmd.extend(["-n", namespace])
            
        return await self.run_kubernetes_command(cmd)

    async def handle_kubectl(self, args: Dict[str, Any]) -> str:
        """Handle the kubectl tool call."""
        # Split the command, respecting quoted strings
        cmd_string = args["command"].strip()
        logger.debug(f"Raw kubectl command: {cmd_string}")
        
        if not cmd_string.startswith("kubectl"):
            cmd_string = "kubectl " + cmd_string
            
        # Process command into appropriate pieces
        try:
            import shlex
            parts = shlex.split(cmd_string)
            # Ensure the first part is kubectl
            if parts[0] != "kubectl":
                return f"Error: First command must be kubectl, got: {parts[0]}"
                
            logger.debug(f"Parsed command parts: {parts}")
            return await self.run_kubernetes_command(parts)
        except Exception as e:
            error_msg = f"Error parsing kubectl command: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def handle_switch_namespace(self, args: Dict[str, Any]) -> str:
        """Handle the switch_namespace tool call."""
        namespace = args["namespace"]
        cmd = ["kubectl", "config", "set-context", "--current", "--namespace", namespace]
        result = await self.run_kubernetes_command(cmd)
        return f"Switched to namespace {namespace}. {result}"

    async def handle_get_current_context(self, args: Dict[str, Any]) -> str:
        """Handle the get_current_context tool call."""
        # Get current context
        context_cmd = ["kubectl", "config", "current-context"]
        context_result = await self.run_kubernetes_command(context_cmd)
        
        # Get cluster info
        cluster_cmd = ["kubectl", "cluster-info"]
        cluster_result = await self.run_kubernetes_command(cluster_cmd)
        
        # Get current namespace
        namespace_cmd = ["kubectl", "config", "view", "--minify", "--output", "jsonpath={..namespace}"]
        namespace_result = await self.run_kubernetes_command(namespace_cmd)
        
        if not namespace_result or "Error:" in namespace_result:
            namespace_result = "default"
        
        return f"Current context: {context_result}\nCurrent namespace: {namespace_result}\nCluster info:\n{cluster_result}"
        
    async def handle_check_cluster_status(self, args: Dict[str, Any]) -> str:
        """Handle the check_cluster_status tool call."""
        # Check if the cluster is accessible
        try:
            # Check if we can connect to the cluster
            cluster_cmd = ["kubectl", "cluster-info"]
            cluster_result = await self.run_kubernetes_command(cluster_cmd)
            
            # Check the status of nodes
            nodes_cmd = ["kubectl", "get", "nodes"]
            nodes_result = await self.run_kubernetes_command(nodes_cmd)
            
            # Check the status of core services
            core_services_cmd = ["kubectl", "get", "pods", "-n", "kube-system"]
            core_services_result = await self.run_kubernetes_command(core_services_cmd)
            
            return f"Cluster Status: Connected\n\nCluster Info:\n{cluster_result}\n\nNodes:\n{nodes_result}\n\nCore Services:\n{core_services_result}"
            
        except Exception as e:
            return f"Cluster Status: Error - Not connected\n\nError Details: {str(e)}"

    async def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Dispatch to the appropriate tool handler."""
        handlers = {
            "get_pods": self.handle_get_pods,
            "get_namespaces": self.handle_get_namespaces,
            "describe": self.handle_describe,
            "kubectl": self.handle_kubectl,
            "switch_namespace": self.handle_switch_namespace,
            "get_current_context": self.handle_get_current_context,
            "check_cluster_status": self.handle_check_cluster_status,
        }
        
        if tool_name in handlers:
            return await handlers[tool_name](args)
        else:
            return f"Error: Unknown tool '{tool_name}'"

    def get_next_request_id(self) -> str:
        """Generate a unique request ID."""
        self.request_id_counter += 1
        return str(self.request_id_counter)

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the initialize request."""
        logger.info(f"Handling initialize request: {params}")
        self.initialized = True
        
        return {
            "id": params.get("id", self.get_next_request_id()),
            "jsonrpc": "2.0",
            "result": {
                "serverInfo": {
                    "name": "kubectl-mcp-server",
                    "version": "0.1.0"
                },
                "capabilities": {
                    "tools": {}
                }
            }
        }

    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the tools/list request."""
        logger.info("Handling tools/list request")
        
        return {
            "id": params.get("id", self.get_next_request_id()),
            "jsonrpc": "2.0",
            "result": {
                "tools": self.tools
            }
        }

    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the tools/call request."""
        logger.info(f"Handling tools/call request: {params}")
        
        tool_name = params["params"]["name"]
        arguments = params["params"]["arguments"]
        
        result = await self.handle_tool_call(tool_name, arguments)
        
        return {
            "id": params.get("id", self.get_next_request_id()),
            "jsonrpc": "2.0",
            "result": {
                "result": [
                    {
                        "type": "text",
                        "text": result
                    }
                ]
            }
        }

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming JSON-RPC message."""
        method = message.get("method")
        
        if not self.initialized and method != "initialize":
            return {
                "id": message.get("id", self.get_next_request_id()),
                "jsonrpc": "2.0",
                "error": {
                    "code": -32002,
                    "message": "Server not initialized"
                }
            }
        
        handlers = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_list_tools,
            "tools/call": self.handle_call_tool,
        }
        
        if method in handlers:
            return await handlers[method](message)
        else:
            return {
                "id": message.get("id", self.get_next_request_id()),
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    async def process_stdin_line(self, line: str) -> None:
        """Process a single line from stdin and send response to stdout."""
        if not line.strip():
            logger.debug("Received empty line, ignoring")
            return
            
        logger.debug(f"Received: {line}")
        
        try:
            message = json.loads(line)
            response = await self.handle_message(message)
            
            if response:
                response_str = json.dumps(response)
                logger.debug(f"Sending: {response_str}")
                try:
                    print(response_str, flush=True)
                except (BrokenPipeError, IOError) as e:
                    logger.error(f"Failed to write to stdout: {str(e)}")
                    # Don't exit, just log the error
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {line}")
            try:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    },
                    "id": None
                }
                print(json.dumps(error_response), flush=True)
            except (BrokenPipeError, IOError) as e:
                logger.error(f"Failed to write error to stdout: {str(e)}")
        
        except Exception as e:
            logger.exception(f"Error handling message: {str(e)}")
            try:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": None
                }
                print(json.dumps(error_response), flush=True)
            except (BrokenPipeError, IOError) as e:
                logger.error(f"Failed to write error to stdout: {str(e)}")
                
    def _handle_stdin(self) -> None:
        """Read and process a line from stdin."""
        try:
            line = sys.stdin.readline()
            if not line:  # EOF
                logger.info("Received EOF, client may have disconnected")
                # Don't exit immediately on EOF, give a chance for reconnection
                asyncio.get_event_loop().call_later(5, self._check_stdin_status)
                return
                
            asyncio.create_task(self.process_stdin_line(line))
        except Exception as e:
            logger.error(f"Error reading from stdin: {str(e)}")
            # Don't exit, try to continue reading
            
    def _check_stdin_status(self) -> None:
        """Check if stdin is still available after EOF."""
        try:
            # Try to peek at stdin to see if we can read anything
            if sys.stdin.isatty() or select.select([sys.stdin], [], [], 0)[0]:
                logger.info("stdin is still available, continuing to read")
                # Re-add the reader if it was removed
                loop = asyncio.get_event_loop()
                try:
                    loop.add_reader(sys.stdin.fileno(), self._handle_stdin)
                except Exception:
                    # Reader might already be registered
                    pass
            else:
                logger.info("stdin appears to be closed, but keeping server running")
        except Exception as e:
            logger.error(f"Error checking stdin status: {str(e)}")

    async def run(self) -> None:
        """Run the MCP server, processing commands from stdin and responding to stdout."""
        logger.info("Starting kubectl MCP server")
        
        loop = asyncio.get_event_loop()
        
        # Set up non-blocking stdin reading
        loop.add_reader(sys.stdin.fileno(), self._handle_stdin)
        
        # Set up a heartbeat to keep the connection alive
        heartbeat_task = asyncio.create_task(self._send_heartbeat())
        
        try:
            # Just wait indefinitely until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down kubectl MCP server")
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            loop.remove_reader(sys.stdin.fileno())

    async def _send_heartbeat(self) -> None:
        """Send a heartbeat every 30 seconds to keep the connection alive."""
        while True:
            try:
                await asyncio.sleep(30)
                # Log a heartbeat but don't send to stdout to avoid interfering with MCP protocol
                logger.debug("Heartbeat: MCP server is alive")
            except asyncio.CancelledError:
                logger.debug("Heartbeat task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat: {str(e)}")

def main() -> None:
    """Main entry point."""
    logger.info(f"Starting kubectl MCP server, Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    
    # Check if we can access kubectl before starting
    try:
        result = subprocess.run(
            ["kubectl", "version", "--client"],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        if result.returncode == 0:
            logger.info(f"kubectl client check passed: {result.stdout.strip()}")
        else:
            logger.warning(f"kubectl client check warning: {result.stderr}")
    except Exception as e:
        logger.warning(f"kubectl availability check failed: {str(e)}")
    
    # Create server instance
    server = KubectlMcpServer()
    
    # Set up signal handlers for graceful shutdown
    try:
        import signal
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down gracefully")
            asyncio.get_event_loop().stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except Exception as e:
        logger.warning(f"Failed to set up signal handlers: {str(e)}")
    
    # Run the server with retry logic
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Starting server (attempt {retry_count + 1}/{max_retries})")
            asyncio.run(server.run())
            break  # If we get here without an exception, break the loop
        except KeyboardInterrupt:
            logger.info("Interrupted by user, shutting down")
            break
        except Exception as e:
            retry_count += 1
            logger.exception(f"Unhandled error (attempt {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                logger.info(f"Retrying in 3 seconds...")
                time.sleep(3)
            else:
                logger.error("Maximum retry attempts reached, shutting down")
                return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 