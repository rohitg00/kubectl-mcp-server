"""
Unit tests for vind (vCluster in Docker) tools.

This module tests the vCluster management toolset.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import subprocess


class TestVindHelpers:
    """Tests for vind helper functions."""

    @pytest.mark.unit
    def test_vind_module_imports(self):
        """Test that vind module can be imported."""
        from kubectl_mcp_tool.tools.vind import (
            register_vind_tools,
            _vcluster_available,
            _get_vcluster_version,
            _run_vcluster,
            vind_detect,
            vind_list_clusters,
            vind_status,
            vind_get_kubeconfig,
            vind_logs,
            vind_create_cluster,
            vind_delete_cluster,
            vind_pause,
            vind_resume,
            vind_connect,
            vind_disconnect,
            vind_upgrade,
            vind_describe,
            vind_platform_start,
        )
        assert callable(register_vind_tools)
        assert callable(_vcluster_available)
        assert callable(_get_vcluster_version)
        assert callable(_run_vcluster)
        assert callable(vind_detect)
        assert callable(vind_list_clusters)
        assert callable(vind_status)
        assert callable(vind_get_kubeconfig)
        assert callable(vind_logs)
        assert callable(vind_create_cluster)
        assert callable(vind_delete_cluster)
        assert callable(vind_pause)
        assert callable(vind_resume)
        assert callable(vind_connect)
        assert callable(vind_disconnect)
        assert callable(vind_upgrade)
        assert callable(vind_describe)
        assert callable(vind_platform_start)

    @pytest.mark.unit
    def test_vcluster_available_when_installed(self):
        """Test _vcluster_available returns True when CLI is installed."""
        from kubectl_mcp_tool.tools.vind import _vcluster_available

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = _vcluster_available()
            assert result is True

    @pytest.mark.unit
    def test_vcluster_available_when_not_installed(self):
        """Test _vcluster_available returns False when CLI is not installed."""
        from kubectl_mcp_tool.tools.vind import _vcluster_available

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = _vcluster_available()
            assert result is False

    @pytest.mark.unit
    def test_get_vcluster_version(self):
        """Test _get_vcluster_version extracts version correctly."""
        from kubectl_mcp_tool.tools.vind import _get_vcluster_version

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="vcluster version v0.19.0"
            )
            result = _get_vcluster_version()
            assert result == "v0.19.0"

    @pytest.mark.unit
    def test_get_vcluster_version_not_installed(self):
        """Test _get_vcluster_version returns None when not installed."""
        from kubectl_mcp_tool.tools.vind import _get_vcluster_version

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = _get_vcluster_version()
            assert result is None

    @pytest.mark.unit
    def test_run_vcluster_not_available(self):
        """Test _run_vcluster returns error when CLI not available."""
        from kubectl_mcp_tool.tools.vind import _run_vcluster

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = _run_vcluster(["list"])
            assert result["success"] is False
            assert "not available" in result["error"]

    @pytest.mark.unit
    def test_run_vcluster_success(self):
        """Test _run_vcluster returns success on successful command."""
        from kubectl_mcp_tool.tools.vind import _run_vcluster

        with patch("subprocess.run") as mock_run:
            # First call for availability check
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="test output",
                stderr=""
            )
            result = _run_vcluster(["list"])
            assert result["success"] is True
            assert result["output"] == "test output"

    @pytest.mark.unit
    def test_run_vcluster_timeout(self):
        """Test _run_vcluster handles timeout."""
        from kubectl_mcp_tool.tools.vind import _run_vcluster

        with patch("subprocess.run") as mock_run:
            # First call succeeds (availability check), second times out
            mock_run.side_effect = [
                MagicMock(returncode=0),  # availability check
                subprocess.TimeoutExpired(cmd="vcluster", timeout=120)
            ]
            result = _run_vcluster(["create", "test"])
            assert result["success"] is False
            assert "timed out" in result["error"]

    @pytest.mark.unit
    def test_run_vcluster_with_json_output(self):
        """Test _run_vcluster parses JSON output."""
        from kubectl_mcp_tool.tools.vind import _run_vcluster

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='[{"Name": "test", "Status": "Running"}]',
                stderr=""
            )
            result = _run_vcluster(["list"], json_output=True)
            assert result["success"] is True
            assert result["data"] == [{"Name": "test", "Status": "Running"}]


class TestVindDetect:
    """Tests for vind_detect function."""

    @pytest.mark.unit
    def test_vind_detect_installed(self):
        """Test vind_detect when vcluster is installed."""
        from kubectl_mcp_tool.tools.vind import vind_detect

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="vcluster version v0.19.0"
            )
            result = vind_detect()
            assert result["installed"] is True
            assert result["cli_available"] is True
            assert result["version"] == "v0.19.0"
            assert result["install_instructions"] is None

    @pytest.mark.unit
    def test_vind_detect_not_installed(self):
        """Test vind_detect when vcluster is not installed."""
        from kubectl_mcp_tool.tools.vind import vind_detect

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = vind_detect()
            assert result["installed"] is False
            assert result["cli_available"] is False
            assert result["version"] is None
            assert result["install_instructions"] is not None


class TestVindListClusters:
    """Tests for vind_list_clusters function."""

    @pytest.mark.unit
    def test_vind_list_clusters_success(self):
        """Test vind_list_clusters returns cluster list."""
        from kubectl_mcp_tool.tools.vind import vind_list_clusters

        mock_clusters = [
            {
                "Name": "dev-cluster",
                "Namespace": "vcluster-dev",
                "Status": "Running",
                "Version": "v1.29.0",
                "Connected": True,
                "Created": "2024-01-01T00:00:00Z",
                "Age": "1d"
            }
        ]

        with patch("kubectl_mcp_tool.tools.vind._vcluster_available", return_value=True):
            with patch("kubectl_mcp_tool.tools.vind.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=json.dumps(mock_clusters),
                    stderr=""
                )
                result = vind_list_clusters()
                assert result["success"] is True
                assert result["total"] == 1
                assert len(result["clusters"]) == 1
                assert result["clusters"][0]["name"] == "dev-cluster"

    @pytest.mark.unit
    def test_vind_list_clusters_empty(self):
        """Test vind_list_clusters returns empty list."""
        from kubectl_mcp_tool.tools.vind import vind_list_clusters

        with patch("kubectl_mcp_tool.tools.vind._vcluster_available", return_value=True):
            with patch("kubectl_mcp_tool.tools.vind.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="[]",
                    stderr=""
                )
                result = vind_list_clusters()
                assert result["success"] is True
                assert result["total"] == 0


class TestVindCreateCluster:
    """Tests for vind_create_cluster function."""

    @pytest.mark.unit
    def test_vind_create_cluster_basic(self):
        """Test vind_create_cluster with basic options."""
        from kubectl_mcp_tool.tools.vind import vind_create_cluster

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="vCluster 'test' created successfully",
                stderr=""
            )
            result = vind_create_cluster(name="test")
            assert result["success"] is True
            assert "created" in result["message"].lower()

    @pytest.mark.unit
    def test_vind_create_cluster_with_options(self):
        """Test vind_create_cluster with all options."""
        from kubectl_mcp_tool.tools.vind import vind_create_cluster

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="vCluster 'prod' created successfully",
                stderr=""
            )
            result = vind_create_cluster(
                name="prod",
                namespace="production",
                kubernetes_version="v1.29.0",
                set_values=["sync.toHost.pods.enabled=true"],
                connect=True
            )
            assert result["success"] is True


class TestVindPauseResume:
    """Tests for vind_pause and vind_resume functions."""

    @pytest.mark.unit
    def test_vind_pause_success(self):
        """Test vind_pause pauses cluster."""
        from kubectl_mcp_tool.tools.vind import vind_pause

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="vCluster 'test' paused",
                stderr=""
            )
            result = vind_pause(name="test")
            assert result["success"] is True
            assert "paused" in result["message"].lower()

    @pytest.mark.unit
    def test_vind_resume_success(self):
        """Test vind_resume resumes cluster."""
        from kubectl_mcp_tool.tools.vind import vind_resume

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="vCluster 'test' resumed",
                stderr=""
            )
            result = vind_resume(name="test")
            assert result["success"] is True
            assert "resumed" in result["message"].lower()


class TestVindConnect:
    """Tests for vind_connect and vind_disconnect functions."""

    @pytest.mark.unit
    def test_vind_connect_success(self):
        """Test vind_connect connects to cluster."""
        from kubectl_mcp_tool.tools.vind import vind_connect

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Connected to vCluster 'test'",
                stderr=""
            )
            result = vind_connect(name="test")
            assert result["success"] is True
            assert "connected" in result["message"].lower()

    @pytest.mark.unit
    def test_vind_disconnect_success(self):
        """Test vind_disconnect disconnects from cluster."""
        from kubectl_mcp_tool.tools.vind import vind_disconnect

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Disconnected",
                stderr=""
            )
            result = vind_disconnect("", "")
            assert result["success"] is True


class TestVindToolsRegistration:
    """Tests for vind tools registration."""

    @pytest.mark.unit
    def test_vind_tools_import(self):
        """Test that vind tools can be imported."""
        from kubectl_mcp_tool.tools.vind import register_vind_tools
        assert callable(register_vind_tools)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vind_tools_register(self, mock_all_kubernetes_apis):
        """Test that vind tools register correctly."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        tools = await server.server.list_tools()
        tool_names = {t.name for t in tools}

        vind_tools = [
            "vind_detect_tool",
            "vind_list_clusters_tool",
            "vind_status_tool",
            "vind_get_kubeconfig_tool",
            "vind_logs_tool",
            "vind_create_cluster_tool",
            "vind_delete_cluster_tool",
            "vind_pause_tool",
            "vind_resume_tool",
            "vind_connect_tool",
            "vind_disconnect_tool",
            "vind_upgrade_tool",
            "vind_describe_tool",
            "vind_platform_start_tool",
        ]
        for tool in vind_tools:
            assert tool in tool_names, f"vind tool '{tool}' not registered"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vind_tool_count(self, mock_all_kubernetes_apis):
        """Test that correct number of vind tools are registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        tools = await server.server.list_tools()
        tool_names = {t.name for t in tools}
        vind_tools = [name for name in tool_names if name.startswith("vind_")]
        assert len(vind_tools) == 14, f"Expected 14 vind tools, got {len(vind_tools)}: {vind_tools}"

    @pytest.mark.unit
    def test_vind_non_destructive_mode(self, mock_all_kubernetes_apis):
        """Test that vind write operations are blocked in non-destructive mode."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test", disable_destructive=True)

        assert server.non_destructive is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_vind_tools_have_descriptions(self, mock_all_kubernetes_apis):
        """Test that all vind tools have descriptions."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        tools = await server.server.list_tools()
        vind_tools = [t for t in tools if t.name.startswith("vind_")]
        tools_without_description = [
            t.name for t in vind_tools
            if not t.description or len(t.description.strip()) == 0
        ]
        assert not tools_without_description, f"vind tools without descriptions: {tools_without_description}"


class TestVindNonDestructiveBlocking:
    """Tests for non-destructive mode blocking of vind write operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that vind_create_cluster_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.vind import register_vind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_vind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("vind_create_cluster_tool")
        result = tool.fn(name="test")
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that vind_delete_cluster_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.vind import register_vind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_vind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("vind_delete_cluster_tool")
        result = tool.fn(name="test")
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pause_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that vind_pause_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.vind import register_vind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_vind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("vind_pause_tool")
        result = tool.fn(name="test")
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_read_operations_allowed_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that read operations work in non-destructive mode."""
        from kubectl_mcp_tool.tools.vind import register_vind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_vind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("vind_detect_tool")
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = tool.fn()
            result_dict = json.loads(result)
            assert "installed" in result_dict
