#!/usr/bin/env python3
"""
Async FastMCP server implementation for kubectl-mcp-tool.
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP, Context
from kubectl_mcp_tool.natural_language import process_query

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="async_fastmcp_server.log"
)
logger = logging.getLogger("async-fastmcp-server")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

class AsyncKubectlMCPServer:
    """Async FastMCP-based server for kubectl operations."""
    
    def __init__(self, name: str = "kubectl-mcp-tool"):
        """Initialize the FastMCP server."""
        self.mcp = FastMCP(name)
        self.register_tools()
        logger.info(f"AsyncKubectlMCPServer initialized: {name}")
    
    def register_tools(self):
        """Register all tools with the FastMCP server."""
        # Register the natural language processing tool
        @self.mcp.tool()
        def process_natural_language(query: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Process natural language queries for kubectl operations.
            
            Args:
                query: Natural language query for kubectl operations
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info(f"Processing natural language query: {query}")
            result = process_query(query)
            return result
        
        # Register other kubectl tools
        @self.mcp.tool()
        def get_pods(namespace: str = "default", ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Get pods in the specified namespace.
            
            Args:
                namespace: Namespace to get pods from
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info(f"Getting pods in namespace: {namespace}")
            result = process_query(f"get pods in namespace {namespace}")
            return result
        
        @self.mcp.tool()
        def get_namespaces(ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Get all namespaces.
            
            Args:
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info("Getting namespaces")
            result = process_query("show namespaces")
            return result
        
        @self.mcp.tool()
        def switch_namespace(namespace: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Switch to the specified namespace.
            
            Args:
                namespace: Namespace to switch to
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info(f"Switching to namespace: {namespace}")
            result = process_query(f"switch to namespace {namespace}")
            return result
        
        @self.mcp.tool()
        def get_deployments(namespace: str = "", ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Get deployments in the specified namespace.
            
            Args:
                namespace: Namespace to get deployments from
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info(f"Getting deployments in namespace: {namespace}")
            query = f"get deployments {f'in namespace {namespace}' if namespace else ''}"
            result = process_query(query)
            return result
        
        @self.mcp.tool()
        def scale_deployment(deployment: str, replicas: int, namespace: str = "default", ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Scale a deployment to the specified number of replicas.
            
            Args:
                deployment: Name of the deployment to scale
                replicas: Number of replicas to scale to
                namespace: Namespace of the deployment
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info(f"Scaling deployment {deployment} to {replicas} replicas in namespace {namespace}")
            result = process_query(f"scale deployment {deployment} to {replicas} replicas in namespace {namespace}")
            return result
        
        @self.mcp.tool()
        def describe_pod(pod: str, namespace: str = "default", ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Describe a pod in the specified namespace.
            
            Args:
                pod: Name of the pod to describe
                namespace: Namespace of the pod
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info(f"Describing pod {pod} in namespace {namespace}")
            result = process_query(f"describe pod {pod} in namespace {namespace}")
            return result
        
        @self.mcp.tool()
        def get_logs(pod: str, namespace: str = "default", container: str = "", ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Get logs from a pod in the specified namespace.
            
            Args:
                pod: Name of the pod to get logs from
                namespace: Namespace of the pod
                container: Container to get logs from (optional)
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info(f"Getting logs from pod {pod} in namespace {namespace}")
            query = f"get logs from pod {pod} in namespace {namespace}"
            if container:
                query += f" container {container}"
            result = process_query(query)
            return result

async def main():
    """Run the async FastMCP server."""
    try:
        logger.info("Starting async FastMCP server")
        
        # Create server
        server = AsyncKubectlMCPServer("kubectl-mcp-tool")
        
        # Print server info
        logger.info(f"Server name: {server.mcp.name}")
        tools = await server.mcp.list_tools()
        logger.info(f"Server tools: {len(tools)}")
        for tool in tools:
            logger.info(f"- {tool}")
        
        # Run the server
        if len(sys.argv) > 1 and sys.argv[1] == "--sse":
            # Run SSE server
            port = 8080
            if len(sys.argv) > 2:
                try:
                    port = int(sys.argv[2])
                except ValueError:
                    pass
            
            logger.info(f"Running SSE server on port {port}")
            await server.mcp.run_sse_async(port=port)
        else:
            # Run stdio server
            logger.info("Running stdio server")
            await server.mcp.run_stdio_async()
    
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
