#!/usr/bin/env python3
"""
Minimal MCP server implementation for debugging.
This server accepts JSON commands over stdin and responds with JSON over stdout.
It doesn't depend on any external packages, just using basic Python libraries.
"""

import asyncio
import json
import os
import sys
import traceback
from datetime import datetime

# Create log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Open a debug log file
debug_file = open(os.path.join(LOG_DIR, "simple_mcp_debug.log"), "w")

def log(message):
    """Log a message to both the debug file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    formatted = f"{timestamp} - {message}"
    print(f"DEBUG: {formatted}", file=sys.stderr)
    debug_file.write(f"{formatted}\n")
    debug_file.flush()

log(f"Starting simple MCP server")
log(f"Python version: {sys.version}")
log(f"Current directory: {os.getcwd()}")

# MCP protocol constants
MCP_VERSION = "0.1.0"
SERVER_NAME = "kubectl-mcp-tool-simple"

async def read_stdin():
    """Read a line from stdin asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sys.stdin.readline)

async def run_server():
    """Run the MCP server."""
    log("Starting server loop")
    
    # Send server information on startup to stderr for debugging
    print(f"MCP Server {SERVER_NAME} v{MCP_VERSION} started", file=sys.stderr)
    
    # Respond to initialization
    try:
        # First message should be initialization
        log("Waiting for initialization message")
        init_req = await read_stdin()
        log(f"Received init: {init_req.strip()}")
        
        # Parse the request
        try:
            request = json.loads(init_req)
            log(f"Parsed request: {request}")
            
            # Check if it's an initialization request
            if request.get("method") == "initialize":
                # Respond with initialization response
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "name": SERVER_NAME,
                        "version": MCP_VERSION,
                        "serverInfo": {
                            "name": SERVER_NAME
                        },
                        "capabilities": {
                            "tools": [
                                {
                                    "name": "kubectl_command",
                                    "description": "Run a kubectl command",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "command": {
                                                "type": "string",
                                                "description": "The kubectl command to run"
                                            }
                                        },
                                        "required": ["command"]
                                    }
                                },
                                {
                                    "name": "get_pods",
                                    "description": "Get all pods in the current namespace",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "namespace": {
                                                "type": "string",
                                                "description": "Optional namespace"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
                
                log("Sending initialization response")
                print(json.dumps(response), flush=True)
            else:
                log(f"Not an initialization request: {request}")
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id", 0),
                    "error": {
                        "code": -32600,
                        "message": "Expected 'initialize' as first message"
                    }
                }
                print(json.dumps(error_response), flush=True)
        except json.JSONDecodeError as e:
            log(f"Failed to parse JSON: {e}")
            # Send error response
            error_response = {
                "jsonrpc": "2.0",
                "id": 0,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
            
        # Main message loop
        while True:
            log("Waiting for message")
            line = await read_stdin()
            if not line:
                log("Empty line received, exiting")
                break
                
            log(f"Received: {line.strip()}")
            
            try:
                request = json.loads(line)
                request_id = request.get("id", 0)
                
                # Handle method calls
                if request.get("method") == "callTool":
                    params = request.get("params", {})
                    tool_name = params.get("name")
                    tool_params = params.get("parameters", {})
                    
                    log(f"Tool call: {tool_name} with params {tool_params}")
                    
                    # Simple response depending on the tool
                    if tool_name == "kubectl_command":
                        cmd = tool_params.get("command", "")
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "command": cmd,
                                "output": f"Simulated output for: {cmd}",
                                "success": True
                            }
                        }
                    elif tool_name == "get_pods":
                        namespace = tool_params.get("namespace", "default")
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "namespace": namespace,
                                "pods": [
                                    {"name": "pod-1", "status": "Running"},
                                    {"name": "pod-2", "status": "Running"}
                                ]
                            }
                        }
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32601,
                                "message": f"Unknown tool: {tool_name}"
                            }
                        }
                # Handle shutdown
                elif request.get("method") == "shutdown":
                    log("Shutdown request received")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": None
                    }
                    print(json.dumps(response), flush=True)
                    break
                else:
                    log(f"Unknown method: {request.get('method')}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {request.get('method')}"
                        }
                    }
                
                log(f"Sending response: {response}")
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                log(f"Failed to parse JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                log(f"Error processing request: {e}\n{traceback.format_exc()}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id", 0) if "request" in locals() else 0,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
    
    except Exception as e:
        log(f"Fatal error: {e}\n{traceback.format_exc()}")
    finally:
        log("Server shutting down")
        debug_file.close()

if __name__ == "__main__":
    try:
        # Set env var for unbuffered output
        os.environ["PYTHONUNBUFFERED"] = "1"
        
        # Run the server
        asyncio.run(run_server())
    except KeyboardInterrupt:
        log("Server stopped by keyboard interrupt")
    except Exception as e:
        log(f"Fatal error: {e}\n{traceback.format_exc()}")
    finally:
        if "debug_file" in globals() and not debug_file.closed:
            debug_file.close() 