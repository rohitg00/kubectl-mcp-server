#!/usr/bin/env python3
"""
CLI module for kubectl-mcp-tool.

Provides command-line interface for starting and managing the MCP server.
"""

import sys
import os
import logging
import asyncio
import argparse
import traceback
from ..mcp_server import MCPServer

# Configure logging
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
    logger.info("Starting MCP server with stdio transport")
    try:
        server = MCPServer("kubernetes")
        await server.serve_stdio()
    except Exception as e:
        logger.error(f"Error in stdio server: {e}")
        logger.error(traceback.format_exc())
        raise


async def serve_sse(host: str, port: int):
    """Serve the MCP server over SSE transport."""
    logger.info(f"Starting MCP server with SSE transport on {host}:{port}")
    try:
        server = MCPServer("kubernetes")
        await server.serve_sse(host=host, port=port)
    except Exception as e:
        logger.error(f"Error in SSE server on {host}:{port}: {e}")
        logger.error(traceback.format_exc())
        raise


async def serve_http(host: str, port: int):
    """Serve the MCP server over HTTP transport."""
    logger.info(f"Starting MCP server with HTTP transport on {host}:{port}")
    try:
        server = MCPServer("kubernetes")
        await server.serve_http(host=host, port=port)
    except Exception as e:
        logger.error(f"Error in HTTP server on {host}:{port}: {e}")
        logger.error(traceback.format_exc())
        raise


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="kubectl-mcp-tool - MCP server for Kubernetes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start server with stdio transport (default, for Claude Desktop/Cursor)
  kubectl-mcp serve
  
  # Start server with SSE transport on port 8000
  kubectl-mcp serve --transport sse --port 8000
  
  # Start server with HTTP transport
  kubectl-mcp serve --transport http --host 0.0.0.0 --port 8000
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the MCP server")
    serve_parser.add_argument(
        "--transport", 
        choices=["stdio", "sse", "http", "streamable-http"],
        default="stdio",
        help="Transport to use. Default: stdio"
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind for SSE/HTTP transport. Default: 0.0.0.0"
    )
    serve_parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port for SSE/HTTP transport. Default: 8000"
    )
    serve_parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode with verbose logging"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version")
    
    # Diagnostics command
    diag_parser = subparsers.add_parser("diagnostics", help="Run diagnostics")
    
    args = parser.parse_args()
    
    # Set up debug mode if requested
    if hasattr(args, 'debug') and args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        os.environ["MCP_DEBUG"] = "1"
        logger.info("Debug mode enabled")
    
    exit_code = 0
    
    try:
        if args.command == "serve":
            try:
                if args.transport == "stdio":
                    asyncio.run(serve_stdio())
                elif args.transport == "sse":
                    asyncio.run(serve_sse(args.host, args.port))
                elif args.transport in ("http", "streamable-http"):
                    asyncio.run(serve_http(args.host, args.port))
            except Exception as e:
                logger.error(f"Error starting MCP server: {e}")
                if args.debug:
                    logger.error(traceback.format_exc())
                exit_code = 1
                
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
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if hasattr(args, 'debug') and args.debug:
            logger.error(traceback.format_exc())
        exit_code = 1
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
