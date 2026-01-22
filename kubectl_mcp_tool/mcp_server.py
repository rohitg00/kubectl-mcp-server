#!/usr/bin/env python3
"""
MCP server implementation for kubectl-mcp-tool.

Compatible with:
- Claude Desktop
- Cursor AI
- Windsurf
- Docker MCP Toolkit (https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)

FastMCP Migration Notes:
------------------------
Currently using: fastmcp (gofastmcp.com) - standalone package with extra features
To revert to official Anthropic MCP SDK:
  1. Change requirements.txt: fastmcp>=3.0.0 -> mcp>=1.8.0
  2. Change import below: from fastmcp import FastMCP -> from mcp.server.fastmcp import FastMCP
  3. Change ToolAnnotations import: from fastmcp.tools import ToolAnnotations -> from mcp.types import ToolAnnotations
"""

import json
import sys
import logging
import asyncio
import os
import platform
from typing import List, Optional, Any

from kubectl_mcp_tool.tools import (
    register_helm_tools,
    register_pod_tools,
    register_core_tools,
    register_cluster_tools,
    register_deployment_tools,
    register_security_tools,
    register_networking_tools,
    register_storage_tools,
    register_operations_tools,
    register_diagnostics_tools,
    register_cost_tools,
)
from kubectl_mcp_tool.resources import register_resources
from kubectl_mcp_tool.prompts import register_prompts
from kubectl_mcp_tool.auth import get_auth_config, create_auth_verifier

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import warnings
warnings.filterwarnings(
    "ignore",
    category=RuntimeWarning,
    message=r".*found in sys.modules after import of package.*"
)

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

logging.basicConfig(
    level=_log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=_handlers
)
logger = logging.getLogger("mcp-server")

for handler in logging.root.handlers[:]:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        logging.root.removeHandler(handler)

# FastMCP 3 from gofastmcp.com (standalone package)
# To revert to official SDK: from mcp.server.fastmcp import FastMCP
try:
    from fastmcp import FastMCP
except ImportError:
    logger.error("FastMCP not found. Installing...")
    import subprocess
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "fastmcp>=3.0.0b1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        from fastmcp import FastMCP
    except Exception as e:
        logger.error(f"Failed to install FastMCP: {e}")
        raise


class MCPServer:
    """MCP server implementation."""

    def __init__(self, name: str, non_destructive: bool = False):
        """Initialize the MCP server.

        Args:
            name: Server name for identification
            non_destructive: If True, block destructive operations

        Environment Variables:
            MCP_AUTH_ENABLED: Enable OAuth 2.1 authentication (default: false)
            MCP_AUTH_ISSUER: OAuth 2.0 Authorization Server URL
            MCP_AUTH_JWKS_URI: JWKS endpoint (optional, derived from issuer)
            MCP_AUTH_AUDIENCE: Expected token audience (default: kubectl-mcp-server)
            MCP_AUTH_REQUIRED_SCOPES: Required scopes (default: mcp:tools)
        """
        self.name = name
        self.non_destructive = non_destructive
        self._dependencies_checked = False
        self._dependencies_available = None

        # Load authentication configuration
        self.auth_config = get_auth_config()
        auth_verifier = self._setup_auth()

        # Initialize FastMCP with optional authentication
        if auth_verifier:
            logger.info("Initializing MCP server with authentication enabled")
            self.server = FastMCP(name=name, auth=auth_verifier)
        else:
            self.server = FastMCP(name=name)

        self.setup_tools()
        self.setup_resources()
        self.setup_prompts()

    def _setup_auth(self) -> Optional[Any]:
        """Set up authentication if enabled."""
        if not self.auth_config.enabled:
            logger.debug("Authentication disabled")
            return None

        try:
            verifier = create_auth_verifier(self.auth_config)
            if verifier:
                logger.info(f"Authentication configured with issuer: {self.auth_config.issuer_url}")
            return verifier
        except Exception as e:
            logger.error(f"Failed to configure authentication: {e}")
            if self.auth_config.enabled:
                raise
            return None

    @property
    def dependencies_available(self) -> bool:
        """Lazy check for dependencies (only runs once, on first access)."""
        if not self._dependencies_checked:
            self._dependencies_available = self._check_dependencies()
            self._dependencies_checked = True
            if not self._dependencies_available:
                logger.warning("Some dependencies are missing. Certain operations may not work correctly.")
        return self._dependencies_available

    def setup_tools(self):
        """Set up the tools for the MCP server by calling all registration functions."""
        # Register all tool modules
        register_helm_tools(self.server, self.non_destructive, self._check_helm_availability)
        register_pod_tools(self.server, self.non_destructive)
        register_core_tools(self.server, self.non_destructive)
        register_cluster_tools(self.server, self.non_destructive)
        register_deployment_tools(self.server, self.non_destructive)
        register_security_tools(self.server, self.non_destructive)
        register_networking_tools(self.server, self.non_destructive)
        register_storage_tools(self.server, self.non_destructive)
        register_operations_tools(self.server, self.non_destructive)
        register_diagnostics_tools(self.server, self.non_destructive)
        register_cost_tools(self.server, self.non_destructive)

    def setup_resources(self):
        """Set up MCP resources for Kubernetes data exposure."""
        register_resources(self.server)

    def setup_prompts(self):
        """Set up MCP prompts."""
        register_prompts(self.server)

    def _check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        kubectl_ok = self._check_kubectl_availability()
        if not kubectl_ok:
            logger.warning("kubectl is not available in PATH")
        return kubectl_ok

    def _check_tool_availability(self, tool: str) -> bool:
        """Check if a tool (kubectl, helm) is available and working."""
        try:
            import subprocess
            import shutil
            if shutil.which(tool) is None:
                return False
            if tool == "kubectl":
                subprocess.check_output(
                    [tool, "version", "--client", "--output=json"],
                    stderr=subprocess.PIPE,
                    timeout=2
                )
            elif tool == "helm":
                subprocess.check_output(
                    [tool, "version", "--short"],
                    stderr=subprocess.PIPE,
                    timeout=2
                )
            return True
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_kubectl_availability(self) -> bool:
        """Check if kubectl is available."""
        return self._check_tool_availability("kubectl")

    def _check_helm_availability(self) -> bool:
        """Check if helm is available."""
        return self._check_tool_availability("helm")

    def _check_destructive(self):
        """Check if destructive operations are allowed.

        Returns None if allowed, error dict if blocked.
        """
        if self.non_destructive:
            return {"success": False, "error": "Operation blocked: non-destructive mode enabled"}
        return None

    def _mask_secrets(self, text: str) -> str:
        """Mask sensitive data in text output.

        Masks base64-encoded secrets, passwords, tokens, and API keys.
        """
        import re

        # Mask base64-encoded data (common in Kubernetes secrets)
        # Match data fields with base64 values (at least 16 chars)
        text = re.sub(
            r'(data:\s*\n(?:\s+\w+:\s*)[A-Za-z0-9+/=]{16,})',
            lambda m: re.sub(r':\s*[A-Za-z0-9+/=]{16,}', ': [MASKED]', m.group(0)),
            text
        )

        # Mask password fields
        text = re.sub(
            r'(password|passwd|secret|credential)(\s*[=:]\s*)["\']?[^"\'\s]+["\']?',
            r'\1\2[MASKED]',
            text,
            flags=re.IGNORECASE
        )

        # Mask token fields
        text = re.sub(
            r'(token|api[_-]?key|auth[_-]?key)(\s*[=:]\s*)["\']?[^"\'\s]+["\']?',
            r'\1\2[MASKED]',
            text,
            flags=re.IGNORECASE
        )

        # Mask Bearer tokens
        text = re.sub(
            r'(Bearer\s+)[A-Za-z0-9._-]+',
            r'\1[MASKED]',
            text
        )

        # Mask JWT tokens (three base64 sections separated by dots)
        text = re.sub(
            r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
            '[MASKED]',
            text
        )

        return text

    async def serve_stdio(self):
        """Serve the MCP server over stdio transport."""
        if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true"):
            logger.debug("Starting MCP server with stdio transport")
            logger.debug(f"Working directory: {os.getcwd()}")
            kube_config = os.environ.get('KUBECONFIG', '~/.kube/config')
            expanded_path = os.path.expanduser(kube_config)
            logger.debug(f"KUBECONFIG: {expanded_path}")
            logger.debug(f"Dependencies: {'available' if self.dependencies_available else 'missing'}")

        await self.server.run_stdio_async()

    async def serve_sse(self, host: str = "0.0.0.0", port: int = 8000):
        """Serve the MCP server over SSE transport."""
        logger.info(f"Starting MCP server with SSE transport on {host}:{port}")

        try:
            # Try newer FastMCP API with host and port
            await self.server.run_sse_async(host=host, port=port)
        except TypeError:
            try:
                # Try with just port parameter
                await self.server.run_sse_async(port=port)
            except TypeError:
                # Fall back to the legacy signature that takes no parameters
                logger.warning(
                    "FastMCP.run_sse_async() does not accept host/port parameters in this version. "
                    "Falling back to the default signature (using FastMCP's internal default port)."
                )
                await self.server.run_sse_async()

    async def serve_http(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Serve the MCP server over HTTP transport (streamable HTTP).
        This is an alternative to SSE that some clients prefer.
        """
        logger.info(f"Starting MCP server with HTTP transport on {host}:{port}")

        try:
            # Check if FastMCP supports streamable HTTP
            if hasattr(self.server, 'run_http_async'):
                await self.server.run_http_async(host=host, port=port)
            elif hasattr(self.server, 'run_streamable_http_async'):
                await self.server.run_streamable_http_async(host=host, port=port)
            else:
                # Fall back to implementing HTTP transport manually using ASGI
                logger.info("FastMCP does not have built-in HTTP support, using custom implementation")
                await self._serve_http_custom(host=host, port=port)
        except TypeError as e:
            logger.warning(f"HTTP transport parameter issue: {e}. Trying alternative signatures...")
            # Try without parameters
            if hasattr(self.server, 'run_http_async'):
                await self.server.run_http_async()
            elif hasattr(self.server, 'run_streamable_http_async'):
                await self.server.run_streamable_http_async()
            else:
                await self._serve_http_custom(host=host, port=port)

    async def _serve_http_custom(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Custom HTTP server implementation using uvicorn and Starlette.
        Provides HTTP/JSON-RPC transport for MCP.
        """
        try:
            from starlette.applications import Starlette
            from starlette.responses import JSONResponse
            from starlette.routing import Route
            import uvicorn
        except ImportError:
            logger.error("HTTP transport requires 'starlette' and 'uvicorn'. Install with: pip install starlette uvicorn")
            raise ImportError("Missing dependencies for HTTP transport. Run: pip install starlette uvicorn")

        async def handle_mcp_request(request):
            """Handle incoming MCP JSON-RPC requests."""
            try:
                body = await request.json()
                logger.debug(f"Received MCP request: {body}")

                # Get the method and params from the JSON-RPC request
                method = body.get("method", "")
                params = body.get("params", {})
                request_id = body.get("id")

                # Handle different MCP methods
                if method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"subscribe": False, "listChanged": True}
                        },
                        "serverInfo": {
                            "name": self.name,
                            "version": "1.2.0"
                        }
                    }
                elif method == "tools/list":
                    # Get list of tools from FastMCP
                    tools = []
                    if hasattr(self.server, '_tool_manager') and hasattr(self.server._tool_manager, 'tools'):
                        for name, tool in self.server._tool_manager.tools.items():
                            tools.append({
                                "name": name,
                                "description": tool.description if hasattr(tool, 'description') else "",
                                "inputSchema": tool.parameters if hasattr(tool, 'parameters') else {}
                            })
                    result = {"tools": tools}
                elif method == "tools/call":
                    tool_name = params.get("name", "")
                    tool_args = params.get("arguments", {})

                    # Execute the tool
                    if hasattr(self.server, '_tool_manager'):
                        try:
                            tool_result = await self.server._tool_manager.call_tool(tool_name, tool_args)
                            result = {"content": [{"type": "text", "text": json.dumps(tool_result)}]}
                        except Exception as e:
                            result = {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "isError": True}
                    else:
                        result = {"content": [{"type": "text", "text": "Tool manager not available"}], "isError": True}
                elif method == "ping":
                    result = {}
                else:
                    result = {"error": f"Unknown method: {method}"}

                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                return JSONResponse(response)
            except Exception as e:
                logger.error(f"Error handling MCP request: {e}")
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }, status_code=500)

        async def health_check(request):
            """Health check endpoint."""
            return JSONResponse({"status": "healthy", "server": self.name})

        app = Starlette(
            routes=[
                Route("/", handle_mcp_request, methods=["POST"]),
                Route("/mcp", handle_mcp_request, methods=["POST"]),
                Route("/health", health_check, methods=["GET"]),
            ]
        )

        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


if __name__ == "__main__":
    import argparse
    import signal

    parser = argparse.ArgumentParser(description="Run the Kubectl MCP Server.")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse", "http", "streamable-http"],
        default="stdio",
        help="Communication transport to use (stdio, sse, http, or streamable-http). Default: stdio.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to use for SSE/HTTP transport. Default: 8000.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to for SSE/HTTP transport. Default: 0.0.0.0.",
    )
    args = parser.parse_args()

    server_name = "kubectl_mcp_server"
    mcp_server = MCPServer(name=server_name)

    # Handle signals gracefully with immediate exit
    def signal_handler(sig, frame):
        print("\nShutting down server...", file=sys.stderr)
        os._exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if args.transport == "stdio":
            logger.info(f"Starting {server_name} with stdio transport.")
            asyncio.run(mcp_server.serve_stdio())
        elif args.transport == "sse":
            logger.info(f"Starting {server_name} with SSE transport on {args.host}:{args.port}.")
            asyncio.run(mcp_server.serve_sse(host=args.host, port=args.port))
        elif args.transport in ("http", "streamable-http"):
            logger.info(f"Starting {server_name} with HTTP transport on {args.host}:{args.port}.")
            asyncio.run(mcp_server.serve_http(host=args.host, port=args.port))
    except KeyboardInterrupt:
        print("\nShutting down server...", file=sys.stderr)
    except SystemExit:
        pass  # Clean exit
    except Exception as e:
        logger.error(f"Server exited with error: {e}", exc_info=True)
