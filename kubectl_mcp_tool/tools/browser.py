"""Browser automation tools using agent-browser (optional module)."""

import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")

BROWSER_ENABLED = os.environ.get("MCP_BROWSER_ENABLED", "").lower() in ("1", "true")
BROWSER_AVAILABLE = shutil.which("agent-browser") is not None

MCP_BROWSER_PROVIDER = os.environ.get("MCP_BROWSER_PROVIDER")
MCP_BROWSER_PROFILE = os.environ.get("MCP_BROWSER_PROFILE")
MCP_BROWSER_CDP_URL = os.environ.get("MCP_BROWSER_CDP_URL")
MCP_BROWSER_PROXY = os.environ.get("MCP_BROWSER_PROXY")
MCP_BROWSER_PROXY_BYPASS = os.environ.get("MCP_BROWSER_PROXY_BYPASS")
MCP_BROWSER_USER_AGENT = os.environ.get("MCP_BROWSER_USER_AGENT")
MCP_BROWSER_ARGS = os.environ.get("MCP_BROWSER_ARGS")
MCP_BROWSER_SESSION = os.environ.get("MCP_BROWSER_SESSION")
MCP_BROWSER_HEADED = os.environ.get("MCP_BROWSER_HEADED", "").lower() in ("1", "true")

MCP_BROWSER_DEBUG = os.environ.get("MCP_BROWSER_DEBUG", "").lower() in ("1", "true")
MCP_BROWSER_MAX_RETRIES = int(os.environ.get("MCP_BROWSER_MAX_RETRIES", "3"))
MCP_BROWSER_RETRY_DELAY = int(os.environ.get("MCP_BROWSER_RETRY_DELAY", "1000"))
MCP_BROWSER_TIMEOUT = int(os.environ.get("MCP_BROWSER_TIMEOUT", "60"))

TRANSIENT_ERRORS = [
    "ECONNREFUSED",
    "ETIMEDOUT",
    "ECONNRESET",
    "EPIPE",
    "timeout",
    "Timeout",
    "connection refused",
    "socket hang up",
]


def is_browser_available() -> bool:
    if not BROWSER_ENABLED:
        return False
    if not BROWSER_AVAILABLE:
        logger.warning("MCP_BROWSER_ENABLED=true but agent-browser not found in PATH")
        return False
    return True


def _debug(message: str) -> None:
    if MCP_BROWSER_DEBUG:
        logger.debug(f"[browser] {message}")


def _get_global_options() -> List[str]:
    opts = []
    if provider := os.environ.get("MCP_BROWSER_PROVIDER"):
        opts.extend(["-p", provider])
    if profile := os.environ.get("MCP_BROWSER_PROFILE"):
        opts.extend(["--profile", os.path.expanduser(profile)])
    if session := os.environ.get("MCP_BROWSER_SESSION"):
        opts.extend(["--session", session])
    if cdp := os.environ.get("MCP_BROWSER_CDP_URL"):
        opts.extend(["--cdp", cdp])
    if proxy := os.environ.get("MCP_BROWSER_PROXY"):
        opts.extend(["--proxy", proxy])
    if proxy_bypass := os.environ.get("MCP_BROWSER_PROXY_BYPASS"):
        opts.extend(["--proxy-bypass", proxy_bypass])
    if user_agent := os.environ.get("MCP_BROWSER_USER_AGENT"):
        opts.extend(["--user-agent", user_agent])
    if args := os.environ.get("MCP_BROWSER_ARGS"):
        opts.extend(["--args", args])
    if os.environ.get("MCP_BROWSER_HEADED", "").lower() in ("1", "true"):
        opts.append("--headed")
    return opts


def _is_transient_error(error_msg: str) -> bool:
    return any(err.lower() in error_msg.lower() for err in TRANSIENT_ERRORS)


def _run_browser(
    args: List[str],
    timeout: int = None,
    use_global_opts: bool = True
) -> Dict[str, Any]:
    timeout = timeout or MCP_BROWSER_TIMEOUT

    cmd = ["agent-browser"]
    if use_global_opts:
        cmd.extend(_get_global_options())
    cmd.extend(args)

    _debug(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

        if result.returncode != 0:
            error_msg = result.stderr.strip() or "Command failed"
            _debug(f"Command failed: {error_msg}")
            return {"success": False, "error": error_msg}

        output = result.stdout.strip()
        if "--json" in args:
            try:
                return {"success": True, "data": json.loads(output)}
            except json.JSONDecodeError:
                return {"success": True, "output": output}

        return {"success": True, "output": output}

    except subprocess.TimeoutExpired:
        _debug(f"Command timed out after {timeout}s")
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "error": "agent-browser not found. Install with: npm install -g agent-browser"}
    except Exception as e:
        _debug(f"Command error: {e}")
        return {"success": False, "error": str(e)}


def _run_browser_with_retry(
    args: List[str],
    timeout: int = None,
    max_retries: int = None,
    use_global_opts: bool = True
) -> Dict[str, Any]:
    max_retries = max_retries if max_retries is not None else MCP_BROWSER_MAX_RETRIES
    delay_ms = MCP_BROWSER_RETRY_DELAY

    for attempt in range(max_retries + 1):
        result = _run_browser(args, timeout=timeout, use_global_opts=use_global_opts)

        if result.get("success"):
            return result

        error_msg = result.get("error", "")
        if not _is_transient_error(error_msg):
            return result
        if attempt == max_retries:
            _debug(f"Max retries ({max_retries}) exceeded")
            return result

        wait_time = (delay_ms * (2 ** attempt)) / 1000
        _debug(f"Transient error, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
        time.sleep(wait_time)

    return result


def _get_ingress_url(service: str, namespace: str) -> Optional[str]:
    try:
        from kubernetes import client, config
        config.load_kube_config()
        networking = client.NetworkingV1Api()
        ingresses = networking.list_namespaced_ingress(namespace)
        for ing in ingresses.items:
            for rule in ing.spec.rules or []:
                for path in (rule.http.paths if rule.http else []):
                    backend = path.backend
                    if backend.service and backend.service.name == service:
                        host = rule.host or ing.status.load_balancer.ingress[0].hostname
                        scheme = "https" if ing.spec.tls else "http"
                        return f"{scheme}://{host}"
        return None
    except Exception:
        return None


def _get_service_url(service: str, namespace: str) -> Optional[str]:
    try:
        from kubernetes import client, config
        config.load_kube_config()
        v1 = client.CoreV1Api()
        svc = v1.read_namespaced_service(service, namespace)
        if svc.spec.type == "LoadBalancer":
            ingress = svc.status.load_balancer.ingress
            if ingress:
                host = ingress[0].hostname or ingress[0].ip
                port = svc.spec.ports[0].port
                return f"http://{host}:{port}"
        elif svc.spec.type == "NodePort":
            node_port = svc.spec.ports[0].node_port
            return f"http://localhost:{node_port}"
        return None
    except Exception:
        return None


def register_browser_tools(server, non_destructive: bool):
    _ = non_destructive

    @server.tool(annotations=ToolAnnotations(title="Browser Open URL", readOnlyHint=True))
    def browser_open(
        url: str,
        wait_for: str = "networkidle",
        headers: Optional[Dict[str, str]] = None,
        session: Optional[str] = None,
        headed: bool = False
    ) -> Dict[str, Any]:
        """Open a URL in the browser.

        Args:
            url: URL to navigate to
            wait_for: Load state to wait for (load, domcontentloaded, networkidle)
            headers: HTTP headers to set for this origin (v0.7+)
            session: Session name for isolation (v0.7+)
            headed: Show browser window (v0.7+)
        """
        # Build open command with optional headers
        open_args = ["open", url]

        if headers:
            open_args.extend(["--headers", json.dumps(headers)])
        if session:
            open_args.extend(["--session", session])
        if headed:
            open_args.append("--headed")

        result = _run_browser_with_retry(open_args)
        if result.get("success") and wait_for:
            _run_browser(["wait", "--load", wait_for])
        return {**result, "url": url}

    @server.tool(annotations=ToolAnnotations(title="Browser Snapshot", readOnlyHint=True))
    def browser_snapshot(
        interactive_only: bool = True,
        compact: bool = True,
        depth: Optional[int] = None,
        selector: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get accessibility tree snapshot of current page.

        Args:
            interactive_only: Only show interactive elements (buttons, inputs, links)
            compact: Remove empty structural elements
            depth: Limit tree depth
            selector: Scope to CSS selector
        """
        args = ["snapshot", "--json"]
        if interactive_only:
            args.append("-i")
        if compact:
            args.append("-c")
        if depth:
            args.extend(["-d", str(depth)])
        if selector:
            args.extend(["-s", selector])
        return _run_browser(args)

    @server.tool(annotations=ToolAnnotations(title="Browser Click"))
    def browser_click(ref: str) -> Dict[str, Any]:
        """Click an element by ref (from snapshot)."""
        return _run_browser(["click", ref])

    @server.tool(annotations=ToolAnnotations(title="Browser Fill"))
    def browser_fill(ref: str, text: str) -> Dict[str, Any]:
        """Fill a form field by ref."""
        return _run_browser(["fill", ref, text])

    @server.tool(annotations=ToolAnnotations(title="Browser Screenshot", readOnlyHint=True))
    def browser_screenshot(
        output_path: Optional[str] = None,
        full_page: bool = False,
        ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """Take a screenshot of the current page or element.

        Args:
            output_path: Path to save screenshot (auto-generated if None)
            full_page: Capture full scrollable page
            ref: Element ref to screenshot (from snapshot)
        """
        if not output_path:
            fd, output_path = tempfile.mkstemp(suffix=".png", prefix="screenshot_")
            os.close(fd)
        args = ["screenshot", output_path]
        if full_page:
            args.append("--full")
        if ref:
            args.extend(["--ref", ref])
        result = _run_browser(args)
        return {**result, "path": output_path}

    @server.tool(annotations=ToolAnnotations(title="Browser Get Text", readOnlyHint=True))
    def browser_get_text(ref: str) -> Dict[str, Any]:
        """Get text content of an element."""
        return _run_browser(["get", "text", ref])

    @server.tool(annotations=ToolAnnotations(title="Browser Get URL", readOnlyHint=True))
    def browser_get_url() -> Dict[str, Any]:
        """Get current page URL."""
        return _run_browser(["get", "url"])

    @server.tool(annotations=ToolAnnotations(title="Browser Wait"))
    def browser_wait(
        selector: Optional[str] = None,
        text: Optional[str] = None,
        timeout_ms: int = 5000
    ) -> Dict[str, Any]:
        """Wait for element, text, or timeout."""
        if text:
            return _run_browser(["wait", "--text", text], timeout=timeout_ms // 1000 + 5)
        elif selector:
            return _run_browser(["wait", selector], timeout=timeout_ms // 1000 + 5)
        else:
            return _run_browser(["wait", str(timeout_ms)])

    @server.tool(annotations=ToolAnnotations(title="Browser Close"))
    def browser_close() -> Dict[str, Any]:
        """Close the browser."""
        return _run_browser(["close"])

    @server.tool(annotations=ToolAnnotations(title="Browser Connect CDP", readOnlyHint=True))
    def browser_connect_cdp(
        target: str,
        session: Optional[str] = None
    ) -> Dict[str, Any]:
        """Connect to an existing browser via Chrome DevTools Protocol.

        Args:
            target: CDP port number (e.g., 9222) or WebSocket URL (wss://...)
            session: Optional session name for this connection
        """
        args = ["connect", target]
        if session:
            args.extend(["--session", session])
        return _run_browser_with_retry(args, use_global_opts=False)

    @server.tool(annotations=ToolAnnotations(title="Browser Install"))
    def browser_install(with_deps: bool = False) -> Dict[str, Any]:
        """Install Chromium browser for agent-browser.

        Args:
            with_deps: Also install system dependencies (Linux only)
        """
        args = ["install"]
        if with_deps:
            args.append("--with-deps")
        return _run_browser(args, timeout=300, use_global_opts=False)

    @server.tool(annotations=ToolAnnotations(title="Browser Set Provider"))
    def browser_set_provider(
        provider: str,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Configure cloud browser provider for current session.

        Args:
            provider: Provider name (browserbase, browseruse)
            api_key: API key (or use env var BROWSERBASE_API_KEY / BROWSER_USE_API_KEY)
            project_id: Project ID for Browserbase
        """
        # Set environment variables for the session
        env_updates = {}
        if provider.lower() == "browserbase":
            if api_key:
                env_updates["BROWSERBASE_API_KEY"] = api_key
            if project_id:
                env_updates["BROWSERBASE_PROJECT_ID"] = project_id
        elif provider.lower() == "browseruse":
            if api_key:
                env_updates["BROWSER_USE_API_KEY"] = api_key

        # Update environment
        for key, value in env_updates.items():
            os.environ[key] = value

        return {
            "success": True,
            "provider": provider,
            "message": f"Provider set to {provider}. Use -p {provider} flag or set MCP_BROWSER_PROVIDER={provider}"
        }

    @server.tool(annotations=ToolAnnotations(title="Browser Session List", readOnlyHint=True))
    def browser_session_list() -> Dict[str, Any]:
        """List active browser sessions."""
        return _run_browser(["session", "list"], use_global_opts=False)

    @server.tool(annotations=ToolAnnotations(title="Browser Session Switch"))
    def browser_session_switch(session: str) -> Dict[str, Any]:
        """Switch to a different browser session.

        Args:
            session: Session name to switch to
        """
        # Update the environment variable for subsequent commands
        os.environ["MCP_BROWSER_SESSION"] = session
        return {
            "success": True,
            "session": session,
            "message": f"Switched to session: {session}"
        }

    @server.tool(annotations=ToolAnnotations(title="Browser Open With Headers", readOnlyHint=True))
    def browser_open_with_headers(
        url: str,
        headers: Dict[str, str],
        wait_for: str = "networkidle"
    ) -> Dict[str, Any]:
        """Open URL with custom HTTP headers (useful for authentication).

        Headers are scoped to the URL's origin for security.

        Args:
            url: URL to navigate to
            headers: HTTP headers to set (e.g., {"Authorization": "Bearer token"})
            wait_for: Load state to wait for
        """
        args = ["open", url, "--headers", json.dumps(headers)]
        result = _run_browser_with_retry(args)
        if result.get("success") and wait_for:
            _run_browser(["wait", "--load", wait_for])
        return {**result, "url": url, "headers_set": list(headers.keys())}

    @server.tool(annotations=ToolAnnotations(title="Browser Set Viewport"))
    def browser_set_viewport(
        width: Optional[int] = None,
        height: Optional[int] = None,
        device: Optional[str] = None
    ) -> Dict[str, Any]:
        """Set browser viewport size or emulate a device.

        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            device: Device to emulate (e.g., "iPhone 14", "iPad Pro")
        """
        if device:
            return _run_browser(["set", "device", device])
        elif width and height:
            return _run_browser(["set", "viewport", str(width), str(height)])
        else:
            return {"success": False, "error": "Specify device or both width and height"}

    @server.tool(annotations=ToolAnnotations(title="Test K8s Ingress", readOnlyHint=True))
    def browser_test_ingress(
        service_name: str,
        namespace: str = "default",
        path: str = "/",
        expected_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test a Kubernetes service via its Ingress URL."""
        url = _get_ingress_url(service_name, namespace)
        if not url:
            url = _get_service_url(service_name, namespace)
        if not url:
            return {"success": False, "error": f"No external URL found for {service_name} in {namespace}"}

        full_url = f"{url}{path}"
        open_result = _run_browser_with_retry(["open", full_url])
        if not open_result.get("success"):
            return {**open_result, "url": full_url}

        _run_browser(["wait", "--load", "networkidle"])
        snapshot = _run_browser(["snapshot", "-i", "--json"])

        result = {
            "success": True,
            "url": full_url,
            "service": service_name,
            "namespace": namespace,
            "accessible": True,
            "snapshot": snapshot.get("data")
        }

        if expected_text:
            text_result = _run_browser(["wait", "--text", expected_text], timeout=10)
            result["expectedTextFound"] = text_result.get("success", False)

        _run_browser(["close"])
        return result

    @server.tool(annotations=ToolAnnotations(title="Screenshot K8s Service", readOnlyHint=True))
    def browser_screenshot_service(
        service_name: str,
        namespace: str = "default",
        path: str = "/",
        output_path: str = "/tmp/service-screenshot.png",
        full_page: bool = True
    ) -> Dict[str, Any]:
        """Take a screenshot of a Kubernetes service's web UI."""
        url = _get_ingress_url(service_name, namespace)
        if not url:
            url = _get_service_url(service_name, namespace)
        if not url:
            return {"success": False, "error": f"No external URL found for {service_name} in {namespace}"}

        full_url = f"{url}{path}"
        _run_browser_with_retry(["open", full_url])
        _run_browser(["wait", "--load", "networkidle"])
        _run_browser(["wait", "2000"])

        args = ["screenshot", output_path]
        if full_page:
            args.append("--full")
        result = _run_browser(args)
        _run_browser(["close"])
        return {**result, "url": full_url, "path": output_path}

    @server.tool(annotations=ToolAnnotations(title="Screenshot Grafana", readOnlyHint=True))
    def browser_screenshot_grafana(
        grafana_url: str,
        dashboard_uid: Optional[str] = None,
        output_path: str = "/tmp/grafana-dashboard.png"
    ) -> Dict[str, Any]:
        """Take a screenshot of a Grafana dashboard."""
        url = grafana_url
        if dashboard_uid:
            url = f"{grafana_url.rstrip('/')}/d/{dashboard_uid}"

        _run_browser_with_retry(["open", url])
        _run_browser(["wait", "--load", "networkidle"])
        _run_browser(["wait", "3000"])
        result = _run_browser(["screenshot", "--full", output_path])
        _run_browser(["close"])
        return {**result, "url": url, "path": output_path}

    @server.tool(annotations=ToolAnnotations(title="Screenshot ArgoCD", readOnlyHint=True))
    def browser_screenshot_argocd(
        argocd_url: str,
        app_name: Optional[str] = None,
        output_path: str = "/tmp/argocd-screenshot.png"
    ) -> Dict[str, Any]:
        """Take a screenshot of ArgoCD application view."""
        url = argocd_url
        if app_name:
            url = f"{argocd_url.rstrip('/')}/applications/{app_name}"

        _run_browser_with_retry(["open", url])
        _run_browser(["wait", "--load", "networkidle"])
        _run_browser(["wait", "2000"])
        result = _run_browser(["screenshot", "--full", output_path])
        _run_browser(["close"])
        return {**result, "url": url, "path": output_path}

    @server.tool(annotations=ToolAnnotations(title="Health Check Web App", readOnlyHint=True))
    def browser_health_check(
        url: str,
        expected_status_text: Optional[str] = None,
        check_elements: Optional[list] = None
    ) -> Dict[str, Any]:
        """Perform health check on a web application."""
        open_result = _run_browser_with_retry(["open", url])
        if not open_result.get("success"):
            return {**open_result, "url": url, "healthy": False}

        _run_browser(["wait", "--load", "networkidle"])
        title_result = _run_browser(["get", "title"])
        url_result = _run_browser(["get", "url"])
        snapshot = _run_browser(["snapshot", "-i", "-c", "--json"])

        result = {
            "success": True,
            "url": url,
            "finalUrl": url_result.get("output"),
            "title": title_result.get("output"),
            "healthy": True,
            "checks": {}
        }

        if expected_status_text:
            text_check = _run_browser(["wait", "--text", expected_status_text], timeout=5)
            result["checks"]["expectedText"] = text_check.get("success", False)
            if not text_check.get("success"):
                result["healthy"] = False

        if check_elements:
            for elem in check_elements:
                elem_check = _run_browser(["is", "visible", elem])
                result["checks"][elem] = "visible" in elem_check.get("output", "").lower()

        _run_browser(["close"])
        return result

    @server.tool(annotations=ToolAnnotations(title="Browser Form Submit"))
    def browser_form_submit(
        url: str,
        form_data: Dict[str, str],
        submit_ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fill and submit a web form."""
        _run_browser_with_retry(["open", url])
        _run_browser(["wait", "--load", "networkidle"])

        for ref, value in form_data.items():
            fill_result = _run_browser(["fill", ref, value])
            if not fill_result.get("success"):
                _run_browser(["close"])
                return {"success": False, "error": f"Failed to fill {ref}", "details": fill_result}

        if submit_ref:
            _run_browser(["click", submit_ref])
            _run_browser(["wait", "--load", "networkidle"])

        snapshot = _run_browser(["snapshot", "-i", "--json"])
        final_url = _run_browser(["get", "url"])
        _run_browser(["close"])

        return {
            "success": True,
            "url": url,
            "finalUrl": final_url.get("output"),
            "formData": list(form_data.keys()),
            "snapshot": snapshot.get("data")
        }

    @server.tool(annotations=ToolAnnotations(title="Browser Session Save"))
    def browser_session_save(path: str = "/tmp/browser-state.json") -> Dict[str, Any]:
        """Save browser session state (cookies, storage)."""
        return _run_browser(["state", "save", path])

    @server.tool(annotations=ToolAnnotations(title="Browser Session Load"))
    def browser_session_load(path: str = "/tmp/browser-state.json") -> Dict[str, Any]:
        """Load browser session state."""
        return _run_browser(["state", "load", path])

    @server.tool(annotations=ToolAnnotations(title="Open Cloud Console", readOnlyHint=True))
    def browser_open_cloud_console(
        provider: str,
        resource_type: str = "clusters",
        region: Optional[str] = None,
        project: Optional[str] = None
    ) -> Dict[str, Any]:
        """Open cloud provider Kubernetes console (eks, gke, aks)."""
        urls = {
            "eks": f"https://{region or 'us-east-1'}.console.aws.amazon.com/eks/home?region={region or 'us-east-1'}#/{resource_type}",
            "gke": f"https://console.cloud.google.com/kubernetes/{resource_type}?project={project or '_'}",
            "aks": "https://portal.azure.com/#browse/Microsoft.ContainerService%2FmanagedClusters",
            "do": "https://cloud.digitalocean.com/kubernetes/clusters",
        }
        url = urls.get(provider.lower())
        if not url:
            return {"success": False, "error": f"Unknown provider: {provider}. Use eks, gke, aks, or do"}

        result = _run_browser_with_retry(["open", url])
        return {**result, "provider": provider, "url": url}

    @server.tool(annotations=ToolAnnotations(title="Browser PDF Export", readOnlyHint=True))
    def browser_pdf_export(url: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Export a web page as PDF."""
        if not output_path:
            fd, output_path = tempfile.mkstemp(suffix=".pdf", prefix="page_")
            os.close(fd)
        _run_browser_with_retry(["open", url])
        _run_browser(["wait", "--load", "networkidle"])
        _run_browser(["wait", "2000"])
        result = _run_browser(["pdf", output_path])
        _run_browser(["close"])
        return {**result, "url": url, "path": output_path}

    logger.info("Registered 26 browser automation tools (agent-browser v0.7+)")
