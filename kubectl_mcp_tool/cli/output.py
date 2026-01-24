"""Output formatting utilities for kubectl-mcp-server CLI."""

import json
import os
import sys
from typing import Any, Dict, List, Optional


COLORS = {
    "reset": "\x1b[0m",
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "italic": "\x1b[3m",
    "underline": "\x1b[4m",
    # Foreground colors
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
    # Bright colors
    "bright_black": "\x1b[90m",
    "bright_red": "\x1b[91m",
    "bright_green": "\x1b[92m",
    "bright_yellow": "\x1b[93m",
    "bright_blue": "\x1b[94m",
    "bright_magenta": "\x1b[95m",
    "bright_cyan": "\x1b[96m",
    "bright_white": "\x1b[97m",
}


def should_colorize() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def color(text: str, *codes: str) -> str:
    if not should_colorize():
        return text
    combined = "".join(codes)
    return f"{combined}{text}{COLORS['reset']}"


def bold(text: str) -> str:
    return color(text, COLORS["bold"])


def dim(text: str) -> str:
    return color(text, COLORS["dim"])


def cyan(text: str) -> str:
    return color(text, COLORS["cyan"])


def green(text: str) -> str:
    return color(text, COLORS["green"])


def yellow(text: str) -> str:
    return color(text, COLORS["yellow"])


def red(text: str) -> str:
    return color(text, COLORS["red"])


def blue(text: str) -> str:
    return color(text, COLORS["blue"])


TOOL_CATEGORIES = {
    "pods": "Pods",
    "deployments": "Deployments & Workloads",
    "core": "Core Resources",
    "cluster": "Cluster Management",
    "networking": "Networking",
    "storage": "Storage",
    "security": "Security & RBAC",
    "helm": "Helm",
    "operations": "Operations",
    "diagnostics": "Diagnostics",
    "cost": "Cost Optimization",
    "browser": "Browser Automation",
    "ui": "UI Dashboards",
}


def format_tools_list(
    tools: List[Dict[str, Any]],
    with_descriptions: bool = False,
    as_json: bool = False
) -> str:
    if as_json:
        return json.dumps(tools, indent=2)

    # Group tools by category
    categories: Dict[str, List[Dict]] = {}
    for tool in tools:
        cat = tool.get("category", "other")
        cat_display = TOOL_CATEGORIES.get(cat, cat.title())
        categories.setdefault(cat_display, []).append(tool)

    lines = []
    for cat, cat_tools in sorted(categories.items()):
        # Category header
        header = f"{cat} ({len(cat_tools)})"
        lines.append(color(header, COLORS["bold"], COLORS["cyan"]))

        # Tools in category
        for t in sorted(cat_tools, key=lambda x: x.get("name", "")):
            name = t.get("name", "unknown")
            if with_descriptions and t.get("description"):
                desc = t["description"]
                # Truncate long descriptions
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                lines.append(f"  {green(name)} - {dim(desc)}")
            else:
                lines.append(f"  {name}")

        lines.append("")  # Empty line between categories

    return "\n".join(lines).rstrip()


def format_tool_schema(tool: Dict[str, Any], as_json: bool = False) -> str:
    if as_json:
        return json.dumps(tool, indent=2)

    lines = []
    name = tool.get("name", "unknown")
    description = tool.get("description", "")
    schema = tool.get("inputSchema", tool.get("input_schema", {}))

    # Header
    lines.append(f"{bold('Tool:')} {green(name)}")
    if description:
        lines.append(f"{bold('Description:')} {description}")

    # Parameters
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    if properties:
        lines.append("")
        lines.append(bold("Parameters:"))
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "any")
            param_desc = param_info.get("description", "")
            is_required = param_name in required
            req_str = yellow("required") if is_required else dim("optional")

            param_line = f"  {cyan(param_name)} ({param_type}, {req_str})"
            if param_desc:
                lines.append(f"{param_line}")
                lines.append(f"    {dim(param_desc)}")
            else:
                lines.append(param_line)

    # Full schema
    lines.append("")
    lines.append(bold("Input Schema:"))
    lines.append(json.dumps(schema, indent=2))

    return "\n".join(lines)


def format_tools_search(
    results: List[Dict[str, Any]],
    pattern: str,
    with_descriptions: bool = False
) -> str:
    if not results:
        return dim(f"No tools matching '{pattern}'")

    lines = [f"Found {len(results)} tools matching '{pattern}':", ""]

    for tool in results:
        name = tool.get("name", "unknown")
        if with_descriptions and tool.get("description"):
            lines.append(f"{green(name)} - {dim(tool['description'])}")
        else:
            lines.append(green(name))

    return "\n".join(lines)


def format_resources_list(
    resources: List[Dict[str, Any]],
    as_json: bool = False
) -> str:
    if as_json:
        return json.dumps(resources, indent=2)

    lines = [bold(f"Resources ({len(resources)}):"), ""]

    for res in resources:
        uri = res.get("uri", res.get("name", "unknown"))
        name = res.get("name", uri)
        description = res.get("description", "")

        lines.append(f"  {cyan(uri)}")
        if name != uri:
            lines.append(f"    Name: {name}")
        if description:
            lines.append(f"    {dim(description)}")

    return "\n".join(lines)


def format_prompts_list(
    prompts: List[Dict[str, Any]],
    as_json: bool = False
) -> str:
    if as_json:
        return json.dumps(prompts, indent=2)

    lines = [bold(f"Prompts ({len(prompts)}):"), ""]

    for prompt in prompts:
        name = prompt.get("name", "unknown")
        description = prompt.get("description", "")
        args = prompt.get("arguments", [])

        lines.append(f"  {green(name)}")
        if description:
            lines.append(f"    {dim(description)}")
        if args:
            arg_names = [a.get("name", "?") for a in args]
            lines.append(f"    Arguments: {', '.join(arg_names)}")

    return "\n".join(lines)


def format_call_result(result: Any, as_json: bool = False) -> str:
    if as_json or not sys.stdout.isatty():
        return json.dumps(result, indent=2, default=str)

    # Try to extract text content from MCP result format
    if isinstance(result, dict):
        content = result.get("content", [])
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            if text_parts:
                return "\n".join(text_parts)

        if result.get("isError"):
            error_msg = result.get("error", result.get("message", "Unknown error"))
            return red(f"Error: {error_msg}")

    return json.dumps(result, indent=2, default=str)


def format_server_info(
    version: str,
    tool_count: int,
    resource_count: int,
    prompt_count: int,
    context: Optional[str] = None,
    safety_mode: Optional[Dict[str, Any]] = None,
    as_json: bool = False
) -> str:
    info = {
        "version": version,
        "tools": tool_count,
        "resources": resource_count,
        "prompts": prompt_count,
        "k8s_context": context,
    }

    if safety_mode:
        info["safety_mode"] = safety_mode

    if as_json:
        return json.dumps(info, indent=2)

    lines = [
        bold("kubectl-mcp-server"),
        "",
        f"  {cyan('Version:')}     {version}",
        f"  {cyan('Tools:')}       {tool_count}",
        f"  {cyan('Resources:')}   {resource_count}",
        f"  {cyan('Prompts:')}     {prompt_count}",
    ]

    if context:
        lines.append(f"  {cyan('K8s Context:')} {context}")

    if safety_mode:
        mode = safety_mode.get("mode", "normal")
        if mode == "normal":
            mode_str = green(mode)
        elif mode == "read_only":
            mode_str = yellow(mode) + " (write operations blocked)"
        else:
            mode_str = yellow(mode) + " (destructive operations blocked)"
        lines.append(f"  {cyan('Safety Mode:')} {mode_str}")

    return "\n".join(lines)


def format_context_info(
    current: str,
    available: List[str],
    as_json: bool = False
) -> str:
    if as_json:
        return json.dumps({
            "current": current,
            "available": available
        }, indent=2)

    lines = [
        f"{bold('Current context:')} {green(current)}",
        "",
        bold("Available contexts:"),
    ]

    for ctx in available:
        if ctx == current:
            lines.append(f"  {green('*')} {green(ctx)} (current)")
        else:
            lines.append(f"    {ctx}")

    return "\n".join(lines)


def format_doctor_results(
    checks: List[Dict[str, Any]],
    as_json: bool = False
) -> str:
    if as_json:
        return json.dumps(checks, indent=2)

    lines = [bold("Checking dependencies..."), ""]
    all_passed = True

    for check in checks:
        name = check.get("name", "unknown")
        status = check.get("status", "unknown")
        details = check.get("details", "")
        version = check.get("version", "")

        if status == "ok":
            icon = green("✓")
            status_text = green("OK")
        elif status == "warning":
            icon = yellow("!")
            status_text = yellow("WARNING")
            all_passed = False
        else:
            icon = red("✗")
            status_text = red("FAILED")
            all_passed = False

        line = f"  {icon} {name}: {status_text}"
        if version:
            line += f" ({version})"
        lines.append(line)

        if details and status != "ok":
            lines.append(f"      {dim(details)}")

    lines.append("")
    if all_passed:
        lines.append(green("All checks passed!"))
    else:
        lines.append(yellow("Some checks failed. See details above."))

    return "\n".join(lines)


def format_error(message: str) -> str:
    return red(f"Error: {message}")


def format_warning(message: str) -> str:
    return yellow(f"Warning: {message}")


def format_success(message: str) -> str:
    return green(message)
