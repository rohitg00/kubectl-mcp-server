#!/usr/bin/env python3
"""
Test script for FastMCP implementation.
"""

import json
import logging
import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_fastmcp.log"
)
logger = logging.getLogger("test-fastmcp")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def send_message(proc, message: Dict[str, Any]):
    """Send a message to the MCP server."""
    json_message = json.dumps(message) + "\n"
    logger.debug(f"Sending: {json_message.strip()}")
    proc.stdin.write(json_message)
    proc.stdin.flush()

def read_message(proc) -> Optional[Dict[str, Any]]:
    """Read a message from the MCP server."""
    line = proc.stdout.readline().strip()
    if not line:
        return None
    
    logger.debug(f"Received: {line}")
    
    try:
        return json.loads(line)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {line} - {e}")
        return None

def test_fastmcp_implementation():
    """Test FastMCP implementation."""
    print("=== Testing FastMCP Implementation ===")
    
    # Create a temporary script that imports the necessary modules
    temp_script = """
#!/usr/bin/env python3
import sys
import logging
from kubectl_mcp_tool.fastmcp_server import KubectlMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("temp-fastmcp-server")

# Create the server
server = KubectlMCPServer("kubectl-mcp-tool")

# Serve over stdio
server.serve_stdio()
"""
    
    with open("temp_fastmcp_server.py", "w") as f:
        f.write(temp_script)
    
    os.chmod("temp_fastmcp_server.py", 0o755)
    
    # Start the server
    try:
        proc = subprocess.Popen(
            ["python3", "temp_fastmcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Give the server time to start
        time.sleep(1)
        
        # Initialize the server
        initialize_message = {
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
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("Sending initialize request...")
        send_message(proc, initialize_message)
        initialize_response = read_message(proc)
        
        if not initialize_response or "result" not in initialize_response:
            print("Failed to initialize server")
            return False
        
        print("Server initialized successfully")
        print(f"Server name: {initialize_response['result']['name']}")
        print(f"Server version: {initialize_response['result']['version']}")
        
        # List tools
        tools_list_message = {
            "jsonrpc": "2.0",
            "id": "tools",
            "method": "mcp.tools.list"
        }
        
        print("\nSending tools/list request...")
        send_message(proc, tools_list_message)
        tools_list_response = read_message(proc)
        
        if not tools_list_response or "result" not in tools_list_response or "tools" not in tools_list_response["result"]:
            print("Failed to list tools")
            return False
        
        tools = tools_list_response["result"]["tools"]
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"- {tool['name']}")
        
        # Test natural language processing
        tool_call_message = {
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
        
        print("\nSending tool/call request...")
        send_message(proc, tool_call_message)
        tool_call_response = read_message(proc)
        
        if not tool_call_response or "result" not in tool_call_response:
            print("Failed to call tool")
            return False
        
        print("Tool call successful:")
        print(f"Command: {tool_call_response['result'].get('command', 'unknown')}")
        print(f"Result: {tool_call_response['result'].get('result', 'unknown')}")
        
        # Test get_pods tool
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": "call",
            "method": "mcp.tool.call",
            "params": {
                "name": "get_pods",
                "input": {
                    "namespace": "default"
                }
            }
        }
        
        print("\nSending get_pods tool/call request...")
        send_message(proc, tool_call_message)
        tool_call_response = read_message(proc)
        
        if not tool_call_response or "result" not in tool_call_response:
            print("Failed to call get_pods tool")
            return False
        
        print("get_pods tool call successful:")
        print(f"Command: {tool_call_response['result'].get('command', 'unknown')}")
        print(f"Result: {tool_call_response['result'].get('result', 'unknown')}")
        
        # Test get_namespaces tool
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": "call",
            "method": "mcp.tool.call",
            "params": {
                "name": "get_namespaces",
                "input": {}
            }
        }
        
        print("\nSending get_namespaces tool/call request...")
        send_message(proc, tool_call_message)
        tool_call_response = read_message(proc)
        
        if not tool_call_response or "result" not in tool_call_response:
            print("Failed to call get_namespaces tool")
            return False
        
        print("get_namespaces tool call successful:")
        print(f"Command: {tool_call_response['result'].get('command', 'unknown')}")
        print(f"Result: {tool_call_response['result'].get('result', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"Error during test: {e}")
        return False
    finally:
        # Clean up
        if 'proc' in locals():
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        
        # Remove temporary script
        if os.path.exists("temp_fastmcp_server.py"):
            os.remove("temp_fastmcp_server.py")

def test_natural_language():
    """Test natural language processing."""
    print("\n=== Testing Natural Language Processing ===")
    
    try:
        # Create a temporary script to test natural language processing
        temp_script = """
#!/usr/bin/env python3
from kubectl_mcp_tool.natural_language import process_query

# Test queries
queries = [
    "get all pods",
    "show namespaces",
    "describe pod nginx-pod in namespace default",
    "scale deployment nginx to 3 replicas",
    "switch to namespace kube-system",
    "get logs from pod nginx-pod container nginx"
]

for query in queries:
    print(f"\\n=== Query: {query} ===")
    result = process_query(query)
    print(f"Command: {result['command']}")
    print(f"Result: {result['result']}")
"""
        
        with open("temp_nlp_test.py", "w") as f:
            f.write(temp_script)
        
        os.chmod("temp_nlp_test.py", 0o755)
        
        # Run the script
        result = subprocess.run(
            ["python3", "temp_nlp_test.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Natural language test failed: {result.stderr}")
            return False
        
        print("Natural language test results:")
        print(result.stdout)
        
        return True
        
    except Exception as e:
        print(f"Error during natural language test: {e}")
        return False
    finally:
        # Remove temporary script
        if os.path.exists("temp_nlp_test.py"):
            os.remove("temp_nlp_test.py")

if __name__ == "__main__":
    # Test FastMCP implementation
    fastmcp_success = test_fastmcp_implementation()
    
    # Test natural language processing
    nlp_success = test_natural_language()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"FastMCP Implementation: {'PASS' if fastmcp_success else 'FAIL'}")
    print(f"Natural Language Processing: {'PASS' if nlp_success else 'FAIL'}")
    
    # Return overall success
    sys.exit(0 if fastmcp_success and nlp_success else 1)
