#!/usr/bin/env python3
"""
Test script for the simplified kubectl MCP server
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, List

async def simulate_mcp_conversation():
    """Simulate a conversation with the MCP server."""
    print("Starting simplified kubectl MCP server test...")
    
    # Start the server process
    process = subprocess.Popen(
        ["python", "simple_kubectl_mcp.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    
    # Wait for server to initialize
    time.sleep(1)
    
    try:
        # Send initialization request
        print("Sending initialization request...")
        init_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "test-client",
                    "version": "0.1.0"
                },
                "capabilities": {}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        init_response = json.loads(process.stdout.readline())
        print(f"Received initialization response: {json.dumps(init_response)}")
        
        # Send tools/list request
        print("Sending tools/list request...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": "2",
            "method": "tools/list"
        }
        
        process.stdin.write(json.dumps(tools_request) + "\n")
        tools_response = json.loads(process.stdout.readline())
        print(f"Received tools response: {json.dumps(tools_response)}")
        
        # Extract and display tool names
        tools = [tool["name"] for tool in tools_response["result"]["tools"]]
        print(f"Available tools: {tools}")
        
        # Test each tool
        for tool_name in tools:
            print(f"\nTesting tool: {tool_name}")
            
            # Prepare arguments based on tool name
            args = {}
            if tool_name == "get_pods":
                args = {"namespace": "default"}
            elif tool_name == "kubectl":
                args = {"command": "get nodes"}
                
            # Send tool call request
            tool_request = {
                "jsonrpc": "2.0",
                "id": "3",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args
                }
            }
            
            process.stdin.write(json.dumps(tool_request) + "\n")
            tool_response = json.loads(process.stdout.readline())
            print(f"Response for {tool_name}:")
            
            # Extract and display text result
            if "result" in tool_response and "result" in tool_response["result"]:
                for item in tool_response["result"]["result"]:
                    if item["type"] == "text":
                        print(f"\n{item['text']}")
            
            # Wait a bit between requests
            await asyncio.sleep(0.5)
            
        print("\nTest completed successfully.")
        
    finally:
        # Clean up
        print("Terminating server...")
        process.terminate()
        process.wait(timeout=5)

def main():
    """Main entry point."""
    asyncio.run(simulate_mcp_conversation())

if __name__ == "__main__":
    main() 