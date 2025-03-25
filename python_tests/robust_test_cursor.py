#!/usr/bin/env python3
"""
Robust test script for Cursor integration with kubectl-mcp-tool.
"""

import json
import logging
import os
import subprocess
import sys
import time
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="robust_test_cursor.log"
)
logger = logging.getLogger("robust-test-cursor")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def send_message(proc: subprocess.Popen, message: Dict[str, Any]) -> bool:
    """Send a message to the MCP server process."""
    try:
        message_str = json.dumps(message) + "\n"
        logger.debug(f"Sending message: {message_str.strip()}")
        proc.stdin.write(message_str.encode())
        proc.stdin.flush()
        return True
    except BrokenPipeError:
        logger.error("Broken pipe when sending message")
        return False
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False

def read_message(proc: subprocess.Popen, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Read a message from the MCP server process with timeout."""
    try:
        # Set stdin to non-blocking mode
        import fcntl
        import os
        import select
        
        fd = proc.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        # Wait for data with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            ready, _, _ = select.select([proc.stdout], [], [], 0.1)
            
            if ready:
                line = proc.stdout.readline().decode().strip()
                
                if not line:
                    time.sleep(0.1)
                    continue
                
                logger.debug(f"Received message: {line}")
                
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON: {line}")
                    return None
            
            # Check if process is still running
            if proc.poll() is not None:
                logger.error(f"Process exited with code {proc.returncode}")
                return None
            
            time.sleep(0.1)
        
        logger.error(f"Timeout waiting for response after {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Error reading message: {e}")
        return None

def test_cursor_integration():
    """Test Cursor integration with kubectl-mcp-tool."""
    try:
        print("Testing Cursor integration with kubectl-mcp-tool...")
        
        # Start the server process
        server_path = os.path.join(os.getcwd(), "fast_cursor_server.py")
        
        if not os.path.exists(server_path):
            print(f"Server script not found at {server_path}")
            return
        
        print(f"Starting server: {server_path}")
        
        proc = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=False
        )
        
        # Give the server time to start
        time.sleep(2)
        
        # Check if process is still running
        if proc.poll() is not None:
            print(f"Server process exited with code {proc.returncode}")
            stderr = proc.stderr.read().decode()
            print(f"Server stderr: {stderr}")
            return
        
        print("Server started successfully")
        
        # Send initialize request
        print("Sending initialize request...")
        
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
        
        if not send_message(proc, initialize_message):
            print("Failed to send initialize message")
            proc.terminate()
            return
        
        # Read initialize response
        initialize_response = read_message(proc)
        
        if not initialize_response:
            print("Failed to receive initialize response")
            proc.terminate()
            return
        
        print(f"Initialize response: {json.dumps(initialize_response, indent=2)}")
        
        # Send tool discovery request
        print("Sending tool discovery request...")
        
        discovery_message = {
            "jsonrpc": "2.0",
            "id": "discovery",
            "method": "mcp.tool.discovery",
            "params": {}
        }
        
        if not send_message(proc, discovery_message):
            print("Failed to send discovery message")
            proc.terminate()
            return
        
        # Read discovery response
        discovery_response = read_message(proc)
        
        if not discovery_response:
            print("Failed to receive discovery response")
            proc.terminate()
            return
        
        print(f"Discovery response: {json.dumps(discovery_response, indent=2)}")
        
        # Get tool names
        tools = discovery_response.get("result", {}).get("tools", [])
        
        if not tools:
            print("No tools found in discovery response")
            proc.terminate()
            return
        
        print(f"Found {len(tools)} tools:")
        
        for i, tool in enumerate(tools, 1):
            tool_name = tool.get("name", "Unknown")
            tool_description = tool.get("description", "No description")
            print(f"{i}. {tool_name}: {tool_description}")
        
        # Test a tool call
        print("\nTesting tool call...")
        
        # Find a tool for natural language processing
        nlp_tool = None
        
        for tool in tools:
            if "natural" in tool.get("name", "").lower() or "query" in tool.get("name", "").lower():
                nlp_tool = tool
                break
        
        if not nlp_tool:
            print("No natural language processing tool found")
            proc.terminate()
            return
        
        tool_name = nlp_tool.get("name", "")
        print(f"Using tool: {tool_name}")
        
        # Send tool call request
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": "call",
            "method": "mcp.tool.call",
            "params": {
                "name": tool_name,
                "input": {
                    "query": "get all pods"
                }
            }
        }
        
        if not send_message(proc, tool_call_message):
            print("Failed to send tool call message")
            proc.terminate()
            return
        
        # Read tool call response
        tool_call_response = read_message(proc, timeout=10)
        
        if not tool_call_response:
            print("Failed to receive tool call response")
            proc.terminate()
            return
        
        print(f"Tool call response: {json.dumps(tool_call_response, indent=2)}")
        
        # Test shutdown
        print("\nTesting shutdown...")
        
        shutdown_message = {
            "jsonrpc": "2.0",
            "id": "shutdown",
            "method": "mcp.shutdown",
            "params": {}
        }
        
        if not send_message(proc, shutdown_message):
            print("Failed to send shutdown message")
            proc.terminate()
            return
        
        # Read shutdown response
        shutdown_response = read_message(proc)
        
        if not shutdown_response:
            print("Failed to receive shutdown response")
            proc.terminate()
            return
        
        print(f"Shutdown response: {json.dumps(shutdown_response, indent=2)}")
        
        # Wait for process to exit
        try:
            proc.wait(timeout=5)
            print(f"Server process exited with code {proc.returncode}")
        except subprocess.TimeoutExpired:
            print("Server process did not exit, terminating...")
            proc.terminate()
        
        print("Test completed successfully")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        if 'proc' in locals():
            proc.terminate()
    except Exception as e:
        print(f"Error during test: {e}")
        if 'proc' in locals():
            proc.terminate()

if __name__ == "__main__":
    test_cursor_integration()
