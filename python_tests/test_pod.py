#!/usr/bin/env python3
"""
Test script for kubectl_mcp_server.py to test pod-related tools
"""

import asyncio
import json
import sys
from subprocess import Popen, PIPE
import uuid

async def test_get_pods(proc):
    """Test getting pods from all namespaces."""
    
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
    
    # Test get_pods with all namespaces
    call_tool_request = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/call",
        "params": {
            "name": "get_pods",
            "arguments": {
                "namespace": "all"
            }
        }
    }
    
    print("Sending tools/call request for get_pods (all namespaces)...")
    proc.stdin.write(json.dumps(call_tool_request) + "\n")
    proc.stdin.flush()
    
    # Wait for response
    call_tool_response = await asyncio.get_event_loop().run_in_executor(None, proc.stdout.readline)
    print(f"Received get_pods response: {call_tool_response.strip()}")
    
    # Parse the response to see pod information
    try:
        resp = json.loads(call_tool_response)
        if "result" in resp and "result" in resp["result"] and len(resp["result"]["result"]) > 0:
            pod_info = resp["result"]["result"][0]["text"]
            print("\n--- Kubernetes Pods (All Namespaces) ---")
            print(pod_info)
            print("----------------------------------------\n")
        else:
            print("No pod information found in the response")
    except json.JSONDecodeError:
        print("Failed to parse pods response")
    
    # Test raw kubectl command to create a test deployment
    call_tool_request = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "kubectl",
            "arguments": {
                "command": "create deployment hello-node --image=registry.k8s.io/e2e-test-images/agnhost:2.39 -- /agnhost netexec --http-port=8080"
            }
        }
    }
    
    print("Sending tools/call request to create a test deployment...")
    proc.stdin.write(json.dumps(call_tool_request) + "\n")
    proc.stdin.flush()
    
    # Wait for response
    call_tool_response = await asyncio.get_event_loop().run_in_executor(None, proc.stdout.readline)
    print(f"Received deployment response: {call_tool_response.strip()}")
    
    # Wait for the pod to start (5 seconds)
    print("Waiting for deployment to start...")
    await asyncio.sleep(5)
    
    # Test get_pods with default namespace
    call_tool_request = {
        "jsonrpc": "2.0",
        "id": "4",
        "method": "tools/call",
        "params": {
            "name": "get_pods",
            "arguments": {
                "namespace": "default"
            }
        }
    }
    
    print("Sending tools/call request for get_pods (default namespace)...")
    proc.stdin.write(json.dumps(call_tool_request) + "\n")
    proc.stdin.flush()
    
    # Wait for response
    call_tool_response = await asyncio.get_event_loop().run_in_executor(None, proc.stdout.readline)
    print(f"Received get_pods response: {call_tool_response.strip()}")
    
    # Parse the response to see pod information
    try:
        resp = json.loads(call_tool_response)
        if "result" in resp and "result" in resp["result"] and len(resp["result"]["result"]) > 0:
            pod_info = resp["result"]["result"][0]["text"]
            print("\n--- Kubernetes Pods (Default Namespace) ---")
            print(pod_info)
            print("----------------------------------------\n")
        else:
            print("No pod information found in the response")
    except json.JSONDecodeError:
        print("Failed to parse pods response")

async def main():
    """Main test function."""
    print("Starting kubectl MCP server pod test...")
    
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
        await test_get_pods(proc)
    finally:
        print("Terminating server...")
        proc.terminate()
        await asyncio.get_event_loop().run_in_executor(None, proc.wait)
        print("Test completed.")

if __name__ == "__main__":
    asyncio.run(main()) 