#!/usr/bin/env python3
"""CLI module for kubectl-mcp-tool."""

import sys
import os
import logging
import asyncio
import argparse
import traceback
import json
import shutil
import fnmatch
from typing import Any, Dict, List, Optional

from ..mcp_server import MCPServer
from .errors import (
    ErrorCode,
    format_cli_error,
    tool_not_found_error,
    tool_execution_error,
    invalid_json_error,
    missing_argument_error,
    unknown_subcommand_error,
    k8s_context_error,
    dependency_missing_error,
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
    format_error,
    format_success,
)
from ..safety import SafetyMode, set_safety_mode, get_mode_info

# Logging setup
log_file = os.environ.get("MCP_LOG_FILE")
log_level = logging.DEBUG if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true") else logging.INFO

handlers = []
if log_file:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handlers.append(logging.FileHandler(log_file))
handlers.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers
)
logger = logging.getLogger("kubectl-mcp-cli")


async def serve_stdio(
    read_only: bool = False,
    disable_destructive: bool = False,
    config_file: Optional[str] = None,
):
    server = MCPServer(
        "kubernetes",
        read_only=read_only,
        disable_destructive=disable_destructive,
        config_file=config_file,
    )
    await server.serve_stdio()


async def serve_sse(
    host: str,
    port: int,
    read_only: bool = False,
    disable_destructive: bool = False,
    config_file: Optional[str] = None,
):
    server = MCPServer(
        "kubernetes",
        read_only=read_only,
        disable_destructive=disable_destructive,
        config_file=config_file,
    )
    await server.serve_sse(host=host, port=port)


async def serve_http(
    host: str,
    port: int,
    read_only: bool = False,
    disable_destructive: bool = False,
    config_file: Optional[str] = None,
):
    server = MCPServer(
        "kubernetes",
        read_only=read_only,
        disable_destructive=disable_destructive,
        config_file=config_file,
    )
    await server.serve_http(host=host, port=port)


def get_all_tools() -> List[Dict[str, Any]]:
    server = MCPServer("kubernetes")

    async def _get():
        tools = await server.server.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description or "",
                "inputSchema": t.inputSchema if hasattr(t, 'inputSchema') else {},
                "category": _get_tool_category(t.name),
            }
            for t in tools
        ]

    return asyncio.run(_get())


def _get_tool_category(tool_name: str) -> str:
    """Determine tool category from name."""
    categories = {
        "pod": "pods",
        "deployment": "deployments",
        "statefulset": "deployments",
        "daemonset": "deployments",
        "replicaset": "deployments",
        "namespace": "core",
        "configmap": "core",
        "secret": "core",
        "service": "networking",
        "ingress": "networking",
        "network": "networking",
        "pvc": "storage",
        "pv": "storage",
        "storage": "storage",
        "rbac": "security",
        "role": "security",
        "serviceaccount": "security",
        "helm": "helm",
        "apply": "operations",
        "patch": "operations",
        "delete": "operations",
        "scale": "operations",
        "rollout": "operations",
        "context": "cluster",
        "cluster": "cluster",
        "node": "cluster",
        "metric": "diagnostics",
        "compare": "diagnostics",
        "event": "diagnostics",
        "cost": "cost",
        "browser": "browser",
        "screenshot": "browser",
        "ui": "ui",
        "dashboard": "ui",
    }

    name_lower = tool_name.lower()
    for keyword, category in categories.items():
        if keyword in name_lower:
            return category

    return "other"


def cmd_tools(args):
    tools = get_all_tools()

    if args.name:
        # Show specific tool schema
        tool = next((t for t in tools if t["name"] == args.name), None)
        if not tool:
            available = [t["name"] for t in tools]
            print(format_cli_error(tool_not_found_error(args.name, available)), file=sys.stderr)
            return ErrorCode.CLIENT_ERROR

        print(format_tool_schema(tool, as_json=args.json))
    else:
        # List all tools
        print(format_tools_list(tools, with_descriptions=args.with_descriptions, as_json=args.json))

    return ErrorCode.SUCCESS


def get_all_resources() -> List[Dict[str, Any]]:
    server = MCPServer("kubernetes")

    async def _get():
        resources = await server.server.list_resources()
        return [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description or "",
                "mimeType": getattr(r, 'mimeType', None),
            }
            for r in resources
        ]

    return asyncio.run(_get())


def cmd_resources(args):
    resources = get_all_resources()
    print(format_resources_list(resources, as_json=args.json))
    return ErrorCode.SUCCESS


def get_all_prompts() -> List[Dict[str, Any]]:
    server = MCPServer("kubernetes")

    async def _get():
        prompts = await server.server.list_prompts()
        return [
            {
                "name": p.name,
                "description": p.description or "",
                "arguments": [
                    {"name": a.name, "description": a.description, "required": a.required}
                    for a in (p.arguments or [])
                ],
            }
            for p in prompts
        ]

    return asyncio.run(_get())


def cmd_prompts(args):
    prompts = get_all_prompts()
    print(format_prompts_list(prompts, as_json=args.json))
    return ErrorCode.SUCCESS


def cmd_call(args):
    tools = get_all_tools()
    tool = next((t for t in tools if t["name"] == args.tool), None)

    if not tool:
        available = [t["name"] for t in tools]
        print(format_cli_error(tool_not_found_error(args.tool, available)), file=sys.stderr)
        return ErrorCode.CLIENT_ERROR

    # Parse JSON arguments
    json_args = args.args

    # Read from stdin if no args provided and stdin is not a tty
    if not json_args and not sys.stdin.isatty():
        json_args = sys.stdin.read().strip()

    # Default to empty object
    if not json_args:
        json_args = "{}"

    try:
        tool_args = json.loads(json_args)
    except json.JSONDecodeError as e:
        print(format_cli_error(invalid_json_error(json_args, str(e))), file=sys.stderr)
        return ErrorCode.CLIENT_ERROR

    # Execute the tool
    server = MCPServer("kubernetes")

    async def _call():
        result = await server.server.call_tool(args.tool, tool_args)
        return result

    try:
        result = asyncio.run(_call())
        print(format_call_result(result, as_json=args.json))
        return ErrorCode.SUCCESS
    except Exception as e:
        print(format_cli_error(tool_execution_error(args.tool, str(e))), file=sys.stderr)
        return ErrorCode.SERVER_ERROR


def cmd_grep(args):
    tools = get_all_tools()
    pattern = args.pattern

    # Support glob patterns
    if not pattern.startswith("*") and not pattern.endswith("*"):
        # Make it a contains search by default
        pattern = f"*{pattern}*"

    matches = [
        t for t in tools
        if fnmatch.fnmatch(t["name"].lower(), pattern.lower())
        or fnmatch.fnmatch((t.get("description") or "").lower(), pattern.lower())
    ]

    print(format_tools_search(matches, args.pattern, with_descriptions=args.with_descriptions))
    return ErrorCode.SUCCESS


def cmd_info(args):
    from .. import __version__

    tools = get_all_tools()
    resources = get_all_resources()
    prompts = get_all_prompts()

    # Get current k8s context
    context = None
    try:
        from kubernetes import config
        _, active_context = config.list_kube_config_contexts()
        context = active_context.get("name") if active_context else None
    except Exception:
        pass

    # Get safety mode info
    mode_info = get_mode_info()

    print(format_server_info(
        version=__version__,
        tool_count=len(tools),
        resource_count=len(resources),
        prompt_count=len(prompts),
        context=context,
        safety_mode=mode_info,
        as_json=getattr(args, 'json', False)
    ))
    return ErrorCode.SUCCESS


def cmd_context(args):
    try:
        from kubernetes import config
        import subprocess

        contexts, active_context = config.list_kube_config_contexts()
        current = active_context.get("name") if active_context else None
        available = [c.get("name") for c in contexts] if contexts else []

        if args.name:
            # Switch context
            if args.name not in available:
                print(format_cli_error(k8s_context_error(args.name, available)), file=sys.stderr)
                return ErrorCode.K8S_ERROR

            result = subprocess.run(
                ["kubectl", "config", "use-context", args.name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(format_success(f"Switched to context: {args.name}"))
                return ErrorCode.SUCCESS
            else:
                print(format_error(result.stderr.strip()), file=sys.stderr)
                return ErrorCode.K8S_ERROR
        else:
            # Show current context
            print(format_context_info(current or "(none)", available, as_json=getattr(args, 'json', False)))
            return ErrorCode.SUCCESS

    except Exception as e:
        print(format_error(f"Failed to get contexts: {e}"), file=sys.stderr)
        return ErrorCode.K8S_ERROR


def cmd_doctor(args):
    checks = []

    # Check kubectl
    kubectl_path = shutil.which("kubectl")
    if kubectl_path:
        try:
            import subprocess
            result = subprocess.run(["kubectl", "version", "--client", "-o", "json"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_info = json.loads(result.stdout)
                version = version_info.get("clientVersion", {}).get("gitVersion", "unknown")
                checks.append({"name": "kubectl", "status": "ok", "version": version, "details": kubectl_path})
            else:
                checks.append({"name": "kubectl", "status": "warning", "details": "kubectl found but version check failed"})
        except Exception as e:
            checks.append({"name": "kubectl", "status": "warning", "details": str(e)})
    else:
        checks.append({"name": "kubectl", "status": "error", "details": "kubectl not found in PATH"})

    # Check helm
    helm_path = shutil.which("helm")
    if helm_path:
        try:
            import subprocess
            result = subprocess.run(["helm", "version", "--short"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                checks.append({"name": "helm", "status": "ok", "version": version, "details": helm_path})
            else:
                checks.append({"name": "helm", "status": "warning", "details": "helm found but version check failed"})
        except Exception as e:
            checks.append({"name": "helm", "status": "warning", "details": str(e)})
    else:
        checks.append({"name": "helm", "status": "warning", "details": "helm not found (optional)"})

    # Check Kubernetes connection
    try:
        from kubernetes import client, config
        config.load_kube_config()
        v1 = client.CoreV1Api()
        v1.list_namespace(limit=1)
        _, active_context = config.list_kube_config_contexts()
        context_name = active_context.get("name") if active_context else "unknown"
        checks.append({"name": "kubernetes", "status": "ok", "version": context_name, "details": "Connected"})
    except Exception as e:
        checks.append({"name": "kubernetes", "status": "error", "details": str(e)})

    # Check agent-browser (optional)
    browser_path = shutil.which("agent-browser")
    if browser_path:
        try:
            import subprocess
            result = subprocess.run(["agent-browser", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                checks.append({"name": "agent-browser", "status": "ok", "version": version, "details": browser_path})
            else:
                checks.append({"name": "agent-browser", "status": "ok", "details": browser_path})
        except Exception:
            checks.append({"name": "agent-browser", "status": "ok", "details": browser_path})
    else:
        enabled = os.environ.get("MCP_BROWSER_ENABLED", "").lower() in ("1", "true")
        if enabled:
            checks.append({"name": "agent-browser", "status": "warning",
                           "details": "MCP_BROWSER_ENABLED=true but agent-browser not found"})
        else:
            checks.append({"name": "agent-browser", "status": "ok",
                           "details": "Not installed (optional, set MCP_BROWSER_ENABLED=true to use)"})

    # Check Python dependencies
    try:
        import fastmcp
        checks.append({"name": "fastmcp", "status": "ok", "version": getattr(fastmcp, '__version__', 'installed')})
    except ImportError:
        checks.append({"name": "fastmcp", "status": "error", "details": "fastmcp not installed"})

    # Check safety mode
    mode_info = get_mode_info()
    mode = mode_info.get("mode", "normal")
    if mode == "normal":
        checks.append({"name": "safety_mode", "status": "ok", "version": mode, "details": "All operations allowed"})
    elif mode == "read_only":
        checks.append({"name": "safety_mode", "status": "warning", "version": mode, "details": "Write operations blocked"})
    else:
        checks.append({"name": "safety_mode", "status": "warning", "version": mode, "details": "Destructive operations blocked"})

    print(format_doctor_results(checks, as_json=getattr(args, 'json', False)))

    # Return error code if any critical checks failed
    has_errors = any(c["status"] == "error" for c in checks)
    return ErrorCode.CLIENT_ERROR if has_errors else ErrorCode.SUCCESS


def main():
    parser = argparse.ArgumentParser(
        prog="kubectl-mcp-server",
        description="MCP server for Kubernetes with 127+ tools, 8 resources, and 8 prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kubectl-mcp-server serve                          # Start stdio server (Claude/Cursor)
  kubectl-mcp-server serve --transport http         # Start HTTP server
  kubectl-mcp-server tools                          # List all tools
  kubectl-mcp-server tools -d                       # List tools with descriptions
  kubectl-mcp-server tools get_pods                 # Show tool schema
  kubectl-mcp-server grep "*pod*"                   # Search for pod-related tools
  kubectl-mcp-server call get_pods '{"namespace": "default"}'  # Call a tool
  echo '{"namespace": "kube-system"}' | kubectl-mcp-server call get_pods
  kubectl-mcp-server context                        # Show k8s context
  kubectl-mcp-server doctor                         # Check dependencies

Environment Variables:
  MCP_DEBUG=true           Enable debug logging
  MCP_BROWSER_ENABLED=true Enable browser automation tools
  NO_COLOR=1               Disable colored output
        """
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # serve command (existing)
    serve_parser = subparsers.add_parser("serve", help="Start the MCP server")
    serve_parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http", "streamable-http"],
        default="stdio",
        help="Transport to use (default: stdio)"
    )
    serve_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for SSE/HTTP (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port for SSE/HTTP (default: 8000)")
    serve_parser.add_argument("--config", type=str, default=None, help="Path to TOML configuration file")
    serve_parser.add_argument("--read-only", action="store_true", help="Enable read-only mode (block all write operations)")
    serve_parser.add_argument("--disable-destructive", action="store_true", help="Disable destructive operations (allow create/update, block delete)")

    # version command (existing)
    subparsers.add_parser("version", help="Show version")

    # diagnostics command (existing)
    subparsers.add_parser("diagnostics", help="Run cluster diagnostics")

    # tools command (new)
    tools_parser = subparsers.add_parser("tools", help="List or inspect tools")
    tools_parser.add_argument("name", nargs="?", help="Tool name to inspect")
    tools_parser.add_argument("-d", "--with-descriptions", action="store_true", help="Include descriptions")
    tools_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # resources command (new)
    resources_parser = subparsers.add_parser("resources", help="List available resources")
    resources_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # prompts command (new)
    prompts_parser = subparsers.add_parser("prompts", help="List available prompts")
    prompts_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # call command (new)
    call_parser = subparsers.add_parser("call", help="Call a tool directly")
    call_parser.add_argument("tool", help="Tool name to call")
    call_parser.add_argument("args", nargs="?", help="JSON arguments (reads stdin if omitted)")
    call_parser.add_argument("--json", action="store_true", help="Force JSON output")

    # grep command (new)
    grep_parser = subparsers.add_parser("grep", help="Search tools by pattern")
    grep_parser.add_argument("pattern", help="Glob pattern to search (e.g., '*pod*')")
    grep_parser.add_argument("-d", "--with-descriptions", action="store_true", help="Include descriptions")

    # info command (new)
    info_parser = subparsers.add_parser("info", help="Show server information")
    info_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # context command (new)
    context_parser = subparsers.add_parser("context", help="Show/switch Kubernetes context")
    context_parser.add_argument("name", nargs="?", help="Context to switch to")
    context_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # doctor command (new)
    doctor_parser = subparsers.add_parser("doctor", help="Check dependencies and configuration")
    doctor_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Enable debug logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        os.environ["MCP_DEBUG"] = "1"

    try:
        if args.command == "serve":
            # Log safety mode (actual mode is applied in MCPServer)
            if args.read_only:
                logger.info("Starting server in READ-ONLY mode")
            elif args.disable_destructive:
                logger.info("Starting server with destructive operations disabled")

            if args.config:
                logger.info(f"Loading configuration from: {args.config}")

            if args.transport == "stdio":
                asyncio.run(serve_stdio(
                    read_only=args.read_only,
                    disable_destructive=args.disable_destructive,
                    config_file=args.config,
                ))
            elif args.transport == "sse":
                asyncio.run(serve_sse(
                    host=args.host,
                    port=args.port,
                    read_only=args.read_only,
                    disable_destructive=args.disable_destructive,
                    config_file=args.config,
                ))
            elif args.transport in ("http", "streamable-http"):
                asyncio.run(serve_http(
                    host=args.host,
                    port=args.port,
                    read_only=args.read_only,
                    disable_destructive=args.disable_destructive,
                    config_file=args.config,
                ))

        elif args.command == "version":
            from .. import __version__
            print(f"kubectl-mcp-server version {__version__}")

        elif args.command == "diagnostics":
            from ..diagnostics import run_diagnostics
            results = run_diagnostics()
            print(json.dumps(results, indent=2))

        elif args.command == "tools":
            return cmd_tools(args)

        elif args.command == "resources":
            return cmd_resources(args)

        elif args.command == "prompts":
            return cmd_prompts(args)

        elif args.command == "call":
            return cmd_call(args)

        elif args.command == "grep":
            return cmd_grep(args)

        elif args.command == "info":
            return cmd_info(args)

        elif args.command == "context":
            return cmd_context(args)

        elif args.command == "doctor":
            return cmd_doctor(args)

        elif args.command is None:
            parser.print_help()

        else:
            # Unknown subcommand
            print(format_cli_error(unknown_subcommand_error(args.command)), file=sys.stderr)
            return ErrorCode.CLIENT_ERROR

    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Error: {e}")
        if args.debug:
            logger.error(traceback.format_exc())
        return ErrorCode.SERVER_ERROR

    return ErrorCode.SUCCESS


if __name__ == "__main__":
    sys.exit(main())
