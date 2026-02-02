"""
Kubectl MCP Tool - A Model Context Protocol server for Kubernetes.

This package provides an MCP server that enables AI assistants to interact
with Kubernetes clusters through natural language commands.

For more information, see: https://github.com/rohitg00/kubectl-mcp-server
"""

__version__ = "1.22.0"

from .mcp_server import MCPServer
from .diagnostics import run_diagnostics, check_kubectl_installation, check_cluster_connection

__all__ = [
    "__version__",
    "MCPServer",
    "run_diagnostics",
    "check_kubectl_installation",
    "check_cluster_connection",
]
