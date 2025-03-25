"""
kubectl-mcp-tool package.

This package provides MCP-based tools for kubectl operations.
"""

__version__ = "0.1.0"

from .natural_language import process_query
from .fastmcp_server import KubectlMCPServer

__all__ = ["KubectlMCPServer", "process_query"]
