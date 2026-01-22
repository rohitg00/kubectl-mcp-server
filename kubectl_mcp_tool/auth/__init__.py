"""MCP Authorization module implementing RFC 9728 OAuth 2.0 Protected Resource Metadata."""

from .config import AuthConfig, get_auth_config
from .scopes import MCPScopes, TOOL_SCOPES
from .verifier import create_auth_verifier

__all__ = [
    "AuthConfig",
    "get_auth_config",
    "MCPScopes",
    "TOOL_SCOPES",
    "create_auth_verifier",
]
