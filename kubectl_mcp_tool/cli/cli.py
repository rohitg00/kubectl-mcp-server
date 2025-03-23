#!/usr/bin/env python3
"""
CLI module for kubectl-mcp-tool.
"""

import sys
import os
import logging
import asyncio
import argparse
import traceback
from ..mcp_server import MCPServer

# Configure logging with file and console output
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=os.path.join(LOG_DIR, "kubectl_mcp_tool_cli.log")
)
logger = logging.getLogger("kubectl-mcp-tool-cli")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

async def serve_stdio():
    """Serve the MCP server over stdio transport."""
    logger.info("Starting standard MCP server with stdio transport")
    try:
        server = MCPServer("kubectl-mcp-tool")
        await server.serve_stdio()
    except Exception as e:
        logger.error(f"Error in stdio server: {e}")
        logger.error(traceback.format_exc())
        raise

async def serve_sse(port: int):
    """Serve the MCP server over SSE transport."""
    logger.info(f"Starting standard MCP server with SSE transport on port {port}")
    try:
        server = MCPServer("kubectl-mcp-tool")
        await server.serve_sse(port)
    except Exception as e:
        logger.error(f"Error in SSE server on port {port}: {e}")
        logger.error(traceback.format_exc())
        raise

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="kubectl MCP tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start the MCP server")
    serve_parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                          help="Transport to use (stdio or sse)")
    serve_parser.add_argument("--port", type=int, default=8080,
                          help="Port to use for SSE transport")
    serve_parser.add_argument("--cursor", action="store_true",
                          help="Enable Cursor compatibility mode")
    serve_parser.add_argument("--debug", action="store_true",
                          help="Enable debug mode with additional logging")
    
    args = parser.parse_args()
    
    # Set up debug mode if requested
    if args.command == "serve" and args.debug:
        console_handler.setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")
    
    exit_code = 0
    
    try:
        if args.command == "serve":
            if args.cursor:
                try:
                    # Import the cursor_mcp_server module
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from cursor_mcp_server import main as cursor_main
                    
                    logger.info("Starting Cursor-compatible MCP server")
                    asyncio.run(cursor_main())
                except ImportError as e:
                    logger.error(f"Error importing cursor_mcp_server module: {e}")
                    logger.error("Make sure cursor_mcp_server.py is in the correct location")
                    exit_code = 1
                except Exception as e:
                    logger.error(f"Error starting Cursor-compatible MCP server: {e}")
                    if args.debug:
                        logger.error(traceback.format_exc())
                    exit_code = 1
            else:
                # Standard MCP server
                try:
                    if args.transport == "stdio":
                        asyncio.run(serve_stdio())
                    else:
                        logger.info(f"Starting SSE server on port {args.port}")
                        asyncio.run(serve_sse(args.port))
                except Exception as e:
                    logger.error(f"Error starting standard MCP server: {e}")
                    if args.debug:
                        logger.error(traceback.format_exc())
                    exit_code = 1
        else:
            parser.print_help()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.command == "serve" and args.debug:
            logger.error(traceback.format_exc())
        exit_code = 1
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
