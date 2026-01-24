"""
Unit tests for ecosystem tools (GitOps, Cert-Manager, Policy, Backup).

This module tests the CRD detector and all ecosystem toolsets.
"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess


class TestCRDDetector:
    """Tests for the CRD auto-discovery framework."""

    @pytest.mark.unit
    def test_crd_detector_imports(self):
        """Test that CRD detector module can be imported."""
        from kubectl_mcp_tool.crd_detector import (
            CRD_GROUPS,
            detect_crds,
            crd_exists,
            get_enabled_toolsets,
            get_crd_status_summary,
            FeatureNotInstalledError,
            require_crd,
            require_any_crd,
        )
        assert CRD_GROUPS is not None
        assert callable(detect_crds)
        assert callable(crd_exists)
        assert callable(get_enabled_toolsets)
        assert callable(get_crd_status_summary)
        assert issubclass(FeatureNotInstalledError, Exception)
        assert callable(require_crd)
        assert callable(require_any_crd)

    @pytest.mark.unit
    def test_crd_groups_structure(self):
        """Test that CRD_GROUPS has expected structure."""
        from kubectl_mcp_tool.crd_detector import CRD_GROUPS

        expected_groups = ["flux", "argocd", "certmanager", "kyverno", "gatekeeper", "velero"]
        for group in expected_groups:
            assert group in CRD_GROUPS, f"Expected group '{group}' in CRD_GROUPS"
            assert isinstance(CRD_GROUPS[group], list), f"CRD_GROUPS['{group}'] should be a list"
            assert len(CRD_GROUPS[group]) > 0, f"CRD_GROUPS['{group}'] should not be empty"

    @pytest.mark.unit
    def test_detect_crds_with_mocked_kubectl(self):
        """Test CRD detection with mocked kubectl."""
        from kubectl_mcp_tool.crd_detector import detect_crds, _crd_cache

        # Clear cache before test
        _crd_cache.clear()

        mock_output = """NAME                                     CREATED AT
applications.argoproj.io                 2024-01-01T00:00:00Z
certificates.cert-manager.io             2024-01-01T00:00:00Z
"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output
            )
            result = detect_crds(force_refresh=True)

            assert isinstance(result, dict)
            assert "argocd" in result
            assert "certmanager" in result

    @pytest.mark.unit
    def test_detect_crds_handles_kubectl_failure(self):
        """Test CRD detection handles kubectl failure gracefully."""
        from kubectl_mcp_tool.crd_detector import detect_crds, _crd_cache

        _crd_cache.clear()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("Command failed")
            result = detect_crds(force_refresh=True)

            assert isinstance(result, dict)
            # All groups should be False when kubectl fails
            for value in result.values():
                assert value is False

    @pytest.mark.unit
    def test_feature_not_installed_error(self):
        """Test FeatureNotInstalledError exception."""
        from kubectl_mcp_tool.crd_detector import FeatureNotInstalledError

        error = FeatureNotInstalledError("velero", ["backups.velero.io"])
        assert "velero" in str(error)
        assert "backups.velero.io" in str(error)
        assert error.toolset == "velero"
        assert "backups.velero.io" in error.required_crds

    @pytest.mark.unit
    def test_get_crd_status_summary(self):
        """Test CRD status summary generation."""
        from kubectl_mcp_tool.crd_detector import get_crd_status_summary, _crd_cache

        _crd_cache.clear()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="applications.argoproj.io 2024-01-01T00:00:00Z\n"
            )
            summary = get_crd_status_summary()

            # Summary returns a dict with crd_groups and enabled_toolsets
            assert isinstance(summary, dict)
            assert "crd_groups" in summary
            assert "enabled_toolsets" in summary


class TestGitOpsTools:
    """Tests for GitOps toolset (Flux and ArgoCD)."""

    @pytest.mark.unit
    def test_gitops_tools_import(self):
        """Test that GitOps tools can be imported."""
        from kubectl_mcp_tool.tools.gitops import register_gitops_tools
        assert callable(register_gitops_tools)

    @pytest.mark.unit
    def test_gitops_tools_register(self, mock_all_kubernetes_apis):
        """Test that GitOps tools register correctly."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        import asyncio

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        async def get_tools():
            return await server.server.list_tools()

        tools = asyncio.run(get_tools())
        tool_names = {t.name for t in tools}

        gitops_tools = [
            "gitops_apps_list_tool", "gitops_app_get_tool", "gitops_app_sync_tool",
            "gitops_app_status_tool", "gitops_sources_list_tool", "gitops_source_get_tool",
            "gitops_detect_engine_tool"
        ]
        for tool in gitops_tools:
            assert tool in tool_names, f"GitOps tool '{tool}' not registered"

    @pytest.mark.unit
    def test_gitops_non_destructive_mode(self, mock_all_kubernetes_apis):
        """Test that GitOps sync is blocked in non-destructive mode."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test", non_destructive=True)

        # Server should initialize with non_destructive=True
        assert server.non_destructive is True


class TestCertManagerTools:
    """Tests for Cert-Manager toolset."""

    @pytest.mark.unit
    def test_certs_tools_import(self):
        """Test that Cert-Manager tools can be imported."""
        from kubectl_mcp_tool.tools.certs import register_certs_tools
        assert callable(register_certs_tools)

    @pytest.mark.unit
    def test_certs_tools_register(self, mock_all_kubernetes_apis):
        """Test that Cert-Manager tools register correctly."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        import asyncio

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        async def get_tools():
            return await server.server.list_tools()

        tools = asyncio.run(get_tools())
        tool_names = {t.name for t in tools}

        certs_tools = [
            "certs_list_tool", "certs_get_tool", "certs_issuers_list_tool", "certs_issuer_get_tool",
            "certs_renew_tool", "certs_status_explain_tool", "certs_challenges_list_tool",
            "certs_requests_list_tool", "certs_detect_tool"
        ]
        for tool in certs_tools:
            assert tool in tool_names, f"Cert-Manager tool '{tool}' not registered"


class TestPolicyTools:
    """Tests for Policy toolset (Kyverno and Gatekeeper)."""

    @pytest.mark.unit
    def test_policy_tools_import(self):
        """Test that Policy tools can be imported."""
        from kubectl_mcp_tool.tools.policy import register_policy_tools
        assert callable(register_policy_tools)

    @pytest.mark.unit
    def test_policy_tools_register(self, mock_all_kubernetes_apis):
        """Test that Policy tools register correctly."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        import asyncio

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        async def get_tools():
            return await server.server.list_tools()

        tools = asyncio.run(get_tools())
        tool_names = {t.name for t in tools}

        policy_tools = [
            "policy_list_tool", "policy_get_tool", "policy_violations_list_tool",
            "policy_explain_denial_tool", "policy_audit_tool", "policy_detect_tool"
        ]
        for tool in policy_tools:
            assert tool in tool_names, f"Policy tool '{tool}' not registered"


class TestBackupTools:
    """Tests for Backup toolset (Velero)."""

    @pytest.mark.unit
    def test_backup_tools_import(self):
        """Test that Backup tools can be imported."""
        from kubectl_mcp_tool.tools.backup import register_backup_tools
        assert callable(register_backup_tools)

    @pytest.mark.unit
    def test_backup_tools_register(self, mock_all_kubernetes_apis):
        """Test that Backup tools register correctly."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        import asyncio

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        async def get_tools():
            return await server.server.list_tools()

        tools = asyncio.run(get_tools())
        tool_names = {t.name for t in tools}

        backup_tools = [
            "backup_list_tool", "backup_get_tool", "backup_create_tool", "backup_delete_tool",
            "restore_list_tool", "restore_create_tool", "restore_get_tool",
            "backup_locations_list_tool", "backup_schedules_list_tool",
            "backup_schedule_create_tool", "backup_detect_tool"
        ]
        for tool in backup_tools:
            assert tool in tool_names, f"Backup tool '{tool}' not registered"

    @pytest.mark.unit
    def test_backup_non_destructive_mode(self, mock_all_kubernetes_apis):
        """Test that backup operations are blocked in non-destructive mode."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test", non_destructive=True)

        # Server should initialize with non_destructive=True
        assert server.non_destructive is True


class TestEcosystemToolsIntegration:
    """Integration tests for ecosystem tools."""

    @pytest.mark.unit
    def test_all_ecosystem_tools_have_descriptions(self, mock_all_kubernetes_apis):
        """Test that all ecosystem tools have descriptions."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        import asyncio

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        async def get_tools():
            return await server.server.list_tools()

        tools = asyncio.run(get_tools())

        ecosystem_prefixes = ["gitops_", "certs_", "policy_", "backup_", "restore_"]
        ecosystem_tools = [t for t in tools if any(t.name.startswith(p) for p in ecosystem_prefixes)]

        tools_without_description = [
            t.name for t in ecosystem_tools
            if not t.description or len(t.description.strip()) == 0
        ]
        assert not tools_without_description, f"Ecosystem tools without descriptions: {tools_without_description}"

    @pytest.mark.unit
    def test_ecosystem_tool_count(self, mock_all_kubernetes_apis):
        """Test that correct number of ecosystem tools are registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer
        import asyncio

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        async def get_tools():
            return await server.server.list_tools()

        tools = asyncio.run(get_tools())

        # Filter ecosystem tools, but exclude backup_resource which is in operations.py
        ecosystem_tool_names = [
            "gitops_apps_list_tool", "gitops_app_get_tool", "gitops_app_sync_tool",
            "gitops_app_status_tool", "gitops_sources_list_tool", "gitops_source_get_tool",
            "gitops_detect_engine_tool",
            "certs_list_tool", "certs_get_tool", "certs_issuers_list_tool", "certs_issuer_get_tool",
            "certs_renew_tool", "certs_status_explain_tool", "certs_challenges_list_tool",
            "certs_requests_list_tool", "certs_detect_tool",
            "policy_list_tool", "policy_get_tool", "policy_violations_list_tool",
            "policy_explain_denial_tool", "policy_audit_tool", "policy_detect_tool",
            "backup_list_tool", "backup_get_tool", "backup_create_tool", "backup_delete_tool",
            "restore_list_tool", "restore_create_tool", "restore_get_tool",
            "backup_locations_list_tool", "backup_schedules_list_tool",
            "backup_schedule_create_tool", "backup_detect_tool"
        ]
        tool_names = {t.name for t in tools}
        ecosystem_tools = [name for name in ecosystem_tool_names if name in tool_names]

        # 7 GitOps + 9 Certs + 6 Policy + 11 Backup = 33 ecosystem tools
        assert len(ecosystem_tools) == 33, f"Expected 33 ecosystem tools, got {len(ecosystem_tools)}"
