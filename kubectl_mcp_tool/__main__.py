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
    parser.add_argument("--non-destructive", "--disable-destructive", action="store_true", help="Block destructive operations")
    parser.add_argument("--read-only", action="store_true", help="Enable read-only mode (block all write operations)")
    parser.add_argument("--confirm-destructive", action="store_true", help="Require confirmation for destructive operations")
    parser.add_argument("--config", type=str, default=None, help="Path to TOML configuration file")
    args = parser.parse_args()

    server = MCPServer(name="kubernetes", read_only=args.read_only, disable_destructive=args.non_destructive, confirm_destructive=args.confirm_destructive, config_file=args.config)

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
