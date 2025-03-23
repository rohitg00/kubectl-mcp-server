#!/usr/bin/env python3
"""
Absolutely minimal MCP server implementation.
This implements only the essential parts of the protocol to work with Cursor.
"""

import asyncio
import json
import os
import sys
import subprocess
from datetime import datetime

# Create log directory
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Set up logging
log_file = open(os.path.join(LOG_DIR, "minimal_mcp.log"), "w")

def log(message):
    """Log a message to both the log file and stderr."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    formatted = f"{timestamp} - {message}"
    print(f"LOG: {formatted}", file=sys.stderr)
    log_file.write(f"{formatted}\n")
    log_file.flush()

# Basic server info
SERVER_NAME = "kubectl-mcp-minimal"
SERVER_VERSION = "0.1.0"

# MCP protocol implementation
async def stdio_transport():
    """Create an asyncio transport over stdin/stdout."""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    
    # Handle stdin
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    
    # Handle stdout
    w_transport, w_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(w_transport, w_protocol, None, loop)
    
    return reader, writer

async def read_message(reader):
    """Read a JSON-RPC message from stdin."""
    line = await reader.readline()
    if not line:
        return None
    
    line_str = line.decode('utf-8').strip()
    log(f"RECEIVED: {line_str}")
    
    try:
        return json.loads(line_str)
    except json.JSONDecodeError as e:
        log(f"JSON parse error: {e}")
        return None

def write_message(writer, message):
    """Write a JSON-RPC message to stdout."""
    json_str = json.dumps(message)
    log(f"SENDING: {json_str}")
    writer.write(f"{json_str}\n".encode('utf-8'))

def run_kubectl(command):
    """Run a kubectl command and return the output."""
    log(f"Running kubectl: {command}")
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=False
        )
        success = result.returncode == 0
        output = result.stdout if success else result.stderr
        return {
            "command": command,
            "output": output.strip(),
            "success": success
        }
    except Exception as e:
        log(f"Error running command: {e}")
        return {
            "command": command,
            "output": f"Error: {str(e)}",
            "success": False
        }

async def run_server():
    """Run the MCP server."""
    log("Starting MCP server")
    reader, writer = await stdio_transport()
    
    # Wait for initialize request
    log("Waiting for initialization message")
    
    # Handle messages
    while True:
        message = await read_message(reader)
        if message is None:
            log("Received empty message, shutting down")
            break
        
        method = message.get("method")
        message_id = message.get("id")
        
        if method == "initialize":
            # Handle initialization
            log("Handling initialization request")
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
                    "capabilities": {
                        "tools": [
                            {
                                "name": "run_kubectl",
                                "description": "Run kubectl command",
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
                                "description": "Get pods in the specified namespace",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "namespace": {
                                            "type": "string",
                                            "description": "Namespace to get pods from (optional)"
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            write_message(writer, response)
        
        elif method == "callTool":
            # Handle tool calls
            log("Handling tool call")
            params = message.get("params", {})
            tool_name = params.get("name", "")
            tool_params = params.get("parameters", {})
            
            log(f"Tool call: {tool_name}, params: {tool_params}")
            
            if tool_name == "run_kubectl":
                cmd = tool_params.get("command", "")
                result = run_kubectl(f"kubectl {cmd}")
                response = {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": result
                }
            
            elif tool_name == "get_pods":
                namespace = tool_params.get("namespace", "")
                cmd = "kubectl get pods" + (f" -n {namespace}" if namespace else "")
                result = run_kubectl(cmd)
                response = {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": result
                }
            
            else:
                # Unknown tool
                response = {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }
            
            write_message(writer, response)
        
        elif method == "shutdown":
            # Handle shutdown
            log("Handling shutdown request")
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": None
            }
            write_message(writer, response)
            break
        
        else:
            # Unknown method
            log(f"Unknown method: {method}")
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            write_message(writer, response)
    
    log("Shutting down server")
    await writer.drain()
    writer.close()

if __name__ == "__main__":
    try:
        # Unbuffered output
        os.environ["PYTHONUNBUFFERED"] = "1"
        
        # Run the server
        log(f"Starting server, Python version: {sys.version}")
        log(f"Current directory: {os.getcwd()}")
        asyncio.run(run_server())
    
    except KeyboardInterrupt:
        log("Server stopped by keyboard interrupt")
    except Exception as e:
        log(f"Fatal error: {str(e)}")
    finally:
        log_file.close() 