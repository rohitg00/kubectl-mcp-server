"""
Pytest configuration and shared fixtures for kubectl-mcp-server tests.
"""

import pytest
import json
import sys
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime


@pytest.fixture
def mock_kube_config():
    """Mock kubernetes config loading."""
    with patch("kubernetes.config.load_kube_config") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_kube_contexts():
    """Mock kubernetes contexts."""
    contexts = [
        {
            "name": "minikube",
            "context": {
                "cluster": "minikube",
                "user": "minikube",
                "namespace": "default"
            }
        },
        {
            "name": "production",
            "context": {
                "cluster": "prod-cluster",
                "user": "admin",
                "namespace": "production"
            }
        }
    ]
    active_context = contexts[0]

    with patch("kubernetes.config.list_kube_config_contexts") as mock:
        mock.return_value = (contexts, active_context)
        yield mock


@pytest.fixture
def mock_pod():
    """Create a mock Pod object."""
    pod = MagicMock()
    pod.metadata.name = "test-pod"
    pod.metadata.namespace = "default"
    pod.metadata.labels = {"app": "test"}
    pod.metadata.creation_timestamp = datetime.now()
    pod.status.phase = "Running"
    pod.status.pod_ip = "10.0.0.1"
    pod.status.conditions = []
    pod.spec.containers = [MagicMock(name="container1", image="nginx:latest")]
    pod.spec.node_name = "node-1"
    return pod


@pytest.fixture
def mock_deployment():
    """Create a mock Deployment object."""
    deployment = MagicMock()
    deployment.metadata.name = "test-deployment"
    deployment.metadata.namespace = "default"
    deployment.metadata.labels = {"app": "test"}
    deployment.metadata.creation_timestamp = datetime.now()
    deployment.spec.replicas = 3
    deployment.status.ready_replicas = 3
    deployment.status.available_replicas = 3
    deployment.status.replicas = 3
    return deployment


@pytest.fixture
def mock_service():
    """Create a mock Service object."""
    service = MagicMock()
    service.metadata.name = "test-service"
    service.metadata.namespace = "default"
    service.spec.type = "ClusterIP"
    service.spec.cluster_ip = "10.96.0.1"
    service.spec.ports = [MagicMock(port=80, target_port=8080, protocol="TCP")]
    return service


@pytest.fixture
def mock_node():
    """Create a mock Node object."""
    node = MagicMock()
    node.metadata.name = "test-node"
    node.metadata.labels = {"node-role.kubernetes.io/control-plane": ""}
    node.status.conditions = [MagicMock(type="Ready", status="True")]
    node.status.node_info.kubelet_version = "v1.28.0"
    node.status.node_info.os_image = "Ubuntu 22.04"
    node.status.node_info.architecture = "amd64"
    node.status.capacity = {"cpu": "4", "memory": "8Gi", "pods": "110"}
    node.status.allocatable = {"cpu": "3800m", "memory": "7Gi", "pods": "100"}
    return node


@pytest.fixture
def mock_namespace():
    """Create a mock Namespace object."""
    namespace = MagicMock()
    namespace.metadata.name = "test-namespace"
    namespace.metadata.labels = {"env": "test"}
    namespace.metadata.creation_timestamp = datetime.now()
    namespace.status.phase = "Active"
    return namespace


@pytest.fixture
def mock_configmap():
    """Create a mock ConfigMap object."""
    configmap = MagicMock()
    configmap.metadata.name = "test-configmap"
    configmap.metadata.namespace = "default"
    configmap.data = {"key1": "value1", "key2": "value2"}
    return configmap


@pytest.fixture
def mock_secret():
    """Create a mock Secret object."""
    secret = MagicMock()
    secret.metadata.name = "test-secret"
    secret.metadata.namespace = "default"
    secret.type = "Opaque"
    secret.data = {"password": "c2VjcmV0"}  # base64 encoded
    return secret


@pytest.fixture
def mock_core_v1_api(mock_pod, mock_service, mock_namespace, mock_configmap, mock_secret, mock_node):
    """Mock CoreV1Api."""
    api = MagicMock()

    # Pod methods
    api.list_namespaced_pod.return_value.items = [mock_pod]
    api.list_pod_for_all_namespaces.return_value.items = [mock_pod]
    api.read_namespaced_pod.return_value = mock_pod
    api.read_namespaced_pod_log.return_value = "Test log output"

    # Service methods
    api.list_namespaced_service.return_value.items = [mock_service]
    api.list_service_for_all_namespaces.return_value.items = [mock_service]
    api.read_namespaced_service.return_value = mock_service

    # Namespace methods
    api.list_namespace.return_value.items = [mock_namespace]
    api.read_namespace.return_value = mock_namespace
    api.create_namespace.return_value = mock_namespace

    # ConfigMap methods
    api.list_namespaced_config_map.return_value.items = [mock_configmap]
    api.read_namespaced_config_map.return_value = mock_configmap

    # Secret methods
    api.list_namespaced_secret.return_value.items = [mock_secret]
    api.read_namespaced_secret.return_value = mock_secret

    # Node methods
    api.list_node.return_value.items = [mock_node]
    api.read_node.return_value = mock_node

    # Events
    api.list_namespaced_event.return_value.items = []

    return api


@pytest.fixture
def mock_apps_v1_api(mock_deployment):
    """Mock AppsV1Api."""
    api = MagicMock()

    api.list_namespaced_deployment.return_value.items = [mock_deployment]
    api.list_deployment_for_all_namespaces.return_value.items = [mock_deployment]
    api.read_namespaced_deployment.return_value = mock_deployment
    api.read_namespaced_deployment_scale.return_value.spec.replicas = 3

    api.list_namespaced_stateful_set.return_value.items = []
    api.list_namespaced_daemon_set.return_value.items = []
    api.list_namespaced_replica_set.return_value.items = []

    return api


@pytest.fixture
def mock_networking_v1_api():
    """Mock NetworkingV1Api."""
    api = MagicMock()

    ingress = MagicMock()
    ingress.metadata.name = "test-ingress"
    ingress.metadata.namespace = "default"
    api.list_namespaced_ingress.return_value.items = [ingress]
    api.read_namespaced_ingress.return_value = ingress

    network_policy = MagicMock()
    network_policy.metadata.name = "test-policy"
    api.list_namespaced_network_policy.return_value.items = [network_policy]

    return api


@pytest.fixture
def mock_batch_v1_api():
    """Mock BatchV1Api."""
    api = MagicMock()

    job = MagicMock()
    job.metadata.name = "test-job"
    job.metadata.namespace = "default"
    api.list_namespaced_job.return_value.items = [job]

    cronjob = MagicMock()
    cronjob.metadata.name = "test-cronjob"
    api.list_namespaced_cron_job.return_value.items = [cronjob]

    return api


@pytest.fixture
def mock_version_api():
    """Mock VersionApi."""
    api = MagicMock()

    version_info = MagicMock()
    version_info.git_version = "v1.28.0"
    version_info.major = "1"
    version_info.minor = "28"
    version_info.platform = "linux/amd64"
    version_info.build_date = "2024-01-01T00:00:00Z"
    version_info.go_version = "go1.21.0"
    version_info.compiler = "gc"

    api.get_code.return_value = version_info
    return api


@pytest.fixture
def mock_kubectl_subprocess():
    """Mock subprocess calls for kubectl."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Command executed successfully",
            stderr=""
        )
        yield mock_run


@pytest.fixture
def mock_helm_subprocess():
    """Mock subprocess calls for helm."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {"name": "test-release", "namespace": "default", "status": "deployed"}
            ]),
            stderr=""
        )
        yield mock_run


@pytest.fixture
def mcp_server(mock_kube_config):
    """Create an MCPServer instance with mocked dependencies."""
    with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies") as mock_deps:
        mock_deps.return_value = True
        from kubectl_mcp_tool.mcp_server import MCPServer
        server = MCPServer(name="test-server")
        yield server


@pytest.fixture
def mock_all_kubernetes_apis(
    mock_kube_config,
    mock_kube_contexts,
    mock_core_v1_api,
    mock_apps_v1_api,
    mock_networking_v1_api,
    mock_batch_v1_api,
    mock_version_api
):
    """Patch all Kubernetes API clients."""
    with patch("kubernetes.client.CoreV1Api", return_value=mock_core_v1_api), \
         patch("kubernetes.client.AppsV1Api", return_value=mock_apps_v1_api), \
         patch("kubernetes.client.NetworkingV1Api", return_value=mock_networking_v1_api), \
         patch("kubernetes.client.BatchV1Api", return_value=mock_batch_v1_api), \
         patch("kubernetes.client.VersionApi", return_value=mock_version_api), \
         patch("kubernetes.client.ApiClient") as mock_api_client:

        mock_api_client.return_value.sanitize_for_serialization.return_value = {}

        yield {
            "core_v1": mock_core_v1_api,
            "apps_v1": mock_apps_v1_api,
            "networking_v1": mock_networking_v1_api,
            "batch_v1": mock_batch_v1_api,
            "version": mock_version_api,
        }


class MockResponse:
    """Mock HTTP response for testing."""
    def __init__(self, json_data: Dict, status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self.json_data


@pytest.fixture
def sample_pod_yaml():
    """Sample pod YAML for testing."""
    return """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
    - containerPort: 80
"""


@pytest.fixture
def sample_deployment_yaml():
    """Sample deployment YAML for testing."""
    return """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
"""


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
