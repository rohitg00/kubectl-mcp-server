"""Authentication configuration loaded from environment variables."""

import os
import logging
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger("mcp-server.auth")


@dataclass
class AuthConfig:
    """Authentication configuration."""

    enabled: bool = False
    issuer_url: Optional[str] = None
    jwks_uri: Optional[str] = None
    audience: str = "kubectl-mcp-server"
    required_scopes: List[str] = field(default_factory=lambda: ["mcp:tools"])
    resource_url: Optional[str] = None

    def validate(self) -> bool:
        """Validate configuration."""
        if not self.enabled:
            return True

        if not self.issuer_url:
            logger.error("MCP_AUTH_ISSUER is required when authentication is enabled")
            return False

        return True

    @property
    def effective_jwks_uri(self) -> Optional[str]:
        """Get JWKS URI, deriving from issuer if not explicitly set."""
        if self.jwks_uri:
            return self.jwks_uri
        if self.issuer_url:
            # Standard OIDC discovery path
            issuer = self.issuer_url.rstrip("/")
            return f"{issuer}/.well-known/jwks.json"
        return None


def get_auth_config() -> AuthConfig:
    """Load authentication configuration from environment variables."""
    enabled = os.environ.get("MCP_AUTH_ENABLED", "").lower() in ("1", "true", "yes")

    config = AuthConfig(
        enabled=enabled,
        issuer_url=os.environ.get("MCP_AUTH_ISSUER"),
        jwks_uri=os.environ.get("MCP_AUTH_JWKS_URI"),
        audience=os.environ.get("MCP_AUTH_AUDIENCE", "kubectl-mcp-server"),
        required_scopes=_parse_scopes(os.environ.get("MCP_AUTH_REQUIRED_SCOPES", "mcp:tools")),
        resource_url=os.environ.get("MCP_AUTH_RESOURCE_URL"),
    )

    if enabled:
        logger.info(f"Authentication enabled with issuer: {config.issuer_url}")
        logger.info(f"Required scopes: {config.required_scopes}")
    else:
        logger.debug("Authentication disabled")

    return config


def _parse_scopes(scopes_str: str) -> List[str]:
    """Parse comma-separated scopes string."""
    if not scopes_str:
        return []
    return [s.strip() for s in scopes_str.split(",") if s.strip()]
