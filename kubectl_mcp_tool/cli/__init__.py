"""
CLI package for kubectl-mcp-tool.

Provides command-line interface for managing the MCP server.
"""

from .cli import main
from .errors import (
    CliError,
    ErrorCode,
    format_cli_error,
    tool_not_found_error,
    tool_execution_error,
    k8s_connection_error,
    k8s_context_error,
    browser_not_found_error,
    browser_connection_error,
    invalid_json_error,
    missing_argument_error,
    unknown_subcommand_error,
)
from .output import (
    format_tools_list,
    format_tool_schema,
    format_tools_search,
    format_resources_list,
    format_prompts_list,
    format_call_result,
    format_server_info,
    format_context_info,
    format_doctor_results,
    should_colorize,
)

__all__ = [
    "main",
    # Errors
    "CliError",
    "ErrorCode",
    "format_cli_error",
    "tool_not_found_error",
    "tool_execution_error",
    "k8s_connection_error",
    "k8s_context_error",
    "browser_not_found_error",
    "browser_connection_error",
    "invalid_json_error",
    "missing_argument_error",
    "unknown_subcommand_error",
    # Output
    "format_tools_list",
    "format_tool_schema",
    "format_tools_search",
    "format_resources_list",
    "format_prompts_list",
    "format_call_result",
    "format_server_info",
    "format_context_info",
    "format_doctor_results",
    "should_colorize",
]
