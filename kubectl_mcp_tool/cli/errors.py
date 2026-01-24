"""Structured error handling for kubectl-mcp-server CLI."""

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional


class ErrorCode(IntEnum):
    SUCCESS = 0
    CLIENT_ERROR = 1
    SERVER_ERROR = 2
    K8S_ERROR = 3
    BROWSER_ERROR = 4
    NETWORK_ERROR = 5


@dataclass
class CliError:
    code: ErrorCode
    type: str
    message: str
    details: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        return format_cli_error(self)


def format_cli_error(error: CliError) -> str:
    lines = [f"Error [{error.type}]: {error.message}"]
    if error.details:
        lines.append(f"  Details: {error.details}")
    if error.suggestion:
        lines.append(f"  Suggestion: {error.suggestion}")
    return "\n".join(lines)


def tool_not_found_error(name: str, available: Optional[List[str]] = None) -> CliError:
    available = available or []
    available_str = ", ".join(available[:5])
    if len(available) > 5:
        available_str += f" (+{len(available) - 5} more)"

    return CliError(
        code=ErrorCode.CLIENT_ERROR,
        type="TOOL_NOT_FOUND",
        message=f'Tool "{name}" not found',
        details=f"Available: {available_str}" if available else None,
        suggestion="Run 'kubectl-mcp-server tools' to see all available tools"
    )


def tool_execution_error(name: str, cause: str) -> CliError:
    suggestion = "Check tool arguments match the expected schema"

    if "validation" in cause.lower() or "invalid" in cause.lower():
        suggestion = f"Run 'kubectl-mcp-server tools {name}' to see the input schema"
    elif "required" in cause.lower():
        suggestion = f"Missing required argument. Run 'kubectl-mcp-server tools {name}' for schema"
    elif "permission" in cause.lower() or "denied" in cause.lower():
        suggestion = "Permission denied. Check RBAC permissions in your cluster"

    return CliError(
        code=ErrorCode.SERVER_ERROR,
        type="TOOL_EXECUTION_FAILED",
        message=f'Tool "{name}" execution failed',
        details=cause,
        suggestion=suggestion
    )


def k8s_connection_error(context: str, cause: str) -> CliError:
    suggestion = "Check your kubeconfig and ensure the cluster is accessible"

    if "refused" in cause.lower():
        suggestion = "Connection refused. Is the cluster running? Check 'kubectl cluster-info'"
    elif "timeout" in cause.lower():
        suggestion = "Connection timed out. Check network connectivity to the cluster"
    elif "unauthorized" in cause.lower() or "401" in cause:
        suggestion = "Authentication failed. Check your credentials with 'kubectl auth whoami'"

    return CliError(
        code=ErrorCode.K8S_ERROR,
        type="K8S_CONNECTION_FAILED",
        message=f'Failed to connect to Kubernetes context "{context}"',
        details=cause,
        suggestion=suggestion
    )


def k8s_context_error(context: str, available: Optional[List[str]] = None) -> CliError:
    available = available or []
    available_str = ", ".join(available[:5]) if available else "(none)"

    return CliError(
        code=ErrorCode.K8S_ERROR,
        type="K8S_CONTEXT_NOT_FOUND",
        message=f'Kubernetes context "{context}" not found',
        details=f"Available contexts: {available_str}",
        suggestion="Run 'kubectl config get-contexts' to list available contexts"
    )


def k8s_resource_error(resource: str, namespace: str, cause: str) -> CliError:
    return CliError(
        code=ErrorCode.K8S_ERROR,
        type="K8S_RESOURCE_ERROR",
        message=f'Failed to access {resource} in namespace "{namespace}"',
        details=cause,
        suggestion="Check if the resource exists and you have permission to access it"
    )


def browser_not_found_error() -> CliError:
    return CliError(
        code=ErrorCode.BROWSER_ERROR,
        type="BROWSER_NOT_FOUND",
        message="agent-browser CLI not found",
        details="Browser automation tools require agent-browser to be installed",
        suggestion="Install with: npm install -g agent-browser && agent-browser install"
    )


def browser_not_enabled_error() -> CliError:
    return CliError(
        code=ErrorCode.BROWSER_ERROR,
        type="BROWSER_NOT_ENABLED",
        message="Browser tools are not enabled",
        details="Set MCP_BROWSER_ENABLED=true to enable browser automation",
        suggestion="Export MCP_BROWSER_ENABLED=true and ensure agent-browser is installed"
    )


def browser_connection_error(cause: str) -> CliError:
    suggestion = "Check browser configuration and try again"

    if "ECONNREFUSED" in cause:
        suggestion = "Connection refused. Is the browser running? Try 'agent-browser install'"
    elif "timeout" in cause.lower():
        suggestion = "Connection timed out. Try increasing MCP_BROWSER_TIMEOUT"
    elif "CDP" in cause or "websocket" in cause.lower():
        suggestion = "CDP connection failed. Check MCP_BROWSER_CDP_URL is correct"

    return CliError(
        code=ErrorCode.BROWSER_ERROR,
        type="BROWSER_CONNECTION_FAILED",
        message="Failed to connect to browser",
        details=cause,
        suggestion=suggestion
    )


def browser_timeout_error(timeout: int) -> CliError:
    return CliError(
        code=ErrorCode.BROWSER_ERROR,
        type="BROWSER_TIMEOUT",
        message=f"Browser command timed out after {timeout}s",
        details="The command took too long to complete",
        suggestion="Increase timeout or check if the page is loading correctly"
    )


def invalid_json_error(input_str: str, parse_error: str) -> CliError:
    truncated = input_str[:100] + "..." if len(input_str) > 100 else input_str

    return CliError(
        code=ErrorCode.CLIENT_ERROR,
        type="INVALID_JSON",
        message="Invalid JSON in arguments",
        details=f"Parse error: {parse_error}",
        suggestion=f"Use valid JSON format: '{{\"key\": \"value\"}}'. Input was: {truncated}"
    )


def missing_argument_error(command: str, argument: str) -> CliError:
    suggestions = {
        "call": "Use 'kubectl-mcp-server call <tool> '{\"key\": \"value\"}'",
        "tools": "Use 'kubectl-mcp-server tools <name>' to inspect a tool",
        "grep": "Use 'kubectl-mcp-server grep \"*pattern*\"' to search tools",
        "context": "Use 'kubectl-mcp-server context <name>' to switch context",
    }

    return CliError(
        code=ErrorCode.CLIENT_ERROR,
        type="MISSING_ARGUMENT",
        message=f"Missing required argument: {argument}",
        details=f"Command '{command}' requires {argument}",
        suggestion=suggestions.get(command, "Run 'kubectl-mcp-server --help' for usage")
    )


def unknown_subcommand_error(subcommand: str) -> CliError:
    valid_commands = "serve, tools, resources, prompts, call, grep, info, context, doctor, version, diagnostics"

    suggestions = {
        "run": "call",
        "exec": "call",
        "execute": "call",
        "invoke": "call",
        "list": "tools",
        "ls": "tools",
        "get": "tools",
        "show": "info",
        "describe": "tools",
        "search": "grep",
        "find": "grep",
        "check": "doctor",
        "status": "info",
        "start": "serve",
    }

    suggested = suggestions.get(subcommand.lower())
    suggestion_text = (
        f"Did you mean 'kubectl-mcp-server {suggested}'?"
        if suggested
        else "Run 'kubectl-mcp-server --help' for available commands"
    )

    return CliError(
        code=ErrorCode.CLIENT_ERROR,
        type="UNKNOWN_SUBCOMMAND",
        message=f'Unknown subcommand: "{subcommand}"',
        details=f"Valid commands: {valid_commands}",
        suggestion=suggestion_text
    )


def config_error(message: str, suggestion: Optional[str] = None) -> CliError:
    return CliError(
        code=ErrorCode.CLIENT_ERROR,
        type="CONFIG_ERROR",
        message=message,
        suggestion=suggestion or "Check your configuration and try again"
    )


def dependency_missing_error(dependency: str, install_cmd: Optional[str] = None) -> CliError:
    return CliError(
        code=ErrorCode.CLIENT_ERROR,
        type="DEPENDENCY_MISSING",
        message=f"Required dependency not found: {dependency}",
        suggestion=f"Install with: {install_cmd}" if install_cmd else f"Please install {dependency}"
    )


def network_error(cause: str) -> CliError:
    suggestion = "Check your network connection and try again"

    if "ECONNREFUSED" in cause:
        suggestion = "Connection refused. Check if the service is running"
    elif "ETIMEDOUT" in cause or "timeout" in cause.lower():
        suggestion = "Connection timed out. Check network connectivity"
    elif "ENOTFOUND" in cause or "DNS" in cause:
        suggestion = "DNS resolution failed. Check the hostname"

    return CliError(
        code=ErrorCode.NETWORK_ERROR,
        type="NETWORK_ERROR",
        message="Network error occurred",
        details=cause,
        suggestion=suggestion
    )
