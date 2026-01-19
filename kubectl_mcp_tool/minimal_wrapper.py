#!/usr/bin/env python3
"""
Minimal MCP server wrapper for kubectl-mcp-tool.

This is a lightweight fallback implementation that can be used when
the full MCP server implementation has issues with certain clients.

Usage in MCP config:
{
    "mcpServers": {
        "kubernetes": {
            "command": "python",
            "args": ["-m", "kubectl_mcp_tool.minimal_wrapper"]
        }
    }
}
"""

import os
import sys
import json
import logging
import subprocess
import asyncio
from typing import Dict, Any, List, Optional

# Configure logging to stderr to avoid polluting stdout (used for MCP)
log_file = os.environ.get("MCP_LOG_FILE")
log_level = logging.DEBUG if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true") else logging.INFO

handlers = []
if log_file:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handlers.append(logging.FileHandler(log_file))
else:
    handlers.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=handlers
)

logger = logging.getLogger("kubectl-mcp-minimal")


def run_kubectl_command(command: str) -> Dict[str, Any]:
    """Run a kubectl command and return the result."""
    try:
        # Ensure command starts with kubectl
        if not command.strip().startswith("kubectl "):
            command = f"kubectl {command}"
        
        # Parse command safely
        import shlex
        cmd_parts = shlex.split(command)
        
        result = subprocess.run(
            cmd_parts,
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return {
            "command": command,
            "result": result.stdout if result.returncode == 0 else result.stderr,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"command": command, "result": "Command timed out", "success": False}
    except Exception as e:
        return {"command": command, "result": str(e), "success": False}


async def main():
    """Run a minimal MCP server."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        logger.error("MCP SDK not found. Install with: pip install mcp>=1.5.0")
        sys.exit(1)
    
    server = FastMCP("kubernetes")
    
    @server.tool("process_natural_language")
    async def process_natural_language(query: str) -> str:
        """Process a natural language query for kubectl operations."""
        logger.info(f"Processing query: {query}")
        
        query_lower = query.lower().strip()
        
        # Simple pattern matching for common requests
        if "pod" in query_lower and ("get" in query_lower or "list" in query_lower or "show" in query_lower):
            if "all namespace" in query_lower:
                result = run_kubectl_command("kubectl get pods --all-namespaces")
            else:
                result = run_kubectl_command("kubectl get pods")
        elif "namespace" in query_lower and ("get" in query_lower or "list" in query_lower):
            result = run_kubectl_command("kubectl get namespaces")
        elif "deployment" in query_lower:
            result = run_kubectl_command("kubectl get deployments --all-namespaces")
        elif "service" in query_lower:
            result = run_kubectl_command("kubectl get services --all-namespaces")
        elif "node" in query_lower:
            result = run_kubectl_command("kubectl get nodes")
        elif query_lower.startswith("kubectl "):
            result = run_kubectl_command(query)
        else:
            result = run_kubectl_command("kubectl get all")
        
        return json.dumps(result)
    
    @server.tool("kubectl_command")
    async def kubectl_command(command: str) -> str:
        """Execute a kubectl command directly."""
        logger.info(f"Executing command: {command}")
        result = run_kubectl_command(command)
        return json.dumps(result)
    
    @server.tool("get_pods")
    async def get_pods(namespace: Optional[str] = None) -> str:
        """Get pods in a namespace or all namespaces."""
        if namespace:
            result = run_kubectl_command(f"kubectl get pods -n {namespace}")
        else:
            result = run_kubectl_command("kubectl get pods --all-namespaces")
        return json.dumps(result)
    
    @server.tool("get_namespaces")
    async def get_namespaces() -> str:
        """Get all Kubernetes namespaces."""
        result = run_kubectl_command("kubectl get namespaces")
        return json.dumps(result)
    
    @server.tool("get_nodes")
    async def get_nodes() -> str:
        """Get all cluster nodes."""
        result = run_kubectl_command("kubectl get nodes -o wide")
        return json.dumps(result)
    
    @server.tool("get_deployments")
    async def get_deployments(namespace: Optional[str] = None) -> str:
        """Get deployments in a namespace or all namespaces."""
        if namespace:
            result = run_kubectl_command(f"kubectl get deployments -n {namespace}")
        else:
            result = run_kubectl_command("kubectl get deployments --all-namespaces")
        return json.dumps(result)
    
    @server.tool("get_services")
    async def get_services(namespace: Optional[str] = None) -> str:
        """Get services in a namespace or all namespaces."""
        if namespace:
            result = run_kubectl_command(f"kubectl get services -n {namespace}")
        else:
            result = run_kubectl_command("kubectl get services --all-namespaces")
        return json.dumps(result)
    
    @server.tool("health_check")
    async def health_check() -> str:
        """Check cluster health."""
        result = run_kubectl_command("kubectl cluster-info")
        return json.dumps(result)
    
    logger.info("Starting minimal MCP server with stdio transport")
    await server.run_stdio_async()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        sys.exit(1)
