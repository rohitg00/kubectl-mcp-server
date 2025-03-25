#!/usr/bin/env python3
"""
Simple HTTP server for testing Windsurf integration with kubectl-mcp-tool.
"""

import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="simple_http_server.log"
)
logger = logging.getLogger("simple-http-server")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Create FastAPI app
app = FastAPI()

# Store registered tools
tools = {
    "get_pods": {
        "name": "get_pods",
        "description": "Get Kubernetes pods",
        "function": lambda namespace=None: {
            "success": True,
            "command": f"kubectl get pods {'-n ' + namespace if namespace else ''}",
            "result": "NAME                       READY   STATUS    RESTARTS        AGE\nnginx-5869d7778c-glw6b     1/1     Running   1 (2d12h ago)   5d10h"
        }
    },
    "get_namespaces": {
        "name": "get_namespaces",
        "description": "Get Kubernetes namespaces",
        "function": lambda: {
            "success": True,
            "command": "kubectl get namespaces",
            "result": "NAME              STATUS   AGE\ndefault           Active   5d10h\nkube-node-lease   Active   5d10h\nkube-public       Active   5d10h\nkube-system       Active   5d10h"
        }
    },
    "process_natural_language": {
        "name": "process_natural_language",
        "description": "Process natural language queries for Kubernetes operations",
        "function": lambda query: {
            "success": True,
            "command": "kubectl get pod",
            "result": "NAME                       READY   STATUS    RESTARTS        AGE\nnginx-5869d7778c-glw6b     1/1     Running   1 (2d12h ago)   5d10h\nnginx-5869d7778c-jt8rn     1/1     Running   1 (2d12h ago)   5d10h"
        }
    }
}

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP endpoint."""
    try:
        message = await request.json()
        
        jsonrpc = message.get("jsonrpc", "")
        id_value = message.get("id", "")
        method = message.get("method", "")
        params = message.get("params", {})
        
        if jsonrpc != "2.0":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": id_value,
                "error": {
                    "code": -32600,
                    "message": "Invalid Request"
                }
            })
        
        result = None
        
        if method == "mcp.initialize":
            result = {
                "capabilities": {
                    "tools": {
                        "supported": True
                    }
                },
                "server_info": {
                    "name": "kubectl-mcp-tool",
                    "version": "1.0.0"
                }
            }
        elif method == "mcp.tool.discovery":
            tool_list = []
            
            for name, tool in tools.items():
                tool_list.append({
                    "name": name,
                    "description": tool["description"],
                    "input_schema": {},
                    "output_schema": {}
                })
            
            result = {
                "tools": tool_list
            }
        elif method == "mcp.tool.call":
            name = params.get("name", "")
            input_data = params.get("input", {})
            
            if name not in tools:
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "id": id_value,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {name}"
                    }
                })
            
            try:
                tool = tools[name]
                result = tool["function"](**input_data)
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "id": id_value,
                    "error": {
                        "code": -32603,
                        "message": f"Error calling tool {name}: {str(e)}"
                    }
                })
        elif method == "mcp.shutdown":
            result = {}
        else:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": id_value,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })
        
        return JSONResponse(content={
            "jsonrpc": "2.0",
            "id": id_value,
            "result": result
        })
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

def main():
    """Run the simple HTTP server."""
    try:
        logger.info("Starting simple HTTP server for kubectl-mcp-tool")
        
        # Run the server
        uvicorn.run(app, host="127.0.0.1", port=8080)
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
