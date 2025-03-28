#!/usr/bin/env python3
"""
Minimal MCP server for kubectl.
"""

import os
import sys
import json
import logging
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("minimal-mcp")

def run_kubectl_command(command):
    """Run a kubectl command and return the result."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "command": command,
            "result": result.stdout if result.returncode == 0 else result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return {
            "command": command,
            "result": f"Error: {str(e)}",
            "success": False
        }

async def main():
    """Run a simple MCP server."""
    from mcp.server.fastmcp import FastMCP
    
    # Create a FastMCP server
    server = FastMCP("kubectl-mcp")
    
    # Register a simple tool
    @server.tool("process_natural_language")
    async def process_natural_language(query: str):
        """Process natural language query."""
        logger.info(f"Received query: {query}")
        # Simple mapping of queries to kubectl commands
        cmd = "kubectl get all"
        if "pod" in query:
            cmd = "kubectl get pods"
        if "deployment" in query:
            cmd = "kubectl get deployments"
        if "service" in query:
            cmd = "kubectl get services"
        if "namespace" in query.split() and "list" in query:
            cmd = "kubectl get namespaces"
            
        # Run the command
        result = run_kubectl_command(cmd)
        logger.info(f"Command result: {result}")
        return json.dumps(result)
    
    # Register a ping tool
    @server.tool("kubernetes_ping")
    async def kubernetes_ping():
        """Simple ping tool."""
        return "Kubernetes is connected!"
    
    # Start the server with stdio transport
    logger.info("Starting MCP server with stdio transport")
    await server.run_stdio_async()

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1) 