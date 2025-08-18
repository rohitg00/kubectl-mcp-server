#!/usr/bin/env python3
"""
Windsurf-compatible MCP server implementation for kubectl-mcp-tool.
"""

import json
import sys
import logging
import asyncio
import argparse
from aiohttp import web
import aiohttp_sse
from typing import Dict, Any, List, Optional, Callable, Awaitable

# Import from the correct location
from kubectl_mcp_tool.mcp_server import MCPServer
from kubectl_mcp_tool.natural_language import process_query

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="windsurf_mcp_server.log"
)
logger = logging.getLogger("windsurf-mcp-server")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

class WindsurfMCPServer:
    """Windsurf-compatible MCP server implementation."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.tools = {}
        
        # Register the natural language tool
        self.register_tool(
            "process_natural_language",
            "Process natural language query for kubectl",
            {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The natural language query to process"
                    }
                },
                "required": ["query"]
            },
            self._process_natural_language
        )
        
        # Register the get_pods tool
        self.register_tool(
            "get_pods",
            "Get pods in the specified namespace",
            {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Namespace to get pods from"
                    }
                }
            },
            self._get_pods
        )
        
        # Register the switch_namespace tool
        self.register_tool(
            "switch_namespace",
            "Switch to the specified namespace",
            {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Namespace to switch to"
                    }
                },
                "required": ["namespace"]
            },
            self._switch_namespace
        )
        
        # Register the get_current_namespace tool
        self.register_tool(
            "get_current_namespace",
            "Get the current namespace",
            {
                "type": "object",
                "properties": {}
            },
            self._get_current_namespace
        )
        
        # Register the get_deployments tool
        self.register_tool(
            "get_deployments",
            "Get deployments in the specified namespace",
            {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Namespace to get deployments from"
                    }
                }
            },
            self._get_deployments
        )
    
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable):
        """Register a tool with the server."""
        self.tools[name] = {
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
    
    def _process_natural_language(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """Process a natural language query."""
        from kubectl_mcp_tool.natural_language import process_query
        
        query = input_params.get("query", "")
        if not query:
            return {"error": "Missing required parameter: query"}
        
        # Process the query
        result = process_query(query)
        
        # Return the result
        return result
    
    def _get_pods(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get pods in the specified namespace."""
        import subprocess
        
        namespace = input_params.get("namespace", "default")
        
        try:
            # Run kubectl command
            command = f"kubectl get pods -n {namespace}"
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "command": command,
                "result": result.stdout.strip(),
                "success": True
            }
        except subprocess.CalledProcessError as e:
            logger.warning(f"kubectl command failed: {command} - {e}")
            
            # Return mock data as fallback
            return {
                "command": command,
                "result": f"Error: {e.stderr}",
                "success": False,
                "error": e.stderr
            }
    
    def _switch_namespace(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """Switch to the specified namespace."""
        import subprocess
        
        namespace = input_params.get("namespace", "")
        if not namespace:
            return {"error": "Missing required parameter: namespace"}
        
        try:
            # Run kubectl command
            command = f"kubectl config set-context --current --namespace={namespace}"
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
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
                "result": f"Error: {e.stderr}",
                "success": False,
                "error": e.stderr
            }
    
    def _get_current_namespace(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current namespace."""
        import subprocess
        
        try:
            # Run kubectl command
            command = "kubectl config view --minify --output 'jsonpath={..namespace}'"
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "command": command,
                "result": result.stdout.strip() or "default",
                "success": True
            }
        except subprocess.CalledProcessError as e:
            logger.warning(f"kubectl command failed: {command} - {e}")
            
            return {
                "command": command,
                "result": f"Error: {e.stderr}",
                "success": False,
                "error": e.stderr
            }
    
    def _get_deployments(self, input_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get deployments in the specified namespace."""
        import subprocess
        
        namespace = input_params.get("namespace", "default")
        
        try:
            # Run kubectl command
            command = f"kubectl get deployments -n {namespace}"
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
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
                "result": f"Error: {e.stderr}",
                "success": False,
                "error": e.stderr
            }
    
    def handle_initialize(self, message_id: str) -> Dict[str, Any]:
        """Handle initialize request."""
        logger.info("Handling initialize request")
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "capabilities": {
                    "tools": True
                }
            }
        }
    
    def handle_tools_list(self, message_id: str) -> Dict[str, Any]:
        """Handle tools/list request."""
        logger.info("Handling tools/list request")
        tools_list = []
        for name, info in self.tools.items():
            tools_list.append({
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"]
            })
            
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "tools": tools_list
            }
        }
    
    def handle_tool_call(self, message_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool/call request."""
        logger.info(f"Handling tool/call request: {params}")
        
        # Get the tool name and input
        tool_name = params.get("name", "")
        tool_input = params.get("input", {})
        
        # Check if the tool exists
        if tool_name not in self.tools:
            logger.error(f"Tool not found: {tool_name}")
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }
        
        # Call the tool
        try:
            tool_info = self.tools[tool_name]
            
            # Check for required parameters
            required_params = tool_info["parameters"].get("required", [])
            for param_name in required_params:
                if param_name not in tool_input:
                    logger.error(f"Missing required parameter: {param_name}")
                    return {
                        "jsonrpc": "2.0",
                        "id": message_id,
                        "error": {
                            "code": -32602,
                            "message": f"Missing required parameter: {param_name}"
                        }
                    }
            
            # Call the handler
            result = tool_info["handler"](tool_input)
            
            # Format the result
            if "error" in result and not "success" in result:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32603,
                        "message": result["error"]
                    }
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": result
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
    
    def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a message from the client."""
        if "method" not in message:
            logger.error(f"Invalid message, missing method: {message}")
            return None
        
        method = message["method"]
        message_id = message.get("id", "")
        
        # Handle initialize
        if method == "mcp.initialize":
            return self.handle_initialize(message_id)
        
        # Handle tools/list
        elif method == "mcp.tools.list":
            return self.handle_tools_list(message_id)
        
        # Handle tool/call
        elif method == "mcp.tool.call":
            return self.handle_tool_call(message_id, message.get("params", {}))
        
        # Handle unknown method
        else:
            logger.error(f"Unknown method: {method}")
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def serve_sse(self, host: str, port: int):
        """Serve the MCP server over SSE."""
        logger.info(f"Serving MCP server over SSE on {host}:{port}")
        
        # Create the web app
        app = web.Application()
        
        # Create the SSE endpoint
        async def sse_handler(request):
            try:
                # Get the request data
                data = await request.json()
                logger.info(f"Received request: {data}")
                
                # Handle the message
                response = self.handle_message(data)
                
                # Create SSE response
                async with aiohttp_sse.sse_response(request) as resp:
                    if response:
                        # Send the response as SSE event
                        await resp.send(json.dumps(response))
                    
                    # Keep the connection open for a while
                    for _ in range(10):  # Keep alive for a short time
                        await asyncio.sleep(1)
                        
                return resp
            except Exception as e:
                logger.error(f"Error in SSE handler: {e}")
                return web.Response(status=500, text=str(e))
        
        # Create a health check endpoint
        async def health_handler(request):
            return web.Response(text="OK")
        
        # Add the endpoints
        app.router.add_post("/", sse_handler)
        app.router.add_get("/health", health_handler)
        
        # Run the web server
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"SSE server started on {host}:{port}")
        
        # Wait forever
        while True:
            await asyncio.sleep(3600)

async def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="Windsurf-compatible MCP server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    
    # Create the server
    server = WindsurfMCPServer()
    
    # Serve the server
    await server.serve_sse(args.host, args.port)

if __name__ == "__main__":
    asyncio.run(main())
