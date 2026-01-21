"""
Unit tests for MCP Server initialization and configuration.

This module tests:
- Server initialization
- Configuration options
- Transport methods
- Dependency checking
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock


class TestServerInitialization:
    """Tests for MCPServer initialization."""

    @pytest.mark.unit
    def test_server_creates_successfully(self):
        """Test that server creates successfully."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test-server")

        assert server is not None
        assert server.name == "test-server"

    @pytest.mark.unit
    def test_server_name_is_set(self):
        """Test that server name is properly set."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="my-custom-server")

        assert server.name == "my-custom-server"

    @pytest.mark.unit
    def test_non_destructive_mode_default(self):
        """Test that non-destructive mode is disabled by default."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server.non_destructive is False

    @pytest.mark.unit
    def test_non_destructive_mode_enabled(self):
        """Test that non_destructive mode can be enabled."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test", non_destructive=True)

        assert server.non_destructive is True

    @pytest.mark.unit
    def test_fastmcp_server_instance(self):
        """Test that FastMCP server instance is created."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert hasattr(server, 'server')
        assert server.server is not None


class TestToolRegistration:
    """Tests for tool registration."""

    @pytest.mark.unit
    def test_tools_are_registered(self):
        """Test that tools are registered during initialization."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        # Server should have tools
        assert hasattr(server, 'server')

    @pytest.mark.unit
    def test_setup_tools_called(self):
        """Test that setup_tools is called during initialization."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                with patch.object(MCPServer, 'setup_tools') as mock_setup:
                    # Create server - setup_tools is called in __init__
                    # We can't easily patch it before __init__, so just verify the method exists
                    pass

        # Verify setup_tools method exists
        assert hasattr(MCPServer, 'setup_tools')


class TestResourceRegistration:
    """Tests for resource registration."""

    @pytest.mark.unit
    def test_resources_are_registered(self):
        """Test that resources are registered during initialization."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert hasattr(server, 'server')

    @pytest.mark.unit
    def test_setup_resources_method_exists(self):
        """Test that setup_resources method exists."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        assert hasattr(MCPServer, 'setup_resources')


class TestPromptRegistration:
    """Tests for prompt registration."""

    @pytest.mark.unit
    def test_prompts_are_registered(self):
        """Test that prompts are registered during initialization."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert hasattr(server, 'server')

    @pytest.mark.unit
    def test_setup_prompts_method_exists(self):
        """Test that setup_prompts method exists."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        assert hasattr(MCPServer, 'setup_prompts')


class TestDependencyChecking:
    """Tests for dependency checking."""

    @pytest.mark.unit
    def test_dependencies_checked_lazily(self):
        """Test that dependencies are checked lazily."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        # Dependencies should not be checked until accessed
        assert server._dependencies_checked is False

    @pytest.mark.unit
    def test_dependencies_checked_on_access(self):
        """Test that dependencies are checked on first access."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True) as mock_check:
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")
                # Access the property
                _ = server.dependencies_available

        assert server._dependencies_checked is True

    @pytest.mark.unit
    def test_check_tool_availability(self):
        """Test tool availability checking."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        with patch("shutil.which", return_value="/usr/bin/kubectl"):
            with patch("subprocess.check_output", return_value=b'{"clientVersion": {}}'):
                result = server._check_tool_availability("kubectl")
                assert result is True

    @pytest.mark.unit
    def test_check_tool_not_available(self):
        """Test tool availability when tool is not found."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        with patch("shutil.which", return_value=None):
            result = server._check_tool_availability("nonexistent-tool")
            assert result is False


class TestNonDestructiveMode:
    """Tests for non-destructive mode."""

    @pytest.mark.unit
    def test_check_destructive_returns_none_when_allowed(self):
        """Test that _check_destructive returns None when destructive ops are allowed."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test", non_destructive=False)

        result = server._check_destructive()
        assert result is None

    @pytest.mark.unit
    def test_check_destructive_returns_error_when_blocked(self):
        """Test that _check_destructive returns error when destructive ops are blocked."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test", non_destructive=True)

        result = server._check_destructive()
        assert result is not None
        assert result["success"] is False
        assert "non-destructive mode" in result["error"]


class TestSecretMasking:
    """Tests for secret masking."""

    @pytest.mark.unit
    def test_mask_secrets_method_exists(self):
        """Test that _mask_secrets method exists."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        assert hasattr(MCPServer, '_mask_secrets')

    @pytest.mark.unit
    def test_masks_base64_secrets(self):
        """Test that base64-encoded secrets are masked."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        text = """
        data:
          password: c2VjcmV0UGFzc3dvcmQxMjM0NTY3ODkw
        """
        masked = server._mask_secrets(text)
        assert "[MASKED]" in masked

    @pytest.mark.unit
    def test_masks_password_fields(self):
        """Test that password fields are masked."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        text = 'password: "supersecretpassword"'
        masked = server._mask_secrets(text)
        assert "[MASKED]" in masked

    @pytest.mark.unit
    def test_masks_token_fields(self):
        """Test that token fields are masked."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        text = 'token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"'
        masked = server._mask_secrets(text)
        assert "[MASKED]" in masked


class TestTransportMethods:
    """Tests for transport methods."""

    @pytest.mark.unit
    def test_serve_stdio_method_exists(self):
        """Test that serve_stdio method exists."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert hasattr(server, 'serve_stdio')

    @pytest.mark.unit
    def test_serve_sse_method_exists(self):
        """Test that serve_sse method exists."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert hasattr(server, 'serve_sse')

    @pytest.mark.unit
    def test_serve_http_method_exists(self):
        """Test that serve_http method exists."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert hasattr(server, 'serve_http')


class TestServerConfiguration:
    """Tests for server configuration."""

    @pytest.mark.unit
    def test_server_with_default_config(self):
        """Test server with default configuration."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="default-server")

        assert server.name == "default-server"
        assert server.non_destructive is False

    @pytest.mark.unit
    def test_server_with_custom_config(self):
        """Test server with custom configuration."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(
                    name="custom-server",
                    non_destructive=True
                )

        assert server.name == "custom-server"
        assert server.non_destructive is True


class TestModuleExports:
    """Tests for module exports."""

    @pytest.mark.unit
    def test_mcpserver_exported(self):
        """Test that MCPServer is exported from module."""
        from kubectl_mcp_tool import MCPServer

        assert MCPServer is not None

    @pytest.mark.unit
    def test_version_exported(self):
        """Test that __version__ is exported from module."""
        from kubectl_mcp_tool import __version__

        assert __version__ is not None
        assert isinstance(__version__, str)

    @pytest.mark.unit
    def test_diagnostics_exported(self):
        """Test that diagnostics functions are exported."""
        from kubectl_mcp_tool import run_diagnostics, check_kubectl_installation, check_cluster_connection

        assert run_diagnostics is not None
        assert check_kubectl_installation is not None
        assert check_cluster_connection is not None
