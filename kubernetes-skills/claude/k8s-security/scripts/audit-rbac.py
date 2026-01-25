#!/usr/bin/env python3
"""
RBAC Audit Script
Analyzes RBAC configuration for security issues.

Usage within Claude Code:
    This script is called by the k8s-security skill to audit
    RBAC configuration and find potential security issues.
"""

import json
import sys
from typing import Any


def audit_rbac(context: str = "") -> dict[str, Any]:
    """
    Audit RBAC configuration for security issues.

    Args:
        context: Optional kubeconfig context

    Returns:
        Dictionary with audit findings
    """
    audit = {
        "context": context or "current",
        "critical": [],
        "high": [],
        "medium": [],
        "low": [],
        "checks_to_run": []
    }

    # Define checks to run with MCP tools
    audit["checks_to_run"] = [
        {
            "name": "cluster_admin_bindings",
            "tool": "get_cluster_role_bindings",
            "severity": "critical",
            "description": "Check for non-system cluster-admin bindings",
            "look_for": "roleRef.name == 'cluster-admin' AND subject not in system:*"
        },
        {
            "name": "wildcard_roles",
            "tool": "get_cluster_roles",
            "severity": "high",
            "description": "Check for roles with wildcard permissions",
            "look_for": "rules with '*' in verbs, resources, or apiGroups"
        },
        {
            "name": "secrets_access",
            "tool": "get_cluster_roles",
            "severity": "high",
            "description": "Check for roles with secrets access",
            "look_for": "rules with resources=['secrets'] and verbs=['get','list']"
        },
        {
            "name": "pod_exec_access",
            "tool": "get_cluster_roles",
            "severity": "medium",
            "description": "Check for roles with pod/exec access",
            "look_for": "rules with resources=['pods/exec'] and verbs=['create']"
        },
        {
            "name": "namespace_admin_bindings",
            "tool": "get_role_bindings",
            "severity": "medium",
            "description": "Check namespace-level admin bindings",
            "params": {"all_namespaces": True}
        }
    ]

    return audit


def analyze_cluster_role_binding(binding: dict) -> dict[str, Any] | None:
    """
    Analyze a ClusterRoleBinding for security issues.

    Args:
        binding: ClusterRoleBinding data

    Returns:
        Finding if issue detected, None otherwise
    """
    role_ref = binding.get("roleRef", {})
    subjects = binding.get("subjects", [])

    # Check for cluster-admin bindings
    if role_ref.get("name") == "cluster-admin":
        non_system_subjects = [
            s for s in subjects
            if not s.get("name", "").startswith("system:")
        ]

        if non_system_subjects:
            return {
                "severity": "critical",
                "type": "cluster_admin_binding",
                "binding": binding.get("metadata", {}).get("name"),
                "subjects": non_system_subjects,
                "recommendation": "Remove cluster-admin binding, create scoped role instead"
            }

    return None


def analyze_cluster_role(role: dict) -> list[dict[str, Any]]:
    """
    Analyze a ClusterRole for security issues.

    Args:
        role: ClusterRole data

    Returns:
        List of findings
    """
    findings = []
    rules = role.get("rules", [])
    role_name = role.get("metadata", {}).get("name", "unknown")

    for rule in rules:
        verbs = rule.get("verbs", [])
        resources = rule.get("resources", [])
        api_groups = rule.get("apiGroups", [])

        # Check for wildcard verbs
        if "*" in verbs:
            findings.append({
                "severity": "high",
                "type": "wildcard_verbs",
                "role": role_name,
                "rule": rule,
                "recommendation": "Specify exact verbs needed"
            })

        # Check for wildcard resources
        if "*" in resources:
            findings.append({
                "severity": "high",
                "type": "wildcard_resources",
                "role": role_name,
                "rule": rule,
                "recommendation": "Specify exact resources needed"
            })

        # Check for secrets access
        if "secrets" in resources and any(v in verbs for v in ["get", "list", "*"]):
            findings.append({
                "severity": "high",
                "type": "secrets_access",
                "role": role_name,
                "rule": rule,
                "recommendation": "Limit secrets access to specific names using resourceNames"
            })

        # Check for pod/exec access
        if "pods/exec" in resources and any(v in verbs for v in ["create", "*"]):
            findings.append({
                "severity": "medium",
                "type": "pod_exec_access",
                "role": role_name,
                "rule": rule,
                "recommendation": "Restrict pod/exec to specific namespaces"
            })

    return findings


def generate_report(findings: list[dict[str, Any]]) -> str:
    """
    Generate human-readable audit report.

    Args:
        findings: List of findings

    Returns:
        Formatted report string
    """
    report = ["# RBAC Security Audit Report\n"]

    by_severity = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }

    for finding in findings:
        severity = finding.get("severity", "low")
        by_severity[severity].append(finding)

    for severity in ["critical", "high", "medium", "low"]:
        items = by_severity[severity]
        if items:
            report.append(f"\n## {severity.upper()} ({len(items)} findings)\n")
            for item in items:
                report.append(f"- **{item['type']}**: {item.get('role', item.get('binding', 'N/A'))}")
                report.append(f"  - Recommendation: {item['recommendation']}")

    if not any(by_severity.values()):
        report.append("\nNo security issues found.")

    return "\n".join(report)


if __name__ == "__main__":
    context = sys.argv[1] if len(sys.argv) > 1 else ""

    result = audit_rbac(context)
    print(json.dumps(result, indent=2))
