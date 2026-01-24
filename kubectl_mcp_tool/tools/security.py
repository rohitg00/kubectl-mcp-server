import logging
from typing import Any, Dict, List, Optional

from mcp.types import ToolAnnotations

from ..k8s_config import (
    get_k8s_client,
    get_rbac_client,
    get_networking_client,
)

logger = logging.getLogger("mcp-server")


def register_security_tools(server, non_destructive: bool):
    """Register RBAC and security-related tools."""

    @server.tool(
        annotations=ToolAnnotations(
            title="Get RBAC Roles",
            readOnlyHint=True,
        ),
    )
    def get_rbac_roles(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get RBAC Roles in a namespace or cluster-wide.

        Args:
            namespace: Namespace to list roles from (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            rbac = get_rbac_client(context)

            if namespace:
                roles = rbac.list_namespaced_role(namespace)
            else:
                roles = rbac.list_role_for_all_namespaces()

            return {
                "success": True,
                "context": context or "current",
                "roles": [
                    {
                        "name": role.metadata.name,
                        "namespace": role.metadata.namespace,
                        "rules": [
                            {
                                "apiGroups": rule.api_groups,
                                "resources": rule.resources,
                                "verbs": rule.verbs
                            }
                            for rule in (role.rules or [])
                        ]
                    }
                    for role in roles.items
                ]
            }
        except Exception as e:
            logger.error(f"Error getting RBAC roles: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Cluster Roles",
            readOnlyHint=True,
        ),
    )
    def get_cluster_roles(context: str = "") -> Dict[str, Any]:
        """Get ClusterRoles in the cluster.

        Args:
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            rbac = get_rbac_client(context)
            roles = rbac.list_cluster_role()

            return {
                "success": True,
                "context": context or "current",
                "clusterRoles": [
                    {
                        "name": role.metadata.name,
                        "rules": [
                            {
                                "apiGroups": rule.api_groups,
                                "resources": rule.resources,
                                "verbs": rule.verbs
                            }
                            for rule in (role.rules or [])
                        ][:5]
                    }
                    for role in roles.items[:20]
                ]
            }
        except Exception as e:
            logger.error(f"Error getting cluster roles: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Analyze Pod Security",
            readOnlyHint=True,
        ),
    )
    def analyze_pod_security(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Analyze pod security configurations.

        Args:
            namespace: Namespace to analyze pods in (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            if namespace:
                pods = v1.list_namespaced_pod(namespace)
            else:
                pods = v1.list_pod_for_all_namespaces()

            issues = []
            for pod in pods.items:
                pod_issues = []
                spec = pod.spec

                if spec.host_network:
                    pod_issues.append("hostNetwork enabled")
                if spec.host_pid:
                    pod_issues.append("hostPID enabled")
                if spec.host_ipc:
                    pod_issues.append("hostIPC enabled")

                for container in (spec.containers or []):
                    sc = container.security_context
                    if sc:
                        if sc.privileged:
                            pod_issues.append(f"Container {container.name}: privileged mode")
                        if sc.run_as_root:
                            pod_issues.append(f"Container {container.name}: runs as root")
                        if sc.allow_privilege_escalation:
                            pod_issues.append(f"Container {container.name}: privilege escalation allowed")

                if pod_issues:
                    issues.append({
                        "pod": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "issues": pod_issues
                    })

            return {
                "success": True,
                "context": context or "current",
                "totalPods": len(pods.items),
                "podsWithIssues": len(issues),
                "issues": issues[:50]
            }
        except Exception as e:
            logger.error(f"Error analyzing pod security: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Analyze Network Policies",
            readOnlyHint=True,
        ),
    )
    def analyze_network_policies(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Analyze network policies in the cluster.

        Args:
            namespace: Namespace to analyze policies in (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            networking = get_networking_client(context)
            v1 = get_k8s_client(context)

            if namespace:
                policies = networking.list_namespaced_network_policy(namespace)
                namespaces = [v1.read_namespace(namespace)]
            else:
                policies = networking.list_network_policy_for_all_namespaces()
                namespaces = v1.list_namespace().items

            protected_namespaces = set()
            for policy in policies.items:
                protected_namespaces.add(policy.metadata.namespace)

            unprotected = [
                ns.metadata.name for ns in namespaces
                if ns.metadata.name not in protected_namespaces
                and ns.metadata.name not in ["kube-system", "kube-public", "kube-node-lease"]
            ]

            return {
                "success": True,
                "context": context or "current",
                "totalPolicies": len(policies.items),
                "protectedNamespaces": list(protected_namespaces),
                "unprotectedNamespaces": unprotected,
                "policies": [
                    {
                        "name": p.metadata.name,
                        "namespace": p.metadata.namespace,
                        "podSelector": p.spec.pod_selector.match_labels if p.spec.pod_selector else {},
                        "policyTypes": p.spec.policy_types
                    }
                    for p in policies.items
                ]
            }
        except Exception as e:
            logger.error(f"Error analyzing network policies: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Audit RBAC Permissions",
            readOnlyHint=True,
        ),
    )
    def audit_rbac_permissions(
        namespace: Optional[str] = None,
        subject: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Audit RBAC permissions for subjects.

        Args:
            namespace: Namespace to audit (cluster-wide if not specified)
            subject: Filter by subject name
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            rbac = get_rbac_client(context)

            cluster_bindings = rbac.list_cluster_role_binding()
            if namespace:
                role_bindings = rbac.list_namespaced_role_binding(namespace)
            else:
                role_bindings = rbac.list_role_binding_for_all_namespaces()

            permissions = []

            for binding in cluster_bindings.items:
                for subj in (binding.subjects or []):
                    if subject and subj.name != subject:
                        continue
                    permissions.append({
                        "subject": subj.name,
                        "subjectKind": subj.kind,
                        "roleRef": binding.role_ref.name,
                        "scope": "cluster",
                        "bindingName": binding.metadata.name
                    })

            for binding in role_bindings.items:
                for subj in (binding.subjects or []):
                    if subject and subj.name != subject:
                        continue
                    permissions.append({
                        "subject": subj.name,
                        "subjectKind": subj.kind,
                        "roleRef": binding.role_ref.name,
                        "scope": binding.metadata.namespace,
                        "bindingName": binding.metadata.name
                    })

            return {
                "success": True,
                "context": context or "current",
                "permissions": permissions[:100]
            }
        except Exception as e:
            logger.error(f"Error auditing RBAC: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Check Secrets Security",
            readOnlyHint=True,
        ),
    )
    def check_secrets_security(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Check security posture of secrets.

        Args:
            namespace: Namespace to check secrets in (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            if namespace:
                secrets = v1.list_namespaced_secret(namespace)
            else:
                secrets = v1.list_secret_for_all_namespaces()

            findings = []
            for secret in secrets.items:
                issues = []

                if secret.type == "Opaque":
                    issues.append("Generic secret type - consider using specific types")

                if not secret.metadata.annotations:
                    issues.append("No annotations - consider adding metadata")

                if issues:
                    findings.append({
                        "name": secret.metadata.name,
                        "namespace": secret.metadata.namespace,
                        "type": secret.type,
                        "issues": issues
                    })

            return {
                "success": True,
                "context": context or "current",
                "totalSecrets": len(secrets.items),
                "secretsWithIssues": len(findings),
                "findings": findings[:50]
            }
        except Exception as e:
            logger.error(f"Error checking secrets security: {e}")
            return {"success": False, "error": str(e)}

    @server.tool(
        annotations=ToolAnnotations(
            title="Get Pod Security Policies (Deprecated) / Pod Security Standards",
            readOnlyHint=True,
        ),
    )
    def get_pod_security_info(
        namespace: Optional[str] = None,
        context: str = ""
    ) -> Dict[str, Any]:
        """Get Pod Security Standards information for namespaces.

        Args:
            namespace: Namespace to check (all namespaces if not specified)
            context: Kubernetes context to use (uses current context if not specified)
        """
        try:
            v1 = get_k8s_client(context)

            if namespace:
                namespaces = [v1.read_namespace(namespace)]
            else:
                namespaces = v1.list_namespace().items

            result = []
            for ns in namespaces:
                labels = ns.metadata.labels or {}
                pss_info = {
                    "namespace": ns.metadata.name,
                    "enforce": labels.get("pod-security.kubernetes.io/enforce"),
                    "enforceVersion": labels.get("pod-security.kubernetes.io/enforce-version"),
                    "audit": labels.get("pod-security.kubernetes.io/audit"),
                    "auditVersion": labels.get("pod-security.kubernetes.io/audit-version"),
                    "warn": labels.get("pod-security.kubernetes.io/warn"),
                    "warnVersion": labels.get("pod-security.kubernetes.io/warn-version")
                }
                if any(v for k, v in pss_info.items() if k != "namespace"):
                    result.append(pss_info)

            return {
                "success": True,
                "context": context or "current",
                "note": "Pod Security Policies are deprecated. Using Pod Security Standards (PSS) labels.",
                "namespacesWithPSS": result
            }
        except Exception as e:
            logger.error(f"Error getting pod security info: {e}")
            return {"success": False, "error": str(e)}
