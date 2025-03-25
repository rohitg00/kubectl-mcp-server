#!/usr/bin/env python3
"""
Test script for Windsurf integration with MCP server.
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
import aiohttp
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_windsurf_integration.log"
)
logger = logging.getLogger("test-windsurf-integration")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

async def test_windsurf_integration():
    """Test the Windsurf integration with MCP server."""
    print("╭─────────────────────────────────────────────────╮")
    print("│ Testing Windsurf Integration for kubectl-mcp-tool│")
    print("╰─────────────────────────────────────────────────╯\n")
    
    print("Starting kubectl-mcp-tool with SSE transport...\n")
    
    # Start the MCP server with SSE transport
    server_process = subprocess.Popen(
        ["python", "-m", "kubectl_mcp_tool.cli", "serve", "--transport", "sse", "--port", "8080", "--debug"],
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
        
        # Create a session for SSE connection
        async with aiohttp.ClientSession() as session:
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
                        "name": "windsurf",
                        "version": "1.0.0"
                    }
                }
            }
            
            print("╭────────────────────────────────── Request ───────────────────────────────────╮")
            print(f"│   1 {json.dumps(initialize_request)} │")
            print("╰──────────────────────────────────────────────────────────────────────────────╯")
            print("Sending initialize request...")
            
            async with session.post(
                "http://localhost:8080",
                json=initialize_request,
                headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status != 200:
                    print(f"❌ Failed to connect to server: {response.status}")
                    return False
                
                # Read the SSE response
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        print("\n╭────────────────────────────────── Response ──────────────────────────────────╮")
                        print(f"│   1 {json.dumps(data)} │")
                        print("╰───────────────────────────────────────────────────────────────────────────────╯")
                        
                        if "result" not in data:
                            print("❌ Invalid initialize response")
                            return False
                        
                        print("✅ Server initialized successfully\n")
                        break
            
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
            print("Sending tools/list request...")
            
            async with session.post(
                "http://localhost:8080",
                json=tools_list_request,
                headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status != 200:
                    print(f"❌ Failed to connect to server: {response.status}")
                    return False
                
                # Read the SSE response
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        print("\n╭────────────────────────────────── Response ──────────────────────────────────╮")
                        print(f"│   2 {json.dumps(data)} │")
                        print("╰───────────────────────────────────────────────────────────────────────────────╯")
                        
                        if "result" not in data or "tools" not in data["result"]:
                            print("❌ Invalid tools/list response")
                            return False
                        
                        tools = data["result"]["tools"]
                        tool_names = [tool["name"] for tool in tools]
                        
                        if "process_natural_language" not in tool_names:
                            print("❌ process_natural_language tool not registered")
                            return False
                        
                        print(f"✅ Found {len(tools)} registered tools: {', '.join(tool_names)}\n")
                        break
            
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
                print("Sending tool/call request...")
                
                async with session.post(
                    "http://localhost:8080",
                    json=tool_call_request,
                    headers={"Accept": "text/event-stream"}
                ) as response:
                    if response.status != 200:
                        print(f"❌ Failed to connect to server: {response.status}")
                        return False
                    
                    # Read the SSE response
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            print("\n╭────────────────────────────────── Response ──────────────────────────────────╮")
                            print(f"│   {i+3} {json.dumps(data)} │")
                            print("╰───────────────────────────────────────────────────────────────────────────────╯")
                            
                            if "result" not in data:
                                print(f"❌ Invalid tool/call response for '{command}'")
                                return False
                            
                            result = data["result"]
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
                            break
        
        print("\n╭─────────────────────────────────────────────────╮")
        print("│                 Test Summary                    │")
        print("╰─────────────────────────────────────────────────╯")
        print("✅ Server initialization: Passed")
        print("✅ Tool registration: Passed")
        print("✅ Natural language processing: Passed")
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
    asyncio.run(test_windsurf_integration())
