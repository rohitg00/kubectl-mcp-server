#!/usr/bin/env python3
"""
Test script for kubectl_mcp_server.py
Simulates MCP requests to verify server functionality
"""

import asyncio
import json
import sys
from subprocess import Popen, PIPE
import uuid

async def simulate_mcp_conversation(proc):
    """Simulate an MCP conversation with the server."""
    # Send initialization request
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
    
    print("Sending initialization request...")
    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()
    
    # Wait for response
    init_response = await asyncio.get_event_loop().run_in_executor(None, proc.stdout.readline)
    print(f"Received initialization response: {init_response.strip()}")
    
    # List tools
    list_tools_request = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/list",
        "params": {}
    }
    
    print("Sending tools/list request...")
    proc.stdin.write(json.dumps(list_tools_request) + "\n")
    proc.stdin.flush()
    
    # Wait for response
    list_tools_response = await asyncio.get_event_loop().run_in_executor(None, proc.stdout.readline)
    print(f"Received tools response: {list_tools_response.strip()}")
    
    # Parse the response to get available tools
    try:
        tools_resp = json.loads(list_tools_response)
        if "result" in tools_resp and "tools" in tools_resp["result"]:
            print(f"Available tools: {[tool['name'] for tool in tools_resp['result']['tools']]}")
        else:
            print("No tools found in the response")
    except json.JSONDecodeError:
        print("Failed to parse tools response")
    
    # Call the get_current_context tool
    call_tool_request = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "get_current_context",
            "arguments": {}
        }
    }
    
    print("Sending tools/call request for get_current_context...")
    proc.stdin.write(json.dumps(call_tool_request) + "\n")
    proc.stdin.flush()
    
    # Wait for response
    call_tool_response = await asyncio.get_event_loop().run_in_executor(None, proc.stdout.readline)
    print(f"Received tool call response: {call_tool_response.strip()}")
    
    # Try to parse the response to see cluster information
    try:
        resp = json.loads(call_tool_response)
        if "result" in resp and "result" in resp["result"] and len(resp["result"]["result"]) > 0:
            context_info = resp["result"]["result"][0]["text"]
            print("\n--- Kubernetes Cluster Connection Info ---")
            print(context_info)
            print("----------------------------------------\n")
        else:
            print("No cluster information found in the response")
    except json.JSONDecodeError:
        print("Failed to parse context response")
    
    # Call the get_namespaces tool
    call_tool_request = {
        "jsonrpc": "2.0",
        "id": "4",
        "method": "tools/call",
        "params": {
            "name": "get_namespaces",
            "arguments": {}
        }
    }
    
    print("Sending tools/call request for get_namespaces...")
    proc.stdin.write(json.dumps(call_tool_request) + "\n")
    proc.stdin.flush()
    
    # Wait for response
    call_tool_response = await asyncio.get_event_loop().run_in_executor(None, proc.stdout.readline)
    print(f"Received namespaces response: {call_tool_response.strip()}")

async def main():
    """Main test function."""
    print("Starting kubectl MCP server test...")
    
    # Start the server process
    proc = Popen(
        ["python", "kubectl_mcp_server.py"],
        stdin=PIPE,
        stdout=PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1
    )
    
    try:
        await simulate_mcp_conversation(proc)
    finally:
        print("Terminating server...")
        proc.terminate()
        await asyncio.get_event_loop().run_in_executor(None, proc.wait)
        print("Test completed.")

if __name__ == "__main__":
    asyncio.run(main()) 