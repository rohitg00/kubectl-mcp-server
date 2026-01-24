"""Configuration loader with TOML support, drop-in directories, and SIGHUP reload.

This module handles:
- Loading main config from ~/.config/kubectl-mcp-server/config.toml
- Merging drop-in configs from ~/.config/kubectl-mcp-server/config.d/*.toml
- Environment variable overrides
- SIGHUP signal handling for runtime reloads
"""

import logging
import os
import signal
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .schema import (
    BrowserConfig,
    Config,
    KubernetesConfig,
    LoggingConfig,
    MetricsConfig,
    SafetyConfig,
    ServerConfig,
    validate_config,
)

logger = logging.getLogger(__name__)

# Try to import tomli/tomllib for TOML parsing
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore

# Global config instance
_config: Optional[Config] = None
_config_callbacks: List[Callable[[Config], None]] = []


def get_config_paths() -> Dict[str, Path]:
    """Get standard configuration paths.

    Returns:
        Dictionary with paths for config_dir, main_config, and drop_in_dir
    """
    # Check XDG_CONFIG_HOME first, then fall back to ~/.config
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base_dir = Path(xdg_config)
    else:
        base_dir = Path.home() / ".config"

    config_dir = base_dir / "kubectl-mcp-server"

    return {
        "config_dir": config_dir,
        "main_config": config_dir / "config.toml",
        "drop_in_dir": config_dir / "config.d",
    }


def _load_toml_file(path: Path) -> Dict[str, Any]:
    """Load a TOML file and return its contents as a dictionary.

    Args:
        path: Path to the TOML file

    Returns:
        Dictionary containing the TOML data

    Raises:
        RuntimeError: If tomllib/tomli is not available
        FileNotFoundError: If the file doesn't exist
        ValueError: If the TOML is invalid
    """
    if tomllib is None:
        raise RuntimeError(
            "TOML parsing requires Python 3.11+ or the 'tomli' package. "
            "Install with: pip install tomli"
        )

    with open(path, "rb") as f:
        return tomllib.load(f)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary
        override: Override dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _apply_env_overrides(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration.

    Environment variables follow the pattern:
    MCP_<SECTION>_<KEY>=value

    Examples:
        MCP_SERVER_PORT=9000
        MCP_SAFETY_MODE=read-only
        MCP_BROWSER_ENABLED=true

    Args:
        config_dict: Configuration dictionary

    Returns:
        Configuration with environment overrides applied
    """
    result = config_dict.copy()

    env_mappings = {
        # Server settings
        "MCP_SERVER_TRANSPORT": ("server", "transport"),
        "MCP_SERVER_HOST": ("server", "host"),
        "MCP_SERVER_PORT": ("server", "port", int),
        "MCP_DEBUG": ("server", "debug", lambda x: x.lower() in ("true", "1", "yes")),
        "MCP_LOG_FILE": ("server", "log_file"),
        "MCP_LOG_LEVEL": ("server", "log_level"),
        # Safety settings
        "MCP_SAFETY_MODE": ("safety", "mode"),
        # Browser settings
        "MCP_BROWSER_ENABLED": ("browser", "enabled", lambda x: x.lower() in ("true", "1", "yes")),
        "MCP_BROWSER_PROVIDER": ("browser", "provider"),
        "MCP_BROWSER_HEADED": ("browser", "headed", lambda x: x.lower() in ("true", "1", "yes")),
        "BROWSERBASE_API_KEY": ("browser", "browserbase_api_key"),
        "BROWSERBASE_PROJECT_ID": ("browser", "browserbase_project_id"),
        "BROWSER_USE_API_KEY": ("browser", "browseruse_api_key"),
        "MCP_BROWSER_CDP_URL": ("browser", "cdp_url"),
        # Metrics settings
        "MCP_METRICS_ENABLED": ("metrics", "enabled", lambda x: x.lower() in ("true", "1", "yes")),
        "MCP_TRACING_ENABLED": ("metrics", "tracing_enabled", lambda x: x.lower() in ("true", "1", "yes")),
        "OTEL_EXPORTER_OTLP_ENDPOINT": ("metrics", "otlp_endpoint"),
        "OTEL_SERVICE_NAME": ("metrics", "service_name"),
        # Kubernetes settings
        "KUBECONFIG": ("kubernetes", "kubeconfig"),
        "MCP_K8S_CONTEXT": ("kubernetes", "context"),
        "MCP_K8S_NAMESPACE": ("kubernetes", "default_namespace"),
    }

    for env_var, mapping in env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            section = mapping[0]
            key = mapping[1]
            converter = mapping[2] if len(mapping) > 2 else str

            if section not in result:
                result[section] = {}

            try:
                result[section][key] = converter(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid value for {env_var}: {value} ({e})")

    return result


def _dict_to_config(config_dict: Dict[str, Any]) -> Config:
    """Convert a configuration dictionary to a Config dataclass.

    Args:
        config_dict: Configuration dictionary

    Returns:
        Config dataclass instance
    """

    def make_dataclass(cls, data: Dict[str, Any]):
        """Create a dataclass instance from a dictionary, ignoring extra keys."""
        valid_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    server = make_dataclass(ServerConfig, config_dict.get("server", {}))
    safety = make_dataclass(SafetyConfig, config_dict.get("safety", {}))
    browser = make_dataclass(BrowserConfig, config_dict.get("browser", {}))
    metrics = make_dataclass(MetricsConfig, config_dict.get("metrics", {}))
    logging_config = make_dataclass(LoggingConfig, config_dict.get("logging", {}))
    kubernetes = make_dataclass(KubernetesConfig, config_dict.get("kubernetes", {}))

    # Collect custom/unknown sections
    known_sections = {"server", "safety", "browser", "metrics", "logging", "kubernetes"}
    custom = {k: v for k, v in config_dict.items() if k not in known_sections}

    return Config(
        server=server,
        safety=safety,
        browser=browser,
        metrics=metrics,
        logging=logging_config,
        kubernetes=kubernetes,
        custom=custom,
    )


def load_config(
    config_file: Optional[Union[str, Path]] = None,
    skip_env: bool = False,
) -> Config:
    """Load configuration from files and environment.

    Loading order (later takes precedence):
    1. Default values
    2. Main config file (~/.config/kubectl-mcp-server/config.toml)
    3. Drop-in files (~/.config/kubectl-mcp-server/config.d/*.toml) in sorted order
    4. Custom config file (if specified)
    5. Environment variables (unless skip_env=True)

    Args:
        config_file: Optional path to a specific config file
        skip_env: If True, skip environment variable overrides

    Returns:
        Loaded Config instance
    """
    global _config

    config_dict: Dict[str, Any] = {}
    paths = get_config_paths()

    # 1. Load main config file if it exists
    main_config = paths["main_config"]
    if main_config.exists():
        try:
            loaded = _load_toml_file(main_config)
            config_dict = _deep_merge(config_dict, loaded)
            logger.debug(f"Loaded config from {main_config}")
        except Exception as e:
            logger.warning(f"Failed to load {main_config}: {e}")

    # 2. Load drop-in configs in sorted order
    drop_in_dir = paths["drop_in_dir"]
    if drop_in_dir.exists() and drop_in_dir.is_dir():
        drop_in_files = sorted(drop_in_dir.glob("*.toml"))
        for drop_in_file in drop_in_files:
            try:
                loaded = _load_toml_file(drop_in_file)
                config_dict = _deep_merge(config_dict, loaded)
                logger.debug(f"Loaded drop-in config from {drop_in_file}")
            except Exception as e:
                logger.warning(f"Failed to load {drop_in_file}: {e}")

    # 3. Load custom config file if specified
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            try:
                loaded = _load_toml_file(config_path)
                config_dict = _deep_merge(config_dict, loaded)
                logger.debug(f"Loaded custom config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load {config_path}: {e}")
        else:
            logger.warning(f"Config file not found: {config_path}")

    # 4. Apply environment variable overrides
    if not skip_env:
        config_dict = _apply_env_overrides(config_dict)

    # 5. Validate configuration
    errors = validate_config(config_dict)
    if errors:
        for error in errors:
            logger.error(f"Config validation error: {error}")

    # 6. Convert to Config dataclass
    _config = _dict_to_config(config_dict)

    return _config


def get_config() -> Config:
    """Get the current configuration, loading if necessary.

    Returns:
        Current Config instance
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Config:
    """Reload configuration from files.

    This is called by the SIGHUP handler for runtime config updates.

    Returns:
        Newly loaded Config instance
    """
    global _config

    logger.info("Reloading configuration...")
    old_config = _config

    try:
        _config = load_config()
        logger.info("Configuration reloaded successfully")

        # Notify callbacks
        for callback in _config_callbacks:
            try:
                callback(_config)
            except Exception as e:
                logger.error(f"Config reload callback failed: {e}")

    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        _config = old_config
        raise

    return _config


def register_reload_callback(callback: Callable[[Config], None]) -> None:
    """Register a callback to be called when configuration is reloaded.

    Args:
        callback: Function that takes the new Config as argument
    """
    _config_callbacks.append(callback)


def unregister_reload_callback(callback: Callable[[Config], None]) -> None:
    """Unregister a previously registered reload callback.

    Args:
        callback: The callback function to remove
    """
    try:
        _config_callbacks.remove(callback)
    except ValueError:
        pass


def _sighup_handler(signum: int, frame: Any) -> None:
    """Handle SIGHUP signal for configuration reload."""
    logger.info("Received SIGHUP, reloading configuration...")
    try:
        reload_config()
    except Exception as e:
        logger.error(f"Configuration reload failed: {e}")


def setup_sighup_handler() -> bool:
    """Set up SIGHUP handler for runtime configuration reload.

    Returns:
        True if handler was set up, False if not supported (e.g., Windows)
    """
    if sys.platform == "win32":
        logger.debug("SIGHUP not supported on Windows")
        return False

    try:
        signal.signal(signal.SIGHUP, _sighup_handler)
        logger.debug("SIGHUP handler installed for config reload")
        return True
    except (OSError, AttributeError) as e:
        logger.warning(f"Could not install SIGHUP handler: {e}")
        return False


# Re-export Config from schema
Config = Config
