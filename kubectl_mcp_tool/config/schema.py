"""Configuration schema definitions for kubectl-mcp-server.

Defines dataclasses for type-safe configuration with validation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """MCP server configuration."""

    transport: str = "streamable-http"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    log_file: Optional[str] = None
    log_level: str = "INFO"

    def __post_init__(self):
        """Validate configuration values."""
        valid_transports = {"stdio", "sse", "streamable-http"}
        if self.transport not in valid_transports:
            raise ValueError(f"Invalid transport: {self.transport}. Must be one of {valid_transports}")

        if not 1 <= self.port <= 65535:
            raise ValueError(f"Invalid port: {self.port}. Must be between 1 and 65535")

        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Invalid log_level: {self.log_level}. Must be one of {valid_log_levels}")


@dataclass
class SafetyConfig:
    """Safety mode configuration."""

    mode: str = "normal"

    # Additional safety settings
    confirm_destructive: bool = False
    max_delete_count: int = 10
    blocked_namespaces: List[str] = field(default_factory=lambda: ["kube-system", "kube-public"])

    def __post_init__(self):
        """Validate safety mode."""
        valid_modes = {"normal", "read-only", "disable-destructive"}
        if self.mode not in valid_modes:
            raise ValueError(f"Invalid safety mode: {self.mode}. Must be one of {valid_modes}")


@dataclass
class BrowserConfig:
    """Browser automation configuration."""

    enabled: bool = False
    provider: str = "local"
    headed: bool = False
    timeout: int = 60
    max_retries: int = 3

    # Provider-specific settings
    browserbase_api_key: Optional[str] = None
    browserbase_project_id: Optional[str] = None
    browseruse_api_key: Optional[str] = None
    cdp_url: Optional[str] = None

    def __post_init__(self):
        """Validate browser configuration."""
        valid_providers = {"local", "browserbase", "browseruse", "cdp"}
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid browser provider: {self.provider}. Must be one of {valid_providers}")


@dataclass
class MetricsConfig:
    """Metrics and observability configuration."""

    enabled: bool = False
    endpoint: str = "/metrics"

    # Tracing settings
    tracing_enabled: bool = False
    otlp_endpoint: Optional[str] = None
    service_name: str = "kubectl-mcp-server"
    sample_rate: float = 1.0

    def __post_init__(self):
        """Validate metrics configuration."""
        if not 0.0 <= self.sample_rate <= 1.0:
            raise ValueError(f"Invalid sample_rate: {self.sample_rate}. Must be between 0.0 and 1.0")


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    max_size_mb: int = 10
    backup_count: int = 5

    def __post_init__(self):
        """Validate logging configuration."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {self.level}. Must be one of {valid_levels}")


@dataclass
class KubernetesConfig:
    """Kubernetes client configuration."""

    context: Optional[str] = None
    kubeconfig: Optional[str] = None
    in_cluster: bool = False
    default_namespace: str = "default"
    timeout: int = 30


@dataclass
class Config:
    """Root configuration container."""

    server: ServerConfig = field(default_factory=ServerConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    kubernetes: KubernetesConfig = field(default_factory=KubernetesConfig)

    # Custom settings from drop-in configs
    custom: Dict[str, Any] = field(default_factory=dict)


def validate_config(config_dict: Dict[str, Any]) -> List[str]:
    """Validate configuration dictionary and return list of errors.

    Args:
        config_dict: Configuration dictionary to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Validate server section
    if "server" in config_dict:
        server = config_dict["server"]
        valid_transports = {"stdio", "sse", "streamable-http"}
        if server.get("transport") and server["transport"] not in valid_transports:
            errors.append(f"Invalid server.transport: {server['transport']}")

        port = server.get("port")
        if port is not None and not (1 <= port <= 65535):
            errors.append(f"Invalid server.port: {port}")

    # Validate safety section
    if "safety" in config_dict:
        safety = config_dict["safety"]
        valid_modes = {"normal", "read-only", "disable-destructive"}
        if safety.get("mode") and safety["mode"] not in valid_modes:
            errors.append(f"Invalid safety.mode: {safety['mode']}")

    # Validate browser section
    if "browser" in config_dict:
        browser = config_dict["browser"]
        valid_providers = {"local", "browserbase", "browseruse", "cdp"}
        if browser.get("provider") and browser["provider"] not in valid_providers:
            errors.append(f"Invalid browser.provider: {browser['provider']}")

    # Validate metrics section
    if "metrics" in config_dict:
        metrics = config_dict["metrics"]
        sample_rate = metrics.get("sample_rate")
        if sample_rate is not None and not (0.0 <= sample_rate <= 1.0):
            errors.append(f"Invalid metrics.sample_rate: {sample_rate}")

    return errors
