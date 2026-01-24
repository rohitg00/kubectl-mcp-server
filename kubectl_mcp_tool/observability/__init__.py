"""
Observability module for kubectl-mcp-server.

Provides:
- StatsCollector: Runtime statistics and metrics collection
- Prometheus metrics: Standard Prometheus format metrics
- OpenTelemetry tracing: Distributed tracing with OTLP export

Usage:
    # Stats collection
    from kubectl_mcp_tool.observability import get_stats_collector
    stats = get_stats_collector()
    stats.record_tool_call("get_pods", success=True, duration=0.5)

    # Prometheus metrics
    from kubectl_mcp_tool.observability import get_metrics
    metrics_text = get_metrics()

    # Tracing
    from kubectl_mcp_tool.observability import init_tracing, traced_tool_call
    init_tracing()
    with traced_tool_call("get_pods") as span:
        # execute tool
        pass
"""

from .stats import StatsCollector, get_stats_collector
from .metrics import (
    get_metrics,
    record_tool_call_metric,
    record_tool_error_metric,
    record_tool_duration_metric,
    is_prometheus_available,
)
from .tracing import (
    init_tracing,
    traced_tool_call,
    get_tracer,
    is_tracing_available,
    shutdown_tracing,
)

__all__ = [
    # Stats
    "StatsCollector",
    "get_stats_collector",
    # Metrics
    "get_metrics",
    "record_tool_call_metric",
    "record_tool_error_metric",
    "record_tool_duration_metric",
    "is_prometheus_available",
    # Tracing
    "init_tracing",
    "traced_tool_call",
    "get_tracer",
    "is_tracing_available",
    "shutdown_tracing",
]
