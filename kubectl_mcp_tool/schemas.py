from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PodItem(BaseModel):
    name: str
    namespace: str
    status: str
    ip: Optional[str] = None


class GetPodsResponse(BaseModel):
    success: bool
    context: str
    pods: List[PodItem]


class GetLogsResponse(BaseModel):
    success: bool
    context: str
    logs: str


class EventItem(BaseModel):
    name: str
    type: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None


class GetPodEventsResponse(BaseModel):
    success: bool
    context: str
    events: List[EventItem]


class CheckPodHealthResponse(BaseModel):
    success: bool
    context: str
    phase: str
    conditions: List[str]


class DeploymentItem(BaseModel):
    name: str
    namespace: str
    replicas: Optional[int] = None
    ready: int
    available: int


class GetDeploymentsResponse(BaseModel):
    success: bool
    context: str
    deployments: List[DeploymentItem]


class DeploymentHistoryResponse(BaseModel):
    success: bool
    context: str
    history: str


class CheckDeploymentHealthResponse(BaseModel):
    success: bool
    context: str
    healthy: bool
    message: str


class GetNamespacesResponse(BaseModel):
    success: bool
    context: str
    namespaces: List[str]


class ConfigMapItem(BaseModel):
    name: str
    namespace: str
    data: Optional[Dict[str, str]] = None


class GetConfigMapsResponse(BaseModel):
    success: bool
    context: str
    configmaps: List[ConfigMapItem]


class ServiceItem(BaseModel):
    name: str
    namespace: str
    type: str
    cluster_ip: Optional[str] = None


class GetServicesResponse(BaseModel):
    success: bool
    context: str
    services: List[ServiceItem]


class NodeCapacity(BaseModel):
    cpu: Optional[str] = None
    memory: Optional[str] = None
    pods: Optional[str] = None


class NodeSummaryItem(BaseModel):
    name: str
    status: str
    roles: List[str]
    kubeletVersion: Optional[str] = None
    os: Optional[str] = None
    capacity: NodeCapacity


class NodesSummary(BaseModel):
    total: int
    ready: int
    notReady: int
    nodes: List[NodeSummaryItem]


class GetNodesSummaryResponse(BaseModel):
    success: bool
    context: str
    summary: NodesSummary


class ListContextsResponse(BaseModel):
    success: bool
    contexts: List[Any]
    active_context: str
    total: int


class IngressBackend(BaseModel):
    serviceName: Optional[str] = None
    servicePort: Optional[int] = None


class IngressPath(BaseModel):
    path: Optional[str] = None
    pathType: Optional[str] = None
    backend: IngressBackend


class IngressRule(BaseModel):
    host: Optional[str] = None
    paths: List[IngressPath]


class IngressTLS(BaseModel):
    hosts: Optional[List[str]] = None
    secretName: Optional[str] = None


class IngressItem(BaseModel):
    name: str
    namespace: str
    ingressClassName: Optional[str] = None
    rules: List[IngressRule]
    tls: Optional[List[IngressTLS]] = None


class GetIngressResponse(BaseModel):
    success: bool
    context: str
    ingresses: List[IngressItem]


class StorageClassItem(BaseModel):
    name: str
    provisioner: str
    reclaimPolicy: Optional[str] = None
    volumeBindingMode: Optional[str] = None
    allowVolumeExpansion: Optional[bool] = None
    default: bool


class GetStorageClassesResponse(BaseModel):
    success: bool
    context: str
    storageClasses: List[StorageClassItem]


class PVCItem(BaseModel):
    name: str
    namespace: str
    status: str
    capacity: Optional[str] = None
    accessModes: Optional[List[str]] = None
    storageClass: Optional[str] = None
    volumeName: Optional[str] = None


class GetPVCsResponse(BaseModel):
    success: bool
    context: str
    pvcs: List[PVCItem]


class NetworkPolicyItem(BaseModel):
    name: str
    namespace: str
    podSelector: Optional[Dict[str, str]] = None
    policyTypes: Optional[List[str]] = None


class AnalyzeNetworkPoliciesResponse(BaseModel):
    success: bool
    context: str
    totalPolicies: int
    protectedNamespaces: List[str]
    unprotectedNamespaces: List[str]
    policies: List[NetworkPolicyItem]


class RBACRuleItem(BaseModel):
    apiGroups: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    verbs: Optional[List[str]] = None


class RBACRoleItem(BaseModel):
    name: str
    namespace: Optional[str] = None
    rules: List[RBACRuleItem]


class GetRBACRolesResponse(BaseModel):
    success: bool
    context: str
    roles: List[RBACRoleItem]


class HelmListResponse(BaseModel):
    success: bool
    context: str
    releases: List[Dict[str, Any]]
    count: int


class HelmStatusResponse(BaseModel):
    success: bool
    context: str
    status: Dict[str, Any]


class GetCostAnalysisResponse(BaseModel):
    success: bool
    context: str
    note: str
    byNamespace: Any
    topWorkloads: List[Dict[str, Any]]
