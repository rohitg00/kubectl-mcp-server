#!/usr/bin/env python3
"""
Simple async test for FastMCP server implementation.
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="simple_async_test.log"
)
logger = logging.getLogger("simple-async-test")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

async def test_fastmcp_server():
    """Test the FastMCP server implementation."""
    print("\n=== Testing FastMCP Server Implementation ===")
    
    try:
        # Import FastMCP
        from mcp.server.fastmcp import FastMCP, Context
        
        # Create FastMCP server
        server = FastMCP("kubectl-mcp-tool")
        
        # Register a tool
        @server.tool()
        def test_tool(param: str = "default", ctx: Optional[Context] = None) -> Dict[str, Any]:
            """Test tool for FastMCP."""
            return {"result": f"Processed: {param}"}
        
        # Print server info
        print(f"Server name: {server.name}")
        
        # Get tools using the async method
        tools = await server.list_tools()
        print(f"Server tools: {len(tools)}")
        for tool in tools:
            print(f"- {tool}")
        
        return True
    except Exception as e:
        print(f"Error testing FastMCP server: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main_async():
    """Run the async FastMCP test."""
    try:
        # Test FastMCP server
        fastmcp_result = await test_fastmcp_server()
        
        # Print summary
        print("\n=== Test Summary ===")
        print(f"FastMCP Server Implementation: {'PASS' if fastmcp_result else 'FAIL'}")
        
        # Return success if all tests passed
        return 0 if fastmcp_result else 1
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Run the main async function."""
    return asyncio.run(main_async())

if __name__ == "__main__":
    sys.exit(main())
