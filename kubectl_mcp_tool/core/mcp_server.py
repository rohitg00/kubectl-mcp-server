#!/usr/bin/env python3
"""
MCP server implementation for kubectl-mcp-tool.
"""

import json
import sys
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from .natural_language import process_query

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-server")

class MCPServer:
    """MCP server implementation."""
    
    def __init__(self, name: str):
        """Initialize the MCP server."""
        self.name = name
        self.tools = {}
        
        # Register the natural language tool
        self.register_tool(
            "process_natural_language",
            "Process natural language query for kubectl",
            {
                "query": {
                    "type": "string",
                    "description": "The natural language query to process",
                    "required": True
                }
            },
            self._process_natural_language
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
        query = input_params.get("query", "")
        if not query:
            return {"error": "Missing required parameter: query"}
        
        # Process the query
        result = process_query(query)
        
        # Format the result
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Command: {result['command']}\n\nResult:\n{result['result']}"
                }
            ]
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
            tool_info = {
                "name": name,
                "description": info["description"],
                "parameters": {}
            }
            for param_name, param_info in info["parameters"].items():
                tool_info["parameters"][param_name] = {
                    "type": param_info.get("type", "string"),
                    "description": param_info.get("description", ""),
                    "required": param_info.get("required", False)
                }
            tools_list.append(tool_info)
            
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "tools": tools_list
            }
        }
    
    def handle_tool_call(self, message_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool/call request."""
        logger.info("Handling tool/call request")
        
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
            for param_name, param_info in tool_info.get("parameters", {}).items():
                if param_info.get("required", False) and param_name not in tool_input:
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
            if "error" in result:
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
    
    def serve_stdio(self):
        """Serve the MCP server over stdio."""
        logger.info("Serving MCP server over stdio")
        
        while True:
            try:
                # Read a line from stdin
                line = sys.stdin.readline()
                if not line:
                    logger.debug("End of stdin stream")
                    break
                
                logger.debug(f"Received: {line.strip()}")
                
                # Parse the JSON message
                try:
                    message = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {line.strip()} - {e}")
                    continue
                
                # Handle the message
                response = self.handle_message(message)
                if response:
                    # Send the response
                    print(json.dumps(response), flush=True)
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
                # Try to send an error response
                try:
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id", "") if "message" in locals() else "",
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    print(json.dumps(response), flush=True)
                except Exception as e2:
                    logger.error(f"Error sending error response: {e2}")
    
    async def serve_sse(self, port: int):
        """Serve the MCP server over SSE."""
        logger.info(f"Serving MCP server over SSE on port {port}")
        
        # Import the required modules
        from aiohttp import web
        import aiohttp_sse
        
        # Create the web app
        app = web.Application()
        
        # Create the SSE endpoint for streaming responses
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
        site = web.TCPSite(runner, "0.0.0.0", port)  # Listen on all interfaces
        await site.start()
        
        logger.info(f"SSE server started on port {port}")
        
        # Wait forever
        while True:
            await asyncio.sleep(3600)
