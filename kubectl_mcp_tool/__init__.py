"""
Kubectl MCP Tool - A Model Context Protocol server for Kubernetes.
"""

__version__ = "0.1.0"

from .simple_server import KubectlServer, main

__all__ = ["KubectlServer", "main"]
