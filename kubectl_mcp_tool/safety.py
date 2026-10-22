"""
Safety mode implementation for kubectl-mcp-server.

Provides read-only and disable-destructive modes to prevent accidental cluster mutations.
"""

from enum import Enum
from typing import Any, Dict
import logging

logger = logging.getLogger("mcp-server")


class SafetyMode(Enum):
    """Safety mode levels for the MCP server."""
    NORMAL = "normal"
    CONFIRM = "confirm"
    READ_ONLY = "read_only"
    DISABLE_DESTRUCTIVE = "disable_destructive"


# Global safety mode state
_current_mode: SafetyMode = SafetyMode.NORMAL


def get_safety_mode() -> SafetyMode:
    """Get the current safety mode."""
    return _current_mode


def set_safety_mode(mode: SafetyMode) -> None:
    """Set the safety mode globally."""
    global _current_mode
    _current_mode = mode
    logger.info(f"Safety mode set to: {mode.value}")


def get_mode_info() -> Dict[str, Any]:
    """Get information about the current safety mode."""
    mode = get_safety_mode()
    return {
        "mode": mode.value,
        "description": {
            SafetyMode.NORMAL: "All operations allowed",
            SafetyMode.CONFIRM: "Confirm destructive operations via elicitation, block if unsupported",
            SafetyMode.READ_ONLY: "Only read operations allowed (no create/update/delete)",
            SafetyMode.DISABLE_DESTRUCTIVE: "Create/update allowed, delete operations blocked",
        }[mode],
    }
