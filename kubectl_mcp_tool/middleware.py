"""Cross-cutting tool-call guards: safety mode, option injection, scopes, redaction, metrics."""

import logging
import time
from typing import Any, Iterable

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token, get_http_request
from fastmcp.server.middleware import Middleware
from fastmcp.tools import InputRequiredToolResult, ToolResult
from mcp.types import TextContent

from kubectl_mcp_tool.auth.scopes import MCPScopes
from kubectl_mcp_tool.observability import (
    get_stats_collector,
    record_tool_call_metric,
    record_tool_duration_metric,
    record_tool_error_metric,
)
from kubectl_mcp_tool.safety import SafetyMode, get_safety_mode
from kubectl_mcp_tool.utils.helpers import mask_secrets, redact_secrets

logger = logging.getLogger("mcp-server")

FREE_TEXT_PARAMS = frozenset({
    "manifest", "patch", "values", "set_values", "config", "command", "args",
    "query", "message", "condition", "field_selector", "label_selector",
    "jsonpath", "password", "username",
})

UNRESTRICTED_SCOPES = frozenset({MCPScopes.TOOLS.value, MCPScopes.ADMIN.value})
DISCOVERY_TOOLS = frozenset({"search_tools", "call_tool"})


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)):
        yield from (v for v in value if isinstance(v, str))
    elif isinstance(value, dict):
        yield from (k for k in value if isinstance(k, str))


def reject_option_injection(arguments: dict) -> None:
    """Block values that a CLI would parse as flags (e.g. name='--server=https://x')."""
    for key, value in arguments.items():
        if key in FREE_TEXT_PARAMS:
            continue
        for item in _strings(value):
            if item.lstrip().startswith("-"):
                raise ToolError(f"Invalid value for '{key}': values must not start with '-'")


def is_read_only_tool(tool: Any) -> bool:
    annotations = getattr(tool, "annotations", None)
    return bool(annotations and annotations.read_only_hint)


def required_scope(read_only: bool) -> str:
    return MCPScopes.READ.value if read_only else MCPScopes.WRITE.value


class ToolGuardMiddleware(Middleware):
    def __init__(self, enforce_scopes: bool = False, mask: bool = True):
        self.enforce_scopes = enforce_scopes
        self.mask = mask
        self.stats = get_stats_collector()

    async def on_list_tools(self, context, call_next):
        tools = await call_next(context)
        if get_safety_mode() != SafetyMode.READ_ONLY:
            return tools
        return [t for t in tools if t.name in DISCOVERY_TOOLS or is_read_only_tool(t)]

    async def on_call_tool(self, context, call_next):
        params = context.message
        name = params.name
        if name in DISCOVERY_TOOLS:
            return await call_next(context)
        reject_option_injection(params.arguments or {})
        tool = await context.fastmcp_context.fastmcp.get_tool(name)
        if tool is None:
            return await call_next(context)
        read_only = is_read_only_tool(tool)
        if not read_only and get_safety_mode() == SafetyMode.READ_ONLY:
            raise ToolError(f"Blocked: '{name}' modifies state and the server is in read-only mode")
        if self.enforce_scopes:
            _check_scopes(name, read_only)

        started = time.perf_counter()
        try:
            result = await call_next(context)
        except Exception as exc:
            self._record(name, False, time.perf_counter() - started, type(exc).__name__)
            raise
        if isinstance(result, InputRequiredToolResult):
            self._record(name, True, time.perf_counter() - started, "")
            return result
        failed = result.is_error or (isinstance(result.structured_content, dict) and result.structured_content.get("success") is False)
        self._record(name, not failed, time.perf_counter() - started, "tool_error")
        return _redact_result(result) if self.mask else result

    def _record(self, name: str, success: bool, duration: float, error_type: str) -> None:
        self.stats.record_tool_call(name, success=success, duration=duration)
        record_tool_call_metric(name, success=success, duration=duration)
        record_tool_duration_metric(name, duration)
        if not success:
            record_tool_error_metric(name, error_type)


def _in_http_request() -> bool:
    try:
        get_http_request()
        return True
    except RuntimeError:
        return False


def _check_scopes(name: str, read_only: bool) -> None:
    token = get_access_token()
    if token is None:
        if _in_http_request():
            raise ToolError("Unauthorized: missing access token")
        return
    scopes = set(token.scopes or [])
    if scopes & UNRESTRICTED_SCOPES:
        return
    needed = required_scope(read_only)
    if needed not in scopes:
        raise ToolError(f"Forbidden: '{name}' requires scope '{needed}'")


def _redact_result(result: ToolResult) -> ToolResult:
    content = [
        TextContent(type="text", text=mask_secrets(block.text)) if isinstance(block, TextContent) else block
        for block in (result.content or [])
    ]
    structured = result.structured_content
    if structured is not None:
        structured = redact_secrets(structured)
    return ToolResult(content=content, structured_content=structured, meta=result.meta, is_error=result.is_error)
