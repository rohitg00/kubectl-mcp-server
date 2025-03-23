"""
Security operations module for Kubernetes.
"""

import logging
from typing import Dict, Any, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException

logger = logging.getLogger(__name__)

class KubernetesSecurityOps:
    """Security operations for Kubernetes."""
    
    def __init__(self):
        """Initialize Kubernetes client."""
        try:
            config.load_kube_config()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            self.core_v1 = client.CoreV1Api()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def create_role(self, name: str, rules: List[Dict[str, Any]], namespace: str = "default") -> Dict[str, Any]:
        """Create a Role with specified rules."""
        try:
            role = self.rbac_v1.create_namespaced_role(
                namespace=namespace,
                body=client.V1Role(
                    metadata=client.V1ObjectMeta(name=name),
                    rules=rules
                )
            )
            return {
                "status": "success",
                "message": f"Role {name} created successfully",
                "role": role.metadata.name
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create Role: {e.reason}"
            }

    def create_cluster_role(self, name: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a ClusterRole with specified rules."""
        try:
            cluster_role = self.rbac_v1.create_cluster_role(
                body=client.V1ClusterRole(
                    metadata=client.V1ObjectMeta(name=name),
                    rules=rules
                )
            )
            return {
                "status": "success",
                "message": f"ClusterRole {name} created successfully",
                "cluster_role": cluster_role.metadata.name
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create ClusterRole: {e.reason}"
            }

    def create_role_binding(self, name: str, role_name: str, subject_name: str, 
                          subject_kind: str = "ServiceAccount", namespace: str = "default") -> Dict[str, Any]:
        """Create a RoleBinding."""
        try:
            role_binding = self.rbac_v1.create_namespaced_role_binding(
                namespace=namespace,
                body=client.V1RoleBinding(
                    metadata=client.V1ObjectMeta(name=name),
                    role_ref=client.V1RoleRef(
                        api_group="rbac.authorization.k8s.io",
                        kind="Role",
                        name=role_name
                    ),
                    subjects=[client.V1Subject(
                        kind=subject_kind,
                        name=subject_name,
                        namespace=namespace
                    )]
                )
            )
            return {
                "status": "success",
                "message": f"RoleBinding {name} created successfully",
                "role_binding": role_binding.metadata.name
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create RoleBinding: {e.reason}"
            }

    def create_cluster_role_binding(self, name: str, cluster_role_name: str, 
                                  subject_name: str, subject_kind: str = "ServiceAccount",
                                  subject_namespace: str = "default") -> Dict[str, Any]:
        """Create a ClusterRoleBinding."""
        try:
            cluster_role_binding = self.rbac_v1.create_cluster_role_binding(
                body=client.V1ClusterRoleBinding(
                    metadata=client.V1ObjectMeta(name=name),
                    role_ref=client.V1RoleRef(
                        api_group="rbac.authorization.k8s.io",
                        kind="ClusterRole",
                        name=cluster_role_name
                    ),
                    subjects=[client.V1Subject(
                        kind=subject_kind,
                        name=subject_name,
                        namespace=subject_namespace
                    )]
                )
            )
            return {
                "status": "success",
                "message": f"ClusterRoleBinding {name} created successfully",
                "cluster_role_binding": cluster_role_binding.metadata.name
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create ClusterRoleBinding: {e.reason}"
            }

    def create_service_account(self, name: str, namespace: str = "default", 
                             annotations: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a ServiceAccount."""
        try:
            service_account = self.core_v1.create_namespaced_service_account(
                namespace=namespace,
                body=client.V1ServiceAccount(
                    metadata=client.V1ObjectMeta(
                        name=name,
                        annotations=annotations
                    )
                )
            )
            return {
                "status": "success",
                "message": f"ServiceAccount {name} created successfully",
                "service_account": service_account.metadata.name
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to create ServiceAccount: {e.reason}"
            }

    def get_pod_security_policy(self, name: str) -> Dict[str, Any]:
        """Get PodSecurityPolicy details."""
        try:
            api = client.PolicyV1beta1Api()
            psp = api.read_pod_security_policy(name)
            return {
                "status": "success",
                "name": psp.metadata.name,
                "spec": {
                    "privileged": psp.spec.privileged,
                    "host_network": psp.spec.host_network,
                    "host_pid": psp.spec.host_pid,
                    "host_ipc": psp.spec.host_ipc,
                    "run_as_user": psp.spec.run_as_user.rule,
                    "fs_group": psp.spec.fs_group.rule,
                    "volumes": psp.spec.volumes
                }
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to get PodSecurityPolicy: {e.reason}"
            }

    def audit_rbac_permissions(self, namespace: str = None) -> Dict[str, Any]:
        """Audit RBAC permissions in a namespace or cluster-wide."""
        try:
            results = {
                "roles": [],
                "cluster_roles": [],
                "role_bindings": [],
                "cluster_role_bindings": []
            }

            # Get Roles
            if namespace:
                roles = self.rbac_v1.list_namespaced_role(namespace)
                for role in roles.items:
                    results["roles"].append({
                        "name": role.metadata.name,
                        "namespace": role.metadata.namespace,
                        "rules": role.rules
                    })

            # Get ClusterRoles
            cluster_roles = self.rbac_v1.list_cluster_role()
            for cr in cluster_roles.items:
                results["cluster_roles"].append({
                    "name": cr.metadata.name,
                    "rules": cr.rules
                })

            # Get RoleBindings
            if namespace:
                role_bindings = self.rbac_v1.list_namespaced_role_binding(namespace)
                for rb in role_bindings.items:
                    results["role_bindings"].append({
                        "name": rb.metadata.name,
                        "namespace": rb.metadata.namespace,
                        "role_ref": rb.role_ref.name,
                        "subjects": [{"kind": s.kind, "name": s.name, "namespace": s.namespace} 
                                   for s in rb.subjects]
                    })

            # Get ClusterRoleBindings
            cluster_role_bindings = self.rbac_v1.list_cluster_role_binding()
            for crb in cluster_role_bindings.items:
                results["cluster_role_bindings"].append({
                    "name": crb.metadata.name,
                    "role_ref": crb.role_ref.name,
                    "subjects": [{"kind": s.kind, "name": s.name, "namespace": s.namespace} 
                               for s in crb.subjects]
                })

            return {
                "status": "success",
                "audit_results": results
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to audit RBAC permissions: {e.reason}"
            }

    def check_pod_security_context(self, pod_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check pod security context for best practices."""
        security_issues = []
        recommendations = []

        # Check security context
        security_context = pod_spec.get("securityContext", {})
        container_specs = pod_spec.get("containers", [])

        # Pod-level security context checks
        if not security_context.get("runAsNonRoot", False):
            security_issues.append("Pod not configured to run as non-root")
            recommendations.append("Set runAsNonRoot: true in pod securityContext")

        if not security_context.get("seccompProfile"):
            security_issues.append("No SecComp profile configured")
            recommendations.append("Configure SecComp profile to restrict system calls")

        # Container-level security context checks
        for container in container_specs:
            container_security = container.get("securityContext", {})
            
            if container_security.get("privileged", False):
                security_issues.append(f"Container {container['name']} runs in privileged mode")
                recommendations.append(f"Remove privileged mode from container {container['name']}")

            if not container_security.get("readOnlyRootFilesystem", False):
                security_issues.append(f"Container {container['name']} has writable root filesystem")
                recommendations.append(f"Set readOnlyRootFilesystem: true for container {container['name']}")

            if container_security.get("allowPrivilegeEscalation", True):
                security_issues.append(f"Container {container['name']} allows privilege escalation")
                recommendations.append(f"Set allowPrivilegeEscalation: false for container {container['name']}")

        return {
            "status": "success" if not security_issues else "warning",
            "security_issues": security_issues,
            "recommendations": recommendations
        }

    def analyze_network_policies(self, namespace: str = None) -> Dict[str, Any]:
        """Analyze NetworkPolicies for security gaps."""
        try:
            networking_v1 = client.NetworkingV1Api()
            policies = (networking_v1.list_namespaced_network_policy(namespace)
                      if namespace else networking_v1.list_network_policy_for_all_namespaces())

            analysis = []
            for policy in policies.items:
                policy_analysis = {
                    "name": policy.metadata.name,
                    "namespace": policy.metadata.namespace,
                    "pod_selector": policy.spec.pod_selector,
                    "ingress_rules": [],
                    "egress_rules": [],
                    "warnings": []
                }

                # Analyze ingress rules
                if policy.spec.ingress:
                    for rule in policy.spec.ingress:
                        if not rule.from_:
                            policy_analysis["warnings"].append("Ingress rule allows traffic from all sources")
                        policy_analysis["ingress_rules"].append(self._analyze_network_rule(rule))

                # Analyze egress rules
                if policy.spec.egress:
                    for rule in policy.spec.egress:
                        if not rule.to:
                            policy_analysis["warnings"].append("Egress rule allows traffic to all destinations")
                        policy_analysis["egress_rules"].append(self._analyze_network_rule(rule, is_ingress=False))

                analysis.append(policy_analysis)

            return {
                "status": "success",
                "analysis": analysis
            }
        except ApiException as e:
            return {
                "status": "error",
                "error": f"Failed to analyze NetworkPolicies: {e.reason}"
            }

    @staticmethod
    def _analyze_network_rule(rule: Any, is_ingress: bool = True) -> Dict[str, Any]:
        """Analyze a single NetworkPolicy rule."""
        analysis = {
            "ports": [],
            "peers": [],
            "concerns": []
        }

        # Analyze ports
        if rule.ports:
            for port in rule.ports:
                port_info = {
                    "protocol": port.protocol if port.protocol else "TCP",
                    "port": port.port if hasattr(port, "port") else "all"
                }
                analysis["ports"].append(port_info)
                
                if not port.port:
                    analysis["concerns"].append("Rule allows all ports")

        # Analyze peers (from/to)
        peers = rule.from_ if is_ingress else rule.to
        if peers:
            for peer in peers:
                peer_info = {}
                if hasattr(peer, "ip_block"):
                    peer_info["type"] = "ipBlock"
                    peer_info["cidr"] = peer.ip_block.cidr
                    if peer.ip_block.except_:
                        peer_info["except"] = peer.ip_block.except_
                elif hasattr(peer, "namespace_selector"):
                    peer_info["type"] = "namespaceSelector"
                    peer_info["selector"] = peer.namespace_selector.match_labels
                elif hasattr(peer, "pod_selector"):
                    peer_info["type"] = "podSelector"
                    peer_info["selector"] = peer.pod_selector.match_labels
                
                analysis["peers"].append(peer_info)

        return analysis 