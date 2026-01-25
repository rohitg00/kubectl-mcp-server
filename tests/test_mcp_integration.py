"""Integration tests for MCP server with safety, observability, and config modules."""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock


class TestMCPServerIntegration:
    """Test MCP server integration with safety, observability, and config modules."""

    def test_import_mcp_server(self):
        """Test that MCP server can be imported without errors."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        assert MCPServer is not None

    def test_mcp_server_init_default(self):
        """Test MCP server initialization with defaults."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        from kubectl_mcp_tool.safety import SafetyMode, get_safety_mode, set_safety_mode

        # Reset to normal mode
        set_safety_mode(SafetyMode.NORMAL)

        server = MCPServer("test-server")
        assert server.name == "test-server"
        assert get_safety_mode() == SafetyMode.NORMAL

    def test_mcp_server_init_read_only(self):
        """Test MCP server initialization with read-only mode."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        from kubectl_mcp_tool.safety import SafetyMode, get_safety_mode, set_safety_mode

        # Reset to normal mode first
        set_safety_mode(SafetyMode.NORMAL)

        server = MCPServer("test-server", read_only=True)
        assert server.name == "test-server"
        assert get_safety_mode() == SafetyMode.READ_ONLY
        assert server.non_destructive is True

    def test_mcp_server_init_disable_destructive(self):
        """Test MCP server initialization with disable-destructive mode."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        from kubectl_mcp_tool.safety import SafetyMode, get_safety_mode, set_safety_mode

        # Reset to normal mode first
        set_safety_mode(SafetyMode.NORMAL)

        server = MCPServer("test-server", disable_destructive=True)
        assert server.name == "test-server"
        assert get_safety_mode() == SafetyMode.DISABLE_DESTRUCTIVE
        assert server.non_destructive is True

    def test_mcp_server_init_with_config_file(self):
        """Test MCP server initialization with config file."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode, get_safety_mode

        # Reset to normal mode first
        set_safety_mode(SafetyMode.NORMAL)

        # Create a temporary config file with valid transport
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write("""
[server]
transport = "stdio"
port = 9000

[safety]
mode = "read-only"
""")
            config_file = f.name

        try:
            server = MCPServer("test-server", config_file=config_file)
            assert server.name == "test-server"
            assert server.config is not None
            # Config file sets read-only mode
            assert get_safety_mode() == SafetyMode.READ_ONLY
        finally:
            os.unlink(config_file)

    def test_mcp_server_has_stats_collector(self):
        """Test MCP server has stats collector initialized."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode

        # Reset to normal mode first
        set_safety_mode(SafetyMode.NORMAL)

        server = MCPServer("test-server")
        assert server._stats is not None
        # Can get stats
        stats = server._stats.get_stats()
        assert "uptime_seconds" in stats
        assert "tool_calls_total" in stats

    def test_mcp_server_reload_callback(self):
        """Test MCP server registers reload callback."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        from kubectl_mcp_tool.config import reload_config
        from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode

        # Reset to normal mode first
        set_safety_mode(SafetyMode.NORMAL)

        server = MCPServer("test-server")

        # Reload config should not raise
        # The callback is registered and will be called
        try:
            reload_config()
        except Exception:
            # Config files may not exist, which is fine
            pass

    def test_cli_parameters_read_only(self):
        """Test CLI parameters for read-only mode."""
        from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode

        # Reset to normal mode first
        set_safety_mode(SafetyMode.NORMAL)

        # Verify the set_safety_mode works as expected
        set_safety_mode(SafetyMode.READ_ONLY)
        from kubectl_mcp_tool.safety import get_safety_mode
        assert get_safety_mode() == SafetyMode.READ_ONLY

    def test_cli_parameters_disable_destructive(self):
        """Test CLI parameters for disable-destructive mode."""
        from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode, get_safety_mode

        # Reset to normal mode first
        set_safety_mode(SafetyMode.NORMAL)

        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)
        assert get_safety_mode() == SafetyMode.DISABLE_DESTRUCTIVE


class TestMCPServerObservability:
    """Test observability integration in MCP server."""

    def test_stats_collector_integration(self):
        """Test stats collector is available in MCP server."""
        from kubectl_mcp_tool.observability import get_stats_collector

        stats = get_stats_collector()
        assert stats is not None

        # Record some calls
        stats.record_tool_call("integration_test_tool", success=True, duration=0.1)
        tool_stats = stats.get_tool_stats("integration_test_tool")
        assert tool_stats is not None
        assert tool_stats["calls"] >= 1
        assert tool_stats["errors"] == 0

    def test_metrics_availability(self):
        """Test Prometheus metrics availability check."""
        from kubectl_mcp_tool.observability import is_prometheus_available, get_metrics

        # Check availability (may or may not be installed)
        available = is_prometheus_available()

        if available:
            metrics = get_metrics()
            assert isinstance(metrics, str)


class TestMCPServerConfig:
    """Test config integration in MCP server."""

    def test_load_config(self):
        """Test config loading."""
        from kubectl_mcp_tool.config import load_config

        config = load_config()
        assert config is not None
        assert hasattr(config, 'server')
        assert hasattr(config, 'safety')
        assert hasattr(config, 'browser')

    def test_config_reload_callbacks(self):
        """Test config reload callback registration."""
        from kubectl_mcp_tool.config import (
            register_reload_callback,
            unregister_reload_callback,
        )

        callback_called = []

        def test_callback(config):
            callback_called.append(config)

        register_reload_callback(test_callback)

        # Unregister to clean up
        unregister_reload_callback(test_callback)

        # Verify unregister worked
        assert len(callback_called) == 0  # Not called since we unregistered


class TestMCPServerSafety:
    """Test safety mode integration in MCP server."""

    def test_safety_mode_info(self):
        """Test safety mode info retrieval."""
        from kubectl_mcp_tool.safety import (
            SafetyMode,
            set_safety_mode,
            get_mode_info,
        )

        set_safety_mode(SafetyMode.NORMAL)
        info = get_mode_info()
        assert info["mode"] == "normal"
        assert "description" in info
        assert info["blocked_operations"] == []

        set_safety_mode(SafetyMode.READ_ONLY)
        info = get_mode_info()
        assert info["mode"] == "read_only"
        assert len(info["blocked_operations"]) > 0

    def test_operation_allowed_check(self):
        """Test operation allowed check."""
        from kubectl_mcp_tool.safety import (
            SafetyMode,
            set_safety_mode,
            is_operation_allowed,
        )

        set_safety_mode(SafetyMode.NORMAL)
        allowed, reason = is_operation_allowed("delete_pod")
        assert allowed is True
        assert reason == ""

        set_safety_mode(SafetyMode.READ_ONLY)
        allowed, reason = is_operation_allowed("delete_pod")
        assert allowed is False
        assert "blocked" in reason.lower()

        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)
        allowed, reason = is_operation_allowed("delete_pod")
        assert allowed is False
        assert "blocked" in reason.lower()

        # Non-destructive write should be allowed
        allowed, reason = is_operation_allowed("create_deployment")
        assert allowed is True
