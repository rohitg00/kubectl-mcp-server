"""Toolsets: which tools are registered, and the guidance sent to the model.

Only enabled toolsets are registered; disabled tools do not exist on the server.
The default set stays small so it fits in context and stays prompt-cache stable.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Set


@dataclass(frozen=True)
class Toolset:
    description: str
    default: bool = False
    official_servers: List[str] = field(default_factory=list)


TOOLSETS: Dict[str, Toolset] = {
    "core": Toolset("Generic kubectl operations for every resource kind, including CRDs", default=True),
    "helm": Toolset("Helm release lifecycle", default=True),
    "helm_dev": Toolset("Helm charts and repositories: search, show, template, lint, package, dependencies"),
    "ops": Toolset("Maintenance: create, label, annotate, taint, cordon/drain, copy files, wait, cleanup"),
    "diagnostics": Toolset("Network, DNS, node and pod health diagnostics"),
    "security": Toolset("RBAC, pod security and secret hygiene audits"),
    "cost": Toolset("Resource right-sizing and cost allocation"),
    "multicluster": Toolset("Kubeconfig contexts and cross-cluster queries"),
    "crds": Toolset("CRD discovery and custom resource inspection"),
    "gitops": Toolset("Flux and Argo CD", official_servers=[
        "Argo CD: https://github.com/argoproj-labs/mcp-for-argocd",
        "Flux: https://fluxoperator.dev/mcp-server/",
    ]),
    "certs": Toolset("cert-manager certificates and issuers"),
    "policy": Toolset("Kyverno and Gatekeeper policies", official_servers=[
        "Kyverno: https://github.com/nirmata/kyverno-mcp",
    ]),
    "backup": Toolset("Velero backups and restores"),
    "keda": Toolset("KEDA event-driven autoscaling"),
    "cilium": Toolset("Cilium network policies and Hubble flows"),
    "rollouts": Toolset("Argo Rollouts and Flagger progressive delivery"),
    "capi": Toolset("Cluster API lifecycle"),
    "kubevirt": Toolset("KubeVirt virtual machines"),
    "istio": Toolset("Istio service mesh"),
    "kind": Toolset("kind local clusters (runs docker on the server host)"),
    "vind": Toolset("vCluster virtual clusters (runs vcluster on the server host)"),
}

DEFAULT_TOOLSETS = frozenset(name for name, ts in TOOLSETS.items() if ts.default)

_BY_TOOLSET: Dict[str, List[str]] = {
    "core": [
        "kubectl_get", "kubectl_describe", "kubectl_logs", "kubectl_top", "kubectl_explain", "get_api_resources",
        "kubectl_generic", "kubectl_apply", "kubectl_patch", "delete_resource", "kubectl_scale", "kubectl_rollout",
        "exec_in_pod", "list_contexts", "health_check", "diagnose_pod_crash", "detect_pending_pods", "detect_ecosystem",
    ],
    "helm": [
        "helm_list", "helm_status", "helm_get", "helm_history",
        "install_helm_chart", "upgrade_helm_chart", "uninstall_helm_chart", "helm_rollback",
    ],
    "helm_dev": [
        "helm_show", "helm_search_repo", "helm_search_hub", "helm_repo_list", "helm_repo_add", "helm_repo_remove",
        "helm_repo_update", "helm_test", "helm_lint", "helm_package", "helm_dependency_update", "helm_dependency_list",
        "helm_dependency_build", "helm_pull", "helm_create", "helm_template",
    ],
    "ops": [
        "kubectl_create", "kubectl_cp", "backup_resource", "label_resource", "annotate_resource", "taint_node",
        "wait_for_condition", "node_management", "cleanup_pods", "run_pod",
    ],
    "diagnostics": [
        "check_pod_health", "get_evicted_pods", "diagnose_network_connectivity", "check_dns_resolution",
        "trace_service_chain", "compare_namespaces", "get_nodes_summary", "node_logs", "node_stats_summary",
    ],
    "security": [
        "analyze_pod_security", "analyze_network_policies", "audit_rbac_permissions", "check_secrets_security",
        "get_pod_security_info",
    ],
    "cost": [
        "get_resource_recommendations", "get_idle_resources", "get_resource_quotas_usage", "get_cost_analysis",
        "get_overprovisioned_resources", "get_resource_trends", "get_namespace_cost_allocation",
        "optimize_resource_requests",
    ],
    "multicluster": [
        "get_context_details", "kubeconfig_view", "switch_context", "set_namespace_for_context",
        "multi_cluster_query", "multi_cluster_health", "multi_cluster_pod_count",
    ],
    "crds": ["discover_crds", "search_crds", "list_custom_resources", "get_custom_resource", "describe_crd"],
    "gitops": [
        "gitops_apps_list", "gitops_app_get", "gitops_app_sync", "gitops_app_status", "gitops_sources_list",
        "gitops_source_get",
    ],
    "certs": [
        "list_certs", "get_cert", "list_cert_issuers", "get_cert_issuer", "renew_cert", "explain_cert_status",
        "list_cert_challenges", "list_cert_requests",
    ],
    "policy": ["get_policy_list", "get_policy", "get_policy_violations", "explain_policy_denial", "audit_policies"],
    "backup": [
        "list_backups", "get_backup", "create_backup", "delete_backup", "list_restores", "create_restore",
        "get_restore", "list_backup_locations", "list_backup_schedules", "create_backup_schedule",
    ],
    "keda": [
        "keda_scaledobjects_list", "keda_scaledobject_get", "keda_scaledjobs_list", "keda_triggerauths_list",
        "keda_triggerauth_get", "keda_hpa_list",
    ],
    "cilium": [
        "cilium_list_policies", "cilium_get_policy", "cilium_list_endpoints", "cilium_list_identities",
        "cilium_list_nodes", "cilium_get_status", "get_hubble_flows",
    ],
    "rollouts": [
        "get_rollouts_list", "get_rollout", "get_rollout_status", "promote_rollout", "abort_rollout",
        "retry_rollout", "restart_rollout", "get_analysis_runs", "get_flagger_canaries", "get_flagger_canary",
    ],
    "capi": [
        "capi_list_clusters", "capi_get_cluster", "capi_list_machines", "capi_get_machine",
        "capi_list_machinedeployments", "capi_scale_machinedeployment", "capi_list_machinesets",
        "capi_list_machinehealthchecks", "capi_list_clusterclasses", "capi_get_cluster_kubeconfig",
    ],
    "kubevirt": [
        "kubevirt_vms_list", "kubevirt_vm_get", "kubevirt_vmis_list", "kubevirt_vm_start", "kubevirt_vm_stop",
        "kubevirt_vm_restart", "kubevirt_vm_pause", "kubevirt_vm_unpause", "kubevirt_vm_migrate",
        "kubevirt_datasources_list", "kubevirt_instancetypes_list", "kubevirt_datavolumes_list",
    ],
    "istio": [
        "istio_virtualservices_list", "istio_virtualservice_get", "istio_destinationrules_list",
        "istio_gateways_list", "istio_peerauthentications_list", "istio_authorizationpolicies_list",
        "istio_proxy_status", "istio_analyze", "istio_sidecar_status",
    ],
    "kind": [
        "kind_list_clusters", "kind_get_nodes", "kind_get_kubeconfig", "kind_export_logs", "kind_cluster_info",
        "kind_node_labels", "kind_create_cluster", "kind_delete_cluster", "kind_load_image",
        "kind_load_image_archive", "kind_build_node_image", "kind_set_kubeconfig", "kind_config_validate",
        "kind_config_generate", "kind_config_show", "kind_available_images", "kind_registry_create",
        "kind_registry_connect", "kind_registry_status", "kind_node_exec", "kind_node_logs", "kind_node_inspect",
        "kind_node_restart", "kind_network_inspect", "kind_port_mappings", "kind_ingress_setup",
        "kind_cluster_status", "kind_images_list", "kind_provider_info",
    ],
    "vind": [
        "vind_list_clusters", "vind_status", "vind_get_kubeconfig", "vind_create_cluster", "vind_delete_cluster",
        "vind_pause", "vind_resume", "vind_connect", "vind_disconnect", "vind_upgrade", "vind_describe",
    ],
}

TOOL_TOOLSET: Dict[str, str] = {tool: ts for ts, tools in _BY_TOOLSET.items() for tool in tools}

CRD_GROUP_TOOLSET = {
    "flux": "gitops", "argocd": "gitops", "certmanager": "certs", "kyverno": "policy", "gatekeeper": "policy",
    "velero": "backup", "keda": "keda", "cilium": "cilium", "istio": "istio", "argorollouts": "rollouts",
    "kubevirt": "kubevirt", "capi": "capi",
}


def resolve_toolsets(spec: Optional[str]) -> Set[str]:
    """Parse a toolset spec such as "default,gitops" or "all"; unknown names raise ValueError."""
    names = [n.strip().lower() for n in (spec or "default").split(",") if n.strip()]
    enabled: Set[str] = set()
    for name in names or ["default"]:
        if name == "all":
            enabled |= set(TOOLSETS)
        elif name == "default":
            enabled |= DEFAULT_TOOLSETS
        elif name in TOOLSETS:
            enabled.add(name)
        else:
            raise ValueError(f"Unknown toolset '{name}'. Available: default, all, {', '.join(TOOLSETS)}")
    return enabled


class ToolsetServer:
    """Wraps a FastMCP server so tool decorators only register tools of enabled toolsets."""

    def __init__(self, server, enabled: Iterable[str]):
        self._server = server
        self.enabled = frozenset(enabled)
        self.registered: List[str] = []

    def tool(self, name_or_fn: Optional[Callable] = None, **kwargs):
        def decorator(fn: Callable) -> Callable:
            name = kwargs.get("name") or fn.__name__
            toolset = TOOL_TOOLSET.get(name)
            if toolset is None:
                raise KeyError(f"Tool '{name}' is not assigned to a toolset in kubectl_mcp_tool/toolsets.py")
            if toolset not in self.enabled:
                return fn
            options = {**kwargs, "tags": set(kwargs.get("tags") or ()) | {toolset}}
            self.registered.append(name)
            return self._server.tool(**options)(fn)

        return decorator(name_or_fn) if callable(name_or_fn) else decorator

    def __getattr__(self, item):
        return getattr(self._server, item)


def build_instructions(enabled: Iterable[str]) -> str:
    enabled = set(enabled)
    disabled = [n for n in TOOLSETS if n not in enabled]
    lines = [
        "Kubernetes operations through kubectl and Helm.",
        "Start with kubectl_get for any resource kind (including CRDs) and kubectl_describe or kubectl_logs to dig in;",
        "use diagnose_pod_crash and detect_pending_pods for failing workloads. Every tool accepts an optional",
        "`context` to target another kubeconfig context. Prefer label_selector/field_selector over listing everything.",
        "Call detect_ecosystem to see which operators are installed and which toolsets or dedicated MCP servers fit.",
    ]
    if disabled:
        lines.append(
            "Not loaded (operator enables with --toolsets / MCP_TOOLSETS): "
            + ", ".join(f"{n} ({TOOLSETS[n].description})" for n in disabled) + "."
        )
    official = [s for n in TOOLSETS for s in TOOLSETS[n].official_servers]
    lines.append("For deep Argo CD, Flux or Kyverno work, the project-maintained MCP servers are a better fit: " + "; ".join(official) + ".")
    return "\n".join(lines)
