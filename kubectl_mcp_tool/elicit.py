import logging
from fastmcp import Context
from kubectl_mcp_tool.safety import get_safety_mode, SafetyMode

logger = logging.getLogger("mcp-server")


async def confirm_destructive(
    ctx: Context,
    operation: str,
    resource: str,
    namespace: str = "",
) -> dict | None:
    """Request user confirmation before destructive operations.

    Returns None if approved, error dict if blocked/declined.
    """
    mode = get_safety_mode()

    if mode == SafetyMode.READ_ONLY:
        return {"success": False, "error": "Blocked: read-only mode"}
    if mode == SafetyMode.DISABLE_DESTRUCTIVE:
        return {"success": False, "error": "Blocked: destructive operations disabled"}
    if mode == SafetyMode.NORMAL:
        return None

    if mode == SafetyMode.CONFIRM:
        if ctx is None:
            return {"success": False, "error": "Blocked: no client context for confirmation prompt"}
        prompt = f"{operation} '{resource}'"
        if namespace:
            prompt += f" in namespace '{namespace}'"
        prompt += "?"
        try:
            result = await ctx.elicit(prompt)
            if result.action == "accept":
                return None
            return {"success": False, "error": "Operation cancelled by user"}
        except (NotImplementedError, AttributeError) as e:
            logger.debug(f"Elicitation not supported by client: {e}")
            return {"success": False, "error": "Blocked: client doesn't support confirmation prompts"}
        except Exception as e:
            logger.warning(f"Unexpected error during elicitation: {e}")
            return {"success": False, "error": "Blocked: client doesn't support confirmation prompts"}

    return None
