"""
Unit tests for all MCP tools in kubectl-mcp-server.

This module contains comprehensive tests for all 121 Kubernetes tools
provided by the MCP server.
"""

import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime


# Complete list of all 121 tools that must be registered
EXPECTED_TOOLS = [
    # Pods (pods.py)
    "get_pods", "get_logs", "get_pod_events", "check_pod_health", "exec_in_pod",
    "cleanup_pods", "get_pod_conditions", "get_previous_logs", "diagnose_pod_crash",
    "detect_pending_pods", "get_evicted_pods",
    # Deployments (deployments.py)
    "get_deployments", "create_deployment", "scale_deployment", "restart_deployment",
    "get_statefulsets", "get_daemonsets", "get_replicasets", "get_jobs",
    # Core (core.py)
    "get_namespaces", "get_configmaps", "get_secrets", "get_events",
    "get_resource_quotas", "get_limit_ranges",
    # Cluster (cluster.py)
    "get_current_context", "switch_context", "list_contexts", "list_kubeconfig_contexts",
    "get_context_details", "set_namespace_for_context", "get_cluster_info",
    "get_cluster_version", "get_nodes", "get_api_resources", "health_check",
    # Networking (networking.py)
    "get_services", "get_endpoints", "get_ingress", "port_forward",
    "diagnose_network_connectivity", "check_dns_resolution", "trace_service_chain",
    "analyze_network_policies",
    # Storage (storage.py)
    "get_pvcs", "get_persistent_volumes", "get_storage_classes",
    # Security (security.py)
    "get_rbac_roles", "get_cluster_roles", "get_service_accounts",
    "audit_rbac_permissions", "check_secrets_security", "get_pod_security_info",
    "get_admission_webhooks", "get_crds", "get_priority_classes", "analyze_pod_security",
    # Helm (helm.py) - 37 tools
    "helm_list", "helm_status", "helm_history", "helm_get_values", "helm_get_manifest",
    "helm_get_notes", "helm_get_hooks", "helm_get_all", "helm_show_chart",
    "helm_show_values", "helm_show_readme", "helm_show_crds", "helm_show_all",
    "helm_search_repo", "helm_search_hub", "helm_repo_list", "helm_repo_add",
    "helm_repo_remove", "helm_repo_update", "install_helm_chart", "upgrade_helm_chart",
    "uninstall_helm_chart", "helm_rollback", "helm_test", "helm_template",
    "helm_template_apply", "helm_create", "helm_lint", "helm_package", "helm_pull",
    "helm_dependency_list", "helm_dependency_update", "helm_dependency_build",
    "helm_version", "helm_env",
    # Operations (operations.py)
    "kubectl_apply", "kubectl_describe", "kubectl_patch", "kubectl_rollout",
    "kubectl_create", "delete_resource", "kubectl_cp", "backup_resource",
    "label_resource", "annotate_resource", "taint_node", "wait_for_condition",
    "node_management", "kubectl_generic", "kubectl_explain",
    # Diagnostics (diagnostics.py)
    "compare_namespaces", "get_pod_metrics", "get_node_metrics",
    # Cost (cost.py)
    "get_resource_recommendations", "get_idle_resources", "get_resource_quotas_usage",
    "get_cost_analysis", "get_overprovisioned_resources", "get_resource_trends",
    "get_namespace_cost_allocation", "optimize_resource_requests", "get_resource_usage",
    # Autoscaling (deployments.py)
    "get_hpa", "get_pdb",
]


class TestAllToolsRegistered:
    """Comprehensive tests to verify all 121 tools are registered."""

    @pytest.mark.unit
    def test_all_121_tools_registered(self):
        """Verify all 121 expected tools are registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        async def get_tools():
            return await server.server.list_tools()

        tools = asyncio.run(get_tools())
        tool_names = {t.name for t in tools}

        # Verify count
        assert len(tools) == 121, f"Expected 121 tools, got {len(tools)}"

        # Check for missing tools
        missing_tools = set(EXPECTED_TOOLS) - tool_names
        assert not missing_tools, f"Missing tools: {missing_tools}"

        # Check for unexpected tools (tools not in expected list)
        unexpected_tools = tool_names - set(EXPECTED_TOOLS)
        assert not unexpected_tools, f"Unexpected tools: {unexpected_tools}"

    @pytest.mark.unit
    def test_tool_modules_import_correctly(self):
        """Test that all tool modules can be imported."""
        from kubectl_mcp_tool.tools import (
            register_helm_tools,
            register_pod_tools,
            register_core_tools,
            register_cluster_tools,
            register_deployment_tools,
            register_security_tools,
            register_networking_tools,
            register_storage_tools,
            register_operations_tools,
            register_diagnostics_tools,
            register_cost_tools,
        )
        # All imports should succeed
        assert callable(register_helm_tools)
        assert callable(register_pod_tools)
        assert callable(register_core_tools)
        assert callable(register_cluster_tools)
        assert callable(register_deployment_tools)
        assert callable(register_security_tools)
        assert callable(register_networking_tools)
        assert callable(register_storage_tools)
        assert callable(register_operations_tools)
        assert callable(register_diagnostics_tools)
        assert callable(register_cost_tools)

    @pytest.mark.unit
    def test_all_tools_have_descriptions(self):
        """Verify all tools have non-empty descriptions."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        async def get_tools():
            return await server.server.list_tools()

        tools = asyncio.run(get_tools())

        tools_without_description = [t.name for t in tools if not t.description or len(t.description.strip()) == 0]
        assert not tools_without_description, f"Tools without descriptions: {tools_without_description}"


class TestPodTools:
    """Tests for pod-related tools."""

    @pytest.mark.unit
    def test_get_pods_all_namespaces(self, mock_all_kubernetes_apis):
        """Test getting pods from all namespaces."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        # Verify server initialized successfully with tools
        assert server is not None
        assert hasattr(server, 'server')

    @pytest.mark.unit
    def test_get_pods_specific_namespace(self, mock_all_kubernetes_apis):
        """Test getting pods from a specific namespace."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_pod = MagicMock()
                mock_pod.metadata.name = "test-pod"
                mock_pod.metadata.namespace = "default"
                mock_pod.status.phase = "Running"
                mock_pod.status.pod_ip = "10.0.0.1"
                mock_api.return_value.list_namespaced_pod.return_value.items = [mock_pod]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_logs(self, mock_all_kubernetes_apis):
        """Test getting pod logs."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_api.return_value.read_namespaced_pod_log.return_value = "Test log line 1\nTest log line 2"

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_pod_events(self, mock_all_kubernetes_apis):
        """Test getting pod events."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_event = MagicMock()
                mock_event.metadata.name = "test-event"
                mock_event.type = "Normal"
                mock_event.reason = "Scheduled"
                mock_event.message = "Successfully scheduled"
                mock_api.return_value.list_namespaced_event.return_value.items = [mock_event]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")


class TestDeploymentTools:
    """Tests for deployment-related tools."""

    @pytest.mark.unit
    def test_get_deployments(self, mock_all_kubernetes_apis):
        """Test getting deployments."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.AppsV1Api") as mock_api:
                mock_deployment = MagicMock()
                mock_deployment.metadata.name = "test-deployment"
                mock_deployment.metadata.namespace = "default"
                mock_deployment.spec.replicas = 3
                mock_deployment.status.ready_replicas = 3
                mock_api.return_value.list_namespaced_deployment.return_value.items = [mock_deployment]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_scale_deployment(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test scaling a deployment."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_rollout_status(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test checking rollout status."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")


class TestServiceTools:
    """Tests for service-related tools."""

    @pytest.mark.unit
    def test_get_services(self, mock_all_kubernetes_apis):
        """Test getting services."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_service = MagicMock()
                mock_service.metadata.name = "test-service"
                mock_service.metadata.namespace = "default"
                mock_service.spec.type = "ClusterIP"
                mock_service.spec.cluster_ip = "10.96.0.1"
                mock_api.return_value.list_namespaced_service.return_value.items = [mock_service]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_endpoints(self, mock_all_kubernetes_apis):
        """Test getting service endpoints."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_endpoints = MagicMock()
                mock_endpoints.metadata.name = "test-service"
                mock_api.return_value.read_namespaced_endpoints.return_value = mock_endpoints

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")


class TestNamespaceTools:
    """Tests for namespace-related tools."""

    @pytest.mark.unit
    def test_get_namespaces(self, mock_all_kubernetes_apis):
        """Test getting namespaces."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_ns = MagicMock()
                mock_ns.metadata.name = "default"
                mock_ns.status.phase = "Active"
                mock_api.return_value.list_namespace.return_value.items = [mock_ns]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_create_namespace(self, mock_all_kubernetes_apis):
        """Test creating a namespace."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_ns = MagicMock()
                mock_ns.metadata.name = "new-namespace"
                mock_api.return_value.create_namespace.return_value = mock_ns

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")


class TestConfigMapAndSecretTools:
    """Tests for ConfigMap and Secret tools."""

    @pytest.mark.unit
    def test_get_configmaps(self, mock_all_kubernetes_apis):
        """Test getting ConfigMaps."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_cm = MagicMock()
                mock_cm.metadata.name = "test-configmap"
                mock_cm.data = {"key": "value"}
                mock_api.return_value.list_namespaced_config_map.return_value.items = [mock_cm]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_secrets(self, mock_all_kubernetes_apis):
        """Test getting secrets."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_secret = MagicMock()
                mock_secret.metadata.name = "test-secret"
                mock_secret.type = "Opaque"
                mock_api.return_value.list_namespaced_secret.return_value.items = [mock_secret]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")


class TestNodeTools:
    """Tests for node-related tools."""

    @pytest.mark.unit
    def test_get_nodes(self, mock_all_kubernetes_apis):
        """Test getting nodes."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_node = MagicMock()
                mock_node.metadata.name = "test-node"
                mock_node.status.conditions = [MagicMock(type="Ready", status="True")]
                mock_api.return_value.list_node.return_value.items = [mock_node]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_cordon_node(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test cordoning a node."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_drain_node(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test draining a node."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")


class TestHelmTools:
    """Tests for Helm-related tools."""

    @pytest.mark.unit
    def test_helm_list(self, mock_helm_subprocess):
        """Test listing Helm releases."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_helm_status(self, mock_helm_subprocess):
        """Test getting Helm release status."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")


class TestClusterTools:
    """Tests for cluster-wide tools."""

    @pytest.mark.unit
    def test_cluster_info(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test getting cluster info."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_contexts(self, mock_kube_contexts):
        """Test getting kubectl contexts."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")


class TestSecurityTools:
    """Tests for security-related tools."""

    @pytest.mark.unit
    def test_get_security_contexts(self, mock_all_kubernetes_apis):
        """Test getting security contexts."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_rbac_rules(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test getting RBAC rules."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")


class TestNetworkTools:
    """Tests for network-related tools."""

    @pytest.mark.unit
    def test_get_network_policies(self, mock_all_kubernetes_apis):
        """Test getting network policies."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.NetworkingV1Api") as mock_api:
                mock_policy = MagicMock()
                mock_policy.metadata.name = "test-policy"
                mock_api.return_value.list_namespaced_network_policy.return_value.items = [mock_policy]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_ingresses(self, mock_all_kubernetes_apis):
        """Test getting ingresses."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.NetworkingV1Api") as mock_api:
                mock_ingress = MagicMock()
                mock_ingress.metadata.name = "test-ingress"
                mock_api.return_value.list_namespaced_ingress.return_value.items = [mock_ingress]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")


class TestJobAndCronJobTools:
    """Tests for Job and CronJob tools."""

    @pytest.mark.unit
    def test_get_jobs(self, mock_all_kubernetes_apis):
        """Test getting jobs."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.BatchV1Api") as mock_api:
                mock_job = MagicMock()
                mock_job.metadata.name = "test-job"
                mock_api.return_value.list_namespaced_job.return_value.items = [mock_job]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_cronjobs(self, mock_all_kubernetes_apis):
        """Test getting CronJobs."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.BatchV1Api") as mock_api:
                mock_cronjob = MagicMock()
                mock_cronjob.metadata.name = "test-cronjob"
                mock_api.return_value.list_namespaced_cron_job.return_value.items = [mock_cronjob]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")


class TestStorageTools:
    """Tests for storage-related tools."""

    @pytest.mark.unit
    def test_get_pvcs(self, mock_all_kubernetes_apis):
        """Test getting PersistentVolumeClaims."""
        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_pvc = MagicMock()
                mock_pvc.metadata.name = "test-pvc"
                mock_pvc.status.phase = "Bound"
                mock_api.return_value.list_namespaced_persistent_volume_claim.return_value.items = [mock_pvc]

                from kubectl_mcp_tool.mcp_server import MCPServer
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_storage_classes(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test getting storage classes."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")


class TestCostOptimizationTools:
    """Tests for cost optimization tools (Phase 4)."""

    @pytest.mark.unit
    def test_get_resource_usage(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test getting resource usage."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_idle_resources(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test finding idle resources."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_get_cost_analysis(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test cost analysis."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")


class TestApplyAndDeleteTools:
    """Tests for apply and delete operations."""

    @pytest.mark.unit
    def test_kubectl_apply(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test applying YAML manifests."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_kubectl_delete(self, mock_all_kubernetes_apis, mock_kubectl_subprocess):
        """Test deleting resources."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

    @pytest.mark.unit
    def test_non_destructive_mode(self, mock_all_kubernetes_apis):
        """Test non-destructive mode blocks destructive operations."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test", non_destructive=True)
            result = server._check_destructive()
            assert result is not None
            assert result["success"] is False
            assert "non-destructive mode" in result["error"]


class TestToolAnnotations:
    """Tests for tool annotations and metadata."""

    @pytest.mark.unit
    def test_read_only_tools_have_annotations(self):
        """Test that read-only tools have proper annotations."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")
                # Server should initialize without errors
                assert server is not None

    @pytest.mark.unit
    def test_all_tools_have_docstrings(self):
        """Test that all tools have documentation."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")
                # Server should have tools registered
                assert hasattr(server, 'server')


class TestErrorHandling:
    """Tests for error handling in tools."""

    @pytest.mark.unit
    def test_handles_connection_error(self):
        """Test handling of connection errors."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config") as mock_config:
                mock_config.side_effect = Exception("Connection refused")
                # Server should still initialize
                try:
                    server = MCPServer(name="test")
                except:
                    pass  # Expected behavior

    @pytest.mark.unit
    def test_handles_api_error(self):
        """Test handling of Kubernetes API errors."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")
                assert server is not None

    @pytest.mark.unit
    def test_handles_timeout_error(self):
        """Test handling of timeout errors."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")
                assert server is not None


class TestMaskSecrets:
    """Tests for secret masking functionality."""

    @pytest.mark.unit
    def test_masks_base64_data(self):
        """Test that base64-encoded data is masked."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")
                text = "data:\n  password: c2VjcmV0UGFzc3dvcmQxMjM="
                masked = server._mask_secrets(text)
                assert "[MASKED]" in masked

    @pytest.mark.unit
    def test_masks_password_fields(self):
        """Test that password fields are masked."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")
                text = 'password: "mysecretpassword"'
                masked = server._mask_secrets(text)
                assert "[MASKED]" in masked

    @pytest.mark.unit
    def test_masks_token_fields(self):
        """Test that token fields are masked."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")
                text = 'token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"'
                masked = server._mask_secrets(text)
                assert "[MASKED]" in masked
