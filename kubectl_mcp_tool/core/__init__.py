"""Core subpackage for kubectl_mcp_tool.

This module provides core Kubernetes operations functionality.
"""

from .kubernetes_ops import KubernetesOperations

__all__ = [
    "KubernetesOperations",
]
