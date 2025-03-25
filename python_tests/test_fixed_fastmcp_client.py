#!/usr/bin/env python3
"""
Test client for fixed FastMCP server implementation.
"""

import json
import logging
import os
import subprocess
import sys
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_fixed_fastmcp_client.log"
)
logger = logging.getLogger("test-fixed-fastmcp-client")

def send_message(proc: subprocess.Popen, message: Dict[str, Any]) -> None:
    """Send a message to the server process."""
    message_str = json.dumps(message) + "\n"
    logger.debug(f"Sending message: {message_str.strip()}")
    proc.stdin.write(message_str.encode())
    proc.stdin.flush()

def read_message(proc: subprocess.Popen) -> Optional[Dict[str, Any]]:
    """Read a message from the server process."""
    try:
        line = proc.stdout.readline().decode().strip()
        if not line:
            return None
        logger.debug(f"Received message: {line}")
        return json.loads(line)
    except Exception as e:
        logger.error(f"Error reading message: {e}")
        return None

def main():
    """Run the test client."""
    try:
        print("Starting test client for fixed FastMCP server...")
        
        # Start the server process
        server_path = os.path.join(os.getcwd(), "fixed_fastmcp_server.py")
        proc = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=False
        )
        
        # Give server time to start
        time.sleep(2)
        
        # Send initialize request
        print("\nSending initialize request...")
        initialize_message = {
            "jsonrpc": "2.0",
            "id": "init-1",
            "method": "mcp.initialize",
            "params": {
                "capabilities": {
                    "tools": {
                        "supported": True
                    }
                },
                "client_info": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        send_message(proc, initialize_message)
        
        # Read initialize response
        initialize_response = read_message(proc)
        if initialize_response:
            print(f"Initialize response: {json.dumps(initialize_response, indent=2)}")
        else:
            print("No initialize response received")
            return
        
        # Send tool discovery request
        print("\nSending tool discovery request...")
        discovery_message = {
            "jsonrpc": "2.0",
            "id": "discovery-1",
            "method": "mcp.tool.discovery",
            "params": {}
        }
        send_message(proc, discovery_message)
        
        # Read discovery response
        discovery_response = read_message(proc)
        if discovery_response:
            print(f"Discovery response: {json.dumps(discovery_response, indent=2)}")
            
            # Get available tools
            tools = discovery_response.get("result", {}).get("tools", [])
            if tools:
                print(f"\nFound {len(tools)} tools:")
                for tool in tools:
                    print(f"- {tool.get('name')}: {tool.get('description')}")
            else:
                print("No tools found")
        else:
            print("No discovery response received")
            return
        
        # Test get_pods tool
        print("\nTesting get_pods tool...")
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": "call-1",
            "method": "mcp.tool.call",
            "params": {
                "name": "get_pods",
                "input": {}
            }
        }
        send_message(proc, tool_call_message)
        
        # Read tool call response
        tool_call_response = read_message(proc)
        if tool_call_response:
            print(f"Tool call response: {json.dumps(tool_call_response, indent=2)}")
        else:
            print("No tool call response received")
        
        # Test natural language processing
        print("\nTesting natural language processing...")
        nlp_message = {
            "jsonrpc": "2.0",
            "id": "call-2",
            "method": "mcp.tool.call",
            "params": {
                "name": "process_natural_language",
                "input": {
                    "query": "get all pods in kube-system namespace"
                }
            }
        }
        send_message(proc, nlp_message)
        
        # Read NLP response
        nlp_response = read_message(proc)
        if nlp_response:
            print(f"NLP response: {json.dumps(nlp_response, indent=2)}")
        else:
            print("No NLP response received")
        
        # Send shutdown request
        print("\nSending shutdown request...")
        shutdown_message = {
            "jsonrpc": "2.0",
            "id": "shutdown-1",
            "method": "mcp.shutdown",
            "params": {}
        }
        send_message(proc, shutdown_message)
        
        # Read shutdown response
        shutdown_response = read_message(proc)
        if shutdown_response:
            print(f"Shutdown response: {json.dumps(shutdown_response, indent=2)}")
        else:
            print("No shutdown response received")
        
        # Wait for server to exit
        try:
            proc.wait(timeout=5)
            print(f"\nServer exited with code: {proc.returncode}")
        except subprocess.TimeoutExpired:
            print("\nServer did not exit, terminating...")
            proc.terminate()
        
        print("\nTest completed")
    except Exception as e:
        print(f"Error in test client: {e}")
        if 'proc' in locals():
            proc.terminate()

if __name__ == "__main__":
    main()
