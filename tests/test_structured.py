import pytest
from pydantic import ValidationError

from kubectl_mcp_tool.structured import structured_response
from kubectl_mcp_tool.schemas import (
    GetPodsResponse,
    GetLogsResponse,
    GetPodEventsResponse,
    CheckPodHealthResponse,
    GetDeploymentsResponse,
    DeploymentHistoryResponse,
    CheckDeploymentHealthResponse,
    GetNamespacesResponse,
    GetConfigMapsResponse,
    GetServicesResponse,
    GetNodesSummaryResponse,
    ListContextsResponse,
    GetIngressResponse,
    GetStorageClassesResponse,
    GetPVCsResponse,
    AnalyzeNetworkPoliciesResponse,
    GetRBACRolesResponse,
    HelmListResponse,
    HelmStatusResponse,
    GetCostAnalysisResponse,
)


class TestStructuredResponse:

    def test_valid_data(self):
        data = {
            "success": True,
            "context": "current",
            "pods": [{"name": "nginx", "namespace": "default", "status": "Running", "ip": "10.0.0.1"}],
        }
        result = structured_response(data, GetPodsResponse)
        assert result["success"] is True
        assert result["pods"][0]["name"] == "nginx"

    def test_invalid_data_raises(self):
        data = {"success": "not-a-bool", "context": 123}
        with pytest.raises(ValidationError):
            structured_response(data, GetPodsResponse)

    def test_extra_fields_stripped(self):
        data = {
            "success": True,
            "context": "current",
            "logs": "line1\nline2",
            "extra_field": "should be stripped",
        }
        result = structured_response(data, GetLogsResponse)
        assert "extra_field" not in result
        assert result["logs"] == "line1\nline2"


class TestGetPodsResponse:

    def test_full_data(self):
        data = {
            "success": True,
            "context": "minikube",
            "pods": [
                {"name": "web-1", "namespace": "default", "status": "Running", "ip": "10.0.0.1"},
                {"name": "db-1", "namespace": "prod", "status": "Pending", "ip": None},
            ],
        }
        result = structured_response(data, GetPodsResponse)
        assert len(result["pods"]) == 2
        assert result["pods"][1]["ip"] is None

    def test_empty_pods(self):
        data = {"success": True, "context": "current", "pods": []}
        result = structured_response(data, GetPodsResponse)
        assert result["pods"] == []


class TestGetLogsResponse:

    def test_sample(self):
        data = {"success": True, "context": "current", "logs": "2024-01-01 INFO started"}
        result = structured_response(data, GetLogsResponse)
        assert result["logs"] == "2024-01-01 INFO started"


class TestGetPodEventsResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "events": [
                {"name": "evt-1", "type": "Normal", "reason": "Pulled", "message": "image pulled", "timestamp": "2024-01-01T00:00:00"},
                {"name": "evt-2", "type": None, "reason": None, "message": None, "timestamp": None},
            ],
        }
        result = structured_response(data, GetPodEventsResponse)
        assert len(result["events"]) == 2
        assert result["events"][1]["type"] is None


class TestCheckPodHealthResponse:

    def test_sample(self):
        data = {"success": True, "context": "current", "phase": "Running", "conditions": ["Ready", "Initialized"]}
        result = structured_response(data, CheckPodHealthResponse)
        assert result["phase"] == "Running"
        assert len(result["conditions"]) == 2

    def test_empty_conditions(self):
        data = {"success": True, "context": "current", "phase": "Pending", "conditions": []}
        result = structured_response(data, CheckPodHealthResponse)
        assert result["conditions"] == []


class TestGetDeploymentsResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "deployments": [
                {"name": "nginx", "namespace": "default", "replicas": 3, "ready": 3, "available": 3},
                {"name": "api", "namespace": "prod", "replicas": None, "ready": 0, "available": 0},
            ],
        }
        result = structured_response(data, GetDeploymentsResponse)
        assert result["deployments"][0]["replicas"] == 3
        assert result["deployments"][1]["replicas"] is None


class TestDeploymentHistoryResponse:

    def test_sample(self):
        data = {"success": True, "context": "current", "history": "REVISION  CHANGE-CAUSE\n1         initial"}
        result = structured_response(data, DeploymentHistoryResponse)
        assert "REVISION" in result["history"]


class TestCheckDeploymentHealthResponse:

    def test_healthy(self):
        data = {"success": True, "context": "current", "healthy": True, "message": "All replicas available"}
        result = structured_response(data, CheckDeploymentHealthResponse)
        assert result["healthy"] is True

    def test_unhealthy(self):
        data = {"success": True, "context": "current", "healthy": False, "message": "2/3 replicas ready"}
        result = structured_response(data, CheckDeploymentHealthResponse)
        assert result["healthy"] is False


class TestGetNamespacesResponse:

    def test_sample(self):
        data = {"success": True, "context": "current", "namespaces": ["default", "kube-system", "prod"]}
        result = structured_response(data, GetNamespacesResponse)
        assert len(result["namespaces"]) == 3


class TestGetConfigMapsResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "configmaps": [
                {"name": "cfg-1", "namespace": "default", "data": {"key": "value"}},
                {"name": "cfg-2", "namespace": "default", "data": None},
            ],
        }
        result = structured_response(data, GetConfigMapsResponse)
        assert result["configmaps"][0]["data"] == {"key": "value"}
        assert result["configmaps"][1]["data"] is None


class TestGetServicesResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "services": [
                {"name": "svc-1", "namespace": "default", "type": "ClusterIP", "cluster_ip": "10.96.0.1"},
                {"name": "svc-2", "namespace": "default", "type": "NodePort", "cluster_ip": None},
            ],
        }
        result = structured_response(data, GetServicesResponse)
        assert result["services"][0]["type"] == "ClusterIP"
        assert result["services"][1]["cluster_ip"] is None


class TestGetNodesSummaryResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "summary": {
                "total": 2,
                "ready": 1,
                "notReady": 1,
                "nodes": [
                    {
                        "name": "node-1",
                        "status": "Ready",
                        "roles": ["control-plane"],
                        "kubeletVersion": "v1.29.0",
                        "os": "Ubuntu 22.04",
                        "capacity": {"cpu": "4", "memory": "8Gi", "pods": "110"},
                    },
                    {
                        "name": "node-2",
                        "status": "NotReady",
                        "roles": [],
                        "kubeletVersion": None,
                        "os": None,
                        "capacity": {"cpu": None, "memory": None, "pods": None},
                    },
                ],
            },
        }
        result = structured_response(data, GetNodesSummaryResponse)
        assert result["summary"]["total"] == 2
        assert result["summary"]["nodes"][0]["capacity"]["cpu"] == "4"
        assert result["summary"]["nodes"][1]["os"] is None


class TestListContextsResponse:

    def test_sample(self):
        data = {
            "success": True,
            "contexts": ["minikube", "production", "staging"],
            "active_context": "minikube",
            "total": 3,
        }
        result = structured_response(data, ListContextsResponse)
        assert result["active_context"] == "minikube"
        assert result["total"] == 3

    def test_no_context_key(self):
        data = {
            "success": True,
            "contexts": [],
            "active_context": "default",
            "total": 0,
        }
        result = structured_response(data, ListContextsResponse)
        assert "context" not in result


class TestGetIngressResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "ingresses": [
                {
                    "name": "web-ingress",
                    "namespace": "default",
                    "ingressClassName": "nginx",
                    "rules": [
                        {
                            "host": "example.com",
                            "paths": [
                                {"path": "/", "pathType": "Prefix", "backend": {"serviceName": "web-svc", "servicePort": 80}},
                            ],
                        }
                    ],
                    "tls": [{"hosts": ["example.com"], "secretName": "tls-secret"}],
                }
            ],
        }
        result = structured_response(data, GetIngressResponse)
        assert result["ingresses"][0]["rules"][0]["host"] == "example.com"
        assert result["ingresses"][0]["tls"][0]["secretName"] == "tls-secret"

    def test_optional_tls(self):
        data = {
            "success": True,
            "context": "current",
            "ingresses": [
                {
                    "name": "simple",
                    "namespace": "default",
                    "ingressClassName": None,
                    "rules": [{"host": None, "paths": [{"path": None, "pathType": None, "backend": {"serviceName": None, "servicePort": None}}]}],
                    "tls": None,
                }
            ],
        }
        result = structured_response(data, GetIngressResponse)
        assert result["ingresses"][0]["tls"] is None
        assert result["ingresses"][0]["ingressClassName"] is None


class TestGetStorageClassesResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "storageClasses": [
                {
                    "name": "standard",
                    "provisioner": "kubernetes.io/no-provisioner",
                    "reclaimPolicy": "Delete",
                    "volumeBindingMode": "WaitForFirstConsumer",
                    "allowVolumeExpansion": True,
                    "default": True,
                },
                {
                    "name": "fast",
                    "provisioner": "ebs.csi.aws.com",
                    "reclaimPolicy": None,
                    "volumeBindingMode": None,
                    "allowVolumeExpansion": None,
                    "default": False,
                },
            ],
        }
        result = structured_response(data, GetStorageClassesResponse)
        assert result["storageClasses"][0]["default"] is True
        assert result["storageClasses"][1]["allowVolumeExpansion"] is None


class TestGetPVCsResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "pvcs": [
                {
                    "name": "data-vol",
                    "namespace": "default",
                    "status": "Bound",
                    "capacity": "10Gi",
                    "accessModes": ["ReadWriteOnce"],
                    "storageClass": "standard",
                    "volumeName": "pv-001",
                },
                {
                    "name": "tmp-vol",
                    "namespace": "default",
                    "status": "Pending",
                    "capacity": None,
                    "accessModes": None,
                    "storageClass": None,
                    "volumeName": None,
                },
            ],
        }
        result = structured_response(data, GetPVCsResponse)
        assert result["pvcs"][0]["capacity"] == "10Gi"
        assert result["pvcs"][1]["volumeName"] is None


class TestAnalyzeNetworkPoliciesResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "totalPolicies": 2,
            "protectedNamespaces": ["prod"],
            "unprotectedNamespaces": ["default", "staging"],
            "policies": [
                {"name": "deny-all", "namespace": "prod", "podSelector": {"app": "web"}, "policyTypes": ["Ingress", "Egress"]},
                {"name": "allow-dns", "namespace": "prod", "podSelector": None, "policyTypes": None},
            ],
        }
        result = structured_response(data, AnalyzeNetworkPoliciesResponse)
        assert result["totalPolicies"] == 2
        assert result["policies"][1]["podSelector"] is None


class TestGetRBACRolesResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "roles": [
                {
                    "name": "pod-reader",
                    "namespace": "default",
                    "rules": [
                        {"apiGroups": [""], "resources": ["pods"], "verbs": ["get", "list"]},
                    ],
                },
                {
                    "name": "cluster-admin",
                    "namespace": None,
                    "rules": [
                        {"apiGroups": None, "resources": None, "verbs": None},
                    ],
                },
            ],
        }
        result = structured_response(data, GetRBACRolesResponse)
        assert result["roles"][0]["rules"][0]["verbs"] == ["get", "list"]
        assert result["roles"][1]["namespace"] is None


class TestHelmListResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "releases": [
                {"name": "nginx", "namespace": "default", "revision": "1", "status": "deployed"},
            ],
            "count": 1,
        }
        result = structured_response(data, HelmListResponse)
        assert result["count"] == 1
        assert result["releases"][0]["name"] == "nginx"

    def test_empty_releases(self):
        data = {"success": True, "context": "current", "releases": [], "count": 0}
        result = structured_response(data, HelmListResponse)
        assert result["releases"] == []


class TestHelmStatusResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "status": {"name": "nginx", "info": {"status": "deployed"}, "version": 1},
        }
        result = structured_response(data, HelmStatusResponse)
        assert result["status"]["name"] == "nginx"


class TestGetCostAnalysisResponse:

    def test_sample(self):
        data = {
            "success": True,
            "context": "current",
            "note": "Cost estimates based on resource requests.",
            "byNamespace": [
                {"namespace": "default", "totalCpuMillicores": 500, "totalMemoryMi": 256.0, "podCount": 3},
            ],
            "topWorkloads": [
                {"namespace": "default", "pod": "api-1", "ownerKind": "ReplicaSet", "cpuMillicores": 200, "memoryMi": 128.0},
            ],
        }
        result = structured_response(data, GetCostAnalysisResponse)
        assert result["note"].startswith("Cost estimates")
        assert len(result["topWorkloads"]) == 1
