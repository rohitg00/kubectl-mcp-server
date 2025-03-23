#!/usr/bin/env python3
"""
Simple JSON-RPC based MCP server for kubectl operations.
This server uses standard JSON-RPC 2.0 to handle MCP protocol requests.
"""

import asyncio
import json
import os
import sys
import subprocess
import traceback
from datetime import datetime

# Create logs directory
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Open debug log file
debug_file = open(os.path.join(LOG_DIR, "kubectl_jsonrpc_debug.log"), "w")

def log(message):
    """Write a log message to the debug file and stderr."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    debug_msg = f"{timestamp} - {message}"
    print(f"DEBUG: {debug_msg}", file=sys.stderr)
    debug_file.write(f"{debug_msg}\n")
    debug_file.flush()

log(f"Starting kubectl JSON-RPC server")
log(f"Python version: {sys.version}")
log(f"Current directory: {os.getcwd()}")

# Server information
SERVER_NAME = "kubectl-mcp-tool"
SERVER_VERSION = "0.1.0"

async def read_line():
    """Read a line from stdin asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, sys.stdin.readline)

def write_response(response):
    """Write a response to stdout."""
    json_str = json.dumps(response)
    log(f"Sending response: {json_str}")
    print(json_str, flush=True)

def run_kubectl_command(command):
    """Run a kubectl command and return the result."""
    log(f"Running kubectl command: {command}")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        return {
            "command": command,
            "output": result.stdout.strip(),
            "success": True
        }
    except subprocess.CalledProcessError as e:
        log(f"kubectl command failed: {e}")
        return {
            "command": command,
            "output": e.stderr.strip(),
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        log(f"Error running kubectl command: {e}")
        return {
            "command": command,
            "output": f"Error: {str(e)}",
            "success": False,
            "error": str(e)
        }

def process_natural_language(query):
    """Process a natural language query for kubectl operations."""
    log(f"Processing natural language query: {query}")
    
    query_lower = query.lower()
    
    if "get pods" in query_lower:
        command = "kubectl get pods"
        if "namespace" in query_lower:
            parts = query_lower.split("namespace")
            if len(parts) > 1:
                namespace = parts[1].strip()
                command = f"kubectl get pods -n {namespace}"
        return run_kubectl_command(command)
    
    elif "namespaces" in query_lower:
        command = "kubectl get namespaces"
        return run_kubectl_command(command)
    
    elif "current context" in query_lower:
        command = "kubectl config current-context"
        return run_kubectl_command(command)
        
    else:
        # Try as direct kubectl command
        command = f"kubectl {query}"
        return run_kubectl_command(command)

async def run_server():
    """Run the JSON-RPC server for MCP."""
    log("Starting server loop")
    
    try:
        while True:
            log("Waiting for message")
            line = await read_line()
            if not line:
                log("Empty line received, exiting")
                break
            
            log(f"Received: {line.strip()}")
            
            try:
                request = json.loads(line)
                request_id = request.get("id", 0)
                method = request.get("method")
                
                if method == "initialize":
                    # MCP initialization
                    log("Handling initialize method")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "name": SERVER_NAME,
                            "version": SERVER_VERSION,
                            "capabilities": {
                                "tools": [
                                    {
                                        "name": "process_natural_language",
                                        "description": "Process natural language queries for kubectl operations",
                                        "parameters": {
                                            "type": "object",
                                            "properties": {
                                                "query": {
                                                    "type": "string",
                                                    "description": "Natural language query"
                                                }
                                            },
                                            "required": ["query"]
                                        }
                                    },
                                    {
                                        "name": "get_pods",
                                        "description": "Get all pods in the specified namespace",
                                        "parameters": {
                                            "type": "object",
                                            "properties": {
                                                "namespace": {
                                                    "type": "string",
                                                    "description": "Optional namespace (default: current namespace)"
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
                                        "name": "run_kubectl_command",
                                        "description": "Run a raw kubectl command",
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
                                    }
                                ]
                            }
                        }
                    }
                    write_response(response)
                
                elif method == "callTool":
                    # Tool call handling
                    log("Handling callTool method")
                    params = request.get("params", {})
                    tool_name = params.get("name")
                    tool_params = params.get("parameters", {})
                    
                    log(f"Tool call: {tool_name} with params {tool_params}")
                    
                    if tool_name == "process_natural_language":
                        query = tool_params.get("query", "")
                        result = process_natural_language(query)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
                        }
                    
                    elif tool_name == "get_pods":
                        namespace = tool_params.get("namespace", "")
                        cmd = f"kubectl get pods" + (f" -n {namespace}" if namespace else "")
                        result = run_kubectl_command(cmd)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
                        }
                    
                    elif tool_name == "get_namespaces":
                        result = run_kubectl_command("kubectl get namespaces")
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
                        }
                    
                    elif tool_name == "run_kubectl_command":
                        cmd = tool_params.get("command", "")
                        result = run_kubectl_command(cmd)
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": result
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
                    
                    write_response(response)
                
                elif method == "shutdown":
                    # Handle shutdown request
                    log("Received shutdown request")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": None
                    }
                    write_response(response)
                    break
                
                else:
                    # Unknown method
                    log(f"Unknown method: {method}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    write_response(response)
            
            except json.JSONDecodeError as e:
                log(f"Failed to parse JSON: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                write_response(error_response)
            
            except Exception as e:
                log(f"Error processing request: {e}\n{traceback.format_exc()}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if "request" in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                write_response(error_response)
    
    except Exception as e:
        log(f"Fatal error: {e}\n{traceback.format_exc()}")
    finally:
        log("Server shutting down")

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
        debug_file.close() 