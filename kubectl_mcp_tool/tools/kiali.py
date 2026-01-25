"""Kiali/Istio service mesh observability toolset for kubectl-mcp-server."""

import subprocess
import json
import os
from typing import Dict, Any, List

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ..crd_detector import crd_exists
from .utils import run_kubectl, get_resources


VIRTUALSERVICE_CRD = "virtualservices.networking.istio.io"
DESTINATIONRULE_CRD = "destinationrules.networking.istio.io"
GATEWAY_CRD = "gateways.networking.istio.io"
SERVICEENTRY_CRD = "serviceentries.networking.istio.io"
SIDECAR_CRD = "sidecars.networking.istio.io"
PEERAUTHENTICATION_CRD = "peerauthentications.security.istio.io"
AUTHORIZATIONPOLICY_CRD = "authorizationpolicies.security.istio.io"
REQUESTAUTHENTICATION_CRD = "requestauthentications.security.istio.io"


def _istioctl_available() -> bool:
    """Check if istioctl CLI is available."""
    try:
        result = subprocess.run(["istioctl", "version", "--remote=false"],
                                capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def _get_kiali_config() -> Dict[str, str]:
    """Get Kiali connection configuration from environment."""
    return {
        "url": os.environ.get("KIALI_URL", ""),
        "token": os.environ.get("KIALI_TOKEN", ""),
        "username": os.environ.get("KIALI_USERNAME", ""),
        "password": os.environ.get("KIALI_PASSWORD", ""),
    }


def istio_virtualservices_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Istio VirtualServices.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of VirtualServices with their configuration
    """
    if not crd_exists(VIRTUALSERVICE_CRD, context):
        return {
            "success": False,
            "error": "Istio is not installed (virtualservices.networking.istio.io CRD not found)"
        }

    virtualservices = []
    for item in get_resources("virtualservices.networking.istio.io", namespace, context, label_selector):
        spec = item.get("spec", {})
        hosts = spec.get("hosts", [])
        gateways = spec.get("gateways", [])
        http_routes = spec.get("http", [])
        tcp_routes = spec.get("tcp", [])
        tls_routes = spec.get("tls", [])

        virtualservices.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "hosts": hosts,
            "gateways": gateways,
            "http_routes_count": len(http_routes),
            "tcp_routes_count": len(tcp_routes),
            "tls_routes_count": len(tls_routes),
            "total_routes": len(http_routes) + len(tcp_routes) + len(tls_routes),
        })

    return {
        "context": context or "current",
        "total": len(virtualservices),
        "virtualservices": virtualservices,
    }


def istio_virtualservice_get(
    name: str,
    namespace: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a VirtualService.

    Args:
        name: Name of the VirtualService
        namespace: Namespace of the VirtualService
        context: Kubernetes context to use (optional)

    Returns:
        Detailed VirtualService information
    """
    if not crd_exists(VIRTUALSERVICE_CRD, context):
        return {"success": False, "error": "Istio is not installed"}

    args = ["get", "virtualservices.networking.istio.io", name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "virtualservice": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def istio_destinationrules_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Istio DestinationRules.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of DestinationRules
    """
    if not crd_exists(DESTINATIONRULE_CRD, context):
        return {
            "success": False,
            "error": "Istio DestinationRules CRD not found"
        }

    rules = []
    for item in get_resources("destinationrules.networking.istio.io", namespace, context, label_selector):
        spec = item.get("spec", {})
        traffic_policy = spec.get("trafficPolicy", {})
        subsets = spec.get("subsets", [])

        rules.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "host": spec.get("host", ""),
            "subsets_count": len(subsets),
            "subsets": [s.get("name") for s in subsets],
            "has_traffic_policy": bool(traffic_policy),
            "load_balancer": traffic_policy.get("loadBalancer", {}).get("simple"),
            "connection_pool": bool(traffic_policy.get("connectionPool")),
            "outlier_detection": bool(traffic_policy.get("outlierDetection")),
            "tls_mode": traffic_policy.get("tls", {}).get("mode"),
        })

    return {
        "context": context or "current",
        "total": len(rules),
        "destinationrules": rules,
    }


def istio_gateways_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Istio Gateways.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of Gateways
    """
    if not crd_exists(GATEWAY_CRD, context):
        return {
            "success": False,
            "error": "Istio Gateways CRD not found"
        }

    gateways = []
    for item in get_resources("gateways.networking.istio.io", namespace, context, label_selector):
        spec = item.get("spec", {})
        selector = spec.get("selector", {})
        servers = spec.get("servers", [])

        # Extract hosts and ports from servers
        all_hosts = []
        all_ports = []
        for server in servers:
            all_hosts.extend(server.get("hosts", []))
            port = server.get("port", {})
            if port:
                all_ports.append({
                    "number": port.get("number"),
                    "name": port.get("name"),
                    "protocol": port.get("protocol"),
                })

        gateways.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "selector": selector,
            "servers_count": len(servers),
            "hosts": list(set(all_hosts)),
            "ports": all_ports,
        })

    return {
        "context": context or "current",
        "total": len(gateways),
        "gateways": gateways,
    }


def istio_peerauthentications_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Istio PeerAuthentication policies.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of PeerAuthentication policies
    """
    if not crd_exists(PEERAUTHENTICATION_CRD, context):
        return {
            "success": False,
            "error": "Istio PeerAuthentication CRD not found"
        }

    policies = []
    for item in get_resources("peerauthentications.security.istio.io", namespace, context, label_selector):
        spec = item.get("spec", {})
        selector = spec.get("selector", {})
        mtls = spec.get("mtls", {})
        port_level_mtls = spec.get("portLevelMtls", {})

        policies.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "selector": selector.get("matchLabels", {}),
            "mtls_mode": mtls.get("mode", "UNSET"),
            "port_level_mtls_count": len(port_level_mtls),
        })

    return {
        "context": context or "current",
        "total": len(policies),
        "peerauthentications": policies,
    }


def istio_authorizationpolicies_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Istio AuthorizationPolicies.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter

    Returns:
        List of AuthorizationPolicies
    """
    if not crd_exists(AUTHORIZATIONPOLICY_CRD, context):
        return {
            "success": False,
            "error": "Istio AuthorizationPolicy CRD not found"
        }

    policies = []
    for item in get_resources("authorizationpolicies.security.istio.io", namespace, context, label_selector):
        spec = item.get("spec", {})
        selector = spec.get("selector", {})
        rules = spec.get("rules", [])
        action = spec.get("action", "ALLOW")

        policies.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "selector": selector.get("matchLabels", {}),
            "action": action,
            "rules_count": len(rules),
        })

    return {
        "context": context or "current",
        "total": len(policies),
        "authorizationpolicies": policies,
    }


def istio_proxy_status(context: str = "") -> Dict[str, Any]:
    """Get Istio proxy (Envoy) synchronization status.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Proxy sync status for all workloads
    """
    if not _istioctl_available():
        return {
            "success": False,
            "error": "istioctl CLI not available"
        }

    cmd = ["istioctl", "proxy-status", "-o", "json"]
    if context:
        cmd.extend(["--context", context])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                proxies = []
                for proxy in data:
                    proxies.append({
                        "name": proxy.get("proxy", ""),
                        "cluster_id": proxy.get("cluster_id", ""),
                        "istiod": proxy.get("istiod", ""),
                        "cds": proxy.get("cluster_status", ""),
                        "lds": proxy.get("listener_status", ""),
                        "eds": proxy.get("endpoint_status", ""),
                        "rds": proxy.get("route_status", ""),
                        "ecds": proxy.get("extension_config_status", ""),
                    })

                synced = sum(1 for p in proxies if all(
                    p.get(s) == "SYNCED" for s in ["cds", "lds", "eds", "rds"]
                ))

                return {
                    "success": True,
                    "context": context or "current",
                    "total": len(proxies),
                    "synced": synced,
                    "proxies": proxies,
                }
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse response"}

        return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}


def istio_analyze(
    namespace: str = "",
    context: str = ""
) -> Dict[str, Any]:
    """Analyze Istio configuration for potential issues.

    Args:
        namespace: Namespace to analyze (empty for all)
        context: Kubernetes context to use (optional)

    Returns:
        Analysis results with warnings and errors
    """
    if not _istioctl_available():
        return {
            "success": False,
            "error": "istioctl CLI not available"
        }

    cmd = ["istioctl", "analyze", "-o", "json"]
    if namespace:
        cmd.extend(["-n", namespace])
    else:
        cmd.append("-A")
    if context:
        cmd.extend(["--context", context])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # istioctl analyze returns non-zero if issues found, but still outputs valid JSON
        try:
            data = json.loads(result.stdout) if result.stdout else []

            messages = []
            for msg in data:
                messages.append({
                    "code": msg.get("code", ""),
                    "level": msg.get("level", ""),
                    "message": msg.get("message", ""),
                    "origin": msg.get("origin", ""),
                    "documentation_url": msg.get("documentationUrl", ""),
                })

            errors = sum(1 for m in messages if m["level"] == "Error")
            warnings = sum(1 for m in messages if m["level"] == "Warning")
            info = sum(1 for m in messages if m["level"] == "Info")

            return {
                "success": True,
                "context": context or "current",
                "namespace": namespace or "all",
                "total_issues": len(messages),
                "errors": errors,
                "warnings": warnings,
                "info": info,
                "messages": messages,
            }
        except json.JSONDecodeError:
            # If not JSON, return the text output
            return {
                "success": True,
                "context": context or "current",
                "namespace": namespace or "all",
                "output": result.stdout,
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


def istio_sidecar_status(
    namespace: str = "",
    context: str = ""
) -> Dict[str, Any]:
    """Get sidecar injection status for pods.

    Args:
        namespace: Namespace to check (empty for all)
        context: Kubernetes context to use (optional)

    Returns:
        Pods with their sidecar injection status
    """
    args = ["get", "pods", "-o", "json"]
    if namespace:
        args.extend(["-n", namespace])
    else:
        args.append("-A")

    result = run_kubectl(args, context)
    if not result["success"]:
        return {"success": False, "error": result.get("error", "Failed to list pods")}

    try:
        data = json.loads(result["output"])
        pods = data.get("items", [])
    except json.JSONDecodeError:
        return {"success": False, "error": "Failed to parse response"}

    pod_status = []
    for pod in pods:
        containers = pod.get("spec", {}).get("containers", [])
        container_names = [c.get("name") for c in containers]

        has_sidecar = "istio-proxy" in container_names
        annotations = pod.get("metadata", {}).get("annotations", {})
        inject_status = annotations.get("sidecar.istio.io/status")

        pod_status.append({
            "name": pod["metadata"]["name"],
            "namespace": pod["metadata"]["namespace"],
            "has_sidecar": has_sidecar,
            "inject_annotation": annotations.get("sidecar.istio.io/inject"),
            "sidecar_status": "injected" if has_sidecar else "not_injected",
        })

    injected = sum(1 for p in pod_status if p["has_sidecar"])

    return {
        "context": context or "current",
        "total": len(pod_status),
        "injected": injected,
        "not_injected": len(pod_status) - injected,
        "pods": pod_status,
    }


def istio_detect(context: str = "") -> Dict[str, Any]:
    """Detect if Istio is installed and its components.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for Istio
    """
    return {
        "context": context or "current",
        "installed": crd_exists(VIRTUALSERVICE_CRD, context),
        "cli_available": _istioctl_available(),
        "kiali_configured": bool(_get_kiali_config().get("url")),
        "crds": {
            "virtualservices": crd_exists(VIRTUALSERVICE_CRD, context),
            "destinationrules": crd_exists(DESTINATIONRULE_CRD, context),
            "gateways": crd_exists(GATEWAY_CRD, context),
            "serviceentries": crd_exists(SERVICEENTRY_CRD, context),
            "sidecars": crd_exists(SIDECAR_CRD, context),
            "peerauthentications": crd_exists(PEERAUTHENTICATION_CRD, context),
            "authorizationpolicies": crd_exists(AUTHORIZATIONPOLICY_CRD, context),
            "requestauthentications": crd_exists(REQUESTAUTHENTICATION_CRD, context),
        },
    }


def register_istio_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register Istio/Kiali tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_virtualservices_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Istio VirtualServices."""
        return json.dumps(istio_virtualservices_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_virtualservice_get_tool(
        name: str,
        namespace: str,
        context: str = ""
    ) -> str:
        """Get detailed information about a VirtualService."""
        return json.dumps(istio_virtualservice_get(name, namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_destinationrules_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Istio DestinationRules."""
        return json.dumps(istio_destinationrules_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_gateways_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Istio Gateways."""
        return json.dumps(istio_gateways_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_peerauthentications_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Istio PeerAuthentication policies."""
        return json.dumps(istio_peerauthentications_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_authorizationpolicies_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Istio AuthorizationPolicies."""
        return json.dumps(istio_authorizationpolicies_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_proxy_status_tool(context: str = "") -> str:
        """Get Istio proxy synchronization status."""
        return json.dumps(istio_proxy_status(context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_analyze_tool(
        namespace: str = "",
        context: str = ""
    ) -> str:
        """Analyze Istio configuration for potential issues."""
        return json.dumps(istio_analyze(namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_sidecar_status_tool(
        namespace: str = "",
        context: str = ""
    ) -> str:
        """Get sidecar injection status for pods."""
        return json.dumps(istio_sidecar_status(namespace, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def istio_detect_tool(context: str = "") -> str:
        """Detect if Istio is installed and its components."""
        return json.dumps(istio_detect(context), indent=2)
