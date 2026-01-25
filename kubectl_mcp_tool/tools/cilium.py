"""Cilium/Hubble network toolset for kubectl-mcp-server."""

import subprocess
import json
from typing import Dict, Any, List

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ..crd_detector import crd_exists
from .utils import run_kubectl, get_resources


CILIUM_NETWORK_POLICY_CRD = "ciliumnetworkpolicies.cilium.io"
CILIUM_CLUSTERWIDE_POLICY_CRD = "ciliumclusterwidenetworkpolicies.cilium.io"
CILIUM_ENDPOINT_CRD = "ciliumendpoints.cilium.io"
CILIUM_IDENTITY_CRD = "ciliumidentities.cilium.io"
CILIUM_NODE_CRD = "ciliumnodes.cilium.io"


def _cilium_cli_available() -> bool:
    """Check if cilium CLI is available."""
    try:
        result = subprocess.run(["cilium", "version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def _hubble_cli_available() -> bool:
    """Check if hubble CLI is available."""
    try:
        result = subprocess.run(["hubble", "version"], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def cilium_policies_list(
    namespace: str = "",
    context: str = "",
    include_clusterwide: bool = True
) -> Dict[str, Any]:
    """List Cilium network policies.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        include_clusterwide: Include CiliumClusterwideNetworkPolicies

    Returns:
        List of Cilium network policies
    """
    policies = []

    if crd_exists(CILIUM_NETWORK_POLICY_CRD, context):
        for item in get_resources("ciliumnetworkpolicies.cilium.io", namespace, context):
            spec = item.get("spec", {})
            status = item.get("status", {})

            # Parse endpoint selector
            endpoint_selector = spec.get("endpointSelector", {})
            match_labels = endpoint_selector.get("matchLabels", {})

            # Count rules
            ingress_rules = len(spec.get("ingress", []))
            egress_rules = len(spec.get("egress", []))
            ingress_deny = len(spec.get("ingressDeny", []))
            egress_deny = len(spec.get("egressDeny", []))

            policies.append({
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "kind": "CiliumNetworkPolicy",
                "endpoint_selector": match_labels,
                "ingress_rules": ingress_rules,
                "egress_rules": egress_rules,
                "ingress_deny_rules": ingress_deny,
                "egress_deny_rules": egress_deny,
                "total_rules": ingress_rules + egress_rules + ingress_deny + egress_deny,
                "derivate_from_rules": status.get("derivativePolicies", []),
            })

    if include_clusterwide and crd_exists(CILIUM_CLUSTERWIDE_POLICY_CRD, context):
        for item in get_resources("ciliumclusterwidenetworkpolicies.cilium.io", "", context):
            spec = item.get("spec", {})
            status = item.get("status", {})

            endpoint_selector = spec.get("endpointSelector", {})
            match_labels = endpoint_selector.get("matchLabels", {})

            ingress_rules = len(spec.get("ingress", []))
            egress_rules = len(spec.get("egress", []))
            ingress_deny = len(spec.get("ingressDeny", []))
            egress_deny = len(spec.get("egressDeny", []))

            policies.append({
                "name": item["metadata"]["name"],
                "namespace": "",
                "kind": "CiliumClusterwideNetworkPolicy",
                "endpoint_selector": match_labels,
                "ingress_rules": ingress_rules,
                "egress_rules": egress_rules,
                "ingress_deny_rules": ingress_deny,
                "egress_deny_rules": egress_deny,
                "total_rules": ingress_rules + egress_rules + ingress_deny + egress_deny,
                "node_selector": spec.get("nodeSelector", {}),
            })

    return {
        "context": context or "current",
        "total": len(policies),
        "policies": policies,
    }


def cilium_policy_get(
    name: str,
    namespace: str = "",
    kind: str = "CiliumNetworkPolicy",
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a Cilium network policy.

    Args:
        name: Name of the policy
        namespace: Namespace (for CiliumNetworkPolicy)
        kind: CiliumNetworkPolicy or CiliumClusterwideNetworkPolicy
        context: Kubernetes context to use (optional)

    Returns:
        Detailed policy information
    """
    if kind.lower() == "ciliumclusterwidenetworkpolicy":
        crd = "ciliumclusterwidenetworkpolicies.cilium.io"
        args = ["get", crd, name, "-o", "json"]
    else:
        crd = "ciliumnetworkpolicies.cilium.io"
        args = ["get", crd, name, "-n", namespace, "-o", "json"]

    if not crd_exists(crd, context):
        return {"success": False, "error": f"{crd} not found"}

    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "policy": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def cilium_endpoints_list(
    namespace: str = "",
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Cilium endpoints.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter endpoints

    Returns:
        List of Cilium endpoints with their status
    """
    if not crd_exists(CILIUM_ENDPOINT_CRD, context):
        return {
            "success": False,
            "error": "Cilium is not installed (ciliumendpoints.cilium.io CRD not found)"
        }

    endpoints = []
    for item in get_resources("ciliumendpoints.cilium.io", namespace, context, label_selector):
        status = item.get("status", {})
        networking = status.get("networking", {})
        identity = status.get("identity", {})
        policy = status.get("policy", {})

        addresses = networking.get("addressing", [])
        ipv4 = next((a.get("ipv4") for a in addresses if a.get("ipv4")), None)
        ipv6 = next((a.get("ipv6") for a in addresses if a.get("ipv6")), None)

        endpoints.append({
            "name": item["metadata"]["name"],
            "namespace": item["metadata"]["namespace"],
            "identity_id": identity.get("id"),
            "identity_labels": identity.get("labels", []),
            "ipv4": ipv4,
            "ipv6": ipv6,
            "state": status.get("state"),
            "health": status.get("health", {}),
            "policy_enabled": policy.get("ingress", {}).get("enforcing", False) or
                             policy.get("egress", {}).get("enforcing", False),
            "ingress_enforcing": policy.get("ingress", {}).get("enforcing", False),
            "egress_enforcing": policy.get("egress", {}).get("enforcing", False),
        })

    ready_count = sum(1 for e in endpoints if e["state"] == "ready")

    return {
        "context": context or "current",
        "total": len(endpoints),
        "ready": ready_count,
        "endpoints": endpoints,
    }


def cilium_identities_list(
    context: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Cilium identities.

    Args:
        context: Kubernetes context to use (optional)
        label_selector: Label selector to filter identities

    Returns:
        List of Cilium identities
    """
    if not crd_exists(CILIUM_IDENTITY_CRD, context):
        return {
            "success": False,
            "error": "Cilium identities CRD not found"
        }

    identities = []
    for item in get_resources("ciliumidentities.cilium.io", "", context, label_selector):
        security_labels = item.get("security-labels", {})

        identities.append({
            "name": item["metadata"]["name"],
            "id": item["metadata"]["name"],
            "labels": security_labels,
            "namespace": security_labels.get("k8s:io.kubernetes.pod.namespace", ""),
        })

    return {
        "context": context or "current",
        "total": len(identities),
        "identities": identities,
    }


def cilium_nodes_list(context: str = "") -> Dict[str, Any]:
    """List Cilium nodes with their status.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        List of Cilium nodes
    """
    if not crd_exists(CILIUM_NODE_CRD, context):
        return {
            "success": False,
            "error": "Cilium nodes CRD not found"
        }

    nodes = []
    for item in get_resources("ciliumnodes.cilium.io", "", context):
        spec = item.get("spec", {})
        status = item.get("status", {})

        addresses = spec.get("addresses", [])
        ipv4_address = next((a.get("ip") for a in addresses if a.get("type") == "InternalIP"), None)

        nodes.append({
            "name": item["metadata"]["name"],
            "ipv4_address": ipv4_address,
            "ipv4_health": spec.get("ipam", {}).get("podCIDRs", []),
            "encryption_key": spec.get("encryption", {}).get("key"),
            "boot_id": status.get("nodeIdentity"),
        })

    return {
        "context": context or "current",
        "total": len(nodes),
        "nodes": nodes,
    }


def cilium_status(context: str = "") -> Dict[str, Any]:
    """Get Cilium cluster status.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Cilium status information
    """
    # Try using cilium CLI if available
    if _cilium_cli_available():
        try:
            cmd = ["cilium", "status", "--output", "json"]
            if context:
                cmd.extend(["--context", context])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    return {
                        "success": True,
                        "context": context or "current",
                        "source": "cilium-cli",
                        "status": data,
                    }
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

    # Fallback to kubectl
    # Check Cilium pods status
    args = ["get", "pods", "-n", "kube-system", "-l", "k8s-app=cilium", "-o", "json"]
    result = run_kubectl(args, context)

    if not result["success"]:
        return {"success": False, "error": result.get("error", "Failed to get Cilium status")}

    try:
        data = json.loads(result["output"])
        pods = data.get("items", [])
    except json.JSONDecodeError:
        return {"success": False, "error": "Failed to parse response"}

    pod_status = []
    for pod in pods:
        status = pod.get("status", {})
        conditions = status.get("conditions", [])
        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})

        pod_status.append({
            "name": pod["metadata"]["name"],
            "node": pod["spec"].get("nodeName", ""),
            "ready": ready_cond.get("status") == "True",
            "phase": status.get("phase", "Unknown"),
            "restarts": sum(c.get("restartCount", 0) for c in status.get("containerStatuses", [])),
        })

    ready_count = sum(1 for p in pod_status if p["ready"])

    return {
        "success": True,
        "context": context or "current",
        "source": "kubectl",
        "total_agents": len(pod_status),
        "ready_agents": ready_count,
        "agents": pod_status,
        "hubble_cli_available": _hubble_cli_available(),
        "cilium_cli_available": _cilium_cli_available(),
    }


def hubble_flows_query(
    namespace: str = "",
    pod: str = "",
    label_selector: str = "",
    verdict: str = "",
    protocol: str = "",
    last: int = 100,
    context: str = ""
) -> Dict[str, Any]:
    """Query Hubble flows (requires hubble CLI or hubble-relay).

    Args:
        namespace: Filter by namespace
        pod: Filter by pod name
        label_selector: Filter by labels
        verdict: Filter by verdict (FORWARDED, DROPPED, AUDIT)
        protocol: Filter by protocol (TCP, UDP, ICMP)
        last: Number of flows to retrieve (default 100)
        context: Kubernetes context to use (optional)

    Returns:
        Hubble flow data
    """
    if not _hubble_cli_available():
        return {
            "success": False,
            "error": "Hubble CLI not available. Install hubble CLI or use hubble-relay port-forward."
        }

    cmd = ["hubble", "observe", "--output", "json", f"--last={last}"]

    if namespace:
        cmd.extend(["--namespace", namespace])
    if pod:
        cmd.extend(["--pod", pod])
    if label_selector:
        cmd.extend(["--label", label_selector])
    if verdict:
        cmd.extend(["--verdict", verdict.upper()])
    if protocol:
        cmd.extend(["--protocol", protocol.upper()])
    if context:
        cmd.extend(["--context", context])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return {"success": False, "error": result.stderr}

        flows = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    flows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # Summarize flows
        verdicts = {}
        protocols = {}
        for flow in flows:
            v = flow.get("verdict", "UNKNOWN")
            verdicts[v] = verdicts.get(v, 0) + 1

            l4 = flow.get("l4", {})
            if "TCP" in l4:
                protocols["TCP"] = protocols.get("TCP", 0) + 1
            elif "UDP" in l4:
                protocols["UDP"] = protocols.get("UDP", 0) + 1
            elif "ICMPv4" in l4 or "ICMPv6" in l4:
                protocols["ICMP"] = protocols.get("ICMP", 0) + 1

        return {
            "success": True,
            "context": context or "current",
            "total_flows": len(flows),
            "verdicts_summary": verdicts,
            "protocols_summary": protocols,
            "flows": flows[:50],  # Return first 50 for display
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Hubble query timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def cilium_detect(context: str = "") -> Dict[str, Any]:
    """Detect if Cilium is installed and its components.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for Cilium
    """
    return {
        "context": context or "current",
        "installed": crd_exists(CILIUM_NETWORK_POLICY_CRD, context),
        "crds": {
            "ciliumnetworkpolicies": crd_exists(CILIUM_NETWORK_POLICY_CRD, context),
            "ciliumclusterwidenetworkpolicies": crd_exists(CILIUM_CLUSTERWIDE_POLICY_CRD, context),
            "ciliumendpoints": crd_exists(CILIUM_ENDPOINT_CRD, context),
            "ciliumidentities": crd_exists(CILIUM_IDENTITY_CRD, context),
            "ciliumnodes": crd_exists(CILIUM_NODE_CRD, context),
        },
        "cli": {
            "cilium_available": _cilium_cli_available(),
            "hubble_available": _hubble_cli_available(),
        },
    }


def register_cilium_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register Cilium tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def cilium_policies_list_tool(
        namespace: str = "",
        context: str = "",
        include_clusterwide: bool = True
    ) -> str:
        """List Cilium network policies."""
        return json.dumps(cilium_policies_list(namespace, context, include_clusterwide), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def cilium_policy_get_tool(
        name: str,
        namespace: str = "",
        kind: str = "CiliumNetworkPolicy",
        context: str = ""
    ) -> str:
        """Get detailed information about a Cilium network policy."""
        return json.dumps(cilium_policy_get(name, namespace, kind, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def cilium_endpoints_list_tool(
        namespace: str = "",
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Cilium endpoints with their status."""
        return json.dumps(cilium_endpoints_list(namespace, context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def cilium_identities_list_tool(
        context: str = "",
        label_selector: str = ""
    ) -> str:
        """List Cilium identities."""
        return json.dumps(cilium_identities_list(context, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def cilium_nodes_list_tool(context: str = "") -> str:
        """List Cilium nodes with their status."""
        return json.dumps(cilium_nodes_list(context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def cilium_status_tool(context: str = "") -> str:
        """Get Cilium cluster status."""
        return json.dumps(cilium_status(context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def hubble_flows_query_tool(
        namespace: str = "",
        pod: str = "",
        label_selector: str = "",
        verdict: str = "",
        protocol: str = "",
        last: int = 100,
        context: str = ""
    ) -> str:
        """Query Hubble flows for network observability."""
        return json.dumps(hubble_flows_query(namespace, pod, label_selector, verdict, protocol, last, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def cilium_detect_tool(context: str = "") -> str:
        """Detect if Cilium is installed and its components."""
        return json.dumps(cilium_detect(context), indent=2)
