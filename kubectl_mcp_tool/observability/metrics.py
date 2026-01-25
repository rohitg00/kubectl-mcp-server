"""
Prometheus metrics for kubectl-mcp-server.

Provides standard Prometheus format metrics for production monitoring.

Metrics exposed:
- mcp_tool_calls_total: Counter of tool invocations (labels: tool_name, status)
- mcp_tool_errors_total: Counter of tool errors (labels: tool_name, error_type)
- mcp_tool_duration_seconds: Histogram of tool call durations (labels: tool_name)
- mcp_http_requests_total: Counter of HTTP requests (labels: endpoint, method, status)
- mcp_server_info: Gauge with server metadata

Requires: prometheus-client>=0.19.0 (optional dependency)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Check if prometheus_client is available
_prometheus_available = False
_REGISTRY = None
_tool_calls_counter = None
_tool_errors_counter = None
_tool_duration_histogram = None
_http_requests_counter = None
_server_info_gauge = None

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
    )
    _prometheus_available = True

    # Create a custom registry to avoid conflicts
    _REGISTRY = CollectorRegistry()

    # Tool call counter
    _tool_calls_counter = Counter(
        "mcp_tool_calls_total",
        "Total number of MCP tool calls",
        ["tool_name", "status"],
        registry=_REGISTRY,
    )

    # Tool error counter
    _tool_errors_counter = Counter(
        "mcp_tool_errors_total",
        "Total number of MCP tool errors",
        ["tool_name", "error_type"],
        registry=_REGISTRY,
    )

    # Tool duration histogram
    # Buckets optimized for typical k8s API call durations
    _tool_duration_histogram = Histogram(
        "mcp_tool_duration_seconds",
        "Duration of MCP tool calls in seconds",
        ["tool_name"],
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
        registry=_REGISTRY,
    )

    # HTTP requests counter
    _http_requests_counter = Counter(
        "mcp_http_requests_total",
        "Total number of HTTP requests",
        ["endpoint", "method", "status"],
        registry=_REGISTRY,
    )

    # Server info gauge (version, features)
    _server_info_gauge = Gauge(
        "mcp_server_info",
        "MCP server information",
        ["version", "transport"],
        registry=_REGISTRY,
    )

    logger.debug("Prometheus metrics initialized successfully")

except ImportError:
    logger.debug(
        "prometheus_client not installed. Prometheus metrics disabled. "
        "Install with: pip install kubectl-mcp-server[observability]"
    )


def is_prometheus_available() -> bool:
    """Check if Prometheus client is available."""
    return _prometheus_available


def record_tool_call_metric(
    tool_name: str,
    success: bool = True,
    duration: float = 0.0
) -> None:
    """
    Record a tool call in Prometheus metrics.

    Args:
        tool_name: Name of the tool called
        success: Whether the call succeeded
        duration: Call duration in seconds
    """
    if not _prometheus_available:
        return

    status = "success" if success else "error"
    _tool_calls_counter.labels(tool_name=tool_name, status=status).inc()

    if duration > 0:
        _tool_duration_histogram.labels(tool_name=tool_name).observe(duration)


def record_tool_error_metric(
    tool_name: str,
    error_type: str = "unknown"
) -> None:
    """
    Record a tool error in Prometheus metrics.

    Args:
        tool_name: Name of the tool that errored
        error_type: Type/category of error (e.g., "timeout", "validation", "k8s_api")
    """
    if not _prometheus_available:
        return

    _tool_errors_counter.labels(
        tool_name=tool_name,
        error_type=error_type
    ).inc()


def record_tool_duration_metric(tool_name: str, duration: float) -> None:
    """
    Record tool duration in Prometheus histogram.

    Args:
        tool_name: Name of the tool
        duration: Duration in seconds
    """
    if not _prometheus_available:
        return

    _tool_duration_histogram.labels(tool_name=tool_name).observe(duration)


def record_http_request_metric(
    endpoint: str,
    method: str,
    status: int = 200
) -> None:
    """
    Record an HTTP request in Prometheus metrics.

    Args:
        endpoint: Request endpoint path
        method: HTTP method
        status: HTTP status code
    """
    if not _prometheus_available:
        return

    _http_requests_counter.labels(
        endpoint=endpoint,
        method=method,
        status=str(status)
    ).inc()


def set_server_info(version: str, transport: str) -> None:
    """
    Set server info in Prometheus gauge.

    Args:
        version: Server version
        transport: Transport type (stdio, sse, http)
    """
    if not _prometheus_available:
        return

    _server_info_gauge.labels(version=version, transport=transport).set(1)


def get_metrics() -> str:
    """
    Get metrics in Prometheus text format.

    Returns:
        Prometheus metrics as text, or error message if unavailable
    """
    if not _prometheus_available:
        return (
            "# Prometheus metrics not available.\n"
            "# Install with: pip install kubectl-mcp-server[observability]\n"
        )

    try:
        return generate_latest(_REGISTRY).decode("utf-8")
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        return f"# Error generating metrics: {e}\n"


def get_metrics_content_type() -> str:
    """
    Get the content type for Prometheus metrics.

    Returns:
        Prometheus content type string
    """
    if not _prometheus_available:
        return "text/plain; charset=utf-8"
    return CONTENT_TYPE_LATEST
