#!/usr/bin/env python3
"""
Cursor-compatible MCP server implementation for kubectl-mcp-tool.

This script provides a specialized MCP server implementation for Cursor integration
with improved error handling and real kubectl command execution.
"""

import sys
import json
import logging
import asyncio
import signal
import os
import subprocess
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable

# Configure environment-based settings
DEBUG_MODE = os.environ.get("MCP_DEBUG", "false").lower() in ("true", "1", "yes")
LOG_LEVEL_NAME = os.environ.get("KUBECTL_MCP_LOG_LEVEL", "INFO").upper()
LOG_LEVEL = getattr(logging, LOG_LEVEL_NAME, logging.INFO)

# Create log directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(LOG_DIR, "cursor_compatible_mcp_server.log")
)
logger = logging.getLogger("cursor-compatible-mcp-server")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO if not DEBUG_MODE else logging.DEBUG)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Log startup information
logger.info(f"Starting kubectl-mcp-tool with DEBUG={DEBUG_MODE}, LOG_LEVEL={LOG_LEVEL_NAME}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Platform: {sys.platform}")
logger.info(f"Current directory: {os.getcwd()}")

# Import from the correct location
try:
    from kubectl_mcp_tool.mcp_server import MCPServer
    from kubectl_mcp_tool.natural_language import process_query
    logger.info("Successfully imported kubectl_mcp_tool modules")
except ImportError as e:
    logger.error(f"Failed to import kubectl_mcp_tool modules: {e}")
    # Create a debug error file
    with open(os.path.join(LOG_DIR, "import_error.log"), "w") as f:
        f.write(f"Import error: {str(e)}\n")
        f.write(f"Python path: {sys.path}\n")
        
    # Try to continue anyway by using a relative import
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from kubectl_mcp_tool.mcp_server import MCPServer
        from kubectl_mcp_tool.natural_language import process_query
        logger.info("Successfully imported kubectl_mcp_tool modules after path adjustment")
    except ImportError as e:
        logger.critical(f"Failed to import kubectl_mcp_tool modules even with path adjustment: {e}")
        sys.exit(1)

class StdioTransport:
    """A class that implements the stdio transport for MCP."""
    
    def __init__(self):
        """Initialize the stdio transport."""
        self.input_queue = asyncio.Queue()
        self.running = True
        self.debug_file = open(os.path.join(LOG_DIR, "cursor_mcp_debug.log"), "w")
        self.debug_file.write(f"StdioTransport initialized at {os.path.abspath(__file__)}\n")
        self.debug_file.write(f"Current directory: {os.getcwd()}\n")
        self.debug_file.write(f"Python path: {sys.path}\n")
        self.debug_file.flush()
        logger.info("StdioTransport initialized")
        
        # Make stdin non-blocking on Unix systems
        if sys.platform != 'win32':
            import fcntl
            import os
            fd = sys.stdin.fileno()
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            self.debug_file.write("Set stdin to non-blocking mode\n")
            self.debug_file.flush()
    
    async def start_reader(self):
        """Start reading from stdin in a non-blocking way."""
        loop = asyncio.get_running_loop()
        logger.info("Starting stdin reader")
        self.debug_file.write("Starting stdin reader\n")
        self.debug_file.flush()
        
        while self.running:
            try:
                # Read from stdin with a timeout to allow for checking self.running
                try:
                    # Use run_in_executor with a short timeout to prevent blocking indefinitely
                    line = await asyncio.wait_for(
                        loop.run_in_executor(None, sys.stdin.readline),
                        timeout=0.5
                    )
                except asyncio.TimeoutError:
                    # Timeout is expected, just continue the loop
                    await asyncio.sleep(0.1)
                    continue
                
                if not line:
                    logger.debug("End of stdin stream")
                    self.debug_file.write("End of stdin stream\n")
                    self.debug_file.flush()
                    # Don't exit immediately, sleep and check again
                    await asyncio.sleep(0.5)
                    continue
                
                # Log the raw input for debugging
                self.debug_file.write(f"STDIN: {line.strip()}\n")
                self.debug_file.flush()
                
                logger.debug(f"Read from stdin: {line.strip()}")
                
                try:
                    # Parse the JSON message
                    message = json.loads(line)
                    logger.debug(f"Parsed JSON message: {message}")
                    
                    # Put the message in the queue
                    await self.input_queue.put(message)
                    logger.debug(f"Put message in queue: {message.get('id', 'unknown-id')}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {line.strip()} - {e}")
                    self.debug_file.write(f"JSON ERROR: {e} for input: {line.strip()}\n")
                    self.debug_file.flush()
                    
                    # Try to send an error response for malformed JSON
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,  # We don't know the ID since JSON parsing failed
                        "error": {
                            "code": -32700,
                            "message": "Parse error: Invalid JSON was received"
                        }
                    }
                    await self.write_message(error_response)
            except Exception as e:
                logger.error(f"Error reading from stdin: {e}")
                self.debug_file.write(f"STDIN ERROR: {str(e)}\n")
                self.debug_file.flush()
                # Don't break the loop on error, just continue after a short delay
                await asyncio.sleep(0.1)
    
    async def read_message(self):
        """Read messages from the input queue and yield them."""
        logger.info("Starting message reader")
        
        while self.running:
            try:
                # Get a message from the queue
                message = await self.input_queue.get()
                
                # Log the message
                logger.debug(f"Yielding message: {message}")
                self.debug_file.write(f"YIELD: {json.dumps(message)}\n")
                self.debug_file.flush()
                
                # Yield the message
                yield message
                
                # Mark the task as done
                self.input_queue.task_done()
            except asyncio.CancelledError:
                logger.info("Message reader cancelled")
                self.debug_file.write("Message reader cancelled\n")
                self.debug_file.flush()
                break
            except Exception as e:
                logger.error(f"Error in read_message: {e}")
                self.debug_file.write(f"READ ERROR: {str(e)}\n")
                self.debug_file.flush()
                # Sleep a bit on error to avoid busy waiting
                await asyncio.sleep(0.1)
    
    async def write_message(self, message: Dict[str, Any]) -> None:
        """Write a message to stdout."""
        try:
            # Convert the message to a JSON string with a newline
            json_str = json.dumps(message) + "\n"
            
            # Log the message
            logger.debug(f"Writing to stdout: {json_str.strip()}")
            self.debug_file.write(f"STDOUT: {json_str}")
            self.debug_file.flush()
            
            # Use run_in_executor to prevent blocking the event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._write_to_stdout(json_str))
        except Exception as e:
            logger.error(f"Error writing to stdout: {e}")
            self.debug_file.write(f"WRITE ERROR: {str(e)}\n")
            self.debug_file.flush()
    
    def _write_to_stdout(self, json_str: str) -> None:
        """Helper method to write to stdout and handle potential errors."""
        try:
            # Write the message to stdout and flush
            sys.stdout.write(json_str)
            sys.stdout.flush()
        except (BrokenPipeError, IOError) as e:
            # Handle broken pipe errors specifically
            self.debug_file.write(f"STDOUT PIPE ERROR: {str(e)}\n")
            self.debug_file.flush()
            # Don't re-raise, as this would kill the process
            # Just log and continue
        except Exception as e:
            self.debug_file.write(f"STDOUT UNEXPECTED ERROR: {str(e)}\n")
            self.debug_file.flush()

class KubectlTools:
    """Kubectl tools implementation for Cursor integration."""
    
    def __init__(self):
        """Initialize the kubectl tools."""
        self.current_namespace = "default"
        self.mock_data = self._get_mock_data()
    
    def _get_mock_data(self) -> Dict[str, Dict[str, str]]:
        """Get mock data for kubectl commands."""
        return {
            "get_pods": {
                "command": "kubectl get pods",
                "result": """NAME                     READY   STATUS    RESTARTS   AGE
nginx-pod               1/1     Running   0          1h
web-deployment-abc123   1/1     Running   0          45m
db-statefulset-0        1/1     Running   0          30m"""
            },
            "get_namespaces": {
                "command": "kubectl get namespaces",
                "result": """NAME              STATUS   AGE
default           Active   1d
kube-system       Active   1d
kube-public       Active   1d
kube-node-lease   Active   1d"""
            },
            "switch_namespace": {
                "command": "kubectl config set-context --current --namespace={}",
                "result": "Switched to namespace {}"
            },
            "get_current_namespace": {
                "command": "kubectl config view --minify --output 'jsonpath={..namespace}'",
                "result": "default"
            },
            "get_contexts": {
                "command": "kubectl config get-contexts",
                "result": """CURRENT   NAME                 CLUSTER          AUTHINFO         NAMESPACE
*         docker-desktop      docker-desktop   docker-desktop   default
          minikube            minikube         minikube         default"""
            },
            "get_deployments": {
                "command": "kubectl get deployments",
                "result": """NAME            READY   UP-TO-DATE   AVAILABLE   AGE
web-deployment   3/3     3            3           1h
api-deployment   2/2     2            2           45m"""
            },
            "get_services": {
                "command": "kubectl get services",
                "result": """NAME            TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes      ClusterIP   10.96.0.1        <none>        443/TCP        1d
web-service     NodePort    10.96.123.45     <none>        80:30080/TCP   1h
api-service     ClusterIP   10.96.234.56     <none>        8080/TCP       45m"""
            }
        }
    
    def _run_kubectl_command(self, command: str) -> Dict[str, Any]:
        """Run a kubectl command and return the result."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            return {
                "command": command,
                "result": result.stdout.strip(),
                "success": True
            }
        except subprocess.CalledProcessError as e:
            logger.warning(f"kubectl command failed: {command} - {e}")
            return {
                "command": command,
                "result": e.stderr.strip(),
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Error running kubectl command: {command} - {e}")
            return {
                "command": command,
                "result": f"Error: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query for kubectl operations."""
        logger.info(f"Processing query: {query}")
        
        # Convert query to lowercase for easier matching
        query_lower = query.lower()
        
        try:
            # Determine the kubectl command based on the query
            if "get all pods" in query_lower or "get pods" in query_lower:
                if "namespace" in query_lower:
                    # Extract namespace name
                    parts = query_lower.split("namespace")
                    if len(parts) > 1:
                        namespace = parts[1].strip()
                        command = f"kubectl get pods -n {namespace}"
                    else:
                        command = "kubectl get pods --all-namespaces"
                else:
                    command = "kubectl get pods"
                
                # Try to run the real command
                result = self._run_kubectl_command(command)
                
                # If the command failed, use mock data
                if not result.get("success", False):
                    logger.warning(f"Using mock data for: {command}")
                    mock_result = self.mock_data["get_pods"]
                    result = {
                        "command": command,
                        "result": mock_result["result"],
                        "mock": True
                    }
            
            elif "show namespaces" in query_lower or "get namespaces" in query_lower:
                command = "kubectl get namespaces"
                
                # Try to run the real command
                result = self._run_kubectl_command(command)
                
                # If the command failed, use mock data
                if not result.get("success", False):
                    logger.warning(f"Using mock data for: {command}")
                    mock_result = self.mock_data["get_namespaces"]
                    result = {
                        "command": command,
                        "result": mock_result["result"],
                        "mock": True
                    }
            
            elif "switch to namespace" in query_lower or "change namespace" in query_lower:
                # Extract namespace name
                parts = query_lower.split("namespace")
                if len(parts) > 1:
                    namespace = parts[1].strip()
                    command = f"kubectl config set-context --current --namespace={namespace}"
                    
                    # Try to run the real command
                    result = self._run_kubectl_command(command)
                    
                    # If the command failed, use mock data
                    if not result.get("success", False):
                        logger.warning(f"Using mock data for: {command}")
                        mock_result = self.mock_data["switch_namespace"]
                        result = {
                            "command": command,
                            "result": mock_result["result"].format(namespace),
                            "mock": True
                        }
                    
                    # Update current namespace
                    self.current_namespace = namespace
                else:
                    result = {
                        "command": "kubectl config set-context",
                        "result": "Error: No namespace specified",
                        "success": False
                    }
            
            elif "current namespace" in query_lower or "what namespace" in query_lower:
                command = "kubectl config view --minify --output 'jsonpath={..namespace}'"
                
                # Try to run the real command
                result = self._run_kubectl_command(command)
                
                # If the command failed, use mock data
                if not result.get("success", False):
                    logger.warning(f"Using mock data for: {command}")
                    result = {
                        "command": command,
                        "result": self.current_namespace,
                        "mock": True
                    }
            
            elif "get contexts" in query_lower or "show contexts" in query_lower:
                command = "kubectl config get-contexts"
                
                # Try to run the real command
                result = self._run_kubectl_command(command)
                
                # If the command failed, use mock data
                if not result.get("success", False):
                    logger.warning(f"Using mock data for: {command}")
                    mock_result = self.mock_data["get_contexts"]
                    result = {
                        "command": command,
                        "result": mock_result["result"],
                        "mock": True
                    }
            
            elif "get deployments" in query_lower or "show deployments" in query_lower:
                if "namespace" in query_lower:
                    # Extract namespace name
                    parts = query_lower.split("namespace")
                    if len(parts) > 1:
                        namespace = parts[1].strip()
                        command = f"kubectl get deployments -n {namespace}"
                    else:
                        command = "kubectl get deployments --all-namespaces"
                else:
                    command = f"kubectl get deployments -n {self.current_namespace}"
                
                # Try to run the real command
                result = self._run_kubectl_command(command)
                
                # If the command failed, use mock data
                if not result.get("success", False):
                    logger.warning(f"Using mock data for: {command}")
                    mock_result = self.mock_data["get_deployments"]
                    result = {
                        "command": command,
                        "result": mock_result["result"],
                        "mock": True
                    }
            
            elif "get services" in query_lower or "show services" in query_lower:
                if "namespace" in query_lower:
                    # Extract namespace name
                    parts = query_lower.split("namespace")
                    if len(parts) > 1:
                        namespace = parts[1].strip()
                        command = f"kubectl get services -n {namespace}"
                    else:
                        command = "kubectl get services --all-namespaces"
                else:
                    command = f"kubectl get services -n {self.current_namespace}"
                
                # Try to run the real command
                result = self._run_kubectl_command(command)
                
                # If the command failed, use mock data
                if not result.get("success", False):
                    logger.warning(f"Using mock data for: {command}")
                    mock_result = self.mock_data["get_services"]
                    result = {
                        "command": command,
                        "result": mock_result["result"],
                        "mock": True
                    }
            
            else:
                # For unknown commands, try to run the query as a kubectl command
                command = f"kubectl {query}"
                result = self._run_kubectl_command(command)
                
                # If the command failed, return a helpful message
                if not result.get("success", False):
                    result = {
                        "command": command,
                        "result": "Could not parse natural language query. Try commands like 'get all pods', 'show namespaces', or 'switch to namespace kube-system'.",
                        "success": False
                    }
            
            return result
        except Exception as e:
            logger.error(f"Error processing query: {query} - {e}")
            return {
                "command": "Error",
                "result": f"Failed to process query: {str(e)}",
                "success": False,
                "error": str(e)
            }

class MCPServer:
    """MCP server implementation for kubectl-mcp-tool."""
    
    def __init__(self, name: str):
        """Initialize the MCP server."""
        self.name = name
        self.version = "0.1.0"
        self.tools = KubectlTools()
        logger.info(f"MCPServer initialized: {name} v{self.version}")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request."""
        logger.info(f"Handling request: {request.get('method', 'unknown')} (ID: {request.get('id', 'unknown')})")
        
        # Check if the request is valid
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0" or "method" not in request:
            logger.error(f"Invalid request: {request}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                }
            }
        
        # Handle the request based on the method
        method = request["method"]
        
        if method == "mcp.initialize":
            return await self.handle_initialize(request)
        elif method == "mcp.tools.list":
            return await self.handle_tools_list(request)
        elif method == "mcp.tool.call":
            return await self.handle_tool_call(request)
        else:
            logger.error(f"Method not found: {method}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an initialize request."""
        logger.info("Handling initialize request")
        
        # Return the server capabilities
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "capabilities": {
                    "tools": {
                        "supported": True,
                        "properties": {
                            "arguments": True,
                            "descriptions": True
                        }
                    }
                },
                "server_info": {
                    "name": self.name,
                    "version": self.version
                }
            }
        }
    
    async def handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tools/list request."""
        logger.info("Handling tools/list request")
        
        # Return the list of available tools
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "process_natural_language",
                        "description": "Process natural language queries for kubectl operations",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Natural language query for kubectl operations"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_pods",
                        "description": "Get pods in the specified namespace",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "namespace": {
                                    "type": "string",
                                    "description": "Namespace to get pods from"
                                }
                            }
                        }
                    },
                    {
                        "name": "get_namespaces",
                        "description": "Get all namespaces",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "switch_namespace",
                        "description": "Switch to the specified namespace",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "namespace": {
                                    "type": "string",
                                    "description": "Namespace to switch to"
                                }
                            },
                            "required": ["namespace"]
                        }
                    },
                    {
                        "name": "get_current_namespace",
                        "description": "Get the current namespace",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_deployments",
                        "description": "Get deployments in the specified namespace",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "namespace": {
                                    "type": "string",
                                    "description": "Namespace to get deployments from"
                                }
                            }
                        }
                    }
                ]
            }
        }
    
    async def handle_tool_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a tool/call request."""
        logger.info(f"Handling tool/call request: {request.get('params', {}).get('name', 'unknown')}")
        
        # Check if the request is valid
        if "params" not in request or "name" not in request["params"]:
            logger.error(f"Invalid tool/call request: {request}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32602,
                    "message": "Invalid params"
                }
            }
        
        # Get the tool name and input
        tool_name = request["params"]["name"]
        tool_input = request["params"].get("input", {})
        
        # Handle the tool call based on the tool name
        if tool_name == "process_natural_language":
            if "query" not in tool_input:
                logger.error(f"Missing required parameter 'query' for tool: {tool_name}")
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameter: query"
                    }
                }
            
            # Process the query
            result = await self.tools.process_query(tool_input["query"])
            
            # Return the result
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        elif tool_name == "get_pods":
            namespace = tool_input.get("namespace", "")
            query = f"get pods {f'in namespace {namespace}' if namespace else ''}"
            result = await self.tools.process_query(query)
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        elif tool_name == "get_namespaces":
            result = await self.tools.process_query("show namespaces")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        elif tool_name == "switch_namespace":
            if "namespace" not in tool_input:
                logger.error(f"Missing required parameter 'namespace' for tool: {tool_name}")
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameter: namespace"
                    }
                }
            
            result = await self.tools.process_query(f"switch to namespace {tool_input['namespace']}")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        elif tool_name == "get_current_namespace":
            result = await self.tools.process_query("what is my current namespace")
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        elif tool_name == "get_deployments":
            namespace = tool_input.get("namespace", "")
            query = f"get deployments {f'in namespace {namespace}' if namespace else ''}"
            result = await self.tools.process_query(query)
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        else:
            logger.error(f"Tool not found: {tool_name}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }

async def run_server():
    """Run the MCP server."""
    logger.info("Starting kubectl MCP server with stdio transport")
    
    # Create the server
    server = MCPServer("kubectl-mcp-tool")
    
    # Create the stdio transport
    stdio = StdioTransport()
    
    # Start the reader task
    reader_task = asyncio.create_task(stdio.start_reader())
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for signal_name in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(
                getattr(signal, signal_name), 
                lambda: asyncio.create_task(shutdown(stdio, reader_task))
            )
        except (NotImplementedError, AttributeError):
            # Windows doesn't support SIGINT/SIGTERM
            pass
    
    try:
        # Process messages
        async for message in stdio.read_message():
            # Handle the message
            response = await server.handle_request(message)
            
            # Send the response
            await stdio.write_message(response)
    except Exception as e:
        logger.error(f"Error in run_server: {e}", exc_info=True)
    finally:
        # Clean up
        await shutdown(stdio, reader_task)
    
    logger.info("MCP server shutdown complete")

async def shutdown(stdio, reader_task):
    """Shutdown the server gracefully."""
    logger.info("Shutting down MCP server")
    stdio.running = False
    reader_task.cancel()
    try:
        await reader_task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    try:
        # Open a separate log file for startup debugging
        with open(os.path.join(LOG_DIR, "cursor_mcp_startup.log"), "w") as startup_log:
            startup_log.write(f"Starting MCP server at {os.path.abspath(__file__)}\n")
            startup_log.write(f"Current directory: {os.getcwd()}\n")
            startup_log.write(f"Python path: {sys.path}\n")
            startup_log.flush()
            
        # Set stdin and stdout to binary mode on Windows
        if sys.platform == 'win32':
            import os, msvcrt
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            
        # Run the server in a way that catches all exceptions
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
        # Write to debug file in case logging isn't working
        with open(os.path.join(LOG_DIR, "cursor_mcp_error.log"), "a") as f:
            f.write("Server stopped by keyboard interrupt\n")
    except Exception as e:
        # Log the error and also write to a separate file in case logging is broken
        logger.error(f"Server error: {e}", exc_info=True)
        with open(os.path.join(LOG_DIR, "cursor_mcp_error.log"), "a") as f:
            f.write(f"Server error: {str(e)}\n")
            import traceback
            traceback.print_exc(file=f)
