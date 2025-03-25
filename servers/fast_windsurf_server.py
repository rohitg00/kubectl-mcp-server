#!/usr/bin/env python3
"""
Windsurf-compatible MCP server using FastMCP for kubectl-mcp-tool.
"""

import asyncio
import logging
import sys

from kubectl_mcp_tool.fastmcp_server import KubectlMCPServer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="fast_windsurf_server.log"
)
logger = logging.getLogger("fast-windsurf-server")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

async def main():
    """Run the Windsurf-compatible MCP server."""
    try:
        logger.info("Starting Windsurf-compatible MCP server with FastMCP")
        
        # Create the server
        server = KubectlMCPServer("kubectl-mcp-tool")
        
        # Serve over SSE
        await server.serve_sse(port=8080)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
