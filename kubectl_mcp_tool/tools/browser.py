"""Browser automation tools using agent-browser (optional module)."""

import json
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, Optional

from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")

BROWSER_ENABLED = os.environ.get("MCP_BROWSER_ENABLED", "").lower() in ("1", "true")
BROWSER_AVAILABLE = shutil.which("agent-browser") is not None


def is_browser_available() -> bool:
    """Check if browser tools should be registered."""
    if not BROWSER_ENABLED:
        return False
    if not BROWSER_AVAILABLE:
        logger.warning("MCP_BROWSER_ENABLED=true but agent-browser not found in PATH")
        return False
    return True


def _run_browser(args: list, timeout: int = 60) -> Dict[str, Any]:
    """Execute agent-browser command."""
    cmd = ["agent-browser"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            return {"success": False, "error": result.stderr.strip() or "Command failed"}
        output = result.stdout.strip()
        if "--json" in args:
            try:
                return {"success": True, "data": json.loads(output)}
            except json.JSONDecodeError:
                return {"success": True, "output": output}
        return {"success": True, "output": output}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "error": "agent-browser not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_ingress_url(service: str, namespace: str) -> Optional[str]:
    """Get ingress URL for a service."""
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
    """Get service URL (LoadBalancer or NodePort)."""
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
    """Register browser automation tools."""

    @server.tool(annotations=ToolAnnotations(title="Browser Open URL", readOnlyHint=True))
    def browser_open(url: str, wait_for: str = "networkidle") -> Dict[str, Any]:
        """Open a URL in the browser."""
        result = _run_browser(["open", url])
        if result.get("success") and wait_for:
            _run_browser(["wait", "--load", wait_for])
        return {**result, "url": url}

    @server.tool(annotations=ToolAnnotations(title="Browser Snapshot", readOnlyHint=True))
    def browser_snapshot(interactive_only: bool = True, compact: bool = True, depth: Optional[int] = None) -> Dict[str, Any]:
        """Get accessibility tree snapshot of current page."""
        args = ["snapshot", "--json"]
        if interactive_only:
            args.append("-i")
        if compact:
            args.append("-c")
        if depth:
            args.extend(["-d", str(depth)])
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
    def browser_screenshot(output_path: str = "/tmp/screenshot.png", full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot of the current page."""
        args = ["screenshot", output_path]
        if full_page:
            args.append("--full")
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
    def browser_wait(selector: Optional[str] = None, text: Optional[str] = None, timeout_ms: int = 5000) -> Dict[str, Any]:
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
        open_result = _run_browser(["open", full_url])
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
        _run_browser(["open", full_url])
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

        _run_browser(["open", url])
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

        _run_browser(["open", url])
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
        open_result = _run_browser(["open", url])
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
        _run_browser(["open", url])
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

        result = _run_browser(["open", url])
        return {**result, "provider": provider, "url": url}

    @server.tool(annotations=ToolAnnotations(title="Browser PDF Export", readOnlyHint=True))
    def browser_pdf_export(url: str, output_path: str = "/tmp/page.pdf") -> Dict[str, Any]:
        """Export a web page as PDF."""
        _run_browser(["open", url])
        _run_browser(["wait", "--load", "networkidle"])
        _run_browser(["wait", "2000"])
        result = _run_browser(["pdf", output_path])
        _run_browser(["close"])
        return {**result, "url": url, "path": output_path}

    logger.info("Registered 19 browser automation tools")
