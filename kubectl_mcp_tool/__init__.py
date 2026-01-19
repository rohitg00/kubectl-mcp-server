"""
Kubectl MCP Tool - A Model Context Protocol server for Kubernetes.

This package provides an MCP server that enables AI assistants to interact
with Kubernetes clusters through natural language commands.

For more information, see: https://github.com/rohitg00/kubectl-mcp-server
"""

__version__ = "1.2.0"

# Core MCP server implementation
from .mcp_server import MCPServer

# Natural language processing
from .natural_language import process_query, parse_query, execute_command

# Diagnostics
from .diagnostics import (
    run_diagnostics,
    check_kubectl_installation,
    check_cluster_connection,
)

__all__ = [
    # Version
    "__version__",
    # Server
    "MCPServer",
    # Natural Language
    "process_query",
    "parse_query",
    "execute_command",
    # Diagnostics
    "run_diagnostics",
    "check_kubectl_installation",
    "check_cluster_connection",
]
