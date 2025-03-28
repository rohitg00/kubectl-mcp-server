#!/usr/bin/env python3
"""
MCP server implementation for kubectl with comprehensive Kubernetes operations support.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List

# Use FastMCP for the higher-level API
from mcp.server.fastmcp import FastMCP
from kubernetes import client, config

# Configure logging
log_file = os.path.expanduser("~/kubectl-mcp.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('kubectl-mcp')

class KubectlServer:
    def __init__(self):
        # Use FastMCP instead of Server
        self.mcp = FastMCP(name='kubectl-mcp')
        try:
            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            logger.info("Successfully initialized Kubernetes client")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            self.v1 = None
            self.apps_v1 = None
        
        # Register tools using FastMCP's decorator
        self.setup_tools()

    def setup_tools(self):
        @self.mcp.tool()
        def get_pods(namespace: str) -> Dict[str, Any]:
            """List all pods in a namespace"""
            if not self.v1:
                return {"error": "Kubernetes client not initialized"}
            try:
                pods = self.v1.list_namespaced_pod(namespace)
                return {"pods": [pod.metadata.name for pod in pods.items]}
            except Exception as e:
                logger.error(f"Error getting pods: {e}")
                return {"error": str(e)}

        @self.mcp.tool()
        def get_namespaces() -> Dict[str, Any]:
            """List all namespaces"""
            if not self.v1:
                return {"error": "Kubernetes client not initialized"}
            try:
                namespaces = self.v1.list_namespace()
                return {"namespaces": [ns.metadata.name for ns in namespaces.items]}
            except Exception as e:
                logger.error(f"Error getting namespaces: {e}")
                return {"error": str(e)}

    async def serve_stdio(self):
        """Serve using stdio transport"""
        logger.info("Starting kubectl MCP server with stdio transport")
        await self.mcp.run_stdio_async()

async def main():
    logger.info("Starting kubectl MCP server")
    server = KubectlServer()
    try:
        await server.serve_stdio()
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 