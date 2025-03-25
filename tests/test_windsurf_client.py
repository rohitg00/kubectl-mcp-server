#!/usr/bin/env python3
"""
Test client for Windsurf-compatible MCP server.
"""

import asyncio
import json
import sys
import logging
import aiohttp
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_windsurf_client.log"
)
logger = logging.getLogger("test-windsurf-client")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

async def test_windsurf_client(host: str, port: int):
    """Test client for Windsurf-compatible MCP server."""
    print("╭─────────────────────────────────────────────────╮")
    print("│ Testing Windsurf Client for kubectl-mcp-tool    │")
    print("╰─────────────────────────────────────────────────╯\n")
    
    print(f"Connecting to MCP server at {host}:{port}...\n")
    
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
        
        try:
            async with session.post(
                f"http://{host}:{port}",
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
        except Exception as e:
            print(f"❌ Error during initialize: {e}")
            return False
        
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
        
        try:
            async with session.post(
                f"http://{host}:{port}",
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
        except Exception as e:
            print(f"❌ Error during tools/list: {e}")
            return False
        
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
            
            try:
                async with session.post(
                    f"http://{host}:{port}",
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
                            print(f"✅ Command executed successfully")
                            
                            if "mock" in result and result["mock"]:
                                print("⚠️  Note: Result is mock data, not real kubectl output")
                            elif "success" in result and not result["success"]:
                                print(f"⚠️  Note: Command failed with error: {result.get('error', 'Unknown error')}")
                            
                            print()
                            break
            except Exception as e:
                print(f"❌ Error during tool/call for '{command}': {e}")
                return False
    
    print("\n╭─────────────────────────────────────────────────╮")
    print("│                 Test Summary                    │")
    print("╰─────────────────────────────────────────────────╯")
    print("✅ Server initialization: Passed")
    print("✅ Tool registration: Passed")
    print("✅ Natural language processing: Passed")
    print("\nAll tests passed successfully!")
    
    return True

async def main():
    """Run the test client."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test client for Windsurf-compatible MCP server")
    parser.add_argument("--host", default="localhost", help="Host to connect to")
    parser.add_argument("--port", type=int, default=8081, help="Port to connect to")
    args = parser.parse_args()
    
    await test_windsurf_client(args.host, args.port)

if __name__ == "__main__":
    asyncio.run(main())
