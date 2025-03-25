#!/usr/bin/env python3
"""
Minimal test script for FastMCP implementation.
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
    filename="test_fastmcp_minimal.log"
)
logger = logging.getLogger("test-fastmcp-minimal")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_natural_language():
    """Test natural language processing."""
    print("\n=== Testing Natural Language Processing ===")
    
    try:
        # Create a temporary script to test natural language processing
        temp_script = """
#!/usr/bin/env python3
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module
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

def test_fastmcp_server():
    """Test FastMCP server implementation."""
    print("\n=== Testing FastMCP Server Implementation ===")
    
    try:
        # Create a temporary script to test FastMCP server
        temp_script = """
#!/usr/bin/env python3
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module
from kubectl_mcp_tool.fastmcp_server import KubectlMCPServer

# Create the server
server = KubectlMCPServer("kubectl-mcp-tool")

# Print server information
print(f"Server name: {server.mcp.name}")
print(f"Server tools: {len(server.mcp.list_tools())}")
for tool in server.mcp.list_tools():
    print(f"- {tool}")

print("\\nServer initialization successful!")
"""
        
        with open("temp_fastmcp_server_test.py", "w") as f:
            f.write(temp_script)
        
        os.chmod("temp_fastmcp_server_test.py", 0o755)
        
        # Run the script
        result = subprocess.run(
            ["python3", "temp_fastmcp_server_test.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"FastMCP server test failed: {result.stderr}")
            return False
        
        print("FastMCP server test results:")
        print(result.stdout)
        
        return True
        
    except Exception as e:
        print(f"Error during FastMCP server test: {e}")
        return False
    finally:
        # Remove temporary script
        if os.path.exists("temp_fastmcp_server_test.py"):
            os.remove("temp_fastmcp_server_test.py")

if __name__ == "__main__":
    # Test natural language processing
    nlp_success = test_natural_language()
    
    # Test FastMCP server implementation
    fastmcp_success = test_fastmcp_server()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Natural Language Processing: {'PASS' if nlp_success else 'FAIL'}")
    print(f"FastMCP Server Implementation: {'PASS' if fastmcp_success else 'FAIL'}")
    
    # Return overall success
    sys.exit(0 if nlp_success and fastmcp_success else 1)
