"""
Safety mode implementation for kubectl-mcp-server.

Provides read-only and disable-destructive modes to prevent accidental cluster mutations.
"""

from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Set
import logging

logger = logging.getLogger("mcp-server")


class SafetyMode(Enum):
    """Safety mode levels for the MCP server."""
    NORMAL = "normal"
    READ_ONLY = "read_only"
    DISABLE_DESTRUCTIVE = "disable_destructive"


# Global safety mode state
_current_mode: SafetyMode = SafetyMode.NORMAL


# Operations that modify cluster state (blocked in READ_ONLY mode)
WRITE_OPERATIONS: Set[str] = {
    # Pod operations
    "run_pod", "delete_pod",
    # Deployment operations
    "scale_deployment", "restart_deployment", "delete_deployment",
    "rollback_deployment", "create_deployment", "update_deployment",
    # StatefulSet operations
    "scale_statefulset", "restart_statefulset", "delete_statefulset",
    # DaemonSet operations
    "restart_daemonset", "delete_daemonset",
    # Service operations
    "create_service", "delete_service", "update_service",
    # ConfigMap/Secret operations
    "create_configmap", "delete_configmap", "update_configmap",
    "create_secret", "delete_secret", "update_secret",
    # Namespace operations
    "create_namespace", "delete_namespace",
    # Helm operations
    "install_helm_chart", "upgrade_helm_chart", "uninstall_helm_chart",
    "rollback_helm_release",
    # kubectl operations
    "apply_manifest", "delete_resource", "patch_resource",
    "create_resource", "replace_resource",
    # Context operations
    "switch_context", "set_namespace_for_context",
    # Rollout operations
    "rollout_promote_tool", "rollout_abort_tool", "rollout_retry_tool",
    "rollout_restart_tool",
    # KubeVirt operations
    "kubevirt_vm_start_tool", "kubevirt_vm_stop_tool", "kubevirt_vm_restart_tool",
    "kubevirt_vm_pause_tool", "kubevirt_vm_unpause_tool", "kubevirt_vm_migrate_tool",
    # CAPI operations
    "capi_machinedeployment_scale_tool",
}

# Operations that are destructive (blocked in DISABLE_DESTRUCTIVE mode)
DESTRUCTIVE_OPERATIONS: Set[str] = {
    # Delete operations
    "delete_pod", "delete_deployment", "delete_statefulset", "delete_daemonset",
    "delete_service", "delete_configmap", "delete_secret", "delete_namespace",
    "delete_resource",
    # Helm uninstall
    "uninstall_helm_chart",
    # Rollout abort
    "rollout_abort_tool",
    # VM stop
    "kubevirt_vm_stop_tool",
}


def get_safety_mode() -> SafetyMode:
    """Get the current safety mode."""
    return _current_mode


def set_safety_mode(mode: SafetyMode) -> None:
    """Set the safety mode globally."""
    global _current_mode
    _current_mode = mode
    logger.info(f"Safety mode set to: {mode.value}")


def is_operation_allowed(operation_name: str) -> tuple[bool, str]:
    """
    Check if an operation is allowed under the current safety mode.

    Returns:
        Tuple of (allowed: bool, reason: str)
    """
    mode = get_safety_mode()

    if mode == SafetyMode.NORMAL:
        return True, ""

    if mode == SafetyMode.READ_ONLY:
        if operation_name in WRITE_OPERATIONS or operation_name in DESTRUCTIVE_OPERATIONS:
            return False, f"Operation '{operation_name}' blocked: read-only mode is enabled"

    if mode == SafetyMode.DISABLE_DESTRUCTIVE:
        if operation_name in DESTRUCTIVE_OPERATIONS:
            return False, f"Operation '{operation_name}' blocked: destructive operations are disabled"

    return True, ""


def check_safety_mode(func: Callable) -> Callable:
    """
    Decorator to check safety mode before executing a tool function.

    Usage:
        @check_safety_mode
        def delete_pod(...):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        operation_name = func.__name__
        allowed, reason = is_operation_allowed(operation_name)

        if not allowed:
            logger.warning(f"Blocked operation: {operation_name} (mode: {get_safety_mode().value})")
            return {
                "success": False,
                "error": reason,
                "blocked_by": get_safety_mode().value,
                "operation": operation_name
            }

        return func(*args, **kwargs)

    return wrapper


def get_mode_info() -> Dict[str, Any]:
    """Get information about the current safety mode."""
    mode = get_safety_mode()
    return {
        "mode": mode.value,
        "description": {
            SafetyMode.NORMAL: "All operations allowed",
            SafetyMode.READ_ONLY: "Only read operations allowed (no create/update/delete)",
            SafetyMode.DISABLE_DESTRUCTIVE: "Create/update allowed, delete operations blocked",
        }[mode],
        "blocked_operations": {
            SafetyMode.NORMAL: [],
            SafetyMode.READ_ONLY: sorted(WRITE_OPERATIONS | DESTRUCTIVE_OPERATIONS),
            SafetyMode.DISABLE_DESTRUCTIVE: sorted(DESTRUCTIVE_OPERATIONS),
        }[mode]
    }
