#!/usr/bin/env python3
"""
Fixed test for FastMCP server implementation.
"""

import logging
import os
import sys
import tempfile
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="fixed_fastmcp_test.log"
)
logger = logging.getLogger("fixed-fastmcp-test")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_fastmcp_server():
    """Test the FastMCP server implementation."""
    print("\n=== Testing FastMCP Server Implementation ===")
    
    # Create a temporary file for the server script
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        script_content = """
#!/usr/bin/env python3
import logging
import sys
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP, Context
from kubectl_mcp_tool.natural_language import process_query

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("temp-fastmcp-server")

# Create FastMCP server
server = FastMCP("kubectl-mcp-tool")

# Register tools
@server.tool()
def process_natural_language(query: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Process natural language queries for kubectl operations."""
    logger.info(f"Processing natural language query: {query}")
    result = process_query(query)
    return result

@server.tool()
def get_pods(namespace: str = "default", ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Get pods in the specified namespace."""
    logger.info(f"Getting pods in namespace: {namespace}")
    result = process_query(f"get pods in namespace {namespace}")
    return result

# Print server info
print(f"Server name: {server.name}")
print(f"Server tools: {len(server.tool_registry.tools)}")
for tool in server.tool_registry.tools:
    print(f"- {tool}")
"""
        temp_file.write(script_content.encode('utf-8'))
        temp_file_path = temp_file.name
    
    try:
        # Run the server script
        import subprocess
        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check the result
        if result.returncode == 0:
            print("FastMCP server test passed:")
            print(result.stdout)
            return True
        else:
            print("FastMCP server test failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error testing FastMCP server: {e}")
        return False
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

def main():
    """Run the fixed FastMCP test."""
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
        return 1

if __name__ == "__main__":
    sys.exit(main())
