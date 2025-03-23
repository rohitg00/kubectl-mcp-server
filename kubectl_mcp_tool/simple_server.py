#!/usr/bin/env python3
"""
MCP server implementation for kubectl with comprehensive Kubernetes operations support.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List

from fastmcp.server import Server
from fastmcp.models import Tool, Parameter, ParameterType
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

class KubectlServer(Server):
    def __init__(self):
        super().__init__()
        self.name = 'kubectl-mcp'
        self.version = '0.1.0'
        try:
            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            logger.info("Successfully initialized Kubernetes client")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            self.v1 = None
            self.apps_v1 = None

    async def get_tools(self):
        return [
            Tool(
                name="get_pods",
                description="List all pods in a namespace",
                parameters=[
                    Parameter(
                        name="namespace",
                        type=ParameterType.STRING,
                        description="Kubernetes namespace",
                        required=True
                    )
                ]
            ),
            Tool(
                name="get_namespaces",
                description="List all namespaces",
                parameters=[]
            )
        ]

    async def call_tool(self, tool_name: str, parameters: dict):
        logger.info(f'Calling tool {tool_name} with params {parameters}')
        try:
            if tool_name == "get_pods":
                return await self.get_pods(parameters["namespace"])
            elif tool_name == "get_namespaces":
                return await self.get_namespaces()
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.error(f'Error calling tool {tool_name}: {e}')
            return {"error": str(e)}

    async def get_pods(self, namespace: str):
        if not self.v1:
            return {"error": "Kubernetes client not initialized"}
        try:
            pods = self.v1.list_namespaced_pod(namespace)
            return {"pods": [pod.metadata.name for pod in pods.items]}
        except Exception as e:
            logger.error(f"Error getting pods: {e}")
            return {"error": str(e)}

    async def get_namespaces(self):
        if not self.v1:
            return {"error": "Kubernetes client not initialized"}
        try:
            namespaces = self.v1.list_namespace()
            return {"namespaces": [ns.metadata.name for ns in namespaces.items]}
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}")
            return {"error": str(e)}

async def main():
    logger.info("Starting kubectl MCP server")
    server = KubectlServer()
    try:
        await server.stdio_server()
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 