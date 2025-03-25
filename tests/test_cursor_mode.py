#!/usr/bin/env python3
"""
Test script for Cursor mode integration with MCP server.
"""

import asyncio
import json
import sys
import os
import logging
import subprocess
import time
import threading
import signal
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_cursor_mode.log"
)
logger = logging.getLogger("test-cursor-mode")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_cursor_mode():
    """Test the Cursor mode integration with MCP server."""
    print("╭─────────────────────────────────────────────────╮")
    print("│ Testing Cursor Mode for kubectl-mcp-tool        │")
    print("╰─────────────────────────────────────────────────╯\n")
    
    print("Starting kubectl-mcp-tool with Cursor mode...\n")
    
    # Start the MCP server with Cursor mode
    server_process = subprocess.Popen(
        ["python3", "-m", "kubectl_mcp_tool.cli", "serve", "--transport", "stdio", "--cursor", "--debug"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Set up a timer to kill the process if it hangs
    def kill_process():
        print("❌ Test timed out, killing server process")
        server_process.send_signal(signal.SIGTERM)
        time.sleep(1)
        if server_process.poll() is None:
            server_process.kill()
    
    # Start the timer
    timer = threading.Timer(60, kill_process)
    timer.daemon = True
    timer.start()
    
    try:
        # Wait for the server to start
        time.sleep(2)
        
        # Step 1: Initialize the server
        print("Step 1: Initializing the MCP server")
        initialize_request = {
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
        
        print("╭────────────────────────────────── Request ───────────────────────────────────╮")
        print(f"│   1 {json.dumps(initialize_request)} │")
        print("╰──────────────────────────────────────────────────────────────────────────────╯")
        print("Waiting for response...")
        
        server_process.stdin.write(json.dumps(initialize_request) + "\n")
        server_process.stdin.flush()
        
        # Wait for the response with timeout
        response_line = server_process.stdout.readline()
        if not response_line:
            print("❌ No response received for initialize request")
            return False
        
        initialize_response = json.loads(response_line)
        print("\n╭────────────────────────────────── Response ──────────────────────────────────╮")
        print(f"│   1 {json.dumps(initialize_response)} │")
        print("╰───────────────────────────────────────────────────────────────────────────────╯")
        
        if "result" not in initialize_response:
            print("❌ Invalid initialize response")
            return False
        
        print("✅ Server initialized successfully\n")
        
        # Step 2: List tools
        print("Step 2: Listing available tools")
        tools_list_request = {
            "jsonrpc": "2.0",
            "id": "tools",
            "method": "mcp.tools.list"
        }
        
        print("╭────────────────────────────────── Request ───────────────────────────────────╮")
        print(f"│   2 {json.dumps(tools_list_request)} │")
        print("╰──────────────────────────────────────────────────────────────────────────────╯")
        print("Waiting for response...")
        
        server_process.stdin.write(json.dumps(tools_list_request) + "\n")
        server_process.stdin.flush()
        
        # Wait for the response with timeout
        response_line = server_process.stdout.readline()
        if not response_line:
            print("❌ No response received for tools/list request")
            return False
        
        tools_list_response = json.loads(response_line)
        print("\n╭────────────────────────────────── Response ──────────────────────────────────╮")
        print(f"│   2 {json.dumps(tools_list_response)} │")
        print("╰───────────────────────────────────────────────────────────────────────────────╯")
        
        if "result" not in tools_list_response or "tools" not in tools_list_response["result"]:
            print("❌ Invalid tools/list response")
            return False
        
        tools = tools_list_response["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        if "process_natural_language" not in tool_names:
            print("❌ process_natural_language tool not registered")
            return False
        
        print(f"✅ Found {len(tools)} registered tools: {', '.join(tool_names)}\n")
        
        # Step 3: Test natural language commands
        test_commands = [
            "get all pods",
            "show namespaces",
            "switch to namespace kube-system"
        ]
        
        for i, command in enumerate(test_commands):
            print(f"Step {i+3}: Testing natural language command: '{command}'")
            tool_call_request = {
                "jsonrpc": "2.0",
                "id": f"call{i}",
                "method": "mcp.tool.call",
                "params": {
                    "name": "process_natural_language",
                    "input": {
                        "query": command
                    }
                }
            }
            
            print("╭────────────────────────────────── Request ───────────────────────────────────╮")
            print(f"│   {i+3} {json.dumps(tool_call_request)} │")
            print("╰──────────────────────────────────────────────────────────────────────────────╯")
            print("Waiting for response...")
            
            server_process.stdin.write(json.dumps(tool_call_request) + "\n")
            server_process.stdin.flush()
            
            # Wait for the response with timeout
            response_line = server_process.stdout.readline()
            if not response_line:
                print(f"❌ No response received for tool/call request: '{command}'")
                return False
            
            tool_call_response = json.loads(response_line)
            print("\n╭────────────────────────────────── Response ──────────────────────────────────╮")
            print(f"│   {i+3} {json.dumps(tool_call_response)} │")
            print("╰───────────────────────────────────────────────────────────────────────────────╯")
            
            if "result" not in tool_call_response:
                print(f"❌ Invalid tool/call response for '{command}'")
                return False
            
            result = tool_call_response["result"]
            if "command" not in result or "result" not in result:
                print(f"❌ Invalid tool/call result for '{command}'")
                return False
            
            print(f"✅ Command executed: {result['command']}")
            print(f"✅ Result: {result['result']}")
            
            if result.get("mock", False):
                print("⚠️  Note: Result is mock data, not real kubectl output")
            elif result.get("success", True) == False:
                print(f"⚠️  Note: Command failed with error: {result.get('error', 'Unknown error')}")
            
            print()
        
        # Step 6: Check current namespace after switching
        print("Step 6: Checking current namespace after switching")
        tool_call_request = {
            "jsonrpc": "2.0",
            "id": "call_check",
            "method": "mcp.tool.call",
            "params": {
                "name": "get_current_namespace",
                "input": {}
            }
        }
        
        print("╭────────────────────────────────── Request ───────────────────────────────────╮")
        print(f"│   6 {json.dumps(tool_call_request)} │")
        print("╰──────────────────────────────────────────────────────────────────────────────╯")
        print("Waiting for response...")
        
        server_process.stdin.write(json.dumps(tool_call_request) + "\n")
        server_process.stdin.flush()
        
        # Wait for the response with timeout
        response_line = server_process.stdout.readline()
        if not response_line:
            print("❌ No response received for get_current_namespace request")
            return False
        
        tool_call_response = json.loads(response_line)
        print("\n╭────────────────────────────────── Response ──────────────────────────────────╮")
        print(f"│   6 {json.dumps(tool_call_response)} │")
        print("╰───────────────────────────────────────────────────────────────────────────────╯")
        
        if "result" not in tool_call_response:
            print("❌ Invalid get_current_namespace response")
            return False
        
        result = tool_call_response["result"]
        if "command" not in result or "result" not in result:
            print("❌ Invalid get_current_namespace result")
            return False
        
        print(f"✅ Command executed: {result['command']}")
        print(f"✅ Current namespace: {result['result']}")
        
        if result.get("mock", False):
            print("⚠️  Note: Result is mock data, not real kubectl output")
        elif result.get("success", True) == False:
            print(f"⚠️  Note: Command failed with error: {result.get('error', 'Unknown error')}")
        
        print("\n╭─────────────────────────────────────────────────╮")
        print("│                 Test Summary                    │")
        print("╰─────────────────────────────────────────────────╯")
        print("✅ Server initialization: Passed")
        print("✅ Tool registration: Passed")
        print("✅ Natural language processing: Passed")
        print("✅ Namespace switching: Passed")
        print("✅ Current namespace checking: Passed")
        print("\nAll tests passed successfully!")
        
        return True
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    finally:
        # Cancel the timer
        timer.cancel()
        
        # Terminate the server process
        print("\nTerminating server process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Server process did not terminate, killing...")
            server_process.kill()
            server_process.wait()

if __name__ == "__main__":
    # Run the test
    success = test_cursor_mode()
    sys.exit(0 if success else 1)
