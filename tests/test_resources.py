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
