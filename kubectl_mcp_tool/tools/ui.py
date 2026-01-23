"""
MCP-UI enabled tools for kubectl-mcp-server.

These tools return UIResource objects that can be rendered by MCP hosts
that support the mcp-ui specification (Goose, LibreChat, Nanobot, etc.)

For hosts that don't support mcp-ui, these tools can optionally render
the UI to a screenshot using agent-browser, making them accessible to
ALL MCP hosts including Claude Desktop.

Installation: pip install mcp-ui-server
Browser screenshots: Requires agent-browser CLI (MCP_BROWSER_ENABLED=true)
"""

import base64
import json
import logging
import html
import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Union

from mcp.types import ToolAnnotations

logger = logging.getLogger("mcp-server")

# Check if agent-browser is available for screenshot rendering
BROWSER_ENABLED = os.environ.get("MCP_BROWSER_ENABLED", "").lower() in ("1", "true")
BROWSER_AVAILABLE = shutil.which("agent-browser") is not None

# Try to import mcp-ui-server, gracefully handle if not installed
try:
    from mcp_ui_server import create_ui_resource, UIMetadataKey
    from mcp_ui_server.core import UIResource
    MCP_UI_AVAILABLE = True
except ImportError:
    MCP_UI_AVAILABLE = False
    UIResource = Dict[str, Any]  # Fallback type
    logger.warning("mcp-ui-server not installed. UI tools will return plain JSON.")


def _render_html_to_screenshot(html_content: str, width: int = 1200, height: int = 800) -> Optional[str]:
    """Render HTML to a screenshot using agent-browser.

    Returns base64-encoded PNG image or None if browser not available.
    """
    if not BROWSER_ENABLED or not BROWSER_AVAILABLE:
        return None

    try:
        # Save HTML to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            html_path = f.name

        # Screenshot path
        screenshot_path = tempfile.mktemp(suffix='.png')

        try:
            # Use agent-browser to render and screenshot
            # Open the HTML file
            subprocess.run(
                ["agent-browser", "open", f"file://{html_path}"],
                capture_output=True, timeout=10
            )

            # Set viewport size
            subprocess.run(
                ["agent-browser", "eval", f"window.resizeTo({width}, {height})"],
                capture_output=True, timeout=5
            )

            # Wait for render
            subprocess.run(
                ["agent-browser", "wait", "500"],
                capture_output=True, timeout=5
            )

            # Take screenshot
            result = subprocess.run(
                ["agent-browser", "screenshot", screenshot_path],
                capture_output=True, timeout=10
            )

            if result.returncode == 0 and os.path.exists(screenshot_path):
                with open(screenshot_path, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')

            return None
        finally:
            # Cleanup temp files
            if os.path.exists(html_path):
                os.unlink(html_path)
            if os.path.exists(screenshot_path):
                os.unlink(screenshot_path)
    except Exception as e:
        logger.warning(f"Failed to render screenshot: {e}")
        return None


def _can_render_screenshots() -> bool:
    """Check if screenshot rendering is available."""
    return BROWSER_ENABLED and BROWSER_AVAILABLE


# CSS styles for consistent theming across UI components
DARK_THEME_CSS = """
:root {
    --bg-primary: #1e1e2e;
    --bg-secondary: #313244;
    --bg-tertiary: #45475a;
    --text-primary: #cdd6f4;
    --text-secondary: #a6adc8;
    --text-muted: #6c7086;
    --accent-blue: #89b4fa;
    --accent-green: #a6e3a1;
    --accent-yellow: #f9e2af;
    --accent-red: #f38ba8;
    --accent-purple: #cba6f7;
    --border-color: #45475a;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.5;
    padding: 16px;
}
.container { max-width: 100%; }
.header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-color);
}
.header h2 { font-size: 1.25rem; font-weight: 600; }
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 500;
}
.badge-green { background: rgba(166, 227, 161, 0.2); color: var(--accent-green); }
.badge-yellow { background: rgba(249, 226, 175, 0.2); color: var(--accent-yellow); }
.badge-red { background: rgba(243, 139, 168, 0.2); color: var(--accent-red); }
.badge-blue { background: rgba(137, 180, 250, 0.2); color: var(--accent-blue); }
.card {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid var(--border-color);
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.card-title { font-weight: 600; font-size: 0.9rem; }
pre, .log-content {
    background: var(--bg-tertiary);
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.8rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
}
.log-line { display: block; }
.log-line:hover { background: rgba(137, 180, 250, 0.1); }
.log-error { color: var(--accent-red); }
.log-warn { color: var(--accent-yellow); }
.log-info { color: var(--accent-blue); }
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
th, td {
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-color);
}
th {
    background: var(--bg-tertiary);
    font-weight: 600;
    color: var(--text-secondary);
    font-size: 0.75rem;
    text-transform: uppercase;
}
tr:hover td { background: rgba(137, 180, 250, 0.05); }
.btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 6px;
    border: none;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}
.btn-primary { background: var(--accent-blue); color: var(--bg-primary); }
.btn-primary:hover { opacity: 0.9; }
.btn-secondary { background: var(--bg-tertiary); color: var(--text-primary); }
.btn-secondary:hover { background: var(--border-color); }
.btn-danger { background: var(--accent-red); color: var(--bg-primary); }
.actions { display: flex; gap: 8px; margin-top: 12px; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }
.stat-card {
    background: var(--bg-tertiary);
    padding: 12px;
    border-radius: 6px;
    text-align: center;
}
.stat-value { font-size: 1.5rem; font-weight: 700; }
.stat-label { font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; }
.search-box {
    width: 100%;
    padding: 8px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
    font-size: 0.85rem;
    margin-bottom: 12px;
}
.search-box:focus { outline: none; border-color: var(--accent-blue); }
.timestamp { color: var(--text-muted); font-size: 0.75rem; }
.status-indicator {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}
.status-running { background: var(--accent-green); }
.status-pending { background: var(--accent-yellow); }
.status-failed { background: var(--accent-red); }
.status-unknown { background: var(--text-muted); }
"""


def _escape(text: str) -> str:
    """HTML escape text content."""
    return html.escape(str(text)) if text else ""


def _create_ui_or_fallback(
    uri: str,
    html_content: str,
    fallback_data: Dict[str, Any],
    frame_size: tuple = ("800px", "500px"),
    render_screenshot: bool = False
) -> Union[List[UIResource], Dict[str, Any]]:
    """Create UIResource if available, otherwise return fallback JSON.

    Args:
        uri: Unique URI for the resource (e.g., ui://cluster-overview)
        html_content: The HTML content to render
        fallback_data: JSON data to return if MCP-UI not available
        frame_size: Preferred frame size (width, height) in CSS units
        render_screenshot: If True and browser available, also render screenshot
    """
    # Option 1: Render screenshot using agent-browser (works everywhere)
    if render_screenshot and _can_render_screenshots():
        width = int(frame_size[0].replace('px', '').replace('%', '0'))
        height = int(frame_size[1].replace('px', '').replace('%', '0'))
        screenshot_b64 = _render_html_to_screenshot(html_content, width, height)
        if screenshot_b64:
            # Return as embedded image that any MCP host can display
            return {
                "success": True,
                "image": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_b64
                },
                "note": "Screenshot rendered via agent-browser. For interactive UI, use a host that supports MCP-UI.",
                **fallback_data
            }

    # Option 2: Return MCP-UI resource (for compatible hosts)
    if MCP_UI_AVAILABLE:
        try:
            ui_resource = create_ui_resource({
                "uri": uri,
                "content": {
                    "type": "rawHtml",
                    "htmlString": html_content
                },
                "encoding": "text",
                "uiMetadata": {
                    UIMetadataKey.PREFERRED_FRAME_SIZE: list(frame_size)
                }
            })
            return [ui_resource]
        except Exception as e:
            logger.warning(f"Failed to create UI resource: {e}")

    # Option 3: Return plain JSON fallback
    return fallback_data


def register_ui_tools(server, non_destructive: bool):
    """Register UI-enhanced tools with the MCP server.

    Args:
        server: FastMCP server instance
        non_destructive: If True, block destructive operations
    """

    @server.tool(
        annotations=ToolAnnotations(
            title="Show Pod Logs UI",
            readOnlyHint=True,
        ),
    )
    def show_pod_logs_ui(
        pod_name: str,
        namespace: str = "default",
        container: Optional[str] = None,
        tail: int = 100
    ) -> Union[List[UIResource], Dict[str, Any]]:
        """Display pod logs in an interactive UI with search and syntax highlighting."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            logs = v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container,
                tail_lines=tail
            )

            # Process log lines for highlighting
            log_lines = logs.split('\n') if logs else []
            processed_lines = []
            for line in log_lines:
                escaped = _escape(line)
                css_class = "log-line"
                if any(kw in line.lower() for kw in ['error', 'fail', 'exception', 'panic']):
                    css_class += " log-error"
                elif any(kw in line.lower() for kw in ['warn', 'warning']):
                    css_class += " log-warn"
                elif any(kw in line.lower() for kw in ['info']):
                    css_class += " log-info"
                processed_lines.append(f'<span class="{css_class}">{escaped}</span>')

            html_content = f"""<!DOCTYPE html>
<html><head><style>{DARK_THEME_CSS}</style></head>
<body>
<div class="container">
    <div class="header">
        <h2>Pod Logs</h2>
        <span class="badge badge-blue">{_escape(namespace)}/{_escape(pod_name)}</span>
        {f'<span class="badge badge-green">{_escape(container)}</span>' if container else ''}
    </div>
    <input type="text" class="search-box" placeholder="Search logs..." id="search" oninput="filterLogs()">
    <div class="card">
        <div class="card-header">
            <span class="card-title">Last {len(log_lines)} lines</span>
            <div class="actions">
                <button class="btn btn-secondary" onclick="copyLogs()">Copy</button>
                <button class="btn btn-primary" onclick="refreshLogs()">Refresh</button>
            </div>
        </div>
        <pre class="log-content" id="logs">{''.join(processed_lines)}</pre>
    </div>
</div>
<script>
function filterLogs() {{
    const search = document.getElementById('search').value.toLowerCase();
    const lines = document.querySelectorAll('.log-line');
    lines.forEach(line => {{
        line.style.display = line.textContent.toLowerCase().includes(search) ? 'block' : 'none';
    }});
}}
function copyLogs() {{
    const logs = document.getElementById('logs').textContent;
    navigator.clipboard.writeText(logs);
}}
function refreshLogs() {{
    window.parent.postMessage({{
        type: 'tool',
        payload: {{
            toolName: 'show_pod_logs_ui',
            params: {{ pod_name: '{_escape(pod_name)}', namespace: '{_escape(namespace)}', tail: {tail} }}
        }}
    }}, '*');
}}
</script>
</body></html>"""

            return _create_ui_or_fallback(
                uri=f"ui://pod-logs/{namespace}/{pod_name}",
                html_content=html_content,
                fallback_data={"success": True, "logs": logs, "lineCount": len(log_lines)},
                frame_size=("900px", "600px")
            )

        except Exception as e:
            logger.error(f"Error showing pod logs UI: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Show Pods Dashboard UI",
            readOnlyHint=True,
        ),
    )
    def show_pods_dashboard_ui(
        namespace: Optional[str] = None
    ) -> Union[List[UIResource], Dict[str, Any]]:
        """Display an interactive dashboard showing all pods with status, metrics, and actions."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            if namespace:
                pods = v1.list_namespaced_pod(namespace)
            else:
                pods = v1.list_pod_for_all_namespaces()

            # Count by status
            status_counts = {"Running": 0, "Pending": 0, "Failed": 0, "Succeeded": 0, "Unknown": 0}
            pod_rows = []

            for pod in pods.items:
                phase = pod.status.phase or "Unknown"
                status_counts[phase] = status_counts.get(phase, 0) + 1

                # Determine status indicator class
                status_class = {
                    "Running": "status-running",
                    "Pending": "status-pending",
                    "Failed": "status-failed",
                    "Succeeded": "status-running"
                }.get(phase, "status-unknown")

                # Get restart count
                restart_count = 0
                if pod.status.container_statuses:
                    restart_count = sum(cs.restart_count for cs in pod.status.container_statuses)

                pod_rows.append(f"""
                <tr>
                    <td><span class="status-indicator {status_class}"></span>{_escape(pod.metadata.name)}</td>
                    <td>{_escape(pod.metadata.namespace)}</td>
                    <td><span class="badge badge-{'green' if phase == 'Running' else 'yellow' if phase == 'Pending' else 'red'}">{_escape(phase)}</span></td>
                    <td>{restart_count}</td>
                    <td>{_escape(pod.status.pod_ip or '-')}</td>
                    <td>
                        <button class="btn btn-secondary" onclick="viewLogs('{_escape(pod.metadata.name)}', '{_escape(pod.metadata.namespace)}')">Logs</button>
                    </td>
                </tr>""")

            total_pods = len(pods.items)
            ns_display = f"Namespace: {_escape(namespace)}" if namespace else "All Namespaces"

            html_content = f"""<!DOCTYPE html>
<html><head><style>{DARK_THEME_CSS}</style></head>
<body>
<div class="container">
    <div class="header">
        <h2>Pods Dashboard</h2>
        <span class="badge badge-blue">{ns_display}</span>
    </div>

    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-value">{total_pods}</div>
            <div class="stat-label">Total Pods</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: var(--accent-green)">{status_counts.get('Running', 0)}</div>
            <div class="stat-label">Running</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: var(--accent-yellow)">{status_counts.get('Pending', 0)}</div>
            <div class="stat-label">Pending</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: var(--accent-red)">{status_counts.get('Failed', 0)}</div>
            <div class="stat-label">Failed</div>
        </div>
    </div>

    <div class="card" style="margin-top: 16px">
        <input type="text" class="search-box" placeholder="Filter pods..." oninput="filterPods(this.value)">
        <div style="overflow-x: auto;">
            <table id="pods-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Namespace</th>
                        <th>Status</th>
                        <th>Restarts</th>
                        <th>IP</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>{''.join(pod_rows)}</tbody>
            </table>
        </div>
    </div>
</div>
<script>
function filterPods(search) {{
    const rows = document.querySelectorAll('#pods-table tbody tr');
    search = search.toLowerCase();
    rows.forEach(row => {{
        row.style.display = row.textContent.toLowerCase().includes(search) ? '' : 'none';
    }});
}}
function viewLogs(pod, ns) {{
    window.parent.postMessage({{
        type: 'tool',
        payload: {{ toolName: 'show_pod_logs_ui', params: {{ pod_name: pod, namespace: ns, tail: 100 }} }}
    }}, '*');
}}
</script>
</body></html>"""

            return _create_ui_or_fallback(
                uri=f"ui://pods-dashboard/{namespace or 'all'}",
                html_content=html_content,
                fallback_data={
                    "success": True,
                    "totalPods": total_pods,
                    "statusCounts": status_counts,
                    "pods": [
                        {"name": p.metadata.name, "namespace": p.metadata.namespace, "status": p.status.phase}
                        for p in pods.items[:50]  # Limit for JSON response
                    ]
                },
                frame_size=("1000px", "700px")
            )

        except Exception as e:
            logger.error(f"Error showing pods dashboard UI: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Show Resource YAML UI",
            readOnlyHint=True,
        ),
    )
    def show_resource_yaml_ui(
        resource_type: str,
        name: str,
        namespace: str = "default"
    ) -> Union[List[UIResource], Dict[str, Any]]:
        """Display Kubernetes resource YAML with syntax highlighting and actions."""
        try:
            import subprocess
            import yaml

            cmd = ["kubectl", "get", resource_type, name, "-n", namespace, "-o", "yaml"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr.strip()}

            yaml_content = result.stdout

            # Basic YAML syntax highlighting
            highlighted_lines = []
            for line in yaml_content.split('\n'):
                escaped = _escape(line)
                # Highlight keys
                if ':' in line and not line.strip().startswith('-'):
                    key_part = escaped.split(':')[0]
                    rest = ':'.join(escaped.split(':')[1:])
                    escaped = f'<span style="color: var(--accent-blue)">{key_part}</span>:{rest}'
                # Highlight comments
                if line.strip().startswith('#'):
                    escaped = f'<span style="color: var(--text-muted)">{escaped}</span>'
                highlighted_lines.append(escaped)

            # Escape YAML for JavaScript template literal (must be done outside f-string)
            escaped_yaml = yaml_content.replace('`', r'\`').replace('$', r'\$')

            html_content = f"""<!DOCTYPE html>
<html><head><style>{DARK_THEME_CSS}</style></head>
<body>
<div class="container">
    <div class="header">
        <h2>{_escape(resource_type)}: {_escape(name)}</h2>
        <span class="badge badge-blue">{_escape(namespace)}</span>
    </div>
    <div class="card">
        <div class="card-header">
            <span class="card-title">YAML Definition</span>
            <div class="actions">
                <button class="btn btn-secondary" onclick="copyYaml()">Copy YAML</button>
            </div>
        </div>
        <pre id="yaml-content">{chr(10).join(highlighted_lines)}</pre>
    </div>
</div>
<script>
function copyYaml() {{
    const yaml = `{escaped_yaml}`;
    navigator.clipboard.writeText(yaml);
}}
</script>
</body></html>"""

            return _create_ui_or_fallback(
                uri=f"ui://resource-yaml/{resource_type}/{namespace}/{name}",
                html_content=html_content,
                fallback_data={"success": True, "yaml": yaml_content},
                frame_size=("900px", "700px")
            )

        except Exception as e:
            logger.error(f"Error showing resource YAML UI: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Show Cluster Overview UI",
            readOnlyHint=True,
        ),
    )
    def show_cluster_overview_ui() -> Union[List[UIResource], Dict[str, Any]]:
        """Display a comprehensive cluster overview dashboard with nodes, namespaces, and key metrics."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            # Get nodes
            nodes = v1.list_node()
            node_rows = []
            ready_nodes = 0

            for node in nodes.items:
                is_ready = False
                for condition in (node.status.conditions or []):
                    if condition.type == "Ready" and condition.status == "True":
                        is_ready = True
                        ready_nodes += 1
                        break

                # Get allocatable resources
                allocatable = node.status.allocatable or {}
                cpu = allocatable.get("cpu", "N/A")
                memory = allocatable.get("memory", "N/A")

                node_rows.append(f"""
                <tr>
                    <td><span class="status-indicator {'status-running' if is_ready else 'status-failed'}"></span>{_escape(node.metadata.name)}</td>
                    <td><span class="badge badge-{'green' if is_ready else 'red'}">{'Ready' if is_ready else 'NotReady'}</span></td>
                    <td>{_escape(cpu)}</td>
                    <td>{_escape(memory)}</td>
                </tr>""")

            # Get namespaces
            namespaces = v1.list_namespace()
            ns_count = len(namespaces.items)

            # Get pods summary
            pods = v1.list_pod_for_all_namespaces()
            total_pods = len(pods.items)
            running_pods = sum(1 for p in pods.items if p.status.phase == "Running")

            # Get services
            services = v1.list_service_for_all_namespaces()
            svc_count = len(services.items)

            html_content = f"""<!DOCTYPE html>
<html><head><style>{DARK_THEME_CSS}</style></head>
<body>
<div class="container">
    <div class="header">
        <h2>Cluster Overview</h2>
        <span class="badge badge-green">Connected</span>
    </div>

    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-value">{len(nodes.items)}</div>
            <div class="stat-label">Nodes ({ready_nodes} Ready)</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{ns_count}</div>
            <div class="stat-label">Namespaces</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: var(--accent-green)">{running_pods}/{total_pods}</div>
            <div class="stat-label">Pods Running</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{svc_count}</div>
            <div class="stat-label">Services</div>
        </div>
    </div>

    <div class="card" style="margin-top: 16px">
        <div class="card-header">
            <span class="card-title">Nodes</span>
        </div>
        <table>
            <thead>
                <tr><th>Name</th><th>Status</th><th>CPU</th><th>Memory</th></tr>
            </thead>
            <tbody>{''.join(node_rows)}</tbody>
        </table>
    </div>

    <div class="actions">
        <button class="btn btn-primary" onclick="viewPods()">View All Pods</button>
        <button class="btn btn-secondary" onclick="refresh()">Refresh</button>
    </div>
</div>
<script>
function viewPods() {{
    window.parent.postMessage({{
        type: 'tool',
        payload: {{ toolName: 'show_pods_dashboard_ui', params: {{}} }}
    }}, '*');
}}
function refresh() {{
    window.parent.postMessage({{
        type: 'tool',
        payload: {{ toolName: 'show_cluster_overview_ui', params: {{}} }}
    }}, '*');
}}
</script>
</body></html>"""

            return _create_ui_or_fallback(
                uri="ui://cluster-overview",
                html_content=html_content,
                fallback_data={
                    "success": True,
                    "nodes": {"total": len(nodes.items), "ready": ready_nodes},
                    "namespaces": ns_count,
                    "pods": {"total": total_pods, "running": running_pods},
                    "services": svc_count
                },
                frame_size=("1000px", "700px")
            )

        except Exception as e:
            logger.error(f"Error showing cluster overview UI: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Show Events Timeline UI",
            readOnlyHint=True,
        ),
    )
    def show_events_timeline_ui(
        namespace: Optional[str] = None,
        limit: int = 50
    ) -> Union[List[UIResource], Dict[str, Any]]:
        """Display Kubernetes events in a timeline view with filtering by type."""
        try:
            from kubernetes import client, config
            config.load_kube_config()
            v1 = client.CoreV1Api()

            if namespace:
                events = v1.list_namespaced_event(namespace)
            else:
                events = v1.list_event_for_all_namespaces()

            # Sort by timestamp (most recent first)
            sorted_events = sorted(
                events.items,
                key=lambda e: e.last_timestamp or e.metadata.creation_timestamp or "",
                reverse=True
            )[:limit]

            event_items = []
            warning_count = 0
            normal_count = 0

            for event in sorted_events:
                is_warning = event.type == "Warning"
                if is_warning:
                    warning_count += 1
                else:
                    normal_count += 1

                timestamp = event.last_timestamp or event.metadata.creation_timestamp
                time_str = timestamp.strftime("%H:%M:%S") if timestamp else "Unknown"

                event_items.append(f"""
                <div class="card" style="border-left: 3px solid var({'--accent-red' if is_warning else '--accent-green'})">
                    <div class="card-header">
                        <span class="card-title">
                            <span class="badge badge-{'red' if is_warning else 'green'}">{_escape(event.type)}</span>
                            {_escape(event.reason)}
                        </span>
                        <span class="timestamp">{time_str}</span>
                    </div>
                    <p style="font-size: 0.85rem; color: var(--text-secondary)">
                        {_escape(event.involved_object.kind)}: {_escape(event.involved_object.name)}
                        <span style="color: var(--text-muted)">in {_escape(event.metadata.namespace)}</span>
                    </p>
                    <p style="margin-top: 8px; font-size: 0.85rem">{_escape(event.message)}</p>
                </div>""")

            ns_display = f"Namespace: {_escape(namespace)}" if namespace else "All Namespaces"

            html_content = f"""<!DOCTYPE html>
<html><head><style>{DARK_THEME_CSS}</style></head>
<body>
<div class="container">
    <div class="header">
        <h2>Events Timeline</h2>
        <span class="badge badge-blue">{ns_display}</span>
    </div>

    <div class="stat-grid" style="margin-bottom: 16px">
        <div class="stat-card">
            <div class="stat-value">{len(sorted_events)}</div>
            <div class="stat-label">Total Events</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: var(--accent-red)">{warning_count}</div>
            <div class="stat-label">Warnings</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" style="color: var(--accent-green)">{normal_count}</div>
            <div class="stat-label">Normal</div>
        </div>
    </div>

    <div style="display: flex; gap: 8px; margin-bottom: 16px">
        <button class="btn btn-secondary" onclick="filterEvents('all')">All</button>
        <button class="btn btn-secondary" onclick="filterEvents('Warning')">Warnings</button>
        <button class="btn btn-secondary" onclick="filterEvents('Normal')">Normal</button>
    </div>

    <div id="events">{''.join(event_items)}</div>
</div>
<script>
function filterEvents(type) {{
    const events = document.querySelectorAll('#events .card');
    events.forEach(e => {{
        if (type === 'all') e.style.display = 'block';
        else e.style.display = e.innerHTML.includes('>' + type + '<') ? 'block' : 'none';
    }});
}}
</script>
</body></html>"""

            return _create_ui_or_fallback(
                uri=f"ui://events-timeline/{namespace or 'all'}",
                html_content=html_content,
                fallback_data={
                    "success": True,
                    "totalEvents": len(sorted_events),
                    "warnings": warning_count,
                    "normal": normal_count,
                    "events": [
                        {
                            "type": e.type,
                            "reason": e.reason,
                            "message": e.message,
                            "object": f"{e.involved_object.kind}/{e.involved_object.name}"
                        }
                        for e in sorted_events[:20]
                    ]
                },
                frame_size=("900px", "700px")
            )

        except Exception as e:
            logger.error(f"Error showing events timeline UI: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Render K8s Dashboard Screenshot",
            readOnlyHint=True,
        ),
    )
    def render_k8s_dashboard_screenshot(
        dashboard: str = "cluster",
        namespace: Optional[str] = None,
        pod_name: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Render a Kubernetes dashboard to a screenshot image (works in all MCP hosts).

        This uses agent-browser to render the UI and capture a screenshot,
        making visual dashboards accessible even in hosts that don't support MCP-UI.

        Args:
            dashboard: Type of dashboard to render:
                - "cluster": Cluster overview with nodes, pods, services
                - "pods": Pods dashboard with status table
                - "events": Events timeline
                - "logs": Pod logs viewer (requires pod_name)
                - "yaml": Resource YAML viewer (requires resource_type and resource_name)
            namespace: Namespace filter (optional)
            pod_name: Pod name for logs dashboard
            resource_type: Resource type for YAML view (e.g., "deployment", "service")
            resource_name: Resource name for YAML view
        """
        if not _can_render_screenshots():
            return {
                "success": False,
                "error": "Screenshot rendering requires MCP_BROWSER_ENABLED=true and agent-browser installed"
            }

        try:
            from kubernetes import client, config
            config.load_kube_config()

            # Generate the appropriate dashboard HTML
            if dashboard == "cluster":
                # Reuse cluster overview logic
                v1 = client.CoreV1Api()
                nodes = v1.list_node()
                namespaces = v1.list_namespace()
                pods = v1.list_pod_for_all_namespaces()
                services = v1.list_service_for_all_namespaces()

                ready_nodes = sum(1 for n in nodes.items
                    for c in (n.status.conditions or [])
                    if c.type == "Ready" and c.status == "True")
                running_pods = sum(1 for p in pods.items if p.status.phase == "Running")

                node_rows = []
                for node in nodes.items:
                    is_ready = any(c.type == "Ready" and c.status == "True"
                        for c in (node.status.conditions or []))
                    allocatable = node.status.allocatable or {}
                    node_rows.append(f"""
                    <tr>
                        <td><span class="status-indicator {'status-running' if is_ready else 'status-failed'}"></span>{_escape(node.metadata.name)}</td>
                        <td><span class="badge badge-{'green' if is_ready else 'red'}">{'Ready' if is_ready else 'NotReady'}</span></td>
                        <td>{_escape(allocatable.get('cpu', 'N/A'))}</td>
                        <td>{_escape(allocatable.get('memory', 'N/A'))}</td>
                    </tr>""")

                html_content = f"""<!DOCTYPE html>
<html><head><style>{DARK_THEME_CSS}</style></head>
<body>
<div class="container">
    <div class="header">
        <h2>Cluster Overview</h2>
        <span class="badge badge-green">Connected</span>
    </div>
    <div class="stat-grid">
        <div class="stat-card"><div class="stat-value">{len(nodes.items)}</div><div class="stat-label">Nodes ({ready_nodes} Ready)</div></div>
        <div class="stat-card"><div class="stat-value">{len(namespaces.items)}</div><div class="stat-label">Namespaces</div></div>
        <div class="stat-card"><div class="stat-value" style="color: var(--accent-green)">{running_pods}/{len(pods.items)}</div><div class="stat-label">Pods Running</div></div>
        <div class="stat-card"><div class="stat-value">{len(services.items)}</div><div class="stat-label">Services</div></div>
    </div>
    <div class="card" style="margin-top: 16px">
        <div class="card-header"><span class="card-title">Nodes</span></div>
        <table><thead><tr><th>Name</th><th>Status</th><th>CPU</th><th>Memory</th></tr></thead>
        <tbody>{''.join(node_rows)}</tbody></table>
    </div>
</div>
</body></html>"""

            elif dashboard == "pods":
                v1 = client.CoreV1Api()
                if namespace:
                    pods = v1.list_namespaced_pod(namespace)
                else:
                    pods = v1.list_pod_for_all_namespaces()

                pod_rows = []
                for pod in pods.items[:30]:  # Limit for screenshot
                    phase = pod.status.phase or "Unknown"
                    status_class = {"Running": "status-running", "Pending": "status-pending"}.get(phase, "status-failed")
                    badge_color = {"Running": "green", "Pending": "yellow"}.get(phase, "red")
                    pod_rows.append(f"""
                    <tr>
                        <td><span class="status-indicator {status_class}"></span>{_escape(pod.metadata.name[:40])}</td>
                        <td>{_escape(pod.metadata.namespace)}</td>
                        <td><span class="badge badge-{badge_color}">{_escape(phase)}</span></td>
                    </tr>""")

                html_content = f"""<!DOCTYPE html>
<html><head><style>{DARK_THEME_CSS}</style></head>
<body>
<div class="container">
    <div class="header">
        <h2>Pods Dashboard</h2>
        <span class="badge badge-blue">{namespace or 'All Namespaces'}</span>
    </div>
    <div class="card">
        <table><thead><tr><th>Name</th><th>Namespace</th><th>Status</th></tr></thead>
        <tbody>{''.join(pod_rows)}</tbody></table>
    </div>
</div>
</body></html>"""

            elif dashboard == "logs" and pod_name:
                v1 = client.CoreV1Api()
                ns = namespace or "default"
                logs = v1.read_namespaced_pod_log(name=pod_name, namespace=ns, tail_lines=50)
                log_lines = logs.split('\n') if logs else []
                processed = [f'<span class="log-line">{_escape(line)}</span>' for line in log_lines]

                html_content = f"""<!DOCTYPE html>
<html><head><style>{DARK_THEME_CSS}</style></head>
<body>
<div class="container">
    <div class="header">
        <h2>Pod Logs</h2>
        <span class="badge badge-blue">{_escape(ns)}/{_escape(pod_name)}</span>
    </div>
    <div class="card">
        <pre class="log-content">{''.join(processed)}</pre>
    </div>
</div>
</body></html>"""

            else:
                return {"success": False, "error": f"Unknown dashboard type: {dashboard}"}

            # Render to screenshot
            screenshot_b64 = _render_html_to_screenshot(html_content, 1200, 800)
            if screenshot_b64:
                return {
                    "success": True,
                    "dashboard": dashboard,
                    "image": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot_b64
                    }
                }
            else:
                return {"success": False, "error": "Failed to render screenshot"}

        except Exception as e:
            logger.error(f"Error rendering dashboard screenshot: {e}")
            return {"success": False, "error": str(e)}


def is_ui_available() -> bool:
    """Check if MCP-UI is available."""
    return MCP_UI_AVAILABLE


def is_screenshot_available() -> bool:
    """Check if screenshot rendering is available."""
    return _can_render_screenshots()
