#!/usr/bin/env python3
"""CLI module for kubectl-mcp-tool."""

import sys
import os
import logging
import asyncio
import argparse
import traceback
from ..mcp_server import MCPServer

log_file = os.environ.get("MCP_LOG_FILE")
log_level = logging.DEBUG if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true") else logging.INFO

handlers = []
if log_file:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handlers.append(logging.FileHandler(log_file))
handlers.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers
)
logger = logging.getLogger("kubectl-mcp-cli")


async def serve_stdio():
    """Serve the MCP server over stdio transport."""
    server = MCPServer("kubernetes")
    await server.serve_stdio()


async def serve_sse(host: str, port: int):
    """Serve the MCP server over SSE transport."""
    server = MCPServer("kubernetes")
    await server.serve_sse(host=host, port=port)


async def serve_http(host: str, port: int):
    """Serve the MCP server over HTTP transport."""
    server = MCPServer("kubernetes")
    await server.serve_http(host=host, port=port)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="kubectl-mcp-tool - MCP server for Kubernetes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kubectl-mcp serve                          # stdio transport (Claude Desktop/Cursor)
  kubectl-mcp serve --transport sse          # SSE transport
  kubectl-mcp serve --transport http         # HTTP transport
  kubectl-mcp diagnostics                    # Run cluster diagnostics
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    serve_parser = subparsers.add_parser("serve", help="Start the MCP server")
    serve_parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http", "streamable-http"],
        default="stdio",
        help="Transport to use (default: stdio)"
    )
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for SSE/HTTP (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port for SSE/HTTP (default: 8000)")
    serve_parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers.add_parser("version", help="Show version")
    subparsers.add_parser("diagnostics", help="Run cluster diagnostics")

    args = parser.parse_args()

    if hasattr(args, 'debug') and args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        os.environ["MCP_DEBUG"] = "1"

    try:
        if args.command == "serve":
            if args.transport == "stdio":
                asyncio.run(serve_stdio())
            elif args.transport == "sse":
                asyncio.run(serve_sse(args.host, args.port))
            elif args.transport in ("http", "streamable-http"):
                asyncio.run(serve_http(args.host, args.port))
        elif args.command == "version":
            from .. import __version__
            print(f"kubectl-mcp-tool version {__version__}")
        elif args.command == "diagnostics":
            from ..diagnostics import run_diagnostics
            import json
            results = run_diagnostics()
            print(json.dumps(results, indent=2))
        else:
            parser.print_help()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Error: {e}")
        if hasattr(args, 'debug') and args.debug:
            logger.error(traceback.format_exc())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
