#!/usr/bin/env python3
"""
Incident Diagnostics Collection Script
Collects comprehensive diagnostics for incident response.

Usage within Claude Code:
    This script is called by the k8s-incident skill to collect
    all relevant information during an incident.
"""

import json
import sys
from datetime import datetime
from typing import Any


def collect_diagnostics(
    namespace: str = "",
    context: str = "",
    include_logs: bool = True,
    since_minutes: int = 30
) -> dict[str, Any]:
    """
    Collect comprehensive incident diagnostics.

    Args:
        namespace: Focus namespace (empty for cluster-wide)
        context: Optional kubeconfig context
        include_logs: Include pod logs
        since_minutes: Time window for logs/events

    Returns:
        Dictionary with diagnostic collection plan
    """
    diagnostics = {
        "timestamp": datetime.utcnow().isoformat(),
        "namespace": namespace or "all",
        "context": context or "current",
        "since_minutes": since_minutes,
        "collection_plan": []
    }

    # Cluster health
    diagnostics["collection_plan"].extend([
        {
            "category": "cluster_health",
            "priority": 1,
            "checks": [
                {
                    "name": "nodes",
                    "tool": "get_nodes",
                    "params": {"context": context},
                    "description": "List all nodes and their status"
                },
                {
                    "name": "system_pods",
                    "tool": "get_pods",
                    "params": {"namespace": "kube-system", "context": context},
                    "description": "Check control plane pods"
                }
            ]
        }
    ])

    # Namespace-specific if provided
    if namespace:
        diagnostics["collection_plan"].extend([
            {
                "category": "namespace_resources",
                "priority": 2,
                "checks": [
                    {
                        "name": "pods",
                        "tool": "get_pods",
                        "params": {"namespace": namespace, "context": context},
                        "description": "List all pods"
                    },
                    {
                        "name": "deployments",
                        "tool": "get_deployments",
                        "params": {"namespace": namespace, "context": context},
                        "description": "List deployments"
                    },
                    {
                        "name": "services",
                        "tool": "get_services",
                        "params": {"namespace": namespace, "context": context},
                        "description": "List services"
                    },
                    {
                        "name": "endpoints",
                        "tool": "get_endpoints",
                        "params": {"namespace": namespace, "context": context},
                        "description": "Check service backends"
                    },
                    {
                        "name": "events",
                        "tool": "get_events",
                        "params": {"namespace": namespace, "context": context},
                        "description": "Recent events"
                    }
                ]
            }
        ])

        if include_logs:
            diagnostics["collection_plan"].append({
                "category": "logs",
                "priority": 3,
                "note": "Collect logs from failing pods",
                "checks": [
                    {
                        "name": "pod_logs",
                        "tool": "get_pod_logs",
                        "params": {
                            "namespace": namespace,
                            "tail_lines": 100,
                            "previous": True,
                            "context": context
                        },
                        "description": "Get logs from each failing pod"
                    }
                ]
            })

    # Network diagnostics
    diagnostics["collection_plan"].append({
        "category": "networking",
        "priority": 4,
        "checks": [
            {
                "name": "network_policies",
                "tool": "get_network_policies",
                "params": {"namespace": namespace, "context": context},
                "description": "Check network policies"
            },
            {
                "name": "ingresses",
                "tool": "get_ingresses",
                "params": {"namespace": namespace, "context": context},
                "description": "Check ingress configuration"
            }
        ]
    })

    # Storage diagnostics
    diagnostics["collection_plan"].append({
        "category": "storage",
        "priority": 5,
        "checks": [
            {
                "name": "pvcs",
                "tool": "get_pvc",
                "params": {"namespace": namespace, "context": context},
                "description": "Check PVC status"
            }
        ]
    })

    # Resource usage
    diagnostics["collection_plan"].append({
        "category": "resources",
        "priority": 6,
        "checks": [
            {
                "name": "resource_usage",
                "tool": "get_resource_usage",
                "params": {"namespace": namespace, "context": context},
                "description": "Check resource consumption"
            }
        ]
    })

    return diagnostics


def triage_findings(findings: dict[str, Any]) -> dict[str, Any]:
    """
    Triage collected findings by severity.

    Args:
        findings: Collected diagnostic data

    Returns:
        Triaged findings with severity
    """
    triage = {
        "critical": [],
        "warning": [],
        "info": [],
        "summary": ""
    }

    # Critical: Nodes not ready
    nodes = findings.get("nodes", [])
    not_ready = [n for n in nodes if n.get("status") != "Ready"]
    if not_ready:
        triage["critical"].append({
            "type": "nodes_not_ready",
            "count": len(not_ready),
            "nodes": not_ready,
            "action": "Investigate node health immediately"
        })

    # Critical: System pods failing
    system_pods = findings.get("system_pods", [])
    failing_system = [p for p in system_pods if p.get("status") not in ["Running", "Completed"]]
    if failing_system:
        triage["critical"].append({
            "type": "system_pods_failing",
            "count": len(failing_system),
            "pods": failing_system,
            "action": "Check control plane components"
        })

    # Warning: Application pods failing
    pods = findings.get("pods", [])
    failing_pods = [p for p in pods if p.get("status") not in ["Running", "Completed"]]
    if failing_pods:
        triage["warning"].append({
            "type": "pods_failing",
            "count": len(failing_pods),
            "pods": failing_pods,
            "action": "Check pod logs and events"
        })

    # Warning: Empty endpoints
    endpoints = findings.get("endpoints", [])
    empty_endpoints = [e for e in endpoints if not e.get("addresses")]
    if empty_endpoints:
        triage["warning"].append({
            "type": "empty_endpoints",
            "services": empty_endpoints,
            "action": "Check pod selectors and readiness"
        })

    # Generate summary
    critical_count = len(triage["critical"])
    warning_count = len(triage["warning"])

    if critical_count > 0:
        triage["summary"] = f"CRITICAL: {critical_count} critical issues require immediate attention"
    elif warning_count > 0:
        triage["summary"] = f"WARNING: {warning_count} issues detected"
    else:
        triage["summary"] = "No significant issues detected"

    return triage


def generate_incident_report(
    diagnostics: dict[str, Any],
    triage: dict[str, Any]
) -> str:
    """
    Generate incident report.

    Args:
        diagnostics: Collected diagnostics
        triage: Triaged findings

    Returns:
        Formatted incident report
    """
    report = ["# Kubernetes Incident Diagnostic Report\n"]
    report.append(f"Timestamp: {diagnostics['timestamp']}")
    report.append(f"Context: {diagnostics['context']}")
    report.append(f"Namespace: {diagnostics['namespace']}\n")

    report.append(f"## Summary\n{triage['summary']}\n")

    if triage["critical"]:
        report.append("## Critical Issues\n")
        for issue in triage["critical"]:
            report.append(f"### {issue['type']}")
            report.append(f"- Count: {issue.get('count', 'N/A')}")
            report.append(f"- Action: {issue['action']}\n")

    if triage["warning"]:
        report.append("## Warnings\n")
        for issue in triage["warning"]:
            report.append(f"### {issue['type']}")
            report.append(f"- Action: {issue['action']}\n")

    report.append("## Collection Plan\n")
    report.append("Execute the following MCP tools to gather data:\n")

    for category in sorted(diagnostics["collection_plan"], key=lambda x: x["priority"]):
        report.append(f"### {category['category'].replace('_', ' ').title()}")
        for check in category["checks"]:
            report.append(f"- `{check['tool']}`: {check['description']}")
        report.append("")

    return "\n".join(report)


if __name__ == "__main__":
    namespace = sys.argv[1] if len(sys.argv) > 1 else ""
    context = sys.argv[2] if len(sys.argv) > 2 else ""

    result = collect_diagnostics(namespace, context)
    print(json.dumps(result, indent=2))
