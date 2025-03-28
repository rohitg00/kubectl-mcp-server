#!/usr/bin/env python3
"""
Debug wrapper for kubectl-mcp server when run by Cursor.
This script captures detailed logs and handles common errors.
"""

import os
import sys
import time
import traceback
import logging
import shutil
import signal
import atexit
import json

# Set up debug logging to a file
log_dir = os.path.expanduser("~/.cursor/logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "kubectl_mcp_debug.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("cursor-wrapper")

def check_environment():
    """Check environment variables and file permissions."""
    logger.info("----- Environment Check -----")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python path: {sys.path}")
    
    # Check kubectl
    kubectl_path = shutil.which("kubectl")
    if kubectl_path:
        logger.info(f"kubectl found at: {kubectl_path}")
    else:
        logger.error("kubectl not found in PATH")
    
    # Check kubeconfig
    kube_config = os.environ.get('KUBECONFIG', '~/.kube/config')
    expanded_path = os.path.expanduser(kube_config)
    logger.info(f"KUBECONFIG: {kube_config} (expanded: {expanded_path})")
    
    if os.path.exists(expanded_path):
        logger.info(f"Kubernetes config exists at {expanded_path}")
        # Check permissions
        try:
            with open(expanded_path, 'r') as f:
                logger.info("Successfully opened kubeconfig file")
        except Exception as e:
            logger.error(f"Failed to read kubeconfig: {e}")
    else:
        logger.error(f"Kubernetes config does not exist at {expanded_path}")
    
    # List all environment variables
    logger.info("Environment variables:")
    for key, value in sorted(os.environ.items()):
        if key.lower() in ('path', 'pythonpath', 'kubeconfig'):
            logger.info(f"{key}: {value}")
        # Skip logging other env vars for security

    # Test kubectl
    try:
        import subprocess
        result = subprocess.run(
            ["kubectl", "version", "--client"],
            capture_output=True,
            text=True
        )
        logger.info(f"kubectl version result: {result.returncode}")
        logger.info(f"kubectl version output: {result.stdout}")
        if result.stderr:
            logger.warning(f"kubectl stderr: {result.stderr}")
    except Exception as e:
        logger.error(f"Failed to run kubectl: {e}")

def run_direct_mcp_server():
    """Run a direct FastMCP server for better compatibility with Cursor."""
    try:
        logger.info("Creating direct FastMCP server for Cursor")
        # Import the modules needed for the server
        from mcp.server.fastmcp import FastMCP
        from kubectl_mcp_tool.natural_language import process_query
        
        # Create a FastMCP server with explicit name
        server = FastMCP(name="kubectl-mcp")
        logger.info("FastMCP server created successfully")
        
        # Register the natural language processing tool
        @server.tool(
            name="process_natural_language",
            description="Process natural language query for kubectl",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The natural language query to process"
                    }
                },
                "required": ["query"]
            }
        )
        async def process_natural_language(query: str):
            """Process natural language query for kubectl."""
            logger.info(f"Received query from Cursor: {query}")
            result = process_query(query)
            logger.info(f"Result: {result}")
            return json.dumps(result)
        
        # Register a simple ping tool to help with debugging
        @server.tool(
            name="kubernetes_ping",
            description="Ping the kubernetes server to check if it's working"
        )
        async def kubernetes_ping():
            """Simple ping tool for testing connectivity."""
            logger.info("Ping received from Cursor")
            return "Kubernetes MCP server is working!"
        
        # Start the server using stdio transport
        logger.info("Starting FastMCP server with stdio transport")
        import asyncio
        
        # Handle clean exit
        def cleanup():
            logger.info("Shutting down MCP server")
        
        atexit.register(cleanup)
        
        # Run the server
        asyncio.run(server.run_stdio_async())
    except Exception as e:
        logger.error(f"Error running direct MCP server: {e}")
        logger.error(traceback.format_exc())
        raise

def run_mcp_server():
    """Run the MCP server with error handling - old version."""
    try:
        logger.info("Importing kubectl_mcp_tool.cli.cli...")
        from kubectl_mcp_tool.cli import cli
        
        logger.info("Starting MCP server...")
        sys.argv = [sys.argv[0], "serve"]
        cli.main()
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error(f"Python path: {sys.path}")
        # Try to import the module using an absolute path
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, project_root)
            logger.info(f"Added {project_root} to sys.path")
            from kubectl_mcp_tool.cli import cli
            sys.argv = [sys.argv[0], "serve"]
            cli.main()
        except Exception as inner_e:
            logger.error(f"Failed second import attempt: {inner_e}")
            logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"Error starting MCP server: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("===== Starting kubectl-mcp debug wrapper =====")
    check_environment()
    # Use the direct FastMCP implementation for better Cursor compatibility
    run_direct_mcp_server() 