#!/usr/bin/env python3
"""
MCP-compliant server for kubectl operations.

This server implements the Model Context Protocol (MCP) to provide
Kubernetes operations through kubectl to AI assistants.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import traceback
from typing import Any, Dict, List, Optional

# Create log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d",
    filename=os.path.join(LOG_DIR, "mcp_kubectl_server.log"),
)
logger = logging.getLogger("mcp-kubectl-server")

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(levelname)s: %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Log startup information
logger.info("Starting MCP kubectl server")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")

# Create a debug log file 
debug_file = open(os.path.join(LOG_DIR, "debug.log"), "w")
debug_file.write(f"Starting MCP kubectl server at {os.path.abspath(__file__)}\n")
debug_file.write(f"Current directory: {os.getcwd()}\n")
debug_file.flush()

try:
    # Import MCP SDK - use specific version for compatibility
    debug_file.write("Attempting to import MCP SDK...\n")
    debug_file.flush()
    
    # Try to directly install the MCP package first
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp>=1.4.0"], 
                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    from mcp.server import Server
    from mcp.server import stdio
    import mcp.types as types
    from mcp.server.models import InitializationOptions
    from mcp.server.lowlevel import NotificationOptions
    
    debug_file.write("Successfully imported MCP SDK\n")
    debug_file.flush()
    logger.info("Successfully imported MCP SDK")
except ImportError as e:
    error_msg = f"Failed to import MCP SDK: {e}"
    logger.error(error_msg)
    debug_file.write(f"{error_msg}\n")
    debug_file.write(f"Python path: {sys.path}\n")
    debug_file.flush()
    
    logger.info("Attempting to install MCP SDK...")
    try:
        # Try more direct installation methods
        debug_file.write("Installing MCP from git repo...\n")
        debug_file.flush()
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "git+https://github.com/modelcontextprotocol/python-sdk.git"
        ])
        
        from mcp.server import Server
        from mcp.server import stdio
        import mcp.types as types
        from mcp.server.models import InitializationOptions
        from mcp.server.lowlevel import NotificationOptions
        
        logger.info("Successfully installed and imported MCP SDK")
        debug_file.write("Successfully installed MCP from git\n")
        debug_file.flush()
    except Exception as e:
        critical_error = f"Failed to install MCP SDK: {e}"
        logger.critical(critical_error)
        debug_file.write(f"{critical_error}\n")
        debug_file.write(traceback.format_exc())
        debug_file.flush()
        sys.exit(1)

class KubectlServer:
    """Implementation of kubectl operations for MCP."""

    def __init__(self):
        """Initialize the kubectl server."""
        self.current_namespace = "default"
        # Create server with version but remove description parameter which is no longer supported
        self.server = Server(
            name="kubectl-mcp-tool",
            version="0.1.0"
        )
        self.setup_tools()
        logger.info("KubectlServer initialized")
        debug_file.write("KubectlServer initialized\n")
        debug_file.flush()

    def setup_tools(self):
        """Set up the tools for the server."""
        debug_file.write("Setting up tools...\n")
        debug_file.flush()
        
        @self.server.call_tool("process_natural_language")
        async def process_natural_language(query: str) -> Dict[str, Any]:
            """Process natural language queries for kubectl operations."""
            logger.info(f"Processing natural language query: {query}")
            debug_file.write(f"Processing query: {query}\n")
            debug_file.flush()
            return await self._process_query(query)

        @self.server.call_tool("get_pods")
        async def get_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get pods in the specified namespace."""
            query = f"get pods {f'in namespace {namespace}' if namespace else ''}"
            debug_file.write(f"get_pods called with namespace={namespace}\n")
            debug_file.flush()
            return await self._process_query(query)

        @self.server.call_tool("get_namespaces")
        async def get_namespaces() -> Dict[str, Any]:
            """Get all namespaces."""
            debug_file.write("get_namespaces called\n")
            debug_file.flush()
            return await self._process_query("show namespaces")

        @self.server.call_tool("switch_namespace")
        async def switch_namespace(namespace: str) -> Dict[str, Any]:
            """Switch to the specified namespace."""
            debug_file.write(f"switch_namespace called with namespace={namespace}\n")
            debug_file.flush()
            return await self._process_query(f"switch to namespace {namespace}")

        @self.server.call_tool("get_current_namespace")
        async def get_current_namespace() -> Dict[str, Any]:
            """Get the current namespace."""
            debug_file.write("get_current_namespace called\n")
            debug_file.flush()
            return await self._process_query("what is my current namespace")

        @self.server.call_tool("get_deployments")
        async def get_deployments(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get deployments in the specified namespace."""
            query = f"get deployments {f'in namespace {namespace}' if namespace else ''}"
            debug_file.write(f"get_deployments called with namespace={namespace}\n")
            debug_file.flush()
            return await self._process_query(query)

        @self.server.call_tool("get_services")
        async def get_services(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get services in the specified namespace."""
            query = f"get services {f'in namespace {namespace}' if namespace else ''}"
            debug_file.write(f"get_services called with namespace={namespace}\n")
            debug_file.flush()
            return await self._process_query(query)

        @self.server.call_tool("describe_resource")
        async def describe_resource(resource_type: str, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
            """Describe a Kubernetes resource."""
            query = f"describe {resource_type} {name} {f'in namespace {namespace}' if namespace else ''}"
            debug_file.write(f"describe_resource called with type={resource_type}, name={name}, namespace={namespace}\n")
            debug_file.flush()
            return await self._process_query(query)

        @self.server.call_tool("run_kubectl_command")
        async def run_kubectl_command(command: str) -> Dict[str, Any]:
            """Run a raw kubectl command."""
            debug_file.write(f"run_kubectl_command called with command={command}\n")
            debug_file.flush()
            return await self._process_query(command)

        logger.info("Tools setup complete")
        debug_file.write("Tools setup complete\n")
        debug_file.flush()

    def _run_kubectl_command(self, command: str) -> Dict[str, Any]:
        """Run a kubectl command and return the result."""
        debug_file.write(f"Running kubectl command: {command}\n")
        debug_file.flush()
        
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            output = result.stdout.strip()
            debug_file.write(f"Command success, output length: {len(output)}\n")
            debug_file.flush()
            
            return {
                "command": command,
                "result": output,
                "success": True,
            }
        except subprocess.CalledProcessError as e:
            error_msg = f"kubectl command failed: {command} - {e}"
            logger.warning(error_msg)
            debug_file.write(f"{error_msg}\nError output: {e.stderr}\n")
            debug_file.flush()
            
            return {
                "command": command,
                "result": e.stderr.strip(),
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            error_msg = f"Error running kubectl command: {command} - {e}"
            logger.error(error_msg)
            debug_file.write(f"{error_msg}\n{traceback.format_exc()}\n")
            debug_file.flush()
            
            return {
                "command": command,
                "result": f"Error: {str(e)}",
                "success": False,
                "error": str(e),
            }

    async def _process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query for kubectl operations."""
        logger.info(f"Processing query: {query}")
        debug_file.write(f"Processing query: {query}\n")
        debug_file.flush()
        
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
                
            elif "show namespaces" in query_lower or "get namespaces" in query_lower:
                command = "kubectl get namespaces"
                
            elif "switch to namespace" in query_lower or "change namespace" in query_lower:
                # Extract namespace name
                parts = query_lower.split("namespace")
                if len(parts) > 1:
                    namespace = parts[1].strip()
                    command = f"kubectl config set-context --current --namespace={namespace}"
                    # Update current namespace if command succeeds
                    self.current_namespace = namespace
                else:
                    return {
                        "command": "kubectl config set-context",
                        "result": "Error: No namespace specified",
                        "success": False
                    }
            
            elif "current namespace" in query_lower or "what namespace" in query_lower:
                command = "kubectl config view --minify --output 'jsonpath={..namespace}'"
                
            elif "get contexts" in query_lower or "show contexts" in query_lower:
                command = "kubectl config get-contexts"
                
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

            elif "describe" in query_lower:
                # Try to parse a describe command
                words = query_lower.split()
                if len(words) >= 3 and words[0] == "describe":
                    resource_type = words[1]
                    name = words[2]
                    if "namespace" in query_lower:
                        parts = query_lower.split("namespace")
                        if len(parts) > 1:
                            namespace = parts[1].strip()
                            command = f"kubectl describe {resource_type} {name} -n {namespace}"
                        else:
                            command = f"kubectl describe {resource_type} {name}"
                    else:
                        command = f"kubectl describe {resource_type} {name} -n {self.current_namespace}"
                else:
                    command = f"kubectl {query}"
            else:
                # For unknown commands, try to run the query as a kubectl command
                command = f"kubectl {query}"
            
            debug_file.write(f"Determined command: {command}\n")
            debug_file.flush()
            
            # Run the command
            result = self._run_kubectl_command(command)
            return result
        except Exception as e:
            error_msg = f"Error processing query: {query} - {e}"
            logger.error(error_msg)
            debug_file.write(f"{error_msg}\n{traceback.format_exc()}\n")
            debug_file.flush()
            
            return {
                "command": "Error",
                "result": f"Failed to process query: {str(e)}",
                "success": False,
                "error": str(e)
            }

    async def run(self):
        """Run the server with manual initialization."""
        logger.info("Starting KubectlServer run")
        debug_file.write("Starting KubectlServer run method\n")
        debug_file.flush()
        
        try:
            # Use the lower-level stdio server for more control
            debug_file.write("Initializing stdio transport\n")
            debug_file.flush()
            
            async with stdio.stdio_server() as (read_stream, write_stream):
                debug_file.write("Stdio transport started\n")
                debug_file.flush()
                
                # Create initialization options
                init_options = InitializationOptions(
                    server_name="kubectl-mcp-tool",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                )
                
                debug_file.write(f"Running server with initialization options: {init_options}\n")
                debug_file.flush()
                
                # Run the server with explicit initialization
                await self.server.run(
                    read_stream, 
                    write_stream, 
                    initialization_options=init_options
                )
                
                logger.info("Server stopped normally")
                debug_file.write("Server stopped normally\n")
                debug_file.flush()
                
        except Exception as e:
            error_msg = f"Error running server: {e}"
            logger.error(error_msg, exc_info=True)
            debug_file.write(f"{error_msg}\n{traceback.format_exc()}\n")
            debug_file.flush()
            
            # Log to a separate file in case logging is broken
            with open(os.path.join(LOG_DIR, "server_error.log"), "a") as f:
                f.write(f"Server error: {str(e)}\n")
                traceback.print_exc(file=f)


async def main():
    """Run the MCP kubectl server."""
    debug_file.write("Entering main function\n")
    debug_file.flush()
    
    server = KubectlServer()
    debug_file.write("KubectlServer instance created\n")
    debug_file.flush()
    
    await server.run()
    debug_file.write("Server run completed\n")
    debug_file.flush()


if __name__ == "__main__":
    try:
        # Open a separate log file for startup debugging
        with open(os.path.join(LOG_DIR, "startup.log"), "w") as startup_log:
            startup_log.write(f"Starting MCP kubectl server at {os.path.abspath(__file__)}\n")
            startup_log.write(f"Current directory: {os.getcwd()}\n")
            startup_log.write(f"Python path: {sys.path}\n")
            startup_log.flush()
        
        # Set env var for unbuffered output
        os.environ["PYTHONUNBUFFERED"] = "1"
        
        debug_file.write("About to run main async function\n")
        debug_file.flush()
        
        # Run the server
        asyncio.run(main())
        
        debug_file.write("Main function completed\n")
        debug_file.flush()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
        debug_file.write("Server stopped by keyboard interrupt\n")
        debug_file.flush()
        
    except Exception as e:
        error_msg = f"Fatal error: {e}"
        logger.critical(error_msg, exc_info=True)
        debug_file.write(f"{error_msg}\n{traceback.format_exc()}\n")
        debug_file.flush()
        
        with open(os.path.join(LOG_DIR, "fatal_error.log"), "a") as f:
            f.write(f"Fatal error: {str(e)}\n")
            traceback.print_exc(file=f)
    finally:
        debug_file.write("Exiting script\n")
        debug_file.close() 