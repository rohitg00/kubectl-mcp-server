"""
Kubectl MCP Tool - A Model Context Protocol server for Kubernetes.
"""

__version__ = "1.1.0"

# Import implementations with correct FastMCP
from .simple_server import KubectlServer, main
from .mcp_server import MCPServer as _RootMCPServer

# Re-export key symbols for easier import paths in tests
try:
    from .core import KubernetesOperations, MCPServer  # type: ignore
    __all__ = [
        "KubectlServer",
        "MCPServer",
        "KubernetesOperations",
        "main",
    ]
except ModuleNotFoundError:
    # When the package is installed without the *core* package (unlikely)
    # we at least expose the root‐level MCPServer implementation.
    MCPServer = _RootMCPServer  # noqa: N816  (re-export for callers)
    __all__ = ["KubectlServer", "MCPServer", "main"]
