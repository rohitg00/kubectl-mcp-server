#!/usr/bin/env python3
"""
Simplified MCP implementation for kubectl-mcp-tool.

This module provides a simplified implementation of the MCP protocol
that works with both Cursor and Windsurf clients.
"""

import asyncio
import json
import logging
import sys
from typing import Dict, Any, List, Optional, Callable
import uuid

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="simplified_mcp.log"
)
logger = logging.getLogger("simplified-mcp")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

class SimpleMCPServer:
    """Simplified MCP server implementation."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize the MCP server."""
        self.name = name
        self.version = version
        self.tools = {}
        self.initialized = False
        logger.info(f"SimpleMCPServer initialized: {name} v{version}")
    
    def register_tool(self, name: str, description: str, func: Callable):
        """Register a tool with the server."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "function": func
        }
        logger.info(f"Registered tool: {name}")
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process an MCP message."""
        try:
            jsonrpc = message.get("jsonrpc", "")
            id_value = message.get("id", str(uuid.uuid4()))
            method = message.get("method", "")
            params = message.get("params", {})
            
            if jsonrpc != "2.0":
                return {
                    "jsonrpc": "2.0",
                    "id": id_value,
                    "error": {
                        "code": -32600,
                        "message": "Invalid Request"
                    }
                }
            
            # Handle MCP methods
            if method == "mcp.initialize":
                return self._handle_initialize(id_value, params)
            elif method == "mcp.tool.discovery" or method == "mcp.tools.list":
                return self._handle_tool_discovery(id_value)
            elif method == "mcp.tool.call":
                return self._handle_tool_call(id_value, params)
            elif method == "mcp.shutdown":
                return self._handle_shutdown(id_value)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": id_value,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "jsonrpc": "2.0",
                "id": id_value if 'id_value' in locals() else str(uuid.uuid4()),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def _handle_initialize(self, id_value: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mcp.initialize method."""
        self.initialized = True
        logger.info("Server initialized")
        
        return {
            "jsonrpc": "2.0",
            "id": id_value,
            "result": {
                "name": self.name,
                "version": self.version,
                "capabilities": {
                    "tools": {
                        "supported": True
                    }
                }
            }
        }
    
    def _handle_tool_discovery(self, id_value: str) -> Dict[str, Any]:
        """Handle mcp.tool.discovery method."""
        if not self.initialized:
            return {
                "jsonrpc": "2.0",
                "id": id_value,
                "error": {
                    "code": -32002,
                    "message": "Server not initialized"
                }
            }
        
        tool_list = []
        
        for name, tool in self.tools.items():
            tool_list.append({
                "name": name,
                "description": tool["description"],
                "input_schema": {},
                "output_schema": {}
            })
        
        return {
            "jsonrpc": "2.0",
            "id": id_value,
            "result": {
                "tools": tool_list
            }
        }
    
    def _handle_tool_call(self, id_value: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mcp.tool.call method."""
        if not self.initialized:
            return {
                "jsonrpc": "2.0",
                "id": id_value,
                "error": {
                    "code": -32002,
                    "message": "Server not initialized"
                }
            }
        
        name = params.get("name", "")
        input_data = params.get("input", {})
        
        if name not in self.tools:
            return {
                "jsonrpc": "2.0",
                "id": id_value,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {name}"
                }
            }
        
        try:
            tool = self.tools[name]
            result = tool["function"](**input_data)
            
            return {
                "jsonrpc": "2.0",
                "id": id_value,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            
            return {
                "jsonrpc": "2.0",
                "id": id_value,
                "error": {
                    "code": -32603,
                    "message": f"Error calling tool {name}: {str(e)}"
                }
            }
    
    def _handle_shutdown(self, id_value: str) -> Dict[str, Any]:
        """Handle mcp.shutdown method."""
        logger.info("Server shutting down")
        
        return {
            "jsonrpc": "2.0",
            "id": id_value,
            "result": {}
        }
    
    def serve_stdio(self):
        """Serve the MCP server over stdio."""
        logger.info("Serving MCP server over stdio")
        
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                
                try:
                    message = json.loads(line)
                    response = self.process_message(message)
                    
                    # Send the response
                    json_response = json.dumps(response) + "\n"
                    sys.stdout.write(json_response)
                    sys.stdout.flush()
                    
                    # Check if shutdown was requested
                    if message.get("method") == "mcp.shutdown":
                        break
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {line}")
                    
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    
                    json_response = json.dumps(error_response) + "\n"
                    sys.stdout.write(json_response)
                    sys.stdout.flush()
        except KeyboardInterrupt:
            logger.info("Server stopped by keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in stdio transport: {e}")
    
    async def serve_sse(self, port: int = 8080):
        """Serve the MCP server over SSE."""
        from aiohttp import web
        
        logger.info(f"Serving MCP server over SSE on port {port}")
        
        async def handle_mcp(request):
            try:
                message = await request.json()
                logger.debug(f"Received message: {message}")
                
                # Process the message
                response = self.process_message(message)
                
                return web.json_response(response)
                
            except Exception as e:
                logger.error(f"Error handling request: {e}")
                return web.json_response({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }, status=500)
        
        app = web.Application()
        app.router.add_post("/mcp", handle_mcp)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", port)
        await site.start()
        
        logger.info(f"SSE server started on port {port}")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("SSE server shutting down")
            await runner.cleanup()
