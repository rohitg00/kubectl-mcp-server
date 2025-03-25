#!/usr/bin/env python3
"""
Test script for Windsurf integration with fixed FastMCP server.
"""

import json
import logging
import os
import subprocess
import sys
import time
import requests
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_fixed_fastmcp_windsurf.log"
)
logger = logging.getLogger("test-fixed-fastmcp-windsurf")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def main():
    """Run the Windsurf integration test."""
    try:
        print("Testing Windsurf integration with fixed FastMCP server...")
        
        # Start the server process
        server_path = os.path.join(os.getcwd(), "fixed_fastmcp_server.py")
        
        if not os.path.exists(server_path):
            print(f"Server script not found at {server_path}")
            return
        
        print(f"Starting server: {server_path}")
        
        # Create a modified version of the server that serves over HTTP
        with open("fixed_fastmcp_http_server.py", "w") as f:
            with open(server_path, "r") as source:
                content = source.read()
                # Replace main function to use HTTP instead of stdio
                content = content.replace(
                    "def main():",
                    """def main():
    \"\"\"Run the fixed FastMCP server over HTTP.\"\"\"
    try:
        logger.info("Starting fixed FastMCP server over HTTP")
        
        # Create the server
        server = FixedFastMCPServer("kubectl-mcp-tool")
        
        # Register Kubernetes tools
        server.register_kubernetes_tools()
        
        # Create FastAPI app
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        import uvicorn
        
        app = FastAPI()
        
        @app.post("/mcp")
        async def mcp_endpoint(request: Request):
            \"\"\"MCP endpoint.\"\"\"
            try:
                message = await request.json()
                response = server.process_message(message)
                
                return JSONResponse(content=response)
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                )
        
        # Run the server
        uvicorn.run(app, host="127.0.0.1", port=8080)"""
                )
        
        # Make the script executable
        os.chmod("fixed_fastmcp_http_server.py", 0o755)
        
        # Start the HTTP server
        server_proc = subprocess.Popen(
            [sys.executable, "fixed_fastmcp_http_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give the server time to start
        print("Waiting for server to start...")
        time.sleep(5)
        
        # Check if the server is running
        try:
            response = requests.get("http://127.0.0.1:8080/docs")
            if response.status_code == 200:
                print("Server is running")
            else:
                print(f"Server returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print("Failed to connect to server")
            if server_proc.poll() is not None:
                print(f"Server process exited with code: {server_proc.returncode}")
                stderr = server_proc.stderr.read().decode()
                print(f"Server stderr: {stderr}")
            return
        
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
                    "name": "windsurf",
                    "version": "1.0.0"
                }
            }
        }
        
        response = requests.post(
            "http://127.0.0.1:8080/mcp",
            json=initialize_message
        )
        
        if response.status_code == 200:
            initialize_response = response.json()
            print(f"Initialize response: {json.dumps(initialize_response, indent=2)}")
        else:
            print(f"Initialize request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            server_proc.terminate()
            return
        
        # Send tool discovery request
        print("\nSending tool discovery request...")
        
        discovery_message = {
            "jsonrpc": "2.0",
            "id": "discovery-1",
            "method": "mcp.tool.discovery",
            "params": {}
        }
        
        response = requests.post(
            "http://127.0.0.1:8080/mcp",
            json=discovery_message
        )
        
        if response.status_code == 200:
            discovery_response = response.json()
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
            print(f"Discovery request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            server_proc.terminate()
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
        
        response = requests.post(
            "http://127.0.0.1:8080/mcp",
            json=tool_call_message
        )
        
        if response.status_code == 200:
            tool_call_response = response.json()
            print(f"Tool call response: {json.dumps(tool_call_response, indent=2)}")
        else:
            print(f"Tool call request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
        
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
        
        response = requests.post(
            "http://127.0.0.1:8080/mcp",
            json=nlp_message
        )
        
        if response.status_code == 200:
            nlp_response = response.json()
            print(f"NLP response: {json.dumps(nlp_response, indent=2)}")
        else:
            print(f"NLP request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Send shutdown request
        print("\nSending shutdown request...")
        
        shutdown_message = {
            "jsonrpc": "2.0",
            "id": "shutdown-1",
            "method": "mcp.shutdown",
            "params": {}
        }
        
        response = requests.post(
            "http://127.0.0.1:8080/mcp",
            json=shutdown_message
        )
        
        if response.status_code == 200:
            shutdown_response = response.json()
            print(f"Shutdown response: {json.dumps(shutdown_response, indent=2)}")
        else:
            print(f"Shutdown request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
        
        # Terminate the server
        server_proc.terminate()
        
        print("\nTest completed")
    except Exception as e:
        print(f"Error in test: {e}")
        if 'server_proc' in locals():
            server_proc.terminate()

if __name__ == "__main__":
    main()
