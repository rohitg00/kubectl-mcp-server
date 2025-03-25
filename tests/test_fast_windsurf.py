#!/usr/bin/env python3
"""
Test script for Windsurf integration with FastMCP.
"""

import asyncio
import json
import logging
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_fast_windsurf.log"
)
logger = logging.getLogger("test-fast-windsurf")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

async def test_windsurf_integration(host="localhost", port=8080):
    """Test Windsurf integration with FastMCP."""
    print(f"Testing Windsurf integration with FastMCP at {host}:{port}...")
    
    async with aiohttp.ClientSession() as session:
        # Initialize the server
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
        
        print("Sending initialize request...")
        
        try:
            async with session.post(
                f"http://{host}:{port}",
                json=initialize_request,
                headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status != 200:
                    print(f"Failed to connect to server: {response.status}")
                    return
                
                # Read the SSE response
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        
                        if "result" not in data:
                            print("Invalid initialize response")
                            return
                        
                        print("Server initialized successfully")
                        break
        except Exception as e:
            print(f"Error during initialize: {e}")
            return
        
        # List tools
        tools_list_request = {
            "jsonrpc": "2.0",
            "id": "tools",
            "method": "mcp.tools.list"
        }
        
        print("Sending tools/list request...")
        
        try:
            async with session.post(
                f"http://{host}:{port}",
                json=tools_list_request,
                headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status != 200:
                    print(f"Failed to connect to server: {response.status}")
                    return
                
                # Read the SSE response
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        
                        if "result" not in data or "tools" not in data["result"]:
                            print("Invalid tools/list response")
                            return
                        
                        tools = data["result"]["tools"]
                        print(f"Found {len(tools)} tools:")
                        for tool in tools:
                            print(f"- {tool['name']}: {tool['description']}")
                        break
        except Exception as e:
            print(f"Error during tools/list: {e}")
            return
        
        # Test natural language processing
        tool_call_request = {
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
        
        print("Sending tool/call request...")
        
        try:
            async with session.post(
                f"http://{host}:{port}",
                json=tool_call_request,
                headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status != 200:
                    print(f"Failed to connect to server: {response.status}")
                    return
                
                # Read the SSE response
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        data = json.loads(line[6:])
                        
                        if "result" not in data:
                            print("Invalid tool/call response")
                            return
                        
                        print("Tool call successful:")
                        print(f"Command: {data['result'].get('command', 'unknown')}")
                        print(f"Result: {data['result'].get('result', 'unknown')}")
                        break
        except Exception as e:
            print(f"Error during tool/call: {e}")
            return

if __name__ == "__main__":
    asyncio.run(test_windsurf_integration())
