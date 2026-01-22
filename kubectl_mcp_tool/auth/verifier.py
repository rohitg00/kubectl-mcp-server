"""JWT token verification via JWKS endpoints from OIDC-compliant identity providers."""

import logging
from typing import Optional, Any

from .config import AuthConfig

logger = logging.getLogger("mcp-server.auth")


def create_auth_verifier(config: AuthConfig) -> Optional[Any]:
    """
    Create an authentication verifier based on configuration.

    Returns a FastMCP-compatible auth verifier or None if auth is disabled.
    """
    if not config.enabled:
        logger.debug("Authentication disabled, no verifier created")
        return None

    if not config.validate():
        raise ValueError("Invalid authentication configuration")

    try:
        from fastmcp.server.auth import JWTVerifier
    except ImportError:
        logger.warning(
            "FastMCP auth module not available. "
            "Authentication requires fastmcp>=3.0.0 with auth support."
        )
        return None

    jwks_uri = config.effective_jwks_uri
    if not jwks_uri:
        raise ValueError("JWKS URI could not be determined from configuration")

    logger.info(f"Creating JWT verifier with JWKS URI: {jwks_uri}")
    logger.info(f"Expected audience: {config.audience}")
    logger.info(f"Expected issuer: {config.issuer_url}")

    verifier = JWTVerifier(
        jwks_uri=jwks_uri,
        issuer=config.issuer_url,
        audience=config.audience,
    )

    return verifier


def create_auth_settings(config: AuthConfig) -> Optional[Any]:
    """
    Create RFC 9728 Protected Resource Metadata settings.

    This enables the /.well-known/oauth-protected-resource endpoint
    that MCP clients use to discover authorization requirements.
    """
    if not config.enabled:
        return None

    if not config.resource_url:
        logger.debug("No resource URL configured, skipping RFC 9728 metadata")
        return None

    try:
        from pydantic import AnyHttpUrl
        from mcp.server.auth.settings import AuthSettings
    except ImportError:
        logger.warning(
            "MCP auth settings not available. "
            "RFC 9728 metadata requires mcp>=1.8.0."
        )
        return None

    logger.info(f"Creating RFC 9728 auth settings for resource: {config.resource_url}")

    settings = AuthSettings(
        issuer_url=AnyHttpUrl(config.issuer_url),
        resource_server_url=AnyHttpUrl(config.resource_url),
        required_scopes=config.required_scopes,
    )

    return settings
