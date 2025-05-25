#!/usr/bin/env python3
"""
Main entry point for the kubectl MCP tool.
"""

import asyncio
import argparse
import logging
from .mcp_server import MCPServer

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-server-main")

def main():
    """Run the kubectl MCP server."""
    parser = argparse.ArgumentParser(description="Run the Kubectl MCP Server.")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default="stdio",
        help="Communication transport to use (stdio or sse). Default: stdio.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to use for SSE transport. Default: 8080.",
    )
    args = parser.parse_args()

    server_name = "kubernetes"
    mcp_server = MCPServer(name=server_name)

    loop = asyncio.get_event_loop()
    try:
        if args.transport == "stdio":
            logger.info(f"Starting {server_name} with stdio transport.")
            loop.run_until_complete(mcp_server.serve_stdio())
        elif args.transport == "sse":
            logger.info(f"Starting {server_name} with SSE transport on port {args.port}.")
            loop.run_until_complete(mcp_server.serve_sse(port=args.port))
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user.")
    except Exception as e:
        logger.error(f"Server exited with error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down server.")

if __name__ == "__main__":
    main()
