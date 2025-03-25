#!/usr/bin/env python3
"""
Simple MCP server implementation for kubectl-mcp-tool.
This script provides a minimal MCP server implementation for Cursor integration.
"""

import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="simple_mcp_server.log"
)
logger = logging.getLogger("simple-mcp-server")

class KubectlTools:
    """Kubectl tools implementation."""
    
    def __init__(self):
        """Initialize the kubectl tools."""
        self.current_namespace = "default"
    
    async def process_natural_language(self, query: str) -> Dict[str, Any]:
        """Process a natural language query for kubectl operations."""
        logger.info(f"Processing natural language query: {query}")
        
        # This is a simplified implementation that returns mock data
        # In a real implementation, you would use the NLP processor and real kubectl commands
        
        if "get all pods" in query.lower():
            return {
                "command": "kubectl get pods",
                "result": """NAME                     READY   STATUS    RESTARTS   AGE
nginx-pod               1/1     Running   0          1h
web-deployment-abc123   1/1     Running   0          45m
db-statefulset-0        1/1     Running   0          30m"""
            }
        elif "show namespaces" in query.lower() or "get namespaces" in query.lower():
            return {
                "command": "kubectl get namespaces",
                "result": """NAME              STATUS   AGE
default           Active   1d
kube-system       Active   1d
kube-public       Active   1d
kube-node-lease   Active   1d"""
            }
        elif "switch to namespace" in query.lower() or "change namespace" in query.lower():
            namespace = query.lower().split("namespace")[1].strip()
            self.current_namespace = namespace
            return {
                "command": f"kubectl config set-context --current --namespace {namespace}",
                "result": f"Switched to namespace {namespace}"
            }
        elif "current namespace" in query.lower() or "what namespace" in query.lower():
            return {
                "command": "kubectl config view --minify --output jsonpath={..namespace}",
                "result": self.current_namespace
            }
        else:
            return {
                "command": "Unknown command",
                "result": "Could not parse natural language query. Try commands like 'get all pods', 'show namespaces', or 'switch to namespace kube-system'."
            }

class SimpleMCPServer:
    """A simple MCP server implementation."""
    
    def __init__(self, name: str):
        """Initialize the MCP server.
        
        Args:
            name: The name of the server.
        """
        self.name = name
        self.tools = {}
        self.kubectl_tools = KubectlTools()
        
        # Register tools
        self.register_tool(
            "process_natural_language",
            self.process_natural_language,
            "Process a natural language query for kubectl operations",
            {"query": {"type": "string", "description": "The natural language query to process"}}
        )
        
        self.register_tool(
            "get_pods",
            self.get_pods,
            "Get all pods in a namespace",
            {"namespace": {"type": "string", "description": "The namespace to get pods from (optional)"}}
        )
        
        self.register_tool(
            "get_namespaces",
            self.get_namespaces,
            "Get all namespaces in the cluster",
            {}
        )
        
        self.register_tool(
            "switch_namespace",
            self.switch_namespace,
            "Switch to a different namespace",
            {"namespace": {"type": "string", "description": "The namespace to switch to"}}
        )
    
    def register_tool(self, name: str, func: Callable, description: str, parameters: Dict[str, Dict[str, str]]):
        """Register a tool with the server.
        
        Args:
            name: The name of the tool.
            func: The function to call when the tool is invoked.
            description: A description of the tool.
            parameters: A dictionary of parameter names to parameter descriptions.
        """
        self.tools[name] = {
            "func": func,
            "description": description,
            "parameters": parameters
        }
    
    async def process_natural_language(self, query: str) -> List[Dict[str, Any]]:
        """Process a natural language query for kubectl operations.
        
        Args:
            query: The natural language query to process.
        """
        result = await self.kubectl_tools.process_natural_language(query)
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    async def get_pods(self, namespace: str = "") -> List[Dict[str, Any]]:
        """Get all pods in a namespace.
        
        Args:
            namespace: The namespace to get pods from. Defaults to current namespace.
        """
        result = await self.kubectl_tools.process_natural_language(f"get all pods {f'in namespace {namespace}' if namespace else ''}")
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    async def get_namespaces(self) -> List[Dict[str, Any]]:
        """Get all namespaces in the cluster."""
        result = await self.kubectl_tools.process_natural_language("show namespaces")
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    async def switch_namespace(self, namespace: str) -> List[Dict[str, Any]]:
        """Switch to a different namespace.
        
        Args:
            namespace: The namespace to switch to.
        """
        result = await self.kubectl_tools.process_natural_language(f"switch to namespace {namespace}")
        
        return [{"type": "text", "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"}]
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an incoming message.
        
        Args:
            message: The message to handle.
        
        Returns:
            The response message.
        """
        logger.debug(f"Handling message: {message}")
        
        method = message.get("method", "")
        params = message.get("params", {})
        message_id = message.get("id", "")
        
        if method == "mcp.initialize":
            # Handle initialization
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "server_info": {
                        "name": self.name,
                        "version": "0.1.0",
                        "vendor": {
                            "name": "kubectl-mcp-tool"
                        }
                    }
                }
            }
        elif method == "mcp.tools.list":
            # Handle tools list
            tools = []
            for name, tool in self.tools.items():
                tools.append({
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                })
            
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "tools": tools
                }
            }
        elif method == "mcp.tool.call":
            # Handle tool call
            tool_name = params.get("name", "")
            tool_input = params.get("input", {})
            
            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
            
            try:
                # Call the tool
                tool = self.tools[tool_name]
                result = await tool["func"](**tool_input)
                
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": {
                        "output": result
                    }
                }
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32603,
                        "message": f"Error calling tool {tool_name}: {str(e)}"
                    }
                }
        else:
            # Unknown method
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

async def main():
    """Run the MCP server."""
    logger.info("Starting simple MCP server")
    
    # Create the server
    server = SimpleMCPServer("kubectl-mcp-tool")
    
    # Create a file for debugging
    debug_file = open("simple_mcp_debug.log", "w")
    
    # Process stdin/stdout
    while True:
        try:
            # Read a line from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                logger.debug("End of stdin stream")
                break
            
            # Log the raw input for debugging
            debug_file.write(f"STDIN: {line}\n")
            debug_file.flush()
            
            # Parse the message
            try:
                message = json.loads(line)
                
                # Handle the message
                response = await server.handle_message(message)
                
                # Write the response to stdout
                response_str = json.dumps(response) + "\n"
                debug_file.write(f"STDOUT: {response_str}")
                debug_file.flush()
                sys.stdout.write(response_str)
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {line.strip()} - {e}")
                debug_file.write(f"JSON ERROR: {e}\n")
                debug_file.flush()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            debug_file.write(f"ERROR: {e}\n")
            debug_file.flush()
            # Don't break the loop on error, just continue
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(main())
