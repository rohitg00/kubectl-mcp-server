from fastmcp import Context
from kubectl_mcp_tool.safety import get_safety_mode, SafetyMode


async def confirm_destructive(
    ctx: Context,
    operation: str,
    resource: str,
    namespace: str = "default",
) -> dict | None:
    """Request user confirmation before destructive operations.

    Returns None if approved, error dict if blocked/declined.
    """
    mode = get_safety_mode()

    if mode == SafetyMode.READ_ONLY:
        return {"success": False, "error": "Blocked: read-only mode"}
    if mode == SafetyMode.DISABLE_DESTRUCTIVE:
        return {"success": False, "error": "Blocked: destructive operations disabled"}

    if mode in (SafetyMode.NORMAL, SafetyMode.CONFIRM):
        try:
            result = await ctx.elicit(
                f"{operation} '{resource}' in namespace '{namespace}'?"
            )
            if result.action == "accept":
                return None
            return {"success": False, "error": "Operation cancelled by user"}
        except Exception:
            if mode == SafetyMode.CONFIRM:
                return {"success": False, "error": "Blocked: client doesn't support confirmation prompts"}
            return None

    return None
