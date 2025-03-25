#!/usr/bin/env python3
"""
Simple test for FastMCP server implementation.
"""

import logging
import sys
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="simple_fastmcp_test.log"
)
logger = logging.getLogger("simple-fastmcp-test")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_fastmcp_server():
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
        
        # Check if tool_registry exists
        if hasattr(server, 'tool_registry'):
            print(f"Server tools: {len(server.tool_registry.tools)}")
            for tool in server.tool_registry.tools:
                print(f"- {tool}")
        elif hasattr(server, 'tools'):
            print(f"Server tools: {len(server.tools)}")
            for tool in server.tools:
                print(f"- {tool}")
        else:
            print("Server has no tools attribute or tool_registry attribute")
            print(f"Available attributes: {dir(server)}")
        
        return True
    except Exception as e:
        print(f"Error testing FastMCP server: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the simple FastMCP test."""
    try:
        # Test FastMCP server
        fastmcp_result = test_fastmcp_server()
        
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

if __name__ == "__main__":
    sys.exit(main())
