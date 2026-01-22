"""MCP OAuth 2.0 scope definitions for fine-grained access control."""

from enum import Enum
from typing import Dict, List, Set


class MCPScopes(str, Enum):
    """MCP OAuth 2.0 scopes."""

    # Base scopes
    READ = "mcp:read"
    WRITE = "mcp:write"
    ADMIN = "mcp:admin"
    TOOLS = "mcp:tools"

    # Category-specific scopes
    HELM = "mcp:helm"
    DIAGNOSTICS = "mcp:diagnostics"
    NETWORKING = "mcp:networking"
    STORAGE = "mcp:storage"
    SECURITY = "mcp:security"
    COST = "mcp:cost"

    @classmethod
    def all_scopes(cls) -> List[str]:
        """Return all available scopes."""
        return [scope.value for scope in cls]

    @classmethod
    def read_scopes(cls) -> List[str]:
        """Return scopes for read-only access."""
        return [cls.READ.value, cls.DIAGNOSTICS.value]

    @classmethod
    def write_scopes(cls) -> List[str]:
        """Return scopes for write access."""
        return [cls.READ.value, cls.WRITE.value]

    @classmethod
    def admin_scopes(cls) -> List[str]:
        """Return scopes for admin access."""
        return cls.all_scopes()


# Map tool names to required scopes
# Tools not in this map require the default scope (mcp:tools)
TOOL_SCOPES: Dict[str, Set[str]] = {
    # Read-only tools - require mcp:read
    "get_pods": {MCPScopes.READ.value},
    "get_pod_details": {MCPScopes.READ.value},
    "list_namespaces": {MCPScopes.READ.value},
    "get_deployments": {MCPScopes.READ.value},
    "get_services": {MCPScopes.READ.value},
    "get_nodes": {MCPScopes.READ.value},
    "get_events": {MCPScopes.READ.value},
    "get_configmaps": {MCPScopes.READ.value},
    "describe_resource": {MCPScopes.READ.value},
    "get_cluster_info": {MCPScopes.READ.value},
    "get_api_resources": {MCPScopes.READ.value},
    "get_api_versions": {MCPScopes.READ.value},
    "get_resource_usage": {MCPScopes.READ.value},
    "get_pod_logs": {MCPScopes.READ.value},

    # Write tools - require mcp:write
    "create_namespace": {MCPScopes.WRITE.value},
    "delete_namespace": {MCPScopes.WRITE.value, MCPScopes.ADMIN.value},
    "scale_deployment": {MCPScopes.WRITE.value},
    "restart_deployment": {MCPScopes.WRITE.value},
    "delete_pod": {MCPScopes.WRITE.value},
    "apply_manifest": {MCPScopes.WRITE.value},
    "delete_resource": {MCPScopes.WRITE.value},
    "patch_resource": {MCPScopes.WRITE.value},
    "create_configmap": {MCPScopes.WRITE.value},
    "update_configmap": {MCPScopes.WRITE.value},
    "delete_configmap": {MCPScopes.WRITE.value},
    "create_secret": {MCPScopes.WRITE.value, MCPScopes.ADMIN.value},
    "delete_secret": {MCPScopes.WRITE.value, MCPScopes.ADMIN.value},

    # Admin tools - require mcp:admin
    "get_rbac_roles": {MCPScopes.ADMIN.value, MCPScopes.SECURITY.value},
    "get_cluster_roles": {MCPScopes.ADMIN.value, MCPScopes.SECURITY.value},
    "audit_rbac_permissions": {MCPScopes.ADMIN.value, MCPScopes.SECURITY.value},
    "analyze_pod_security": {MCPScopes.ADMIN.value, MCPScopes.SECURITY.value},
    "check_secrets_security": {MCPScopes.ADMIN.value, MCPScopes.SECURITY.value},
    "get_pod_security_info": {MCPScopes.ADMIN.value, MCPScopes.SECURITY.value},
    "cordon_node": {MCPScopes.ADMIN.value},
    "uncordon_node": {MCPScopes.ADMIN.value},
    "drain_node": {MCPScopes.ADMIN.value},
    "taint_node": {MCPScopes.ADMIN.value},

    # Helm tools - require mcp:helm
    "helm_list_releases": {MCPScopes.HELM.value, MCPScopes.READ.value},
    "helm_get_values": {MCPScopes.HELM.value, MCPScopes.READ.value},
    "helm_get_manifest": {MCPScopes.HELM.value, MCPScopes.READ.value},
    "helm_install": {MCPScopes.HELM.value, MCPScopes.WRITE.value},
    "helm_upgrade": {MCPScopes.HELM.value, MCPScopes.WRITE.value},
    "helm_uninstall": {MCPScopes.HELM.value, MCPScopes.WRITE.value},
    "helm_rollback": {MCPScopes.HELM.value, MCPScopes.WRITE.value},
    "helm_repo_add": {MCPScopes.HELM.value, MCPScopes.WRITE.value},
    "helm_repo_list": {MCPScopes.HELM.value, MCPScopes.READ.value},
    "helm_search": {MCPScopes.HELM.value, MCPScopes.READ.value},

    # Diagnostic tools - require mcp:diagnostics
    "run_pod_diagnostics": {MCPScopes.DIAGNOSTICS.value},
    "check_pod_health": {MCPScopes.DIAGNOSTICS.value},
    "analyze_crashloopbackoff": {MCPScopes.DIAGNOSTICS.value},
    "diagnose_pending_pods": {MCPScopes.DIAGNOSTICS.value},
    "check_resource_quotas": {MCPScopes.DIAGNOSTICS.value},
    "analyze_network_policies": {MCPScopes.DIAGNOSTICS.value, MCPScopes.NETWORKING.value},
    "get_cluster_health": {MCPScopes.DIAGNOSTICS.value},

    # Networking tools - require mcp:networking
    "get_network_policies": {MCPScopes.NETWORKING.value, MCPScopes.READ.value},
    "get_ingresses": {MCPScopes.NETWORKING.value, MCPScopes.READ.value},
    "test_service_connectivity": {MCPScopes.NETWORKING.value, MCPScopes.DIAGNOSTICS.value},

    # Storage tools - require mcp:storage
    "get_persistent_volumes": {MCPScopes.STORAGE.value, MCPScopes.READ.value},
    "get_persistent_volume_claims": {MCPScopes.STORAGE.value, MCPScopes.READ.value},
    "get_storage_classes": {MCPScopes.STORAGE.value, MCPScopes.READ.value},
    "analyze_storage_usage": {MCPScopes.STORAGE.value, MCPScopes.DIAGNOSTICS.value},

    # Cost tools - require mcp:cost
    "estimate_workload_cost": {MCPScopes.COST.value},
    "get_resource_recommendations": {MCPScopes.COST.value, MCPScopes.DIAGNOSTICS.value},
    "analyze_resource_efficiency": {MCPScopes.COST.value, MCPScopes.DIAGNOSTICS.value},
}


def get_required_scopes(tool_name: str) -> Set[str]:
    """Get required scopes for a tool."""
    return TOOL_SCOPES.get(tool_name, {MCPScopes.TOOLS.value})


def has_required_scopes(token_scopes: Set[str], tool_name: str) -> bool:
    """Check if token has required scopes for a tool."""
    required = get_required_scopes(tool_name)

    # mcp:tools grants access to all tools
    if MCPScopes.TOOLS.value in token_scopes:
        return True

    # mcp:admin grants access to all tools
    if MCPScopes.ADMIN.value in token_scopes:
        return True

    # Check if token has at least one of the required scopes
    return bool(token_scopes & required)
