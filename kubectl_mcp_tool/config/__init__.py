"""Configuration management for kubectl-mcp-server.

This module provides TOML-based configuration with:
- Main config file support
- Drop-in directory for modular configuration
- SIGHUP reload for runtime updates
- Environment variable overrides
"""

from .loader import (
    Config,
    load_config,
    get_config,
    reload_config,
    get_config_paths,
    setup_sighup_handler,
    register_reload_callback,
    unregister_reload_callback,
)
from .schema import (
    ServerConfig,
    SafetyConfig,
    BrowserConfig,
    MetricsConfig,
    LoggingConfig,
    validate_config,
)

__all__ = [
    # Config loading
    "Config",
    "load_config",
    "get_config",
    "reload_config",
    "get_config_paths",
    "setup_sighup_handler",
    "register_reload_callback",
    "unregister_reload_callback",
    # Config schemas
    "ServerConfig",
    "SafetyConfig",
    "BrowserConfig",
    "MetricsConfig",
    "LoggingConfig",
    "validate_config",
]
