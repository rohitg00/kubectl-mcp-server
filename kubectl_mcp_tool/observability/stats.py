"""
Runtime statistics collection for kubectl-mcp-server.

Provides a singleton StatsCollector that tracks:
- tool_calls_total: Total number of tool invocations
- tool_errors_total: Total number of tool errors
- tool_calls_by_name: Breakdown of calls by tool name
- http_requests_total: Total HTTP requests (for SSE/HTTP transports)
- uptime: Server uptime in seconds
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ToolStats:
    """Statistics for a single tool."""
    calls: int = 0
    errors: int = 0
    total_duration: float = 0.0
    last_call_time: Optional[float] = None
    last_error_time: Optional[float] = None


class StatsCollector:
    """
    Singleton class for collecting runtime statistics.

    Thread-safe statistics collection for production observability.

    Usage:
        stats = get_stats_collector()
        stats.record_tool_call("get_pods", success=True, duration=0.5)

        # Get current stats
        data = stats.get_stats()
    """

    _instance: Optional["StatsCollector"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "StatsCollector":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the stats collector (only once)."""
        if self._initialized:
            return

        self._stats_lock = threading.Lock()
        self._start_time = time.time()

        # Core counters
        self._tool_calls_total = 0
        self._tool_errors_total = 0
        self._http_requests_total = 0

        # Per-tool statistics
        self._tool_stats: Dict[str, ToolStats] = defaultdict(ToolStats)

        # HTTP request breakdown
        self._http_requests_by_endpoint: Dict[str, int] = defaultdict(int)
        self._http_requests_by_method: Dict[str, int] = defaultdict(int)

        self._initialized = True

    def record_tool_call(
        self,
        tool_name: str,
        success: bool = True,
        duration: float = 0.0
    ) -> None:
        """
        Record a tool call.

        Args:
            tool_name: Name of the tool that was called
            success: Whether the call succeeded
            duration: Call duration in seconds
        """
        with self._stats_lock:
            self._tool_calls_total += 1

            stats = self._tool_stats[tool_name]
            stats.calls += 1
            stats.total_duration += duration
            stats.last_call_time = time.time()

            if not success:
                self._tool_errors_total += 1
                stats.errors += 1
                stats.last_error_time = time.time()

    def record_tool_error(self, tool_name: str) -> None:
        """
        Record a tool error (shorthand for failed call).

        Args:
            tool_name: Name of the tool that errored
        """
        self.record_tool_call(tool_name, success=False)

    def record_http_request(
        self,
        endpoint: str = "/",
        method: str = "POST"
    ) -> None:
        """
        Record an HTTP request.

        Args:
            endpoint: Request endpoint path
            method: HTTP method (GET, POST, etc.)
        """
        with self._stats_lock:
            self._http_requests_total += 1
            self._http_requests_by_endpoint[endpoint] += 1
            self._http_requests_by_method[method] += 1

    @property
    def uptime(self) -> float:
        """Get server uptime in seconds."""
        return time.time() - self._start_time

    @property
    def tool_calls_total(self) -> int:
        """Get total tool calls."""
        with self._stats_lock:
            return self._tool_calls_total

    @property
    def tool_errors_total(self) -> int:
        """Get total tool errors."""
        with self._stats_lock:
            return self._tool_errors_total

    @property
    def http_requests_total(self) -> int:
        """Get total HTTP requests."""
        with self._stats_lock:
            return self._http_requests_total

    def get_tool_stats(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dictionary with tool statistics or None if not found
        """
        with self._stats_lock:
            if tool_name not in self._tool_stats:
                return None

            stats = self._tool_stats[tool_name]
            avg_duration = (
                stats.total_duration / stats.calls
                if stats.calls > 0 else 0.0
            )

            return {
                "calls": stats.calls,
                "errors": stats.errors,
                "error_rate": stats.errors / stats.calls if stats.calls > 0 else 0.0,
                "total_duration_seconds": stats.total_duration,
                "average_duration_seconds": avg_duration,
                "last_call_time": stats.last_call_time,
                "last_error_time": stats.last_error_time,
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get all statistics as a JSON-serializable dictionary.

        Returns:
            Dictionary containing all collected statistics
        """
        with self._stats_lock:
            # Calculate tool-level stats
            tool_stats_dict = {}
            for tool_name, stats in self._tool_stats.items():
                avg_duration = (
                    stats.total_duration / stats.calls
                    if stats.calls > 0 else 0.0
                )
                tool_stats_dict[tool_name] = {
                    "calls": stats.calls,
                    "errors": stats.errors,
                    "error_rate": stats.errors / stats.calls if stats.calls > 0 else 0.0,
                    "average_duration_seconds": round(avg_duration, 4),
                }

            # Sort tools by call count (descending)
            sorted_tools = dict(
                sorted(
                    tool_stats_dict.items(),
                    key=lambda x: x[1]["calls"],
                    reverse=True
                )
            )

            return {
                "uptime_seconds": round(self.uptime, 2),
                "tool_calls_total": self._tool_calls_total,
                "tool_errors_total": self._tool_errors_total,
                "tool_error_rate": (
                    self._tool_errors_total / self._tool_calls_total
                    if self._tool_calls_total > 0 else 0.0
                ),
                "http_requests_total": self._http_requests_total,
                "http_requests_by_endpoint": dict(self._http_requests_by_endpoint),
                "http_requests_by_method": dict(self._http_requests_by_method),
                "tool_calls_by_name": sorted_tools,
                "unique_tools_called": len(self._tool_stats),
            }

    def reset(self) -> None:
        """Reset all statistics (useful for testing)."""
        with self._stats_lock:
            self._start_time = time.time()
            self._tool_calls_total = 0
            self._tool_errors_total = 0
            self._http_requests_total = 0
            self._tool_stats.clear()
            self._http_requests_by_endpoint.clear()
            self._http_requests_by_method.clear()


# Module-level singleton accessor
_stats_collector: Optional[StatsCollector] = None


def get_stats_collector() -> StatsCollector:
    """
    Get the singleton StatsCollector instance.

    Returns:
        The global StatsCollector instance
    """
    global _stats_collector
    if _stats_collector is None:
        _stats_collector = StatsCollector()
    return _stats_collector
