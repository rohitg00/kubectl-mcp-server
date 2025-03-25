#!/usr/bin/env python3
"""
Cursor-compatible MCP server implementation for kubectl-mcp-tool.
This script provides a specialized MCP server implementation for Cursor integration.
"""

import sys
import json
import logging
import asyncio
import signal
import os
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
import mcp.server.lowlevel

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="cursor_mcp_server.log"
)
logger = logging.getLogger("cursor-mcp-server")

class StdioTransport:
    """A class that implements the stdio transport for MCP according to the specification."""
    
    def __init__(self):
        """Initialize the stdio transport."""
        self.input_queue = asyncio.Queue()
        self.running = True
        self.debug_file = open("mcp_debug.log", "w")
        self.debug_file.write(f"StdioTransport initialized at {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}\n")
        self.debug_file.flush()
        logger.info("StdioTransport initialized")
    
    async def start_reader(self):
        """Start reading from stdin in a non-blocking way."""
        loop = asyncio.get_running_loop()
        logger.info("Starting stdin reader")
        self.debug_file.write("Starting stdin reader\n")
        self.debug_file.flush()
        
        while self.running:
            try:
                # Always try to read from stdin without checking isatty() or readable()
                # This is more reliable for Cursor integration
                line = await loop.run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    logger.debug("End of stdin stream")
                    self.debug_file.write("End of stdin stream\n")
                    self.debug_file.flush()
                    self.running = False
                    break
                
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
        """Read messages from the input queue and yield them as an async generator.
        
        This method is called by the MCP server to get messages from the client.
        """
        logger.info("Starting message reader")
        self.debug_file.write("Starting message reader\n")
        self.debug_file.flush()
        
        while self.running:
            try:
                # Get a message from the queue
                message = await self.input_queue.get()
                
                # Log the message
                logger.debug(f"Yielding message: {message}")
                self.debug_file.write(f"YIELD: {json.dumps(message)}\n")
                self.debug_file.flush()
                
                # Yield the message to the MCP server
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
        """Write a message to stdout according to the MCP specification.
        
        This method is called by the MCP server to send messages to the client.
        
        Args:
            message: The message to write to stdout.
        """
        try:
            # Convert the message to a JSON string with a newline
            json_str = json.dumps(message) + "\n"
            
            # Log the message
            logger.debug(f"Writing to stdout: {json_str.strip()}")
            self.debug_file.write(f"STDOUT: {json_str}")
            self.debug_file.flush()
            
            # Write the message to stdout and flush
            sys.stdout.write(json_str)
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error writing to stdout: {e}")
            self.debug_file.write(f"WRITE ERROR: {str(e)}\n")
            self.debug_file.flush()
            
            # Try to log the message that failed to write
            try:
                self.debug_file.write(f"FAILED MESSAGE: {json.dumps(message)}\n")
                self.debug_file.flush()
            except:
                self.debug_file.write("Could not log failed message\n")
                self.debug_file.flush()

class KubectlTools:
    """Kubectl tools implementation for Cursor integration."""
    
    def __init__(self):
        """Initialize the kubectl tools."""
        self.current_namespace = "default"
    
    async def process_natural_language(self, query: str) -> Dict[str, Any]:
        """Process a natural language query for kubectl operations."""
        logger.info(f"Processing natural language query: {query}")
        
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
            elif "describe pod" in query_lower:
                # Extract pod name
                parts = query_lower.split("describe pod")
                if len(parts) > 1:
                    pod_name = parts[1].strip()
                    command = f"kubectl describe pod {pod_name} -n {self.current_namespace}"
                else:
                    return {
                        "command": "kubectl describe pod",
                        "result": "Error: No pod name specified",
                        "success": False
                    }
            else:
                # For unknown commands, try to run the query as a kubectl command
                command = f"kubectl {query}"
            
            # Execute the kubectl command
            import subprocess
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
                # Command failed
                return {
                    "command": command,
                    "result": e.stderr.strip(),
                    "success": False,
                    "error": str(e)
                }
        except Exception as e:
            # Other error
            return {
                "command": "Error",
                "result": f"Failed to process query: {str(e)}",
                "success": False,
                "error": str(e)
            }

def create_server():
    """Create and configure the MCP server."""
    # Create the server
    app = mcp.server.lowlevel.Server("kubectl-mcp-tool")
    
    # Create the kubectl tools
    kubectl_tools = KubectlTools()
    
    # Register the process_natural_language tool
    @app.call_tool()
    async def process_natural_language(query: str) -> List[Dict[str, Any]]:
        """Process a natural language query for kubectl.
        
        Args:
            query: The natural language query to process.
        """
        logger.info(f"Processing natural language query: {query}")
        
        # Process the query
        result = await kubectl_tools.process_natural_language(query)
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    # Register additional tools for direct kubectl operations
    @app.call_tool()
    async def get_pods(namespace: str = "") -> List[Dict[str, Any]]:
        """Get all pods in a namespace.
        
        Args:
            namespace: The namespace to get pods from. Defaults to current namespace.
        """
        logger.info(f"Getting pods in namespace: {namespace or 'current'}")
        
        result = await kubectl_tools.process_natural_language(f"get all pods {f'in namespace {namespace}' if namespace else ''}")
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    @app.call_tool()
    async def get_namespaces() -> List[Dict[str, Any]]:
        """Get all namespaces in the cluster."""
        logger.info("Getting all namespaces")
        
        result = await kubectl_tools.process_natural_language("show namespaces")
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    @app.call_tool()
    async def switch_namespace(namespace: str) -> List[Dict[str, Any]]:
        """Switch to a different namespace.
        
        Args:
            namespace: The namespace to switch to.
        """
        logger.info(f"Switching to namespace: {namespace}")
        
        result = await kubectl_tools.process_natural_language(f"switch to namespace {namespace}")
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    @app.call_tool()
    async def get_current_namespace() -> List[Dict[str, Any]]:
        """Get the current namespace."""
        logger.info("Getting current namespace")
        
        result = await kubectl_tools.process_natural_language("what is my current namespace")
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    @app.call_tool()
    async def get_deployments(namespace: str = "") -> List[Dict[str, Any]]:
        """Get all deployments in a namespace.
        
        Args:
            namespace: The namespace to get deployments from. Defaults to current namespace.
        """
        logger.info(f"Getting deployments in namespace: {namespace or 'current'}")
        
        result = await kubectl_tools.process_natural_language(f"get deployments {f'in namespace {namespace}' if namespace else ''}")
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    return app

async def run_server(app, read_message, write_message):
    """Run the MCP server with the provided transport."""
    try:
        # Run the server
        await app.run(
            read_message, write_message, app.create_initialization_options()
        )
    except Exception as e:
        logger.error(f"Error in server run: {e}")
        raise

async def main():
    """Run the MCP server for Cursor integration."""
    logger.info("Starting kubectl MCP server with stdio transport for Cursor integration")
    
    # Create the server
    app = create_server()
    
    # Create the stdio transport
    stdio = StdioTransport()
    
    # Start the reader task
    reader_task = asyncio.create_task(stdio.start_reader())
    
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for signal_name in ('SIGINT', 'SIGTERM'):
        try:
            loop.add_signal_handler(getattr(signal, signal_name), lambda: asyncio.create_task(shutdown(stdio, reader_task)))
        except (NotImplementedError, AttributeError):
            # Windows doesn't support SIGINT/SIGTERM
            pass
    
    try:
        # Create a class that implements the async context manager and iterator protocol
        class ReadMessageContextManager:
            def __init__(self, read_func):
                self.read_func = read_func
                self.gen = None
            
            async def __aenter__(self):
                self.gen = self.read_func()
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if hasattr(self.gen, 'aclose'):
                    await self.gen.aclose()
                return False
                
            def __aiter__(self):
                return self
                
            async def __anext__(self):
                if self.gen is None:
                    self.gen = self.read_func()
                try:
                    return await self.gen.__anext__()
                except StopAsyncIteration:
                    self.gen = None
                    raise
        
        # Use the context manager for read_message
        read_message_cm = ReadMessageContextManager(stdio.read_message)
        
        # Create a class that implements the async context manager protocol for write_message
        class WriteMessageContextManager:
            def __init__(self, write_func):
                self.write_func = write_func
            
            async def __aenter__(self):
                return self.write_func
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False
        
        # Use the context manager for write_message
        write_message_cm = WriteMessageContextManager(stdio.write_message)
        
        # Run the server with proper initialization options according to MCP spec
        logger.info("Starting MCP server run")
        
        # Initialize the server with the correct initialization options
        # The server will handle the mcp.initialize message internally
        await app.run(
            read_message_cm, 
            write_message_cm, 
            None  # Let the server handle initialization based on client messages
        )
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        # Write error to debug file for troubleshooting
        with open("mcp_error.log", "a") as f:
            f.write(f"Error in main: {e}\n")
            import traceback
            traceback.print_exc(file=f)
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
    asyncio.run(main())
