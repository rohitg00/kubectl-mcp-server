"""
OpenTelemetry tracing for kubectl-mcp-server.

Provides distributed tracing with OTLP export for production observability.

Environment Variables:
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint URL (e.g., http://localhost:4317)
    OTEL_EXPORTER_OTLP_HEADERS: Optional headers for OTLP exporter
    OTEL_TRACES_SAMPLER: Sampler type (always_on, always_off, traceidratio, parentbased_always_on)
    OTEL_TRACES_SAMPLER_ARG: Sampler argument (e.g., 0.5 for 50% sampling)
    OTEL_SERVICE_NAME: Service name (default: kubectl-mcp-server)
    OTEL_RESOURCE_ATTRIBUTES: Additional resource attributes

Requires: opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp (optional dependencies)
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Generator, Any, Dict

logger = logging.getLogger(__name__)

# Check if OpenTelemetry is available
_otel_available = False
_tracer = None
_tracer_provider = None

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider, Span
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    _otel_available = True
    logger.debug("OpenTelemetry tracing modules available")

except ImportError:
    logger.debug(
        "OpenTelemetry not installed. Tracing disabled. "
        "Install with: pip install kubectl-mcp-server[observability]"
    )


def is_tracing_available() -> bool:
    """Check if OpenTelemetry tracing is available."""
    return _otel_available


def _get_sampler():
    """
    Get the configured sampler based on environment variables.

    Supports:
    - always_on: Always sample
    - always_off: Never sample
    - traceidratio: Sample based on ratio (OTEL_TRACES_SAMPLER_ARG)
    - parentbased_always_on: Parent-based with always_on default
    """
    if not _otel_available:
        return None

    from opentelemetry.sdk.trace.sampling import (
        ALWAYS_ON,
        ALWAYS_OFF,
        TraceIdRatioBased,
        ParentBasedTraceIdRatio,
    )

    sampler_type = os.environ.get("OTEL_TRACES_SAMPLER", "parentbased_always_on").lower()
    sampler_arg = os.environ.get("OTEL_TRACES_SAMPLER_ARG", "1.0")

    try:
        ratio = float(sampler_arg)
    except ValueError:
        ratio = 1.0
        logger.warning(f"Invalid OTEL_TRACES_SAMPLER_ARG: {sampler_arg}, using 1.0")

    if sampler_type == "always_on":
        return ALWAYS_ON
    elif sampler_type == "always_off":
        return ALWAYS_OFF
    elif sampler_type == "traceidratio":
        return TraceIdRatioBased(ratio)
    elif sampler_type in ("parentbased_always_on", "parentbased_traceidratio"):
        return ParentBasedTraceIdRatio(ratio)
    else:
        logger.warning(f"Unknown sampler type: {sampler_type}, using parentbased_always_on")
        return ParentBasedTraceIdRatio(ratio)


def init_tracing(
    service_name: Optional[str] = None,
    service_version: Optional[str] = None,
) -> bool:
    """
    Initialize OpenTelemetry tracing.

    Args:
        service_name: Service name (default from OTEL_SERVICE_NAME or kubectl-mcp-server)
        service_version: Service version (default from package version)

    Returns:
        True if tracing was initialized, False otherwise
    """
    global _tracer, _tracer_provider

    if not _otel_available:
        logger.debug("OpenTelemetry not available, skipping tracing init")
        return False

    # Already initialized
    if _tracer is not None:
        return True

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME

        # Get service name
        if service_name is None:
            service_name = os.environ.get("OTEL_SERVICE_NAME", "kubectl-mcp-server")

        # Get service version
        if service_version is None:
            try:
                from kubectl_mcp_tool import __version__
                service_version = __version__
            except ImportError:
                service_version = "unknown"

        # Parse additional resource attributes
        resource_attrs = {
            SERVICE_NAME: service_name,
            "service.version": service_version,
        }

        # Add custom attributes from environment
        custom_attrs = os.environ.get("OTEL_RESOURCE_ATTRIBUTES", "")
        if custom_attrs:
            for attr in custom_attrs.split(","):
                if "=" in attr:
                    key, value = attr.split("=", 1)
                    resource_attrs[key.strip()] = value.strip()

        # Create resource
        resource = Resource.create(resource_attrs)

        # Create tracer provider with sampler
        sampler = _get_sampler()
        _tracer_provider = TracerProvider(resource=resource, sampler=sampler)

        # Add exporter based on environment
        otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

        if otlp_endpoint:
            # Use OTLP exporter
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

                otlp_headers = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
                headers_dict = {}
                if otlp_headers:
                    for header in otlp_headers.split(","):
                        if "=" in header:
                            key, value = header.split("=", 1)
                            headers_dict[key.strip()] = value.strip()

                exporter = OTLPSpanExporter(
                    endpoint=otlp_endpoint,
                    headers=headers_dict if headers_dict else None,
                )
                _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(f"OpenTelemetry OTLP exporter configured: {otlp_endpoint}")

            except ImportError:
                # Try HTTP exporter as fallback
                try:
                    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPOTLPSpanExporter

                    exporter = HTTPOTLPSpanExporter(endpoint=f"{otlp_endpoint}/v1/traces")
                    _tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
                    logger.info(f"OpenTelemetry HTTP OTLP exporter configured: {otlp_endpoint}")

                except ImportError:
                    logger.warning(
                        "OTLP exporter not available. "
                        "Install with: pip install opentelemetry-exporter-otlp"
                    )
                    # Fall back to console exporter for debugging
                    from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                    _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
                    logger.info("Using console span exporter (OTLP exporter not available)")

        elif os.environ.get("OTEL_TRACES_EXPORTER") == "console":
            # Explicitly use console exporter
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            _tracer_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            logger.info("Using console span exporter")
        else:
            # No exporter configured, log a message
            logger.debug(
                "No OTEL_EXPORTER_OTLP_ENDPOINT set, tracing spans will not be exported. "
                "Set OTEL_TRACES_EXPORTER=console for debug output."
            )

        # Set the global tracer provider
        trace.set_tracer_provider(_tracer_provider)

        # Create tracer
        _tracer = trace.get_tracer(
            "kubectl-mcp-server",
            service_version,
        )

        logger.info(f"OpenTelemetry tracing initialized for {service_name} v{service_version}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry tracing: {e}")
        return False


def get_tracer():
    """
    Get the OpenTelemetry tracer.

    Returns:
        The tracer instance, or None if not initialized
    """
    return _tracer


def shutdown_tracing() -> None:
    """Shutdown the tracer provider and flush any pending spans."""
    global _tracer, _tracer_provider

    if _tracer_provider is not None:
        try:
            _tracer_provider.shutdown()
            logger.debug("OpenTelemetry tracing shut down")
        except Exception as e:
            logger.error(f"Error shutting down tracing: {e}")

    _tracer = None
    _tracer_provider = None


@contextmanager
def traced_tool_call(
    tool_name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> Generator[Any, None, None]:
    """
    Context manager for tracing a tool call.

    Creates a span for the tool call and records attributes and errors.

    Args:
        tool_name: Name of the tool being called
        attributes: Optional additional span attributes

    Yields:
        The span object (or a no-op if tracing is disabled)

    Example:
        with traced_tool_call("get_pods", {"namespace": "default"}) as span:
            result = await get_pods(namespace="default")
            span.set_attribute("pod_count", len(result))
    """
    if not _otel_available or _tracer is None:
        # Return a no-op context
        yield None
        return

    from opentelemetry.trace import Status, StatusCode

    with _tracer.start_as_current_span(
        f"mcp.tool.{tool_name}",
        kind=trace.SpanKind.INTERNAL,
    ) as span:
        # Set base attributes
        span.set_attribute("mcp.tool.name", tool_name)

        # Set additional attributes
        if attributes:
            for key, value in attributes.items():
                if isinstance(value, (str, int, float, bool)):
                    span.set_attribute(f"mcp.tool.{key}", value)

        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_attribute(key: str, value: Any) -> None:
    """
    Add an attribute to the current span.

    Args:
        key: Attribute key
        value: Attribute value (must be str, int, float, or bool)
    """
    if not _otel_available:
        return

    span = trace.get_current_span()
    if span is not None and isinstance(value, (str, int, float, bool)):
        span.set_attribute(key, value)


def record_span_exception(exception: Exception) -> None:
    """
    Record an exception on the current span.

    Args:
        exception: The exception to record
    """
    if not _otel_available:
        return

    span = trace.get_current_span()
    if span is not None:
        span.record_exception(exception)
