#!/usr/bin/env python3
"""
Pod Diagnostic Script
Collects comprehensive diagnostics for a pod.

Usage within Claude Code:
    This script is called by the k8s-troubleshoot skill to gather
    pod diagnostics in a structured format.
"""

import json
import sys
from typing import Any


def diagnose_pod(name: str, namespace: str, context: str = "") -> dict[str, Any]:
    """
    Collect comprehensive diagnostics for a pod.

    Args:
        name: Pod name
        namespace: Kubernetes namespace
        context: Optional kubeconfig context

    Returns:
        Dictionary with diagnostic information
    """
    diagnostics = {
        "pod": name,
        "namespace": namespace,
        "context": context or "current",
        "checks": [],
        "issues": [],
        "recommendations": []
    }

    # Note: In actual usage, Claude will call the MCP tools directly.
    # This script structure shows what diagnostics to collect.

    diagnostics["checks"] = [
        {
            "name": "pod_status",
            "tool": "get_pods",
            "params": {"namespace": namespace, "context": context},
            "description": "Get pod status and phase"
        },
        {
            "name": "pod_details",
            "tool": "describe_pod",
            "params": {"name": name, "namespace": namespace, "context": context},
            "description": "Get detailed pod description"
        },
        {
            "name": "pod_logs",
            "tool": "get_pod_logs",
            "params": {"name": name, "namespace": namespace, "previous": True, "context": context},
            "description": "Get logs (including previous container)"
        },
        {
            "name": "pod_events",
            "tool": "get_events",
            "params": {"namespace": namespace, "field_selector": f"involvedObject.name={name}", "context": context},
            "description": "Get events related to this pod"
        },
        {
            "name": "pod_metrics",
            "tool": "get_pod_metrics",
            "params": {"name": name, "namespace": namespace, "context": context},
            "description": "Get resource usage metrics"
        }
    ]

    return diagnostics


def analyze_pod_state(status: str) -> dict[str, Any]:
    """
    Analyze pod state and provide recommendations.

    Args:
        status: Pod status from describe

    Returns:
        Analysis with issues and recommendations
    """
    analysis = {
        "issues": [],
        "recommendations": []
    }

    # Common patterns
    patterns = {
        "CrashLoopBackOff": {
            "issue": "Container is crashing repeatedly",
            "checks": [
                "Check logs with get_pod_logs(previous=True)",
                "Check exit code in describe output",
                "Verify resource limits aren't too restrictive"
            ],
            "common_causes": [
                "Application error - check logs",
                "OOMKilled - increase memory limit",
                "Missing dependencies - check init containers"
            ]
        },
        "ImagePullBackOff": {
            "issue": "Cannot pull container image",
            "checks": [
                "Verify image name and tag",
                "Check imagePullSecrets",
                "Test registry accessibility"
            ],
            "common_causes": [
                "Wrong image name or tag",
                "Private registry without credentials",
                "Registry rate limiting"
            ]
        },
        "Pending": {
            "issue": "Pod cannot be scheduled",
            "checks": [
                "Check node resources",
                "Verify node selectors",
                "Check for taints/tolerations"
            ],
            "common_causes": [
                "Insufficient CPU/memory on nodes",
                "No nodes match selectors",
                "PVC not bound"
            ]
        },
        "ContainerCreating": {
            "issue": "Container stuck creating",
            "checks": [
                "Check events for mount errors",
                "Verify PVCs are bound",
                "Check image pull status"
            ],
            "common_causes": [
                "Volume mount failure",
                "Slow image pull",
                "Network plugin issue"
            ]
        }
    }

    for pattern, info in patterns.items():
        if pattern.lower() in status.lower():
            analysis["issues"].append(info["issue"])
            analysis["recommendations"].extend(info["checks"])
            analysis["common_causes"] = info["common_causes"]
            break

    return analysis


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: diagnose-pod.py <pod-name> <namespace> [context]")
        sys.exit(1)

    pod_name = sys.argv[1]
    namespace = sys.argv[2]
    context = sys.argv[3] if len(sys.argv) > 3 else ""

    result = diagnose_pod(pod_name, namespace, context)
    print(json.dumps(result, indent=2))
