"""Tests for configuration management module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestServerConfig:
    """Test ServerConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        from kubectl_mcp_tool.config.schema import ServerConfig

        config = ServerConfig()
        assert config.transport == "streamable-http"
        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert config.debug is False
        assert config.log_file is None

    def test_custom_values(self):
        """Test custom configuration values."""
        from kubectl_mcp_tool.config.schema import ServerConfig

        config = ServerConfig(
            transport="stdio",
            host="0.0.0.0",
            port=9000,
            debug=True,
            log_file="/var/log/mcp.log",
        )
        assert config.transport == "stdio"
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.debug is True
        assert config.log_file == "/var/log/mcp.log"

    def test_invalid_transport(self):
        """Test validation rejects invalid transport."""
        from kubectl_mcp_tool.config.schema import ServerConfig

        with pytest.raises(ValueError, match="Invalid transport"):
            ServerConfig(transport="invalid")

    def test_invalid_port(self):
        """Test validation rejects invalid port."""
        from kubectl_mcp_tool.config.schema import ServerConfig

        with pytest.raises(ValueError, match="Invalid port"):
            ServerConfig(port=0)

        with pytest.raises(ValueError, match="Invalid port"):
            ServerConfig(port=70000)


class TestSafetyConfig:
    """Test SafetyConfig dataclass."""

    def test_default_values(self):
        """Test default safety configuration."""
        from kubectl_mcp_tool.config.schema import SafetyConfig

        config = SafetyConfig()
        assert config.mode == "normal"
        assert config.confirm_destructive is False
        assert config.max_delete_count == 10
        assert "kube-system" in config.blocked_namespaces

    def test_valid_modes(self):
        """Test all valid safety modes."""
        from kubectl_mcp_tool.config.schema import SafetyConfig

        for mode in ["normal", "read-only", "disable-destructive"]:
            config = SafetyConfig(mode=mode)
            assert config.mode == mode

    def test_invalid_mode(self):
        """Test validation rejects invalid mode."""
        from kubectl_mcp_tool.config.schema import SafetyConfig

        with pytest.raises(ValueError, match="Invalid safety mode"):
            SafetyConfig(mode="invalid")


class TestBrowserConfig:
    """Test BrowserConfig dataclass."""

    def test_default_values(self):
        """Test default browser configuration."""
        from kubectl_mcp_tool.config.schema import BrowserConfig

        config = BrowserConfig()
        assert config.enabled is False
        assert config.provider == "local"
        assert config.headed is False
        assert config.timeout == 60

    def test_valid_providers(self):
        """Test all valid browser providers."""
        from kubectl_mcp_tool.config.schema import BrowserConfig

        for provider in ["local", "browserbase", "browseruse", "cdp"]:
            config = BrowserConfig(provider=provider)
            assert config.provider == provider

    def test_invalid_provider(self):
        """Test validation rejects invalid provider."""
        from kubectl_mcp_tool.config.schema import BrowserConfig

        with pytest.raises(ValueError, match="Invalid browser provider"):
            BrowserConfig(provider="invalid")


class TestMetricsConfig:
    """Test MetricsConfig dataclass."""

    def test_default_values(self):
        """Test default metrics configuration."""
        from kubectl_mcp_tool.config.schema import MetricsConfig

        config = MetricsConfig()
        assert config.enabled is False
        assert config.endpoint == "/metrics"
        assert config.sample_rate == 1.0

    def test_invalid_sample_rate(self):
        """Test validation rejects invalid sample rate."""
        from kubectl_mcp_tool.config.schema import MetricsConfig

        with pytest.raises(ValueError, match="Invalid sample_rate"):
            MetricsConfig(sample_rate=1.5)

        with pytest.raises(ValueError, match="Invalid sample_rate"):
            MetricsConfig(sample_rate=-0.1)


class TestValidateConfig:
    """Test validate_config function."""

    def test_valid_config(self):
        """Test validation passes for valid config."""
        from kubectl_mcp_tool.config.schema import validate_config

        config = {
            "server": {"transport": "stdio", "port": 8000},
            "safety": {"mode": "read-only"},
            "browser": {"provider": "browserbase"},
            "metrics": {"sample_rate": 0.5},
        }
        errors = validate_config(config)
        assert errors == []

    def test_invalid_config(self):
        """Test validation catches errors."""
        from kubectl_mcp_tool.config.schema import validate_config

        config = {
            "server": {"transport": "invalid", "port": 0},
            "safety": {"mode": "invalid"},
            "browser": {"provider": "invalid"},
            "metrics": {"sample_rate": 2.0},
        }
        errors = validate_config(config)
        assert len(errors) == 5


class TestConfigPaths:
    """Test get_config_paths function."""

    def test_default_paths(self):
        """Test default config paths."""
        from kubectl_mcp_tool.config.loader import get_config_paths

        paths = get_config_paths()
        assert "config_dir" in paths
        assert "main_config" in paths
        assert "drop_in_dir" in paths
        assert paths["main_config"].name == "config.toml"
        assert paths["drop_in_dir"].name == "config.d"

    def test_xdg_config_home(self):
        """Test XDG_CONFIG_HOME is respected."""
        from kubectl_mcp_tool.config.loader import get_config_paths

        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
            paths = get_config_paths()
            assert str(paths["config_dir"]).startswith("/custom/config")


class TestDeepMerge:
    """Test _deep_merge function."""

    def test_simple_merge(self):
        """Test simple dictionary merge."""
        from kubectl_mcp_tool.config.loader import _deep_merge

        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        """Test nested dictionary merge."""
        from kubectl_mcp_tool.config.loader import _deep_merge

        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 20, "z": 30}}
        result = _deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 20, "z": 30}, "b": 3}


class TestEnvOverrides:
    """Test _apply_env_overrides function."""

    def test_server_port_override(self):
        """Test MCP_SERVER_PORT environment override."""
        from kubectl_mcp_tool.config.loader import _apply_env_overrides

        with patch.dict(os.environ, {"MCP_SERVER_PORT": "9000"}):
            result = _apply_env_overrides({})
            assert result["server"]["port"] == 9000

    def test_safety_mode_override(self):
        """Test MCP_SAFETY_MODE environment override."""
        from kubectl_mcp_tool.config.loader import _apply_env_overrides

        with patch.dict(os.environ, {"MCP_SAFETY_MODE": "read-only"}):
            result = _apply_env_overrides({})
            assert result["safety"]["mode"] == "read-only"

    def test_browser_enabled_override(self):
        """Test MCP_BROWSER_ENABLED environment override."""
        from kubectl_mcp_tool.config.loader import _apply_env_overrides

        with patch.dict(os.environ, {"MCP_BROWSER_ENABLED": "true"}):
            result = _apply_env_overrides({})
            assert result["browser"]["enabled"] is True

    def test_debug_override(self):
        """Test MCP_DEBUG environment override."""
        from kubectl_mcp_tool.config.loader import _apply_env_overrides

        with patch.dict(os.environ, {"MCP_DEBUG": "1"}):
            result = _apply_env_overrides({})
            assert result["server"]["debug"] is True


class TestLoadConfig:
    """Test load_config function."""

    def test_load_default_config(self):
        """Test loading config with defaults."""
        from kubectl_mcp_tool.config.loader import load_config

        config = load_config(skip_env=True)
        assert config.server.transport == "streamable-http"
        assert config.server.port == 8000
        assert config.safety.mode == "normal"

    def test_load_from_file(self):
        """Test loading config from TOML file."""
        pytest.importorskip("tomli", reason="tomli required for TOML parsing")
        from kubectl_mcp_tool.config.loader import load_config

        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False, mode="w") as f:
            f.write("""
[server]
port = 9999
debug = true

[safety]
mode = "read-only"
""")
            f.flush()

            try:
                config = load_config(config_file=f.name, skip_env=True)
                assert config.server.port == 9999
                assert config.server.debug is True
                assert config.safety.mode == "read-only"
            finally:
                os.unlink(f.name)

    def test_env_overrides_applied(self):
        """Test environment overrides are applied."""
        from kubectl_mcp_tool.config.loader import load_config

        with patch.dict(os.environ, {"MCP_SERVER_PORT": "7777"}):
            config = load_config()
            assert config.server.port == 7777


class TestGetConfig:
    """Test get_config function."""

    def test_get_config_singleton(self):
        """Test get_config returns same instance."""
        from kubectl_mcp_tool.config import loader

        # Reset global config
        loader._config = None

        config1 = loader.get_config()
        config2 = loader.get_config()
        assert config1 is config2


class TestReloadConfig:
    """Test reload_config function."""

    def test_reload_config(self):
        """Test configuration reload."""
        from kubectl_mcp_tool.config import loader

        # Load initial config
        loader._config = None
        config1 = loader.load_config(skip_env=True)

        # Reload
        config2 = loader.reload_config()
        assert config2 is not None
        assert config2.server.port == config1.server.port

    def test_reload_callback(self):
        """Test reload callbacks are called."""
        from kubectl_mcp_tool.config import loader

        callback_called = []

        def callback(config):
            callback_called.append(config)

        loader._config = None
        loader.load_config(skip_env=True)
        loader.register_reload_callback(callback)

        try:
            loader.reload_config()
            assert len(callback_called) == 1
        finally:
            loader.unregister_reload_callback(callback)


class TestSighupHandler:
    """Test SIGHUP handler setup."""

    def test_setup_sighup_handler(self):
        """Test SIGHUP handler can be installed."""
        import sys

        from kubectl_mcp_tool.config.loader import setup_sighup_handler

        if sys.platform == "win32":
            result = setup_sighup_handler()
            assert result is False
        else:
            result = setup_sighup_handler()
            assert result is True


class TestConfigDataclass:
    """Test Config root dataclass."""

    def test_config_has_all_sections(self):
        """Test Config has all expected sections."""
        from kubectl_mcp_tool.config.schema import Config

        config = Config()
        assert hasattr(config, "server")
        assert hasattr(config, "safety")
        assert hasattr(config, "browser")
        assert hasattr(config, "metrics")
        assert hasattr(config, "logging")
        assert hasattr(config, "kubernetes")
        assert hasattr(config, "custom")

    def test_config_custom_section(self):
        """Test Config custom section for unknown keys."""
        from kubectl_mcp_tool.config.schema import Config

        config = Config(custom={"my_plugin": {"setting": "value"}})
        assert config.custom["my_plugin"]["setting"] == "value"
