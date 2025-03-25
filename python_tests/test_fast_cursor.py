#!/usr/bin/env python3
"""
Test script for Cursor integration with SimpleMCPServer.
"""

import json
import logging
import subprocess
import sys
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_fast_cursor.log"
)
logger = logging.getLogger("test-fast-cursor")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def send_message(proc, message: Dict[str, Any]):
    """Send a message to the MCP server."""
    json_message = json.dumps(message) + "\n"
    logger.debug(f"Sending: {json_message.strip()}")
    proc.stdin.write(json_message)
    proc.stdin.flush()

def read_message(proc) -> Optional[Dict[str, Any]]:
    """Read a message from the MCP server."""
    line = proc.stdout.readline().strip()
    if not line:
        return None
    
    logger.debug(f"Received: {line}")
    
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {line} - {e}")
        return None

def test_cursor_integration():
    """Test Cursor integration with SimpleMCPServer."""
    print("Testing Cursor integration with SimpleMCPServer...")
    
    # Start the server
    try:
        proc = subprocess.Popen(
            ["python3", "fast_cursor_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Give the server time to start
        time.sleep(1)
        
        # Initialize the server
        initialize_message = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "mcp.initialize",
            "params": {
                "capabilities": {
                    "tools": {
                        "supported": True
                    }
                },
                "client_info": {
                    "name": "cursor",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialize request...")
        send_message(proc, initialize_message)
        initialize_response = read_message(proc)
        
        if not initialize_response or "result" not in initialize_response:
            print("Failed to initialize server")
            return
        
        print("Server initialized successfully")
        print(f"Server name: {initialize_response['result']['name']}")
        print(f"Server version: {initialize_response['result']['version']}")
        
        # List tools
        tools_list_message = {
            "jsonrpc": "2.0",
            "id": "tools",
            "method": "mcp.tools.list"
        }
        
        print("\nSending tools/list request...")
        send_message(proc, tools_list_message)
        tools_list_response = read_message(proc)
        
        if not tools_list_response or "result" not in tools_list_response or "tools" not in tools_list_response["result"]:
            print("Failed to list tools")
            return
        
        tools = tools_list_response["result"]["tools"]
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"- {tool['name']}: {tool['description']}")
        
        # Test natural language processing
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": "call",
            "method": "mcp.tool.call",
            "params": {
                "name": "process_natural_language",
                "input": {
                    "query": "get all pods"
                }
            }
        }
        
        print("\nSending tool/call request...")
        send_message(proc, tool_call_message)
        tool_call_response = read_message(proc)
        
        if not tool_call_response or "result" not in tool_call_response:
            print("Failed to call tool")
            return
        
        print("Tool call successful:")
        print(f"Command: {tool_call_response['result'].get('command', 'unknown')}")
        print(f"Result: {tool_call_response['result'].get('result', 'unknown')}")
        
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Clean up
        if 'proc' in locals():
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

if __name__ == "__main__":
    test_cursor_integration()
