"""
Kubectl MCP Tool - A Model Context Protocol server for Kubernetes.
"""

__version__ = "1.1.0"

# Import implementations with correct FastMCP
from .simple_server import KubectlServer, main
from .mcp_server import MCPServer

__all__ = ["KubectlServer", "MCPServer", "main"]
