"""MCP OAuth 2.0 scope definitions for fine-grained access control."""

from enum import Enum
from typing import List


class MCPScopes(str, Enum):
    """MCP OAuth 2.0 scopes."""

    # Base scopes
    READ = "mcp:read"
    WRITE = "mcp:write"
    ADMIN = "mcp:admin"
    TOOLS = "mcp:tools"

    # Category-specific scopes
    HELM = "mcp:helm"
    DIAGNOSTICS = "mcp:diagnostics"
    NETWORKING = "mcp:networking"
    STORAGE = "mcp:storage"
    SECURITY = "mcp:security"
    COST = "mcp:cost"

    @classmethod
    def all_scopes(cls) -> List[str]:
        """Return all available scopes."""
        return [scope.value for scope in cls]

    @classmethod
    def read_scopes(cls) -> List[str]:
        """Return scopes for read-only access."""
        return [cls.READ.value, cls.DIAGNOSTICS.value]

    @classmethod
    def write_scopes(cls) -> List[str]:
        """Return scopes for write access."""
        return [cls.READ.value, cls.WRITE.value]

    @classmethod
    def admin_scopes(cls) -> List[str]:
        """Return scopes for admin access."""
        return cls.all_scopes()
