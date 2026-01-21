#!/usr/bin/env python3
"""Main entry point for the kubectl MCP tool."""

import asyncio
import argparse
import logging
import sys
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from .mcp_server import MCPServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("mcp-server")


def main():
    """Run the kubectl MCP server."""
    parser = argparse.ArgumentParser(description="Kubectl MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "http", "streamable-http"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--non-destructive", action="store_true", help="Block destructive operations")
    args = parser.parse_args()

    server = MCPServer(name="kubernetes", non_destructive=args.non_destructive)

    try:
        if args.transport == "stdio":
            asyncio.run(server.serve_stdio())
        elif args.transport == "sse":
            asyncio.run(server.serve_sse(host=args.host, port=args.port))
        elif args.transport in ("http", "streamable-http"):
            asyncio.run(server.serve_http(host=args.host, port=args.port))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
