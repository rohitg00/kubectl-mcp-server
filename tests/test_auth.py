"""Tests for the MCP Authorization module."""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestAuthConfig:
    """Tests for authentication configuration."""

    def test_auth_disabled_by_default(self):
        """Test that auth is disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.enabled is False

    def test_auth_enabled_via_env(self):
        """Test enabling auth via environment variable."""
        with patch.dict(os.environ, {"MCP_AUTH_ENABLED": "true"}, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.enabled is True

    def test_auth_issuer_from_env(self):
        """Test issuer URL from environment."""
        with patch.dict(os.environ, {
            "MCP_AUTH_ENABLED": "true",
            "MCP_AUTH_ISSUER": "https://auth.example.com"
        }, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.issuer_url == "https://auth.example.com"

    def test_auth_audience_default(self):
        """Test default audience value."""
        with patch.dict(os.environ, {}, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.audience == "kubectl-mcp-server"

    def test_auth_audience_custom(self):
        """Test custom audience value."""
        with patch.dict(os.environ, {
            "MCP_AUTH_AUDIENCE": "custom-audience"
        }, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.audience == "custom-audience"

    def test_auth_required_scopes_default(self):
        """Test default required scopes."""
        with patch.dict(os.environ, {}, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert "mcp:tools" in config.required_scopes

    def test_auth_required_scopes_custom(self):
        """Test custom required scopes."""
        with patch.dict(os.environ, {
            "MCP_AUTH_REQUIRED_SCOPES": "mcp:read,mcp:write"
        }, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert "mcp:read" in config.required_scopes
            assert "mcp:write" in config.required_scopes

    def test_effective_jwks_uri_derived(self):
        """Test JWKS URI is derived from issuer."""
        with patch.dict(os.environ, {
            "MCP_AUTH_ISSUER": "https://auth.example.com"
        }, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.effective_jwks_uri == "https://auth.example.com/.well-known/jwks.json"

    def test_effective_jwks_uri_explicit(self):
        """Test explicit JWKS URI takes precedence."""
        with patch.dict(os.environ, {
            "MCP_AUTH_ISSUER": "https://auth.example.com",
            "MCP_AUTH_JWKS_URI": "https://custom.example.com/jwks"
        }, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.effective_jwks_uri == "https://custom.example.com/jwks"

    def test_config_validation_disabled(self):
        """Test validation passes when auth is disabled."""
        with patch.dict(os.environ, {}, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.validate() is True

    def test_config_validation_enabled_without_issuer(self):
        """Test validation fails when enabled without issuer."""
        with patch.dict(os.environ, {
            "MCP_AUTH_ENABLED": "true"
        }, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.validate() is False

    def test_config_validation_enabled_with_issuer(self):
        """Test validation passes when properly configured."""
        with patch.dict(os.environ, {
            "MCP_AUTH_ENABLED": "true",
            "MCP_AUTH_ISSUER": "https://auth.example.com"
        }, clear=True):
            from kubectl_mcp_tool.auth.config import get_auth_config
            config = get_auth_config()
            assert config.validate() is True


class TestMCPScopes:
    """Tests for MCP scope definitions."""

    def test_all_scopes_returns_list(self):
        """Test all_scopes returns a list."""
        from kubectl_mcp_tool.auth.scopes import MCPScopes
        scopes = MCPScopes.all_scopes()
        assert isinstance(scopes, list)
        assert len(scopes) > 0

    def test_scope_values(self):
        """Test scope enum values."""
        from kubectl_mcp_tool.auth.scopes import MCPScopes
        assert MCPScopes.READ.value == "mcp:read"
        assert MCPScopes.WRITE.value == "mcp:write"
        assert MCPScopes.ADMIN.value == "mcp:admin"
        assert MCPScopes.TOOLS.value == "mcp:tools"
        assert MCPScopes.HELM.value == "mcp:helm"

    def test_read_scopes(self):
        """Test read-only scopes."""
        from kubectl_mcp_tool.auth.scopes import MCPScopes
        scopes = MCPScopes.read_scopes()
        assert "mcp:read" in scopes
        assert "mcp:diagnostics" in scopes

    def test_admin_scopes_includes_all(self):
        """Test admin scopes include all scopes."""
        from kubectl_mcp_tool.auth.scopes import MCPScopes
        admin_scopes = MCPScopes.admin_scopes()
        all_scopes = MCPScopes.all_scopes()
        assert set(admin_scopes) == set(all_scopes)


class TestToolScopes:
    """Tests for tool-to-scope mappings."""

    def test_get_required_scopes_read_tool(self):
        """Test read tools require read scope."""
        from kubectl_mcp_tool.auth.scopes import get_required_scopes, MCPScopes
        scopes = get_required_scopes("get_pods")
        assert MCPScopes.READ.value in scopes

    def test_get_required_scopes_write_tool(self):
        """Test write tools require write scope."""
        from kubectl_mcp_tool.auth.scopes import get_required_scopes, MCPScopes
        scopes = get_required_scopes("scale_deployment")
        assert MCPScopes.WRITE.value in scopes

    def test_get_required_scopes_admin_tool(self):
        """Test admin tools require admin scope."""
        from kubectl_mcp_tool.auth.scopes import get_required_scopes, MCPScopes
        scopes = get_required_scopes("drain_node")
        assert MCPScopes.ADMIN.value in scopes

    def test_get_required_scopes_helm_tool(self):
        """Test helm tools require helm scope."""
        from kubectl_mcp_tool.auth.scopes import get_required_scopes, MCPScopes
        scopes = get_required_scopes("helm_list_releases")
        assert MCPScopes.HELM.value in scopes

    def test_get_required_scopes_unknown_tool(self):
        """Test unknown tools require default scope."""
        from kubectl_mcp_tool.auth.scopes import get_required_scopes, MCPScopes
        scopes = get_required_scopes("unknown_tool_xyz")
        assert MCPScopes.TOOLS.value in scopes

    def test_has_required_scopes_with_tools_scope(self):
        """Test mcp:tools grants access to all tools."""
        from kubectl_mcp_tool.auth.scopes import has_required_scopes, MCPScopes
        token_scopes = {MCPScopes.TOOLS.value}
        assert has_required_scopes(token_scopes, "get_pods") is True
        assert has_required_scopes(token_scopes, "drain_node") is True

    def test_has_required_scopes_with_admin_scope(self):
        """Test mcp:admin grants access to all tools."""
        from kubectl_mcp_tool.auth.scopes import has_required_scopes, MCPScopes
        token_scopes = {MCPScopes.ADMIN.value}
        assert has_required_scopes(token_scopes, "get_pods") is True
        assert has_required_scopes(token_scopes, "drain_node") is True

    def test_has_required_scopes_read_only(self):
        """Test read scope grants access to read tools only."""
        from kubectl_mcp_tool.auth.scopes import has_required_scopes, MCPScopes
        token_scopes = {MCPScopes.READ.value}
        assert has_required_scopes(token_scopes, "get_pods") is True
        assert has_required_scopes(token_scopes, "scale_deployment") is False

    def test_has_required_scopes_write_not_admin(self):
        """Test write scope doesn't grant admin access."""
        from kubectl_mcp_tool.auth.scopes import has_required_scopes, MCPScopes
        token_scopes = {MCPScopes.WRITE.value}
        assert has_required_scopes(token_scopes, "scale_deployment") is True
        assert has_required_scopes(token_scopes, "drain_node") is False


class TestAuthVerifier:
    """Tests for authentication verifier creation."""

    def test_create_verifier_auth_disabled(self):
        """Test verifier is None when auth disabled."""
        with patch.dict(os.environ, {}, clear=True):
            from kubectl_mcp_tool.auth import get_auth_config, create_auth_verifier
            config = get_auth_config()
            verifier = create_auth_verifier(config)
            assert verifier is None

    def test_create_verifier_missing_fastmcp_auth(self):
        """Test graceful handling when FastMCP auth not available."""
        with patch.dict(os.environ, {
            "MCP_AUTH_ENABLED": "true",
            "MCP_AUTH_ISSUER": "https://auth.example.com"
        }, clear=True):
            from kubectl_mcp_tool.auth import get_auth_config, create_auth_verifier
            config = get_auth_config()

            # Mock the import to fail
            with patch.dict('sys.modules', {'fastmcp.server.auth': None}):
                verifier = create_auth_verifier(config)
                # Should return None gracefully when auth module not available
                assert verifier is None


class TestMCPServerAuth:
    """Tests for MCP server with authentication."""

    def test_server_initializes_without_auth(self):
        """Test server initializes with auth disabled."""
        with patch.dict(os.environ, {}, clear=True):
            from kubectl_mcp_tool.mcp_server import MCPServer
            server = MCPServer(name="test-server")
            assert server.auth_config.enabled is False

    def test_server_with_auth_enabled(self):
        """Test server with auth enabled loads config."""
        with patch.dict(os.environ, {
            "MCP_AUTH_ENABLED": "true",
            "MCP_AUTH_ISSUER": "https://auth.example.com"
        }, clear=True):
            from kubectl_mcp_tool.mcp_server import MCPServer
            server = MCPServer(name="test-server")
            assert server.auth_config.enabled is True
            assert server.auth_config.issuer_url == "https://auth.example.com"
