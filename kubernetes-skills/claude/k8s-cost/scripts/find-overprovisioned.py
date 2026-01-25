#!/usr/bin/env python3
"""
Resource Optimization Script
Identifies overprovisioned resources for cost savings.

Usage within Claude Code:
    This script is called by the k8s-cost skill to find
    overprovisioned resources and provide recommendations.
"""

import json
import sys
from typing import Any


def find_overprovisioned(namespace: str = "", context: str = "") -> dict[str, Any]:
    """
    Find overprovisioned resources in cluster.

    Args:
        namespace: Optional namespace filter
        context: Optional kubeconfig context

    Returns:
        Dictionary with findings and recommendations
    """
    analysis = {
        "namespace": namespace or "all",
        "context": context or "current",
        "checks": [],
        "thresholds": {
            "cpu_underutilized": 0.1,      # <10% usage
            "memory_underutilized": 0.3,   # <30% usage
            "cpu_overutilized": 0.8,       # >80% usage
            "memory_overutilized": 0.9     # >90% usage
        }
    }

    # Define checks to run with MCP tools
    analysis["checks"] = [
        {
            "name": "resource_recommendations",
            "tool": "get_resource_recommendations",
            "params": {"namespace": namespace, "context": context},
            "description": "Get VPA-style recommendations"
        },
        {
            "name": "pod_metrics",
            "tool": "get_resource_usage",
            "params": {"namespace": namespace, "context": context},
            "description": "Get current resource usage"
        },
        {
            "name": "unused_pvcs",
            "tool": "find_orphaned_pvcs",
            "params": {"namespace": namespace, "context": context},
            "description": "Find PVCs not mounted by any pod"
        },
        {
            "name": "unused_resources",
            "tool": "find_unused_resources",
            "params": {"namespace": namespace, "context": context},
            "description": "Find unused ConfigMaps/Secrets"
        },
        {
            "name": "namespace_cost",
            "tool": "get_namespace_cost",
            "params": {"namespace": namespace, "context": context},
            "description": "Get namespace cost breakdown"
        }
    ]

    return analysis


def analyze_pod_resources(pod: dict, metrics: dict) -> dict[str, Any] | None:
    """
    Analyze a pod's resource usage vs requests.

    Args:
        pod: Pod spec with resources
        metrics: Pod metrics data

    Returns:
        Finding if optimization possible, None otherwise
    """
    finding = {
        "pod": pod.get("name"),
        "namespace": pod.get("namespace"),
        "containers": []
    }

    has_issues = False

    for container in pod.get("containers", []):
        container_name = container.get("name")
        resources = container.get("resources", {})
        requests = resources.get("requests", {})

        # Get actual usage from metrics
        container_metrics = metrics.get("containers", {}).get(container_name, {})

        cpu_request = parse_cpu(requests.get("cpu", "0"))
        cpu_usage = container_metrics.get("cpu_cores", 0)
        memory_request = parse_memory(requests.get("memory", "0"))
        memory_usage = container_metrics.get("memory_bytes", 0)

        container_finding = {
            "name": container_name,
            "issues": [],
            "recommendations": []
        }

        # Check CPU
        if cpu_request > 0 and cpu_usage > 0:
            cpu_ratio = cpu_usage / cpu_request
            if cpu_ratio < 0.1:
                container_finding["issues"].append(
                    f"CPU severely underutilized: {cpu_ratio*100:.1f}% of request"
                )
                container_finding["recommendations"].append(
                    f"Reduce CPU request from {cpu_request} to {cpu_usage * 2:.3f} cores"
                )
                has_issues = True
            elif cpu_ratio > 0.8:
                container_finding["issues"].append(
                    f"CPU highly utilized: {cpu_ratio*100:.1f}% of request"
                )
                container_finding["recommendations"].append(
                    f"Increase CPU request/limit to prevent throttling"
                )
                has_issues = True

        # Check Memory
        if memory_request > 0 and memory_usage > 0:
            memory_ratio = memory_usage / memory_request
            if memory_ratio < 0.3:
                container_finding["issues"].append(
                    f"Memory underutilized: {memory_ratio*100:.1f}% of request"
                )
                container_finding["recommendations"].append(
                    f"Reduce memory request"
                )
                has_issues = True
            elif memory_ratio > 0.9:
                container_finding["issues"].append(
                    f"Memory near limit: {memory_ratio*100:.1f}% of request"
                )
                container_finding["recommendations"].append(
                    f"Increase memory limit to prevent OOMKill"
                )
                has_issues = True

        if container_finding["issues"]:
            finding["containers"].append(container_finding)

    return finding if has_issues else None


def parse_cpu(cpu_str: str) -> float:
    """Parse CPU string to cores."""
    if not cpu_str:
        return 0
    if cpu_str.endswith("m"):
        return float(cpu_str[:-1]) / 1000
    return float(cpu_str)


def parse_memory(memory_str: str) -> int:
    """Parse memory string to bytes."""
    if not memory_str:
        return 0

    units = {
        "Ki": 1024,
        "Mi": 1024**2,
        "Gi": 1024**3,
        "Ti": 1024**4,
        "K": 1000,
        "M": 1000**2,
        "G": 1000**3,
        "T": 1000**4
    }

    for suffix, multiplier in units.items():
        if memory_str.endswith(suffix):
            return int(float(memory_str[:-len(suffix)]) * multiplier)

    return int(memory_str)


def calculate_savings(findings: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate potential cost savings from findings.

    Args:
        findings: List of optimization findings

    Returns:
        Summary of potential savings
    """
    # Rough cost estimates (cloud provider specific)
    cpu_cost_per_core_month = 30  # USD
    memory_cost_per_gb_month = 5  # USD

    savings = {
        "cpu_cores_reducible": 0,
        "memory_gb_reducible": 0,
        "estimated_monthly_savings_usd": 0,
        "actions": []
    }

    for finding in findings:
        for container in finding.get("containers", []):
            for rec in container.get("recommendations", []):
                if "Reduce CPU" in rec:
                    # Extract cores from recommendation
                    savings["actions"].append({
                        "pod": finding["pod"],
                        "container": container["name"],
                        "action": rec
                    })
                elif "Reduce memory" in rec:
                    savings["actions"].append({
                        "pod": finding["pod"],
                        "container": container["name"],
                        "action": rec
                    })

    return savings


def generate_report(analysis: dict[str, Any], findings: list[dict[str, Any]]) -> str:
    """
    Generate cost optimization report.

    Args:
        analysis: Analysis configuration
        findings: List of findings

    Returns:
        Formatted report
    """
    report = ["# Kubernetes Cost Optimization Report\n"]
    report.append(f"Namespace: {analysis['namespace']}")
    report.append(f"Context: {analysis['context']}\n")

    if not findings:
        report.append("No optimization opportunities found.")
        return "\n".join(report)

    report.append(f"## Found {len(findings)} pods with optimization opportunities\n")

    for finding in findings:
        report.append(f"### Pod: {finding['namespace']}/{finding['pod']}")
        for container in finding.get("containers", []):
            report.append(f"  Container: {container['name']}")
            for issue in container.get("issues", []):
                report.append(f"    - Issue: {issue}")
            for rec in container.get("recommendations", []):
                report.append(f"    - Action: {rec}")
        report.append("")

    return "\n".join(report)


if __name__ == "__main__":
    namespace = sys.argv[1] if len(sys.argv) > 1 else ""
    context = sys.argv[2] if len(sys.argv) > 2 else ""

    result = find_overprovisioned(namespace, context)
    print(json.dumps(result, indent=2))
