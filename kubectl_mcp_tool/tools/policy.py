"""Policy toolset for kubectl-mcp-server (Kyverno and Gatekeeper)."""

import json
from typing import Dict, Any, List, Optional

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ..crd_detector import crd_exists
from .utils import run_kubectl, get_resources


KYVERNO_CLUSTER_POLICY_CRD = "clusterpolicies.kyverno.io"
KYVERNO_POLICY_CRD = "policies.kyverno.io"
KYVERNO_POLICY_REPORT_CRD = "policyreports.wgpolicyk8s.io"
KYVERNO_CLUSTER_POLICY_REPORT_CRD = "clusterpolicyreports.wgpolicyk8s.io"
GATEKEEPER_CONSTRAINT_TEMPLATE_CRD = "constrainttemplates.templates.gatekeeper.sh"
GATEKEEPER_CONFIG_CRD = "configs.config.gatekeeper.sh"


def _get_condition(conditions: List[Dict], condition_type: str) -> Optional[Dict]:
    """Get a specific condition from conditions list."""
    return next((c for c in conditions if c.get("type") == condition_type), None)


def policy_list(
    namespace: str = "",
    context: str = "",
    engine: str = "all",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List policies from Kyverno or Gatekeeper.

    Args:
        namespace: Filter by namespace (empty for cluster-wide)
        context: Kubernetes context to use (optional)
        engine: Policy engine filter (kyverno, gatekeeper, all)
        label_selector: Label selector to filter policies

    Returns:
        List of policies with their status
    """
    policies = []

    if engine in ("kyverno", "all"):
        if crd_exists(KYVERNO_CLUSTER_POLICY_CRD, context):
            for item in get_resources("clusterpolicies.kyverno.io", "", context, label_selector):
                status = item.get("status", {})
                conditions = status.get("conditions", [])
                ready_cond = _get_condition(conditions, "Ready")
                spec = item.get("spec", {})

                policies.append({
                    "name": item["metadata"]["name"],
                    "namespace": "",
                    "kind": "ClusterPolicy",
                    "engine": "kyverno",
                    "ready": ready_cond.get("status") == "True" if ready_cond else True,
                    "validation_failure_action": spec.get("validationFailureAction", "Audit"),
                    "background": spec.get("background", True),
                    "rules_count": len(spec.get("rules", [])),
                    "message": ready_cond.get("message", "") if ready_cond else "",
                })

        if crd_exists(KYVERNO_POLICY_CRD, context):
            for item in get_resources("policies.kyverno.io", namespace, context, label_selector):
                status = item.get("status", {})
                conditions = status.get("conditions", [])
                ready_cond = _get_condition(conditions, "Ready")
                spec = item.get("spec", {})

                policies.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "kind": "Policy",
                    "engine": "kyverno",
                    "ready": ready_cond.get("status") == "True" if ready_cond else True,
                    "validation_failure_action": spec.get("validationFailureAction", "Audit"),
                    "background": spec.get("background", True),
                    "rules_count": len(spec.get("rules", [])),
                    "message": ready_cond.get("message", "") if ready_cond else "",
                })

    if engine in ("gatekeeper", "all"):
        if crd_exists(GATEKEEPER_CONSTRAINT_TEMPLATE_CRD, context):
            for item in get_resources("constrainttemplates.templates.gatekeeper.sh", "", context, label_selector):
                status = item.get("status", {})
                spec = item.get("spec", {})

                created = status.get("created", False)
                policies.append({
                    "name": item["metadata"]["name"],
                    "namespace": "",
                    "kind": "ConstraintTemplate",
                    "engine": "gatekeeper",
                    "ready": created,
                    "crd_kind": spec.get("crd", {}).get("spec", {}).get("names", {}).get("kind", ""),
                    "targets": [t.get("target", "") for t in spec.get("targets", [])],
                })

            constraints = _get_gatekeeper_constraints(context)
            for constraint in constraints:
                policies.append(constraint)

    enforce_count = sum(1 for p in policies if p.get("validation_failure_action") == "Enforce" or p.get("kind") == "Constraint")

    return {
        "context": context or "current",
        "total": len(policies),
        "enforcing": enforce_count,
        "policies": policies,
    }


def _get_gatekeeper_constraints(context: str = "") -> List[Dict]:
    """Get all Gatekeeper constraints dynamically."""
    constraints = []

    templates = get_resources("constrainttemplates.templates.gatekeeper.sh", "", context)
    for template in templates:
        crd_kind = template.get("spec", {}).get("crd", {}).get("spec", {}).get("names", {}).get("kind", "")
        if not crd_kind:
            continue

        try:
            constraint_items = get_resources(crd_kind.lower(), "", context)
            for item in constraint_items:
                status = item.get("status", {})
                spec = item.get("spec", {})
                match = spec.get("match", {})

                total_violations = status.get("totalViolations", 0)

                constraints.append({
                    "name": item["metadata"]["name"],
                    "namespace": "",
                    "kind": "Constraint",
                    "constraint_kind": crd_kind,
                    "engine": "gatekeeper",
                    "ready": True,
                    "enforcement_action": spec.get("enforcementAction", "deny"),
                    "total_violations": total_violations,
                    "match_kinds": match.get("kinds", []),
                    "match_namespaces": match.get("namespaces", []),
                    "excluded_namespaces": match.get("excludedNamespaces", []),
                })
        except Exception:
            continue

    return constraints


def policy_get(
    name: str,
    namespace: str = "",
    kind: str = "ClusterPolicy",
    context: str = ""
) -> Dict[str, Any]:
    """Get detailed information about a policy.

    Args:
        name: Name of the policy
        namespace: Namespace (for namespaced policies)
        kind: Kind of policy (ClusterPolicy, Policy, ConstraintTemplate, or constraint kind)
        context: Kubernetes context to use (optional)

    Returns:
        Detailed policy information
    """
    kind_map = {
        "clusterpolicy": "clusterpolicies.kyverno.io",
        "policy": "policies.kyverno.io",
        "constrainttemplate": "constrainttemplates.templates.gatekeeper.sh",
    }

    k8s_kind = kind_map.get(kind.lower(), kind.lower())

    if namespace:
        args = ["get", k8s_kind, name, "-n", namespace, "-o", "json"]
    else:
        args = ["get", k8s_kind, name, "-o", "json"]

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


def policy_violations_list(
    namespace: str = "",
    context: str = "",
    engine: str = "all",
    severity: str = ""
) -> Dict[str, Any]:
    """List policy violations from PolicyReports or Gatekeeper.

    Args:
        namespace: Filter by namespace (empty for all)
        context: Kubernetes context to use (optional)
        engine: Policy engine filter (kyverno, gatekeeper, all)
        severity: Filter by severity (high, medium, low)

    Returns:
        List of policy violations
    """
    violations = []

    if engine in ("kyverno", "all"):
        if crd_exists(KYVERNO_POLICY_REPORT_CRD, context):
            for report in get_resources("policyreports.wgpolicyk8s.io", namespace, context):
                results = report.get("results", [])
                for result in results:
                    if result.get("result") in ("fail", "error"):
                        if severity and result.get("severity", "").lower() != severity.lower():
                            continue
                        violations.append({
                            "source": "PolicyReport",
                            "engine": "kyverno",
                            "namespace": report["metadata"]["namespace"],
                            "policy": result.get("policy", ""),
                            "rule": result.get("rule", ""),
                            "result": result.get("result", ""),
                            "severity": result.get("severity", ""),
                            "message": result.get("message", ""),
                            "category": result.get("category", ""),
                            "resources": result.get("resources", []),
                        })

        if crd_exists(KYVERNO_CLUSTER_POLICY_REPORT_CRD, context):
            for report in get_resources("clusterpolicyreports.wgpolicyk8s.io", "", context):
                results = report.get("results", [])
                for result in results:
                    if result.get("result") in ("fail", "error"):
                        if severity and result.get("severity", "").lower() != severity.lower():
                            continue
                        violations.append({
                            "source": "ClusterPolicyReport",
                            "engine": "kyverno",
                            "namespace": "",
                            "policy": result.get("policy", ""),
                            "rule": result.get("rule", ""),
                            "result": result.get("result", ""),
                            "severity": result.get("severity", ""),
                            "message": result.get("message", ""),
                            "category": result.get("category", ""),
                            "resources": result.get("resources", []),
                        })

    if engine in ("gatekeeper", "all"):
        constraints = _get_gatekeeper_constraints(context)
        for constraint in constraints:
            if constraint.get("total_violations", 0) > 0:
                constraint_detail = policy_get(
                    constraint["name"], "", constraint["constraint_kind"], context
                )
                if constraint_detail.get("success"):
                    policy_data = constraint_detail["policy"]
                    status_violations = policy_data.get("status", {}).get("violations", [])
                    for v in status_violations:
                        violations.append({
                            "source": "GatekeeperConstraint",
                            "engine": "gatekeeper",
                            "constraint": constraint["name"],
                            "constraint_kind": constraint["constraint_kind"],
                            "enforcement_action": v.get("enforcementAction", "deny"),
                            "kind": v.get("kind", ""),
                            "name": v.get("name", ""),
                            "namespace": v.get("namespace", ""),
                            "message": v.get("message", ""),
                        })

    critical = sum(1 for v in violations if v.get("severity", "").lower() == "high")

    return {
        "context": context or "current",
        "total": len(violations),
        "critical": critical,
        "violations": violations,
    }


def policy_explain_denial(
    message: str,
    context: str = ""
) -> Dict[str, Any]:
    """Explain an admission denial message by matching against policies.

    Args:
        message: The denial message from Kubernetes admission
        context: Kubernetes context to use (optional)

    Returns:
        Explanation with matched policies and recommendations
    """
    matches = []
    recommendations = []

    message_lower = message.lower()

    if crd_exists(KYVERNO_CLUSTER_POLICY_CRD, context):
        for policy in get_resources("clusterpolicies.kyverno.io", "", context):
            policy_name = policy["metadata"]["name"]
            if policy_name.lower() in message_lower:
                spec = policy.get("spec", {})
                matches.append({
                    "engine": "kyverno",
                    "type": "ClusterPolicy",
                    "name": policy_name,
                    "confidence": 0.9,
                    "validation_failure_action": spec.get("validationFailureAction", "Audit"),
                    "rules": [r.get("name", "") for r in spec.get("rules", [])],
                })

            for rule in policy.get("spec", {}).get("rules", []):
                rule_name = rule.get("name", "")
                if rule_name.lower() in message_lower:
                    matches.append({
                        "engine": "kyverno",
                        "type": "ClusterPolicy",
                        "name": policy_name,
                        "rule": rule_name,
                        "confidence": 0.85,
                    })

    if crd_exists(GATEKEEPER_CONSTRAINT_TEMPLATE_CRD, context):
        constraints = _get_gatekeeper_constraints(context)
        for constraint in constraints:
            if constraint["name"].lower() in message_lower:
                matches.append({
                    "engine": "gatekeeper",
                    "type": "Constraint",
                    "name": constraint["name"],
                    "constraint_kind": constraint.get("constraint_kind", ""),
                    "confidence": 0.9,
                    "enforcement_action": constraint.get("enforcement_action", "deny"),
                })

    if "kyverno" in message_lower:
        recommendations.append("This appears to be a Kyverno policy denial")
        recommendations.append("Check policy with: kubectl get clusterpolicy -o yaml")
        recommendations.append("View violations: kubectl get policyreport -A")
    elif "gatekeeper" in message_lower or "admission webhook" in message_lower:
        recommendations.append("This appears to be a Gatekeeper/OPA policy denial")
        recommendations.append("Check constraints with: kubectl get constraints")
        recommendations.append("View constraint templates: kubectl get constrainttemplates")

    if not matches:
        recommendations.append("No exact policy match found")
        recommendations.append("Try listing all policies: policy_list()")
        recommendations.append("Check admission webhooks: kubectl get validatingwebhookconfigurations")

    return {
        "context": context or "current",
        "original_message": message,
        "matches": matches,
        "recommendations": recommendations,
    }


def policy_audit(
    namespace: str = "",
    context: str = "",
    resource_kind: str = ""
) -> Dict[str, Any]:
    """Audit resources against installed policies.

    Args:
        namespace: Namespace to audit (empty for all)
        context: Kubernetes context to use (optional)
        resource_kind: Filter by resource kind

    Returns:
        Audit results with violation summary
    """
    violations = policy_violations_list(namespace, context)
    policies = policy_list(namespace, context)

    by_policy = {}
    by_namespace = {}
    by_kind = {}

    for v in violations.get("violations", []):
        policy_name = v.get("policy", v.get("constraint", "unknown"))
        if policy_name not in by_policy:
            by_policy[policy_name] = 0
        by_policy[policy_name] += 1

        ns = v.get("namespace", "cluster-scoped")
        if ns not in by_namespace:
            by_namespace[ns] = 0
        by_namespace[ns] += 1

        kind = v.get("kind", "unknown")
        if resource_kind and kind.lower() != resource_kind.lower():
            continue
        if kind not in by_kind:
            by_kind[kind] = 0
        by_kind[kind] += 1

    return {
        "context": context or "current",
        "summary": {
            "total_policies": policies.get("total", 0),
            "enforcing_policies": policies.get("enforcing", 0),
            "total_violations": violations.get("total", 0),
            "critical_violations": violations.get("critical", 0),
        },
        "violations_by_policy": by_policy,
        "violations_by_namespace": by_namespace,
        "violations_by_kind": by_kind,
        "top_violating_policies": sorted(by_policy.items(), key=lambda x: x[1], reverse=True)[:5],
        "top_violating_namespaces": sorted(by_namespace.items(), key=lambda x: x[1], reverse=True)[:5],
    }


def policy_detect(context: str = "") -> Dict[str, Any]:
    """Detect which policy engines are installed in the cluster.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for Kyverno and Gatekeeper
    """
    kyverno_installed = any([
        crd_exists(KYVERNO_CLUSTER_POLICY_CRD, context),
        crd_exists(KYVERNO_POLICY_CRD, context),
    ])

    gatekeeper_installed = crd_exists(GATEKEEPER_CONSTRAINT_TEMPLATE_CRD, context)

    return {
        "context": context or "current",
        "kyverno": {
            "installed": kyverno_installed,
            "cluster_policies": crd_exists(KYVERNO_CLUSTER_POLICY_CRD, context),
            "policies": crd_exists(KYVERNO_POLICY_CRD, context),
            "policy_reports": crd_exists(KYVERNO_POLICY_REPORT_CRD, context),
            "cluster_policy_reports": crd_exists(KYVERNO_CLUSTER_POLICY_REPORT_CRD, context),
        },
        "gatekeeper": {
            "installed": gatekeeper_installed,
            "constraint_templates": crd_exists(GATEKEEPER_CONSTRAINT_TEMPLATE_CRD, context),
            "config": crd_exists(GATEKEEPER_CONFIG_CRD, context),
        },
    }


def register_policy_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register policy tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def policy_list_tool(
        namespace: str = "",
        context: str = "",
        engine: str = "all",
        label_selector: str = ""
    ) -> str:
        """List policies from Kyverno or Gatekeeper."""
        return json.dumps(policy_list(namespace, context, engine, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def policy_get_tool(
        name: str,
        namespace: str = "",
        kind: str = "ClusterPolicy",
        context: str = ""
    ) -> str:
        """Get detailed information about a policy."""
        return json.dumps(policy_get(name, namespace, kind, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def policy_violations_list_tool(
        namespace: str = "",
        context: str = "",
        engine: str = "all",
        severity: str = ""
    ) -> str:
        """List policy violations from PolicyReports or Gatekeeper."""
        return json.dumps(policy_violations_list(namespace, context, engine, severity), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def policy_explain_denial_tool(
        message: str,
        context: str = ""
    ) -> str:
        """Explain an admission denial message by matching against policies."""
        return json.dumps(policy_explain_denial(message, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def policy_audit_tool(
        namespace: str = "",
        context: str = "",
        resource_kind: str = ""
    ) -> str:
        """Audit resources against installed policies."""
        return json.dumps(policy_audit(namespace, context, resource_kind), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def policy_detect_tool(context: str = "") -> str:
        """Detect which policy engines are installed in the cluster."""
        return json.dumps(policy_detect(context), indent=2)
