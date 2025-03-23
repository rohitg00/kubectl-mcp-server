#!/usr/bin/env python3
"""
Main entry point for the kubectl-mcp-tool CLI.
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

import anyio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    ServerCapabilities,
    ToolsCapability,
    PromptsCapability,
    ResourcesCapability,
    LoggingCapability
)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("kubectl-mcp")

class KubectlServer(Server):
    """Kubectl MCP server implementation."""
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls."""
        if name == "get_pods":
            return await self.get_pods(arguments.get("namespace"))
        elif name == "get_namespaces":
            return await self.get_namespaces()
        return {"success": False, "error": f"Unknown tool: {name}"}
    
    async def get_pods(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get all pods in the specified namespace."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            
            if namespace:
                pods = v1.list_namespaced_pod(namespace)
            else:
                pods = v1.list_pod_for_all_namespaces()
            
            return {
                "success": True,
                "pods": [
                    {
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": pod.status.phase,
                        "ip": pod.status.pod_ip
                    }
                    for pod in pods.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting pods: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_namespaces(self) -> Dict[str, Any]:
        """Get all Kubernetes namespaces."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()
            
            namespaces = v1.list_namespace()
            return {
                "success": True,
                "namespaces": [ns.metadata.name for ns in namespaces.items]
            }
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}")
            return {"success": False, "error": str(e)}

@asynccontextmanager
async def server_lifespan(server: KubectlServer):
    """Server lifespan context manager."""
    # Set up server capabilities
    server.capabilities = ServerCapabilities(
        tools=ToolsCapability(enabled=True),
        prompts=PromptsCapability(enabled=False),
        resources=ResourcesCapability(enabled=False),
        logging=LoggingCapability(enabled=True)
    )
    
    # Register tools
    server.tools = [
        {
            "name": "get_pods",
            "description": "Get all pods in the specified namespace",
            "parameters": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "The Kubernetes namespace (optional)"
                    }
                }
            }
        },
        {
            "name": "get_namespaces",
            "description": "Get all Kubernetes namespaces",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    ]
    
    yield

async def run_server():
    """Run the MCP server."""
    # Create server
    server = KubectlServer(
        name="kubectl-mcp",
        version="0.1.0",
        lifespan=server_lifespan
    )
    
    # Create initialization options
    init_options = InitializationOptions(
        server_name="kubectl-mcp",
        server_version="0.1.0",
        capabilities=ServerCapabilities(
            tools=ToolsCapability(enabled=True),
            prompts=PromptsCapability(enabled=False),
            resources=ResourcesCapability(enabled=False),
            logging=LoggingCapability(enabled=True)
        )
    )
    
    # Start server
    logger.info("Starting MCP server")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)

def main():
    """Main entry point."""
    anyio.run(run_server)

if __name__ == "__main__":
    main() 