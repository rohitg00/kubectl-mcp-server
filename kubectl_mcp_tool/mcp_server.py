#!/usr/bin/env python3
"""MCP server for Kubernetes.

Serves the stateless MCP 2026-07-28 protocol and every earlier handshake-era
revision from the same process, over stdio or Streamable HTTP.
"""

import argparse
import asyncio
import ipaddress
import logging
import os
import platform
import subprocess
import shutil
import sys
import warnings
from typing import Any, List, Optional

import kubectl_mcp_tool.k8s_config  # noqa: F401

from kubectl_mcp_tool import __version__
from kubectl_mcp_tool.auth import create_auth_verifier, get_auth_config
from kubectl_mcp_tool.config import load_config, register_reload_callback, setup_sighup_handler
from kubectl_mcp_tool.middleware import ToolGuardMiddleware
from kubectl_mcp_tool.observability import (
    get_metrics,
    get_stats_collector,
    init_tracing,
    is_prometheus_available,
)
from kubectl_mcp_tool.prompts import register_prompts
from kubectl_mcp_tool.resources import register_resources
from kubectl_mcp_tool.safety import SafetyMode, get_mode_info, get_safety_mode, set_safety_mode
from kubectl_mcp_tool.toolsets import DEFAULT_TOOLSETS, TOOL_TOOLSET, ToolsetServer, build_instructions, resolve_toolsets
from kubectl_mcp_tool.tools import (
    register_backup_tools,
    register_capi_tools,
    register_certs_tools,
    register_cilium_tools,
    register_cluster_tools,
    register_cost_tools,
    register_custom_resource_tools,
    register_diagnostics_tools,
    register_gitops_tools,
    register_helm_tools,
    register_istio_tools,
    register_keda_tools,
    register_kind_tools,
    register_kubectl_tools,
    register_kubevirt_tools,
    register_multicluster_tools,
    register_networking_tools,
    register_operations_tools,
    register_pod_tools,
    register_policy_tools,
    register_rollouts_tools,
    register_security_tools,
    register_vind_tools,
)
from kubectl_mcp_tool.utils.helpers import mask_secrets, secret_masking_enabled

from fastmcp import FastMCP

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

warnings.filterwarnings("ignore", category=RuntimeWarning, message=r".*found in sys.modules after import of package.*")

_log_file = os.environ.get("MCP_LOG_FILE")
_log_level = logging.DEBUG if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true") else logging.INFO

_handlers: List[logging.Handler] = []
if _log_file:
    try:
        os.makedirs(os.path.dirname(_log_file), exist_ok=True)
        _handlers.append(logging.FileHandler(_log_file))
    except (OSError, ValueError):
        _handlers.append(logging.StreamHandler(sys.stderr))
else:
    _handlers.append(logging.StreamHandler(sys.stderr))

logging.basicConfig(level=_log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=_handlers)
logger = logging.getLogger("mcp-server")

for handler in logging.root.handlers[:]:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        logging.root.removeHandler(handler)

MCP_PATH = "/mcp"
TRUTHY = ("1", "true", "yes")

SAFETY_MODE_ALIASES = {
    "read-only": SafetyMode.READ_ONLY,
    "read_only": SafetyMode.READ_ONLY,
    "disable-destructive": SafetyMode.DISABLE_DESTRUCTIVE,
    "disable_destructive": SafetyMode.DISABLE_DESTRUCTIVE,
    "confirm": SafetyMode.CONFIRM,
    "confirm-destructive": SafetyMode.CONFIRM,
    "confirm_destructive": SafetyMode.CONFIRM,
}


class NetworkExposureError(RuntimeError):
    """Raised when a network transport would expose the server without authentication."""


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").lower() in TRUTHY


def _env_list(name: str) -> Optional[List[str]]:
    values = [v.strip() for v in os.environ.get(name, "").split(",") if v.strip()]
    return values or None


def is_loopback_host(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def ensure_network_exposure_allowed(host: str, auth_enabled: bool, allow_unauthenticated: bool) -> None:
    """Refuse to serve tools on a non-loopback address unless auth is on or the operator opted out."""
    if auth_enabled or is_loopback_host(host):
        return
    if not allow_unauthenticated:
        raise NetworkExposureError(
            f"Refusing to listen on {host} without authentication: anyone who can reach this port "
            "would get your Kubernetes credentials. Enable OAuth (MCP_AUTH_ENABLED=true and "
            "MCP_AUTH_ISSUER=...), bind to 127.0.0.1, or, if the network is already protected, "
            "pass --allow-unauthenticated (MCP_ALLOW_UNAUTHENTICATED=true)."
        )
    logger.warning(f"Serving on {host} WITHOUT authentication (--allow-unauthenticated). "
                   "Every client that can reach this port can act with this server's Kubernetes credentials.")


def _request_state_security() -> Optional[Any]:
    key = os.environ.get("MCP_REQUEST_STATE_KEY")
    if not key:
        return None
    if len(key.encode()) < 32:
        raise ValueError("MCP_REQUEST_STATE_KEY must be at least 32 bytes")
    from mcp.server.request_state import RequestStateSecurity
    return RequestStateSecurity(keys=[key.encode()])


class MCPServer:
    """Kubernetes MCP server."""

    def __init__(
        self,
        name: str,
        read_only: bool = False,
        disable_destructive: bool = False,
        confirm_destructive: bool = False,
        config_file: Optional[str] = None,
        toolsets: Optional[str] = None,
        tool_search: Optional[bool] = None,
    ):
        self.name = name
        self._dependencies_checked = False
        self._dependencies_available = None
        self._stats = get_stats_collector()

        self._cli_read_only = read_only
        self._cli_disable_destructive = disable_destructive
        self._cli_confirm_destructive = confirm_destructive

        self.config = self._load_configuration(config_file)
        self._apply_safety_mode()
        self.non_destructive = get_safety_mode() != SafetyMode.NORMAL
        self._init_observability()

        register_reload_callback(self._on_config_reload)
        setup_sighup_handler()

        self.auth_config = get_auth_config()
        auth_verifier = self._setup_auth()

        self.toolsets = resolve_toolsets(toolsets if toolsets is not None else os.environ.get("MCP_TOOLSETS"))
        server_kwargs: dict = {"name": name, "version": __version__, "instructions": build_instructions(self.toolsets)}
        if auth_verifier:
            server_kwargs["auth"] = auth_verifier
        request_state_security = _request_state_security()
        if request_state_security:
            server_kwargs["request_state_security"] = request_state_security
        self.server = FastMCP(**server_kwargs)
        self.server.add_middleware(ToolGuardMiddleware(
            enforce_scopes=auth_verifier is not None,
            mask=secret_masking_enabled(),
        ))

        self.setup_tools()
        self.tool_search = _env_flag("MCP_TOOL_SEARCH") if tool_search is None else tool_search
        if self.tool_search:
            self._enable_tool_search()
        self.setup_resources()
        self.setup_prompts()
        self._setup_routes()

        mode_info = get_mode_info()
        logger.info(f"MCP Server initialized: {name} v{__version__}")
        logger.info(f"Safety mode: {mode_info['mode']} - {mode_info['description']}")

    def _load_configuration(self, config_file: Optional[str]) -> Any:
        return load_config(config_file=config_file or None)

    def _apply_safety_mode(self) -> None:
        """Apply safety mode; CLI flags take precedence over config file and MCP_SAFETY_MODE."""
        if self._cli_read_only:
            mode = SafetyMode.READ_ONLY
        elif self._cli_disable_destructive:
            mode = SafetyMode.DISABLE_DESTRUCTIVE
        elif self._cli_confirm_destructive:
            mode = SafetyMode.CONFIRM
        else:
            configured = str(getattr(getattr(self.config, "safety", None), "mode", "normal")).lower()
            mode = SAFETY_MODE_ALIASES.get(configured, SafetyMode.NORMAL)
        set_safety_mode(mode)

    def _init_observability(self) -> None:
        metrics = getattr(self.config, "metrics", None)
        if getattr(metrics, "tracing_enabled", False) or getattr(metrics, "otlp_endpoint", None) or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
            try:
                init_tracing()
                logger.info("OpenTelemetry tracing initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize tracing: {e}")

    def _on_config_reload(self, new_config: Any) -> None:
        logger.info("Configuration reloaded")
        self.config = new_config
        self._apply_safety_mode()
        self.non_destructive = get_safety_mode() != SafetyMode.NORMAL
        logger.info(f"Safety mode after reload: {get_mode_info()['mode']}")

    def _setup_auth(self) -> Optional[Any]:
        if not self.auth_config.enabled:
            return None
        verifier = create_auth_verifier(self.auth_config)
        if verifier is None:
            raise RuntimeError("MCP_AUTH_ENABLED is set but no token verifier could be created")
        logger.info(f"Authentication configured with issuer: {self.auth_config.issuer_url}")
        return verifier

    @property
    def dependencies_available(self) -> bool:
        if not self._dependencies_checked:
            self._dependencies_available = self._check_dependencies()
            self._dependencies_checked = True
            if not self._dependencies_available:
                logger.warning("Some dependencies are missing. Certain operations may not work correctly.")
        return self._dependencies_available

    def setup_tools(self):
        registrar = ToolsetServer(self.server, self.toolsets)
        register_kubectl_tools(registrar, self.non_destructive)
        register_helm_tools(registrar, self.non_destructive, self._check_helm_availability)
        for register in (
            register_operations_tools,
            register_pod_tools,
            register_cluster_tools,
            register_multicluster_tools,
            register_networking_tools,
            register_diagnostics_tools,
            register_security_tools,
            register_cost_tools,
            register_custom_resource_tools,
            register_gitops_tools,
            register_certs_tools,
            register_policy_tools,
            register_backup_tools,
            register_keda_tools,
            register_cilium_tools,
            register_rollouts_tools,
            register_capi_tools,
            register_kubevirt_tools,
            register_istio_tools,
            register_kind_tools,
            register_vind_tools,
        ):
            register(registrar, self.non_destructive)
        self.registered_tools = registrar.registered
        logger.info(f"Toolsets: {', '.join(sorted(self.toolsets))} ({len(self.registered_tools)} tools)")

    def _enable_tool_search(self) -> None:
        """List only default-toolset tools plus search_tools/call_tool; the rest is found on demand."""
        from fastmcp.server.transforms.search import BM25SearchTransform

        pinned = [n for n in self.registered_tools if TOOL_TOOLSET[n] in DEFAULT_TOOLSETS]
        self.server.add_transform(BM25SearchTransform(max_results=8, always_visible=pinned))
        logger.info(f"Tool search enabled: {len(pinned)} tools pinned, {len(self.registered_tools) - len(pinned)} searchable")

    def setup_resources(self):
        register_resources(self.server)

    def setup_prompts(self):
        prompts_config = getattr(self.config, "prompts", None)
        register_prompts(self.server, config_path=getattr(prompts_config, "file", None))

    def _setup_routes(self) -> None:
        from starlette.responses import JSONResponse, PlainTextResponse

        @self.server.custom_route("/health", methods=["GET"], include_in_schema=False)
        async def health(request):
            return JSONResponse({"status": "healthy", "server": self.name, "version": __version__})

        @self.server.custom_route("/stats", methods=["GET"], include_in_schema=False)
        async def stats(request):
            return JSONResponse(self._stats.get_stats())

        @self.server.custom_route("/metrics", methods=["GET"], include_in_schema=False)
        async def metrics(request):
            if is_prometheus_available():
                return PlainTextResponse(get_metrics(), media_type="text/plain; version=0.0.4; charset=utf-8")
            return PlainTextResponse("# Prometheus metrics not available\n", media_type="text/plain")

        @self.server.custom_route("/safety", methods=["GET"], include_in_schema=False)
        async def safety(request):
            return JSONResponse(get_mode_info())

    def _check_dependencies(self) -> bool:
        kubectl_ok = self._check_kubectl_availability()
        if not kubectl_ok:
            logger.warning("kubectl is not available in PATH")
        return kubectl_ok

    def _check_tool_availability(self, tool: str) -> bool:
        if shutil.which(tool) is None:
            return False
        version_args = {"kubectl": ["version", "--client", "--output=json"], "helm": ["version", "--short"]}
        try:
            subprocess.check_output([tool, *version_args.get(tool, ["version"])], stderr=subprocess.PIPE, timeout=2)
            return True
        except (subprocess.SubprocessError, OSError):
            return False

    def _check_kubectl_availability(self) -> bool:
        return self._check_tool_availability("kubectl")

    def _check_helm_availability(self) -> bool:
        return self._check_tool_availability("helm")

    def _check_destructive(self):
        """Return None if destructive operations are allowed, an error dict otherwise."""
        if self.non_destructive:
            return {"success": False, "error": "Operation blocked: non-destructive mode enabled"}
        return None

    def _mask_secrets(self, text: str) -> str:
        return mask_secrets(text)

    async def serve_stdio(self):
        if _env_flag("MCP_DEBUG"):
            logger.debug(f"Working directory: {os.getcwd()}")
            logger.debug(f"KUBECONFIG: {os.path.expanduser(os.environ.get('KUBECONFIG', '~/.kube/config'))}")
            logger.debug(f"Dependencies: {'available' if self.dependencies_available else 'missing'}")
        await self.server.run_stdio_async(show_banner=False)

    async def serve_http(self, host: str = "127.0.0.1", port: int = 8000, allow_unauthenticated: bool = False):
        """Serve Streamable HTTP at /mcp. Stateless: any replica can answer any request."""
        ensure_network_exposure_allowed(host, self.auth_config.enabled, allow_unauthenticated)
        logger.info(f"Streamable HTTP (stateless) on http://{host}:{port}{MCP_PATH}; health at /health")
        await self.server.run_http_async(
            transport="http",
            host=host,
            port=port,
            path=MCP_PATH,
            stateless_http=True,
            show_banner=False,
            allowed_hosts=_env_list("MCP_ALLOWED_HOSTS"),
            allowed_origins=_env_list("MCP_ALLOWED_ORIGINS"),
        )

    async def serve_sse(self, host: str = "127.0.0.1", port: int = 8000, allow_unauthenticated: bool = False):
        """Serve the legacy HTTP+SSE transport (deprecated by the MCP spec; use --transport http)."""
        ensure_network_exposure_allowed(host, self.auth_config.enabled, allow_unauthenticated)
        logger.warning("The SSE transport is deprecated (SEP-2596) and session-bound; prefer --transport http.")
        await self.server.run_http_async(
            transport="sse",
            host=host,
            port=port,
            show_banner=False,
            allowed_hosts=_env_list("MCP_ALLOWED_HOSTS"),
            allowed_origins=_env_list("MCP_ALLOWED_ORIGINS"),
        )


def add_serve_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "streamable-http", "sse"],
        default=os.environ.get("MCP_SERVER_TRANSPORT", "stdio"),
        help="stdio (default), http/streamable-http (stateless), or sse (deprecated). Env: MCP_SERVER_TRANSPORT",
    )
    parser.add_argument("--host", default=os.environ.get("MCP_SERVER_HOST", "127.0.0.1"),
                        help="Bind address for network transports (default: 127.0.0.1). Env: MCP_SERVER_HOST")
    parser.add_argument("--port", type=int, default=int(os.environ.get("MCP_SERVER_PORT", "8000")),
                        help="Port for network transports (default: 8000). Env: MCP_SERVER_PORT")
    parser.add_argument("--allow-unauthenticated", action="store_true", default=_env_flag("MCP_ALLOW_UNAUTHENTICATED"),
                        help="Allow binding a non-loopback address without OAuth. Env: MCP_ALLOW_UNAUTHENTICATED")
    parser.add_argument("--read-only", action="store_true", help="Hide and block every tool that modifies state")
    parser.add_argument("--disable-destructive", "--non-destructive", action="store_true",
                        help="Allow create/update, block delete operations")
    parser.add_argument("--confirm-destructive", action="store_true",
                        help="Ask the user to confirm destructive operations (blocked if the client cannot ask)")
    parser.add_argument("--toolsets", default=os.environ.get("MCP_TOOLSETS"),
                        help="Comma-separated toolsets: default (core,helm), all, or names such as gitops,certs. Env: MCP_TOOLSETS")
    parser.add_argument("--tool-search", action="store_true", default=_env_flag("MCP_TOOL_SEARCH"),
                        help="List only default tools plus search_tools/call_tool for on-demand discovery. Env: MCP_TOOL_SEARCH")
    parser.add_argument("--config", default=None, help="Path to TOML configuration file")
    parser.add_argument("--stateless", action="store_true",
                        help="Do not cache Kubernetes API clients; reload kubeconfig on every request. Env: MCP_STATELESS_MODE")
    parser.add_argument("--watch-kubeconfig", action="store_true",
                        help="Reload kubeconfig automatically when the file changes. Env: MCP_KUBECONFIG_WATCH")
    parser.add_argument("--watch-interval", type=float, default=5.0, help="Kubeconfig watch interval in seconds (default: 5.0)")
    return parser


def run_server(args: argparse.Namespace, name: str = "kubernetes") -> int:
    if args.stateless or _env_flag("MCP_STATELESS_MODE"):
        from kubectl_mcp_tool.k8s_config import set_stateless_mode
        set_stateless_mode(True)

    if args.watch_kubeconfig or _env_flag("MCP_KUBECONFIG_WATCH"):
        from kubectl_mcp_tool.k8s_config import enable_kubeconfig_watch
        enable_kubeconfig_watch(check_interval=args.watch_interval)

    server = MCPServer(
        name=name,
        read_only=args.read_only,
        disable_destructive=args.disable_destructive,
        confirm_destructive=args.confirm_destructive,
        config_file=args.config,
        toolsets=args.toolsets,
        tool_search=args.tool_search,
    )

    try:
        if args.transport == "stdio":
            asyncio.run(server.serve_stdio())
        elif args.transport == "sse":
            asyncio.run(server.serve_sse(host=args.host, port=args.port, allow_unauthenticated=args.allow_unauthenticated))
        else:
            asyncio.run(server.serve_http(host=args.host, port=args.port, allow_unauthenticated=args.allow_unauthenticated))
    except NetworkExposureError as e:
        logger.error(str(e))
        return 2
    except KeyboardInterrupt:
        pass
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["serve"]:
        argv = argv[1:]
    parser = argparse.ArgumentParser(prog="kubectl-mcp-server", description="MCP server for Kubernetes")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    add_serve_arguments(parser)
    return run_server(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
