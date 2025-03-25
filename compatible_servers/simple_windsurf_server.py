#!/usr/bin/env python3
"""
Windsurf-compatible MCP server for kubectl-mcp-tool.
"""

import logging
import sys
from typing import Any, Dict

# Update the import to reference the module from the same directory
from .simplified_mcp_implementation import SimpleMCPServer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="simple_windsurf_server.log"
)
logger = logging.getLogger("simple-windsurf-server")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def process_query(query: str) -> Dict[str, Any]:
    """Process a natural language query and return the result."""
    try:
        # Implement your natural language processing logic here
        # This is a simplified example
        if "pods" in query:
            return {
                "command": "kubectl get pods",
                "result": "NAME              READY   STATUS    RESTARTS   AGE\nnginx-pod          1/1     Running   0          10m\napi-pod            1/1     Running   0          5m"
            }
        elif "namespace" in query:
            return {
                "command": "kubectl get namespaces",
                "result": "NAME              STATUS   AGE\ndefault           Active   1d\nkube-system       Active   1d\nkube-public       Active   1d"
            }
        else:
            return {
                "command": f"kubectl {query}",
                "result": "Command executed successfully."
            }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return {
            "command": f"kubectl {query}",
            "error": str(e)
        }

def main():
    """Run the Windsurf-compatible MCP server."""
    try:
        logger.info("Starting Windsurf-compatible MCP server")
        
        # Create the server
        server = SimpleMCPServer("kubectl-mcp-tool")
        
        # Register tools
        server.register_tool("process_natural_language", {
            "description": "Process a natural language query for kubectl operations",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The natural language query to process"
                    }
                },
                "required": ["query"]
            }
        }, process_query)
        
        # Serve over stdio
        server.serve_sse(port=8080)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
