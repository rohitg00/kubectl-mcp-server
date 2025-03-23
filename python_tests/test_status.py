#!/usr/bin/env python3
"""
Test script for kubectl_mcp_server.py to test cluster status functionality
"""

import asyncio
import json
import sys
from subprocess import Popen, PIPE
import uuid

async def test_cluster_status(proc):
    """Test checking the cluster status."""
    
    # Initialize the server first
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
    
    # Test check_cluster_status 
    call_tool_request = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/call",
        "params": {
            "name": "check_cluster_status",
            "arguments": {}
        }
    }
    
    print("Sending tools/call request for check_cluster_status...")
    proc.stdin.write(json.dumps(call_tool_request) + "\n")
    proc.stdin.flush()
    
    # Wait for response
    call_tool_response = await asyncio.get_event_loop().run_in_executor(None, proc.stdout.readline)
    print(f"Received cluster status response: {call_tool_response.strip()}")
    
    # Parse the response to see cluster status
    try:
        resp = json.loads(call_tool_response)
        if "result" in resp and "result" in resp["result"] and len(resp["result"]["result"]) > 0:
            status_info = resp["result"]["result"][0]["text"]
            print("\n--- Kubernetes Cluster Status ---")
            print(status_info)
            print("----------------------------------------\n")
        else:
            print("No cluster status information found in the response")
    except json.JSONDecodeError:
        print("Failed to parse cluster status response")

async def main():
    """Main test function."""
    print("Starting kubectl MCP server cluster status test...")
    
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
        await test_cluster_status(proc)
    finally:
        print("Terminating server...")
        proc.terminate()
        await asyncio.get_event_loop().run_in_executor(None, proc.wait)
        print("Test completed.")

if __name__ == "__main__":
    asyncio.run(main()) 