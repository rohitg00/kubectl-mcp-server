#!/usr/bin/env python3
"""
Test script for async FastMCP server implementation.
"""

import asyncio
import json
import logging
import os
import sys
import subprocess
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_async_fastmcp.log"
)
logger = logging.getLogger("test-async-fastmcp")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

async def test_async_fastmcp():
    """Test the async FastMCP server implementation."""
    print("\n=== Testing Async FastMCP Server Implementation ===")
    
    # Create a temporary script to test async FastMCP server
    temp_script = """
#!/usr/bin/env python3
import asyncio
import sys
import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="temp_async_fastmcp.log"
)
logger = logging.getLogger("temp-async-fastmcp")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    # Import the module
    from mcp.server.fastmcp import FastMCP, Context
    
    # Create the server
    server = FastMCP("kubectl-mcp-tool")
    
    # Register a tool
    @server.tool()
    def test_tool(param: str = "default", ctx: Optional[Context] = None) -> Dict[str, Any]:
        """Test tool for FastMCP."""
        return {"result": f"Processed: {param}"}
    
    # Print server information
    print(f"Server name: {server.name}")
    
    # Get tools using the async method
    tools = await server.list_tools()
    print(f"Server tools: {len(tools)}")
    for tool in tools:
        print(f"- {tool}")
    
    print("\\nServer initialization successful!")

if __name__ == "__main__":
    from typing import Dict, Any, Optional
    asyncio.run(main())
"""
    
    with open("temp_async_fastmcp_test.py", "w") as f:
        f.write(temp_script)
    
    os.chmod("temp_async_fastmcp_test.py", 0o755)
    
    # Run the script
    result = subprocess.run(
        ["python3", "temp_async_fastmcp_test.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Async FastMCP server test failed: {result.stderr}")
        return False
    
    print("Async FastMCP server test results:")
    print(result.stdout)
    
    return True

async def test_async_kubectl_mcp_server():
    """Test the AsyncKubectlMCPServer implementation."""
    print("\n=== Testing AsyncKubectlMCPServer Implementation ===")
    
    # Create a temporary script to test AsyncKubectlMCPServer
    temp_script = """
#!/usr/bin/env python3
import asyncio
import sys
import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="temp_async_kubectl_mcp.log"
)
logger = logging.getLogger("temp-async-kubectl-mcp")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    # Import the module
    from async_fastmcp_server import AsyncKubectlMCPServer
    
    # Create the server
    server = AsyncKubectlMCPServer("kubectl-mcp-tool")
    
    # Print server information
    print(f"Server name: {server.mcp.name}")
    
    # Get tools using the async method
    tools = await server.mcp.list_tools()
    print(f"Server tools: {len(tools)}")
    for tool in tools:
        print(f"- {tool}")
    
    print("\\nServer initialization successful!")

if __name__ == "__main__":
    asyncio.run(main())
"""
    
    with open("temp_async_kubectl_mcp_test.py", "w") as f:
        f.write(temp_script)
    
    os.chmod("temp_async_kubectl_mcp_test.py", 0o755)
    
    # Run the script
    result = subprocess.run(
        ["python3", "temp_async_kubectl_mcp_test.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    if result.returncode != 0:
        print(f"AsyncKubectlMCPServer test failed: {result.stderr}")
        return False
    
    print("AsyncKubectlMCPServer test results:")
    print(result.stdout)
    
    return True

async def main_async():
    """Run the async tests."""
    # Test async FastMCP server
    fastmcp_success = await test_async_fastmcp()
    
    # Test AsyncKubectlMCPServer
    kubectl_mcp_success = await test_async_kubectl_mcp_server()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Async FastMCP Server Implementation: {'PASS' if fastmcp_success else 'FAIL'}")
    print(f"AsyncKubectlMCPServer Implementation: {'PASS' if kubectl_mcp_success else 'FAIL'}")
    
    # Return overall success
    return 0 if fastmcp_success and kubectl_mcp_success else 1

def main():
    """Run the main async function."""
    try:
        return asyncio.run(main_async())
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Remove temporary scripts
        for script in ["temp_async_fastmcp_test.py", "temp_async_kubectl_mcp_test.py"]:
            if os.path.exists(script):
                os.remove(script)

if __name__ == "__main__":
    sys.exit(main())
