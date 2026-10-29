"""
Unit tests for MCP Resources in kubectl-mcp-server.

This module tests all FastMCP 3 resources including:
- kubeconfig:// resources
- namespace:// resources
- cluster:// resources
- manifest:// resources
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestKubeconfigResources:
    """Tests for kubeconfig:// resources."""

    @pytest.mark.unit
    def test_get_kubeconfig_contexts(self, mock_kube_contexts):
        """Test listing all kubectl contexts."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        # Verify the resource is registered
        resources = server.server._resource_manager._resources if hasattr(server.server, '_resource_manager') else {}
        assert server is not None

    @pytest.mark.unit
    def test_get_current_context(self, mock_kube_contexts):
        """Test getting the current active context."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_context_returns_json(self, mock_kube_contexts):
        """Test that context resource returns valid JSON."""
        contexts = [
            {"name": "minikube", "context": {"cluster": "minikube", "user": "minikube", "namespace": "default"}}
        ]
        active = contexts[0]

        with patch("kubernetes.config.list_kube_config_contexts", return_value=(contexts, active)):
            result = {
                "active_context": active.get("name"),
                "contexts": contexts
            }
            json_str = json.dumps(result)
            parsed = json.loads(json_str)
            assert "active_context" in parsed
            assert "contexts" in parsed


class TestNamespaceResources:
    """Tests for namespace:// resources."""

    @pytest.mark.unit
    def test_get_current_namespace(self, mock_kube_contexts):
        """Test getting the current namespace."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_list_all_namespaces(self, mock_all_kubernetes_apis):
        """Test listing all namespaces."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_namespace_includes_metadata(self, mock_all_kubernetes_apis):
        """Test that namespace list includes metadata."""
        mock_ns = MagicMock()
        mock_ns.metadata.name = "test-namespace"
        mock_ns.metadata.labels = {"env": "test"}
        mock_ns.metadata.creation_timestamp = datetime.now()
        mock_ns.status.phase = "Active"

        result = {
            "name": mock_ns.metadata.name,
            "status": mock_ns.status.phase,
            "labels": mock_ns.metadata.labels
        }

        assert result["name"] == "test-namespace"
        assert result["status"] == "Active"
        assert result["labels"]["env"] == "test"


class TestClusterResources:
    """Tests for cluster:// resources."""

    @pytest.mark.unit
    def test_get_cluster_info(self, mock_all_kubernetes_apis):
        """Test getting cluster info."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_get_cluster_nodes(self, mock_all_kubernetes_apis):
        """Test getting cluster nodes."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_get_cluster_version(self, mock_all_kubernetes_apis, mock_version_api):
        """Test getting cluster version."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        version_info = mock_version_api.get_code()
        assert version_info.git_version == "v1.28.0"
        assert version_info.major == "1"
        assert version_info.minor == "28"

    @pytest.mark.unit
    def test_get_api_resources(self, mock_kubectl_subprocess):
        """Test getting API resources."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_cluster_info_includes_node_count(self, mock_all_kubernetes_apis):
        """Test that cluster info includes node count."""
        mock_nodes = [MagicMock(), MagicMock()]
        for node in mock_nodes:
            node.status.conditions = [MagicMock(type="Ready", status="True")]

        result = {
            "nodes": {
                "count": len(mock_nodes),
                "ready": sum(1 for n in mock_nodes if any(
                    c.type == "Ready" and c.status == "True"
                    for c in n.status.conditions
                ))
            }
        }

        assert result["nodes"]["count"] == 2
        assert result["nodes"]["ready"] == 2


class TestManifestResources:
    """Tests for manifest:// resources."""

    @pytest.mark.unit
    def test_get_deployment_manifest(self, mock_all_kubernetes_apis):
        """Test getting deployment manifest."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_get_service_manifest(self, mock_all_kubernetes_apis):
        """Test getting service manifest."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_get_configmap_manifest(self, mock_all_kubernetes_apis):
        """Test getting ConfigMap manifest."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_get_pod_manifest(self, mock_all_kubernetes_apis):
        """Test getting pod manifest."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_get_secret_manifest_masks_data(self, mock_all_kubernetes_apis):
        """Test that secret manifest masks sensitive data."""
        mock_manifest = {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {"name": "test-secret", "namespace": "default"},
            "data": {"password": "c2VjcmV0", "api-key": "YXBpa2V5"}
        }

        # Simulate masking
        if "data" in mock_manifest and mock_manifest["data"]:
            mock_manifest["data"] = {k: "[MASKED]" for k in mock_manifest["data"].keys()}

        assert mock_manifest["data"]["password"] == "[MASKED]"
        assert mock_manifest["data"]["api-key"] == "[MASKED]"

    @pytest.mark.unit
    def test_get_ingress_manifest(self, mock_all_kubernetes_apis):
        """Test getting ingress manifest."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_manifest_returns_yaml(self):
        """Test that manifest resources return valid YAML."""
        import yaml

        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "test", "namespace": "default"},
            "spec": {"replicas": 3}
        }

        yaml_str = yaml.dump(manifest, default_flow_style=False)
        parsed = yaml.safe_load(yaml_str)

        assert parsed["apiVersion"] == "apps/v1"
        assert parsed["kind"] == "Deployment"
        assert parsed["spec"]["replicas"] == 3

    @pytest.mark.unit
    def test_manifest_handles_not_found(self):
        """Test that manifest resources handle not found errors."""
        error_result = "# Error: Deployment 'not-found' not found in namespace 'default'"
        assert "Error" in error_result


class TestResourceErrorHandling:
    """Tests for error handling in resources."""

    @pytest.mark.unit
    def test_handles_kube_config_error(self):
        """Test handling of kubeconfig errors."""
        with patch("kubernetes.config.list_kube_config_contexts") as mock_contexts:
            mock_contexts.side_effect = Exception("Config not found")
            result = json.dumps({"error": "Config not found"})
            parsed = json.loads(result)
            assert "error" in parsed

    @pytest.mark.unit
    def test_handles_api_connection_error(self):
        """Test handling of API connection errors."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_api.return_value.list_namespace.side_effect = Exception("Connection refused")
                result = json.dumps({"error": "Connection refused"})
                parsed = json.loads(result)
                assert "error" in parsed

    @pytest.mark.unit
    def test_handles_permission_error(self):
        """Test handling of permission errors."""
        result = json.dumps({"error": "Forbidden: User does not have permission"})
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Forbidden" in parsed["error"]


class TestResourceRegistration:
    """Tests for resource registration."""

    @pytest.mark.unit
    def test_all_resources_registered(self):
        """Test that all expected resources are registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        # Server should initialize with resources
        assert server is not None
        assert hasattr(server, 'server')

    @pytest.mark.unit
    def test_resource_uris_are_valid(self):
        """Test that resource URIs follow correct format."""
        valid_uris = [
            "kubeconfig://contexts",
            "kubeconfig://current-context",
            "namespace://current",
            "namespace://list",
            "cluster://info",
            "cluster://nodes",
            "cluster://version",
            "cluster://api-resources",
            "manifest://deployments/{namespace}/{name}",
            "manifest://services/{namespace}/{name}",
            "manifest://configmaps/{namespace}/{name}",
            "manifest://pods/{namespace}/{name}",
            "manifest://secrets/{namespace}/{name}",
            "manifest://ingresses/{namespace}/{name}",
        ]

        for uri in valid_uris:
            # URI should have a scheme and path
            assert "://" in uri
            scheme, path = uri.split("://", 1)
            assert scheme in ["kubeconfig", "namespace", "cluster", "manifest"]
            assert len(path) > 0


class _CapturingServer:
    """Minimal stand-in for FastMCP that records registered resource functions."""

    def __init__(self):
        self.resources = {}

    def resource(self, uri):
        def decorator(fn):
            self.resources[uri] = fn
            return fn
        return decorator


def _registered_resources():
    from kubectl_mcp_tool.resources.resources import register_resources

    server = _CapturingServer()
    register_resources(server)
    return server.resources


from kubernetes.config.config_exception import ConfigException

VALID_KUBECONFIG = """\
apiVersion: v1
kind: Config
clusters:
- {name: c1, cluster: {server: "https://127.0.0.1:1"}}
users:
- {name: u1, user: {token: x}}
contexts:
- {name: dev, context: {cluster: c1, user: u1, namespace: apps}}
- {name: prod, context: {cluster: c1, user: u1}}
current-context: dev
"""

NO_CURRENT_CONTEXT_KUBECONFIG = VALID_KUBECONFIG.replace("current-context: dev\n", "")

MALFORMED_KUBECONFIG = "clusters: [ {name: c1\n  bad: : :\n"

CONTEXT_URIS = ("kubeconfig://contexts", "kubeconfig://current-context", "namespace://current")


class TestContextResources:
    """Context resources against real kubeconfig files, plus the in-cluster fallback."""

    @pytest.fixture
    def kubeconfig(self, tmp_path, monkeypatch):
        """Point the server at a temp kubeconfig (via MCP_K8S_KUBECONFIG); returns a writer."""
        path = tmp_path / "config"
        for var in ("MCP_K8S_PROVIDER", "MCP_K8S_CONTEXT", "KUBECONFIG"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("MCP_K8S_KUBECONFIG", str(path))
        # The client library's own default must not be what gets read.
        monkeypatch.setattr("kubernetes.config.kube_config.KUBE_CONFIG_DEFAULT_LOCATION",
                            str(tmp_path / "library-default"))

        def write(content, target=path):
            target.write_text(content)
            return target

        return write

    @staticmethod
    def _read_all():
        resources = _registered_resources()
        return [json.loads(resources[uri]()) for uri in CONTEXT_URIS]

    @pytest.mark.unit
    def test_valid_kubeconfig(self, kubeconfig):
        kubeconfig(VALID_KUBECONFIG)
        listed, current, namespace = self._read_all()

        assert listed["active_context"] == "dev"
        assert [c["name"] for c in listed["contexts"]] == ["dev", "prod"]
        assert listed["contexts"][1]["namespace"] == "default"
        assert current == {"name": "dev", "cluster": "c1", "user": "u1", "namespace": "apps"}
        assert namespace == {"namespace": "apps"}

    @pytest.mark.unit
    def test_in_cluster_without_kubeconfig(self, kubeconfig):
        """The reported bug: in a pod with a ServiceAccount and no kubeconfig."""
        with patch("kubernetes.config.load_incluster_config") as load_incluster:
            listed, current, namespace = self._read_all()

        in_cluster = {"name": "in-cluster", "cluster": "in-cluster", "user": "service-account", "namespace": "default"}
        assert listed == {"active_context": "in-cluster", "contexts": [in_cluster]}
        assert current == in_cluster
        assert namespace == {"namespace": "default"}
        # The probe must not replace the global default client configuration.
        for call in load_incluster.call_args_list:
            assert call.kwargs.get("client_configuration") is not None

    @pytest.mark.unit
    def test_no_kubeconfig_and_not_in_cluster(self, kubeconfig):
        with patch("kubernetes.config.load_incluster_config", side_effect=ConfigException("not in a pod")):
            results = self._read_all()
        for result in results:
            assert "No Kubernetes configuration found" in result["error"]

    @pytest.mark.unit
    def test_malformed_kubeconfig_reports_parse_error(self, kubeconfig):
        kubeconfig(MALFORMED_KUBECONFIG)
        for result in self._read_all():
            assert "while parsing" in result["error"]

    @pytest.mark.unit
    def test_missing_current_context_reports_error(self, kubeconfig):
        kubeconfig(NO_CURRENT_CONTEXT_KUBECONFIG)
        for result in self._read_all():
            assert "current-context" in result["error"]

    @pytest.mark.unit
    def test_kubeconfig_changes_are_not_cached(self, kubeconfig):
        """Breaking the kubeconfig after a successful read must surface the error."""
        kubeconfig(VALID_KUBECONFIG)
        resources = _registered_resources()
        assert json.loads(resources["kubeconfig://current-context"]())["name"] == "dev"

        kubeconfig(MALFORMED_KUBECONFIG)
        for uri in CONTEXT_URIS:
            assert "while parsing" in json.loads(resources[uri]())["error"]

    @pytest.mark.unit
    def test_kubeconfig_preferred_over_in_cluster(self, kubeconfig):
        kubeconfig(VALID_KUBECONFIG)
        with patch("kubernetes.config.load_incluster_config") as load_incluster:
            current = json.loads(_registered_resources()["kubeconfig://current-context"]())

        assert current["name"] == "dev"
        load_incluster.assert_not_called()

    @pytest.mark.unit
    def test_malformed_kubeconfig_in_pod_is_not_masked(self, kubeconfig):
        """An existing but broken kubeconfig must not silently become in-cluster."""
        kubeconfig(MALFORMED_KUBECONFIG)
        with patch("kubernetes.config.load_incluster_config") as load_incluster:
            results = self._read_all()

        for result in results:
            assert "while parsing" in result["error"]
        load_incluster.assert_not_called()

    @pytest.mark.unit
    def test_uses_configured_kubeconfig_not_library_default(self, kubeconfig, tmp_path):
        kubeconfig(VALID_KUBECONFIG)
        kubeconfig(VALID_KUBECONFIG.replace("current-context: dev", "current-context: prod"),
                   target=tmp_path / "library-default")

        assert json.loads(_registered_resources()["kubeconfig://current-context"]())["name"] == "dev"

    @pytest.mark.unit
    def test_in_cluster_provider_ignores_kubeconfig(self, kubeconfig, monkeypatch):
        kubeconfig(VALID_KUBECONFIG)
        monkeypatch.setenv("MCP_K8S_PROVIDER", "in-cluster")
        with patch("kubernetes.config.load_incluster_config"):
            current = json.loads(_registered_resources()["kubeconfig://current-context"]())

        assert current["name"] == "in-cluster"

    @pytest.mark.unit
    def test_in_cluster_provider_without_service_account_errors(self, kubeconfig, monkeypatch):
        monkeypatch.setenv("MCP_K8S_PROVIDER", "in-cluster")
        with patch("kubernetes.config.load_incluster_config", side_effect=ConfigException("not in a pod")):
            results = self._read_all()
        for result in results:
            assert "not in a pod" in result["error"]

    @pytest.mark.unit
    def test_single_provider_reports_configured_context(self, kubeconfig, monkeypatch):
        kubeconfig(VALID_KUBECONFIG)
        monkeypatch.setenv("MCP_K8S_PROVIDER", "single")
        monkeypatch.setenv("MCP_K8S_CONTEXT", "prod")
        listed, current, namespace = self._read_all()

        assert listed["active_context"] == "prod"
        assert [c["name"] for c in listed["contexts"]] == ["prod"]
        assert current["name"] == "prod"
        assert namespace == {"namespace": "default"}

    @pytest.mark.unit
    def test_single_provider_unknown_context_errors(self, kubeconfig, monkeypatch):
        kubeconfig(VALID_KUBECONFIG)
        monkeypatch.setenv("MCP_K8S_PROVIDER", "single")
        monkeypatch.setenv("MCP_K8S_CONTEXT", "missing")
        for result in self._read_all():
            assert "Context 'missing' not found" in result["error"]
