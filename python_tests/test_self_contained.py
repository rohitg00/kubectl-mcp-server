#!/usr/bin/env python3
"""
Self-contained test script for FastMCP implementation.
This script tests both Cursor and Windsurf compatible servers.
"""

import json
import logging
import os
import subprocess
import sys
import time
import asyncio
import httpx
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_self_contained.log"
)
logger = logging.getLogger("test-self-contained")

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

def test_cursor_integration():
    """Test Cursor integration with FastMCP."""
    print("\n=== Testing Cursor Integration with FastMCP ===")
    
    # Create a temporary script that imports the necessary modules
    temp_script = """
#!/usr/bin/env python3
import sys
import logging
from kubectl_mcp_tool.fastmcp_server import KubectlMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("temp-cursor-server")

# Create the server
server = KubectlMCPServer("kubectl-mcp-tool")

# Serve over stdio
server.serve_stdio()
"""
    
    with open("temp_cursor_server.py", "w") as f:
        f.write(temp_script)
    
    os.chmod("temp_cursor_server.py", 0o755)
    
    # Start the server
    try:
        proc = subprocess.Popen(
            ["python3", "temp_cursor_server.py"],
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
                    "name": "cursor",
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
        
        return True
        
    except Exception as e:
        print(f"Error during Cursor test: {e}")
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
        if os.path.exists("temp_cursor_server.py"):
            os.remove("temp_cursor_server.py")

async def test_windsurf_integration():
    """Test Windsurf integration with FastMCP."""
    print("\n=== Testing Windsurf Integration with FastMCP ===")
    
    # Create a temporary script that imports the necessary modules
    temp_script = """
#!/usr/bin/env python3
import asyncio
import sys
import logging
from kubectl_mcp_tool.fastmcp_server import KubectlMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("temp-windsurf-server")

async def main():
    # Create the server
    server = KubectlMCPServer("kubectl-mcp-tool")
    
    # Serve over SSE
    await server.serve_sse(port=8080)

if __name__ == "__main__":
    asyncio.run(main())
"""
    
    with open("temp_windsurf_server.py", "w") as f:
        f.write(temp_script)
    
    os.chmod("temp_windsurf_server.py", 0o755)
    
    # Start the server
    proc = None
    try:
        proc = subprocess.Popen(
            ["python3", "temp_windsurf_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give the server time to start
        print("Starting Windsurf server...")
        time.sleep(3)
        
        # Test the server using httpx
        print("Testing server with httpx...")
        
        # Initialize the server
        async with httpx.AsyncClient() as client:
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
                        "name": "windsurf",
                        "version": "1.0.0"
                    }
                }
            }
            
            try:
                print("Sending initialize request...")
                response = await client.post(
                    "http://localhost:8080/jsonrpc",
                    json=initialize_message,
                    timeout=5.0
                )
                
                if response.status_code != 200:
                    print(f"Failed to initialize server: {response.status_code}")
                    return False
                
                initialize_response = response.json()
                
                if "result" not in initialize_response:
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
                response = await client.post(
                    "http://localhost:8080/jsonrpc",
                    json=tools_list_message,
                    timeout=5.0
                )
                
                if response.status_code != 200:
                    print(f"Failed to list tools: {response.status_code}")
                    return False
                
                tools_list_response = response.json()
                
                if "result" not in tools_list_response or "tools" not in tools_list_response["result"]:
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
                response = await client.post(
                    "http://localhost:8080/jsonrpc",
                    json=tool_call_message,
                    timeout=5.0
                )
                
                if response.status_code != 200:
                    print(f"Failed to call tool: {response.status_code}")
                    return False
                
                tool_call_response = response.json()
                
                if "result" not in tool_call_response:
                    print("Failed to call tool")
                    return False
                
                print("Tool call successful:")
                print(f"Command: {tool_call_response['result'].get('command', 'unknown')}")
                print(f"Result: {tool_call_response['result'].get('result', 'unknown')}")
                
                return True
                
            except httpx.RequestError as e:
                print(f"Error during Windsurf test: {e}")
                return False
            
    except Exception as e:
        print(f"Error during Windsurf test: {e}")
        return False
    finally:
        # Clean up
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        
        # Remove temporary script
        if os.path.exists("temp_windsurf_server.py"):
            os.remove("temp_windsurf_server.py")

def test_cli_output():
    """Test CLI output formatting."""
    print("\n=== Testing CLI Output Formatting ===")
    
    try:
        # Create a temporary script to test CLI output
        temp_script = """
#!/usr/bin/env python3
from kubectl_mcp_tool.cli_output import format_pod_list, format_namespace_list
import json

# Sample pod data
pod_data = '''
{
    "items": [
        {
            "metadata": {
                "name": "nginx-pod",
                "namespace": "default"
            },
            "status": {
                "phase": "Running",
                "containerStatuses": [
                    {
                        "name": "nginx",
                        "ready": true,
                        "restartCount": 0
                    }
                ]
            }
        },
        {
            "metadata": {
                "name": "redis-pod",
                "namespace": "default"
            },
            "status": {
                "phase": "Pending",
                "containerStatuses": [
                    {
                        "name": "redis",
                        "ready": false,
                        "restartCount": 2
                    }
                ]
            }
        }
    ]
}
'''

# Sample namespace data
namespace_data = '''
{
    "items": [
        {
            "metadata": {
                "name": "default"
            },
            "status": {
                "phase": "Active"
            }
        },
        {
            "metadata": {
                "name": "kube-system"
            },
            "status": {
                "phase": "Active"
            }
        }
    ]
}
'''

# Test pod list formatting
print("\\n=== Pod List Formatting ===")
pods = json.loads(pod_data)
formatted_pods = format_pod_list(pods)
print(formatted_pods)

# Test namespace list formatting
print("\\n=== Namespace List Formatting ===")
namespaces = json.loads(namespace_data)
formatted_namespaces = format_namespace_list(namespaces)
print(formatted_namespaces)
"""
        
        with open("temp_cli_output_test.py", "w") as f:
            f.write(temp_script)
        
        os.chmod("temp_cli_output_test.py", 0o755)
        
        # Run the script
        result = subprocess.run(
            ["python3", "temp_cli_output_test.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"CLI output test failed: {result.stderr}")
            return False
        
        print("CLI output test results:")
        print(result.stdout)
        
        return True
        
    except Exception as e:
        print(f"Error during CLI output test: {e}")
        return False
    finally:
        # Remove temporary script
        if os.path.exists("temp_cli_output_test.py"):
            os.remove("temp_cli_output_test.py")

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

async def main():
    """Run all tests."""
    print("=== Running FastMCP Implementation Tests ===")
    
    # Test Cursor integration
    cursor_success = test_cursor_integration()
    
    # Test Windsurf integration
    windsurf_success = await test_windsurf_integration()
    
    # Test CLI output formatting
    cli_output_success = test_cli_output()
    
    # Test natural language processing
    nlp_success = test_natural_language()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Cursor Integration: {'PASS' if cursor_success else 'FAIL'}")
    print(f"Windsurf Integration: {'PASS' if windsurf_success else 'FAIL'}")
    print(f"CLI Output Formatting: {'PASS' if cli_output_success else 'FAIL'}")
    print(f"Natural Language Processing: {'PASS' if nlp_success else 'FAIL'}")
    
    # Return overall success
    return cursor_success and windsurf_success and cli_output_success and nlp_success

if __name__ == "__main__":
    asyncio.run(main())
