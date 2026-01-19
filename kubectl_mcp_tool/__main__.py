#!/usr/bin/env python3
"""
Main entry point for the kubectl MCP tool.
"""

import asyncio
import argparse
import logging
import sys
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from .mcp_server import MCPServer

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("mcp-server-main")

def main():
    """Run the kubectl MCP server."""
    parser = argparse.ArgumentParser(description="Run the Kubectl MCP Server.")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "http", "streamable-http"],
        default="stdio",
        help="Communication transport to use (stdio, sse, http, or streamable-http). Default: stdio.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to use for SSE/HTTP transport. Default: 8000.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to for SSE/HTTP transport. Default: 0.0.0.0.",
    )
    parser.add_argument(
        "--non-destructive",
        action="store_true",
        help="Block destructive operations (delete, apply, create, etc.).",
    )
    args = parser.parse_args()

    server_name = "kubernetes"
    mcp_server = MCPServer(name=server_name, non_destructive=args.non_destructive)

    loop = asyncio.get_event_loop()
    try:
        if args.transport == "stdio":
            logger.info(f"Starting {server_name} with stdio transport.")
            loop.run_until_complete(mcp_server.serve_stdio())
        elif args.transport == "sse":
            logger.info(f"Starting {server_name} with SSE transport on {args.host}:{args.port}.")
            loop.run_until_complete(mcp_server.serve_sse(host=args.host, port=args.port))
        elif args.transport in ("http", "streamable-http"):
            logger.info(f"Starting {server_name} with HTTP transport on {args.host}:{args.port}.")
            loop.run_until_complete(mcp_server.serve_http(host=args.host, port=args.port))
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user.")
    except Exception as e:
        logger.error(f"Server exited with error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down server.")

if __name__ == "__main__":
    main()
