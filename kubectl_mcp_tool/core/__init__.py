"""Core subpackage for kubectl_mcp_tool.

This file makes the modules inside the *core* directory importable as a
regular Python package so that test-suites (e.g.  ``from
kubectl_mcp_tool.core.kubernetes_ops import KubernetesOperations``)
resolve correctly.

In addition, the most frequently used classes are re-exported for
convenience.
"""

from .kubernetes_ops import KubernetesOperations  # noqa: F401
from .mcp_server import MCPServer  # noqa: F401

__all__ = [
    "KubernetesOperations",
    "MCPServer",
]
