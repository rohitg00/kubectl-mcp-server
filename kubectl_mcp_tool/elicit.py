import hashlib
import logging
from typing import Any, Dict, Optional, Union

from fastmcp import Context
from mcp.types import ElicitRequest, ElicitRequestFormParams, InputRequiredResult

from kubectl_mcp_tool.safety import get_safety_mode, SafetyMode

try:
    from mcp_types.version import MODERN_PROTOCOL_VERSIONS
except ImportError:
    MODERN_PROTOCOL_VERSIONS = frozenset({"2026-07-28"})

logger = logging.getLogger("mcp-server")

CONFIRM_KEY = "confirm"

Blocked = Optional[Union[Dict[str, Any], InputRequiredResult]]


async def check_write_allowed() -> Optional[Dict[str, Any]]:
    """Check if write operations are allowed in current safety mode.

    Use for non-destructive write tools (create, scale, update, restart).
    Only blocks in READ_ONLY mode. Returns None if allowed, error dict if blocked.
    """
    if get_safety_mode() == SafetyMode.READ_ONLY:
        return {"success": False, "error": "Blocked: read-only mode"}
    return None


def _is_modern(ctx: Context) -> bool:
    rc = getattr(ctx, "request_context", None)
    return getattr(rc, "protocol_version", None) in MODERN_PROTOCOL_VERSIONS


def _ask(prompt: str, digest: str) -> InputRequiredResult:
    params = ElicitRequestFormParams(
        message=prompt,
        requested_schema={
            "type": "object",
            "properties": {CONFIRM_KEY: {"type": "boolean", "title": "Confirm"}},
            "required": [CONFIRM_KEY],
        },
    )
    return InputRequiredResult(
        result_type="input_required",
        input_requests={CONFIRM_KEY: ElicitRequest(method="elicitation/create", params=params)},
        request_state=digest,
    )


async def confirm_destructive(
    ctx: Context,
    operation: str,
    resource: str,
    namespace: str = "",
) -> Blocked:
    """Request user confirmation before destructive operations.

    Blocks in READ_ONLY and DISABLE_DESTRUCTIVE modes. In CONFIRM mode, asks the
    user: on 2026-07-28 connections the tool returns an InputRequiredResult and the
    client retries with the answer (stateless multi round-trip); on older
    connections it falls back to a server-initiated elicitation. Returns None when
    the operation may proceed, otherwise a value the tool must return as-is.
    """
    mode = get_safety_mode()

    if mode == SafetyMode.READ_ONLY:
        return {"success": False, "error": "Blocked: read-only mode"}
    if mode == SafetyMode.DISABLE_DESTRUCTIVE:
        return {"success": False, "error": "Blocked: destructive operations disabled"}
    if mode != SafetyMode.CONFIRM:
        return None
    if ctx is None:
        return {"success": False, "error": "Blocked: no client context for confirmation prompt"}

    prompt = f"{operation} '{resource}'"
    if namespace:
        prompt += f" in namespace '{namespace}'"
    prompt += "?"

    if _is_modern(ctx):
        digest = hashlib.sha256(prompt.encode()).hexdigest()[:32]
        responses = ctx.input_responses
        if not responses or CONFIRM_KEY not in responses or ctx.request_state != digest:
            return _ask(prompt, digest)
        answer = responses[CONFIRM_KEY]
        content = getattr(answer, "content", None) or {}
        if getattr(answer, "action", None) == "accept" and content.get(CONFIRM_KEY) is True:
            return None
        return {"success": False, "error": "Operation cancelled by user"}

    try:
        result = await ctx.elicit(prompt, response_type=bool, response_title="Confirm")
    except Exception as e:
        logger.debug(f"Elicitation not available: {e}")
        return {"success": False, "error": "Blocked: client doesn't support confirmation prompts"}
    if result.action == "accept" and getattr(result, "data", False) is True:
        return None
    return {"success": False, "error": "Operation cancelled by user"}
