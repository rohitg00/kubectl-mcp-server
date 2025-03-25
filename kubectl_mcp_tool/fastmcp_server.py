#!/usr/bin/env python3
"""
FastMCP server implementation for kubectl-mcp-tool.

This module provides a FastMCP-based implementation of the kubectl MCP server
using the official MCP Python SDK.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP, Context
from .natural_language import process_query

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fastmcp-server")

class KubectlMCPServer:
    """FastMCP-based server for kubectl operations."""
    
    def __init__(self, name: str = "kubectl-mcp-tool"):
        """Initialize the FastMCP server."""
        self.mcp = FastMCP(name)
        self.register_tools()
        logger.info(f"KubectlMCPServer initialized: {name}")
    
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
        def get_current_namespace(ctx: Optional[Context] = None) -> Dict[str, Any]:
            """
            Get the current namespace.
            
            Args:
                ctx: Optional MCP context
            
            Returns:
                Dictionary containing the command and result
            """
            logger.info("Getting current namespace")
            result = process_query("what is my current namespace")
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
    
    def serve_stdio(self):
        """Serve the MCP server over stdio."""
        logger.info("Serving MCP server over stdio")
        import uvicorn
        import sys
        from .transports.stdio import StdioTransport
        
        # Create a stdio transport
        transport = StdioTransport(sys.stdin, sys.stdout)
        
        # Use the transport to handle stdio communication
        try:
            while True:
                message = transport.receive()
                if not message:
                    break
                    
                # Process the message through FastMCP
                response = self.mcp.process_message(message)
                
                # Send the response
                transport.send(response)
        except Exception as e:
            logger.error(f"Error in stdio transport: {e}")
            raise
    
    async def serve_sse(self, port: int = 8080):
        """Serve the MCP server over SSE."""
        logger.info(f"Serving MCP server over SSE on port {port}")
        from .transports.sse import SSETransport
        
        # Create and start SSE transport
        transport = SSETransport(port=port)
        await transport.start()
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("SSE transport shutting down")
