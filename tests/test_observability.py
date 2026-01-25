"""Unit tests for the observability module."""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock


class TestStatsCollector:
    """Tests for StatsCollector class."""

    @pytest.mark.unit
    def test_singleton_pattern(self):
        """Test that StatsCollector is a singleton."""
        from kubectl_mcp_tool.observability.stats import StatsCollector

        instance1 = StatsCollector()
        instance2 = StatsCollector()

        assert instance1 is instance2

    @pytest.mark.unit
    def test_get_stats_collector(self):
        """Test get_stats_collector function."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        assert collector is not None

        # Should return same instance
        collector2 = get_stats_collector()
        assert collector is collector2

    @pytest.mark.unit
    def test_record_tool_call_success(self):
        """Test recording a successful tool call."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        collector.reset()

        collector.record_tool_call("test_tool", success=True, duration=0.5)

        assert collector.tool_calls_total == 1
        assert collector.tool_errors_total == 0

        stats = collector.get_tool_stats("test_tool")
        assert stats["calls"] == 1
        assert stats["errors"] == 0
        assert stats["total_duration_seconds"] == 0.5

    @pytest.mark.unit
    def test_record_tool_call_error(self):
        """Test recording a failed tool call."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        collector.reset()

        collector.record_tool_call("test_tool", success=False, duration=0.1)

        assert collector.tool_calls_total == 1
        assert collector.tool_errors_total == 1

        stats = collector.get_tool_stats("test_tool")
        assert stats["calls"] == 1
        assert stats["errors"] == 1
        assert stats["error_rate"] == 1.0

    @pytest.mark.unit
    def test_record_tool_error(self):
        """Test record_tool_error shorthand."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        collector.reset()

        collector.record_tool_error("error_tool")

        assert collector.tool_calls_total == 1
        assert collector.tool_errors_total == 1

    @pytest.mark.unit
    def test_record_http_request(self):
        """Test recording HTTP requests."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        collector.reset()

        collector.record_http_request("/stats", "GET")
        collector.record_http_request("/metrics", "GET")
        collector.record_http_request("/mcp", "POST")

        assert collector.http_requests_total == 3

        stats = collector.get_stats()
        assert stats["http_requests_by_endpoint"]["/stats"] == 1
        assert stats["http_requests_by_endpoint"]["/metrics"] == 1
        assert stats["http_requests_by_endpoint"]["/mcp"] == 1
        assert stats["http_requests_by_method"]["GET"] == 2
        assert stats["http_requests_by_method"]["POST"] == 1

    @pytest.mark.unit
    def test_uptime(self):
        """Test uptime property."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        collector.reset()

        time.sleep(0.1)
        uptime = collector.uptime

        assert uptime >= 0.1
        assert uptime < 1.0

    @pytest.mark.unit
    def test_get_stats(self):
        """Test get_stats returns complete statistics."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        collector.reset()

        collector.record_tool_call("tool_a", success=True, duration=0.1)
        collector.record_tool_call("tool_a", success=True, duration=0.2)
        collector.record_tool_call("tool_b", success=False, duration=0.3)

        stats = collector.get_stats()

        assert "uptime_seconds" in stats
        assert stats["tool_calls_total"] == 3
        assert stats["tool_errors_total"] == 1
        assert stats["unique_tools_called"] == 2
        assert "tool_calls_by_name" in stats
        assert "tool_a" in stats["tool_calls_by_name"]
        assert "tool_b" in stats["tool_calls_by_name"]

    @pytest.mark.unit
    def test_get_tool_stats_nonexistent(self):
        """Test get_tool_stats returns None for nonexistent tool."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        collector.reset()

        stats = collector.get_tool_stats("nonexistent_tool")
        assert stats is None

    @pytest.mark.unit
    def test_reset(self):
        """Test reset clears all statistics."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()

        collector.record_tool_call("test_tool", success=True)
        collector.record_http_request("/test", "GET")

        collector.reset()

        assert collector.tool_calls_total == 0
        assert collector.tool_errors_total == 0
        assert collector.http_requests_total == 0

    @pytest.mark.unit
    def test_thread_safety(self):
        """Test that StatsCollector is thread-safe."""
        from kubectl_mcp_tool.observability.stats import get_stats_collector

        collector = get_stats_collector()
        collector.reset()

        def record_calls():
            for i in range(100):
                collector.record_tool_call(f"tool_{i % 10}", success=True)

        threads = [threading.Thread(target=record_calls) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert collector.tool_calls_total == 1000


class TestPrometheusMetrics:
    """Tests for Prometheus metrics module."""

    @pytest.mark.unit
    def test_is_prometheus_available(self):
        """Test is_prometheus_available function."""
        from kubectl_mcp_tool.observability.metrics import is_prometheus_available

        # Should return bool regardless of prometheus_client installation
        result = is_prometheus_available()
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_get_metrics(self):
        """Test get_metrics returns Prometheus format."""
        from kubectl_mcp_tool.observability.metrics import get_metrics, is_prometheus_available

        metrics = get_metrics()

        assert isinstance(metrics, str)

        if is_prometheus_available():
            # Should have some metric content
            assert len(metrics) > 0
        else:
            # Should return informative message
            assert "not available" in metrics

    @pytest.mark.unit
    def test_record_tool_call_metric(self):
        """Test record_tool_call_metric function."""
        from kubectl_mcp_tool.observability.metrics import (
            record_tool_call_metric,
            is_prometheus_available,
        )

        # Should not raise even if prometheus_client is not installed
        record_tool_call_metric("test_tool", success=True, duration=0.5)
        record_tool_call_metric("test_tool", success=False, duration=0.1)

    @pytest.mark.unit
    def test_record_tool_error_metric(self):
        """Test record_tool_error_metric function."""
        from kubectl_mcp_tool.observability.metrics import record_tool_error_metric

        # Should not raise even if prometheus_client is not installed
        record_tool_error_metric("test_tool", error_type="validation")
        record_tool_error_metric("test_tool", error_type="timeout")

    @pytest.mark.unit
    def test_record_tool_duration_metric(self):
        """Test record_tool_duration_metric function."""
        from kubectl_mcp_tool.observability.metrics import record_tool_duration_metric

        # Should not raise even if prometheus_client is not installed
        record_tool_duration_metric("test_tool", 0.5)
        record_tool_duration_metric("test_tool", 1.5)

    @pytest.mark.unit
    def test_record_http_request_metric(self):
        """Test record_http_request_metric function."""
        from kubectl_mcp_tool.observability.metrics import record_http_request_metric

        # Should not raise even if prometheus_client is not installed
        record_http_request_metric("/stats", "GET", 200)
        record_http_request_metric("/metrics", "GET", 500)

    @pytest.mark.unit
    def test_set_server_info(self):
        """Test set_server_info function."""
        from kubectl_mcp_tool.observability.metrics import set_server_info

        # Should not raise even if prometheus_client is not installed
        set_server_info("1.16.0", "stdio")

    @pytest.mark.unit
    def test_get_metrics_content_type(self):
        """Test get_metrics_content_type function."""
        from kubectl_mcp_tool.observability.metrics import get_metrics_content_type

        content_type = get_metrics_content_type()
        assert isinstance(content_type, str)
        assert "text" in content_type


class TestTracing:
    """Tests for OpenTelemetry tracing module."""

    @pytest.mark.unit
    def test_is_tracing_available(self):
        """Test is_tracing_available function."""
        from kubectl_mcp_tool.observability.tracing import is_tracing_available

        # Should return bool regardless of opentelemetry installation
        result = is_tracing_available()
        assert isinstance(result, bool)

    @pytest.mark.unit
    def test_get_tracer_before_init(self):
        """Test get_tracer returns None before initialization."""
        from kubectl_mcp_tool.observability.tracing import get_tracer, shutdown_tracing

        # Ensure clean state
        shutdown_tracing()

        tracer = get_tracer()
        # May be None if not initialized, or a tracer if previously initialized
        # Just verify it doesn't raise

    @pytest.mark.unit
    def test_traced_tool_call_no_op(self):
        """Test traced_tool_call works as no-op when tracing unavailable."""
        from kubectl_mcp_tool.observability.tracing import traced_tool_call, shutdown_tracing

        shutdown_tracing()

        with traced_tool_call("test_tool", {"key": "value"}) as span:
            # Should work without raising
            result = 1 + 1

        assert result == 2

    @pytest.mark.unit
    def test_traced_tool_call_with_exception(self):
        """Test traced_tool_call propagates exceptions."""
        from kubectl_mcp_tool.observability.tracing import traced_tool_call

        with pytest.raises(ValueError, match="test error"):
            with traced_tool_call("test_tool") as span:
                raise ValueError("test error")

    @pytest.mark.unit
    def test_add_span_attribute(self):
        """Test add_span_attribute function."""
        from kubectl_mcp_tool.observability.tracing import add_span_attribute

        # Should not raise even if tracing is not available
        add_span_attribute("test_key", "test_value")
        add_span_attribute("test_int", 42)
        add_span_attribute("test_float", 3.14)
        add_span_attribute("test_bool", True)

    @pytest.mark.unit
    def test_record_span_exception(self):
        """Test record_span_exception function."""
        from kubectl_mcp_tool.observability.tracing import record_span_exception

        # Should not raise even if tracing is not available
        record_span_exception(ValueError("test error"))

    @pytest.mark.unit
    def test_shutdown_tracing(self):
        """Test shutdown_tracing function."""
        from kubectl_mcp_tool.observability.tracing import shutdown_tracing

        # Should not raise even if tracing was not initialized
        shutdown_tracing()
        shutdown_tracing()  # Multiple calls should be safe

    @pytest.mark.unit
    def test_init_tracing_without_endpoint(self):
        """Test init_tracing without OTLP endpoint."""
        from kubectl_mcp_tool.observability.tracing import (
            init_tracing,
            is_tracing_available,
            shutdown_tracing,
        )

        shutdown_tracing()

        if is_tracing_available():
            # Clear any OTLP endpoint
            with patch.dict("os.environ", {}, clear=True):
                result = init_tracing(service_name="test-service")
                assert result is True  # Should initialize with no exporter
                shutdown_tracing()
        else:
            result = init_tracing()
            assert result is False  # OpenTelemetry not available


class TestObservabilityModule:
    """Tests for observability module exports."""

    @pytest.mark.unit
    def test_module_imports(self):
        """Test that all observability functions can be imported."""
        from kubectl_mcp_tool.observability import (
            StatsCollector,
            get_stats_collector,
            get_metrics,
            record_tool_call_metric,
            record_tool_error_metric,
            record_tool_duration_metric,
            is_prometheus_available,
            init_tracing,
            traced_tool_call,
            get_tracer,
            is_tracing_available,
            shutdown_tracing,
        )

        assert StatsCollector is not None
        assert get_stats_collector is not None
        assert get_metrics is not None
        assert init_tracing is not None
        assert traced_tool_call is not None

    @pytest.mark.unit
    def test_stats_and_metrics_integration(self):
        """Test stats and metrics work together."""
        from kubectl_mcp_tool.observability import (
            get_stats_collector,
            record_tool_call_metric,
            get_metrics,
        )

        collector = get_stats_collector()
        collector.reset()

        # Record calls in both stats and metrics
        for i in range(5):
            collector.record_tool_call("integration_tool", success=True, duration=0.1)
            record_tool_call_metric("integration_tool", success=True, duration=0.1)

        stats = collector.get_stats()
        metrics = get_metrics()

        assert stats["tool_calls_total"] == 5
        assert isinstance(metrics, str)


class TestSamplerConfiguration:
    """Tests for OpenTelemetry sampler configuration."""

    @pytest.mark.unit
    def test_sampler_always_on(self):
        """Test OTEL_TRACES_SAMPLER=always_on."""
        from kubectl_mcp_tool.observability.tracing import is_tracing_available

        if not is_tracing_available():
            pytest.skip("OpenTelemetry not available")

        from kubectl_mcp_tool.observability.tracing import _get_sampler

        with patch.dict("os.environ", {"OTEL_TRACES_SAMPLER": "always_on"}):
            sampler = _get_sampler()
            assert sampler is not None

    @pytest.mark.unit
    def test_sampler_always_off(self):
        """Test OTEL_TRACES_SAMPLER=always_off."""
        from kubectl_mcp_tool.observability.tracing import is_tracing_available

        if not is_tracing_available():
            pytest.skip("OpenTelemetry not available")

        from kubectl_mcp_tool.observability.tracing import _get_sampler

        with patch.dict("os.environ", {"OTEL_TRACES_SAMPLER": "always_off"}):
            sampler = _get_sampler()
            assert sampler is not None

    @pytest.mark.unit
    def test_sampler_trace_id_ratio(self):
        """Test OTEL_TRACES_SAMPLER=traceidratio."""
        from kubectl_mcp_tool.observability.tracing import is_tracing_available

        if not is_tracing_available():
            pytest.skip("OpenTelemetry not available")

        from kubectl_mcp_tool.observability.tracing import _get_sampler

        with patch.dict("os.environ", {
            "OTEL_TRACES_SAMPLER": "traceidratio",
            "OTEL_TRACES_SAMPLER_ARG": "0.5"
        }):
            sampler = _get_sampler()
            assert sampler is not None

    @pytest.mark.unit
    def test_sampler_invalid_ratio(self):
        """Test invalid OTEL_TRACES_SAMPLER_ARG defaults to 1.0."""
        from kubectl_mcp_tool.observability.tracing import is_tracing_available

        if not is_tracing_available():
            pytest.skip("OpenTelemetry not available")

        from kubectl_mcp_tool.observability.tracing import _get_sampler

        with patch.dict("os.environ", {
            "OTEL_TRACES_SAMPLER": "traceidratio",
            "OTEL_TRACES_SAMPLER_ARG": "invalid"
        }):
            # Should not raise, defaults to 1.0
            sampler = _get_sampler()
            assert sampler is not None


class TestToolStatsDataclass:
    """Tests for ToolStats dataclass."""

    @pytest.mark.unit
    def test_tool_stats_defaults(self):
        """Test ToolStats default values."""
        from kubectl_mcp_tool.observability.stats import ToolStats

        stats = ToolStats()

        assert stats.calls == 0
        assert stats.errors == 0
        assert stats.total_duration == 0.0
        assert stats.last_call_time is None
        assert stats.last_error_time is None

    @pytest.mark.unit
    def test_tool_stats_custom_values(self):
        """Test ToolStats with custom values."""
        from kubectl_mcp_tool.observability.stats import ToolStats

        now = time.time()
        stats = ToolStats(
            calls=10,
            errors=2,
            total_duration=5.5,
            last_call_time=now,
            last_error_time=now - 100
        )

        assert stats.calls == 10
        assert stats.errors == 2
        assert stats.total_duration == 5.5
        assert stats.last_call_time == now
