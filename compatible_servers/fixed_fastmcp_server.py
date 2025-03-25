#!/usr/bin/env python3
"""
Fixed FastMCP server implementation for kubectl-mcp-tool.
"""

import json
import logging
import os
import subprocess
import sys
from typing import Dict, Any, List, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="fixed_fastmcp_server.log"
)
logger = logging.getLogger("fixed-fastmcp-server")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

class FixedFastMCPServer:
    """Fixed FastMCP server implementation for kubectl-mcp-tool."""
    
    def __init__(self, name: str):
        """Initialize the FixedFastMCPServer."""
        self.name = name
        self.tools = {}
        self.initialized = False
        logger.info(f"FixedFastMCPServer initialized: {name}")
    
    def tool(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a tool."""
        def decorator(func: Callable):
            nonlocal name, description
            
            # Use function name if name is not provided
            if name is None:
                name = func.__name__
            
            # Use function docstring if description is not provided
            if description is None and func.__doc__:
                description = func.__doc__.strip()
            elif description is None:
                description = f"Tool: {name}"
            
            # Register the tool
            self.tools[name] = {
                "function": func,
                "description": description,
                "name": name
            }
            
            logger.debug(f"Registered tool: {name}")
            
            return func
        
        return decorator
    
    def register_kubernetes_tools(self):
        """Register Kubernetes tools."""
        
        @self.tool("get_pods", "Get Kubernetes pods")
        def get_pods(namespace: Optional[str] = None) -> Dict[str, Any]:
            """Get Kubernetes pods."""
            try:
                cmd = ["kubectl", "get", "pods"]
                
                if namespace:
                    cmd.extend(["-n", namespace])
                
                cmd.extend(["-o", "json"])
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "command": " ".join(cmd),
                        "result": json.loads(result.stdout)
                    }
                else:
                    return {
                        "success": False,
                        "command": " ".join(cmd),
                        "error": result.stderr
                    }
            except Exception as e:
                logger.error(f"Error getting pods: {e}")
                return {
                    "success": False,
                    "command": "kubectl get pods",
                    "error": str(e)
                }
        
        @self.tool("get_namespaces", "Get Kubernetes namespaces")
        def get_namespaces() -> Dict[str, Any]:
            """Get Kubernetes namespaces."""
            try:
                result = subprocess.run(
                    ["kubectl", "get", "namespaces", "-o", "json"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "command": "kubectl get namespaces -o json",
                        "result": json.loads(result.stdout)
                    }
                else:
                    return {
                        "success": False,
                        "command": "kubectl get namespaces -o json",
                        "error": result.stderr
                    }
            except Exception as e:
                logger.error(f"Error getting namespaces: {e}")
                return {
                    "success": False,
                    "command": "kubectl get namespaces -o json",
                    "error": str(e)
                }
        
        @self.tool("process_natural_language", "Process natural language queries for Kubernetes operations")
        def process_natural_language(query: str) -> Dict[str, Any]:
            """Process natural language queries for Kubernetes operations."""
            try:
                from kubectl_mcp_tool.natural_language import process_query
                
                return process_query(query)
            except Exception as e:
                logger.error(f"Error processing natural language query: {e}")
                return {
                    "success": False,
                    "command": f"process_natural_language({query})",
                    "error": str(e)
                }
        
        logger.info("Registered Kubernetes tools")
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        self.initialized = True
        
        return {
            "capabilities": {
                "tools": {
                    "supported": True
                }
            },
            "server_info": {
                "name": self.name,
                "version": "1.0.0"
            }
        }
    
    def handle_tool_discovery(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool discovery request."""
        tools = []
        
        for name, tool in self.tools.items():
            tools.append({
                "name": name,
                "description": tool["description"],
                "input_schema": {},
                "output_schema": {}
            })
        
        return {
            "tools": tools
        }
    
    def handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request."""
        name = params.get("name", "")
        input_data = params.get("input", {})
        
        if name not in self.tools:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {name}"
                }
            }
        
        try:
            tool = self.tools[name]
            result = tool["function"](**input_data)
            
            return result
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            
            return {
                "error": {
                    "code": -32603,
                    "message": f"Error calling tool {name}: {str(e)}"
                }
            }
    
    def handle_shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shutdown request."""
        self.initialized = False
        
        return {}
    
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message."""
        jsonrpc = message.get("jsonrpc", "")
        id_value = message.get("id", "")
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
        
        result = None
        
        if method == "mcp.initialize":
            result = self.handle_initialize(params)
        elif method == "mcp.tool.discovery":
            result = self.handle_tool_discovery(params)
        elif method == "mcp.tool.call":
            result = self.handle_tool_call(params)
        elif method == "mcp.shutdown":
            result = self.handle_shutdown(params)
        else:
            return {
                "jsonrpc": "2.0",
                "id": id_value,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": id_value,
            "result": result
        }
    
    def serve_stdio(self):
        """Serve over stdio."""
        logger.info("Serving MCP server over stdio")
        
        # Register Kubernetes tools
        self.register_kubernetes_tools()
        
        try:
            while True:
                line = sys.stdin.readline()
                
                if not line:
                    break
                
                try:
                    message = json.loads(line)
                    response = self.process_message(message)
                    
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
                    
                    # Check for shutdown
                    if message.get("method", "") == "mcp.shutdown":
                        break
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON: {line}")
                    
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down")
        except Exception as e:
            logger.error(f"Error in stdio transport: {e}")
    
    async def serve_sse(self, host: str = "0.0.0.0", port: int = 8080):
        """Serve over SSE."""
        logger.info(f"Serving MCP server over SSE on {host}:{port}")
        
        # Register Kubernetes tools
        self.register_kubernetes_tools()
        
        try:
            from fastapi import FastAPI, Request
            from fastapi.responses import JSONResponse
            from sse_starlette.sse import EventSourceResponse
            import uvicorn
            import asyncio
            from queue import Queue
            import uuid
            
            app = FastAPI()
            
            # Store client connections
            clients = {}
            
            @app.post("/mcp")
            async def mcp_endpoint(request: Request):
                """MCP endpoint."""
                try:
                    message = await request.json()
                    response = self.process_message(message)
                    
                    return JSONResponse(content=response)
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    
                    return JSONResponse(
                        status_code=500,
                        content={
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32603,
                                "message": f"Internal error: {str(e)}"
                            }
                        }
                    )
            
            @app.get("/mcp/sse")
            async def mcp_sse_endpoint(request: Request):
                """MCP SSE endpoint."""
                client_id = str(uuid.uuid4())
                queue = asyncio.Queue()
                clients[client_id] = queue
                
                async def event_generator():
                    try:
                        while True:
                            message = await queue.get()
                            
                            if message is None:
                                break
                            
                            yield {
                                "data": json.dumps(message)
                            }
                    except Exception as e:
                        logger.error(f"Error in event generator: {e}")
                    finally:
                        clients.pop(client_id, None)
                
                return EventSourceResponse(event_generator())
            
            @app.post("/mcp/sse/{client_id}")
            async def mcp_sse_client_endpoint(client_id: str, request: Request):
                """MCP SSE client endpoint."""
                try:
                    message = await request.json()
                    response = self.process_message(message)
                    
                    if client_id in clients:
                        await clients[client_id].put(response)
                    
                    return JSONResponse(content={"status": "ok"})
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    
                    return JSONResponse(
                        status_code=500,
                        content={
                            "status": "error",
                            "message": str(e)
                        }
                    )
            
            # Run the server
            config = uvicorn.Config(app, host=host, port=port)
            server = uvicorn.Server(config)
            await server.serve()
        except ImportError:
            logger.error("Error: FastAPI, uvicorn, and sse_starlette are required for SSE transport")
        except Exception as e:
            logger.error(f"Error in SSE transport: {e}")

def main():
    """Run the fixed FastMCP server."""
    try:
        logger.info("Starting fixed FastMCP server")
        
        # Create the server
        server = FixedFastMCPServer("kubectl-mcp-tool")
        
        # Serve over stdio
        server.serve_stdio()
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
