"""
Unit tests for kind (Kubernetes IN Docker) tools.

This module tests the kind local cluster management toolset.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import subprocess


class TestKindHelpers:
    """Tests for kind helper functions."""

    @pytest.mark.unit
    def test_kind_module_imports(self):
        """Test that kind module can be imported."""
        from kubectl_mcp_tool.tools.kind import (
            register_kind_tools,
            _kind_available,
            _get_kind_version,
            _run_kind,
            _run_docker,
            kind_detect,
            kind_version,
            kind_list_clusters,
            kind_get_nodes,
            kind_get_kubeconfig,
            kind_export_logs,
            kind_create_cluster,
            kind_delete_cluster,
            kind_delete_all_clusters,
            kind_load_image,
            kind_load_image_archive,
            kind_build_node_image,
            kind_cluster_info,
            kind_node_labels,
            kind_config_validate,
            kind_config_generate,
            kind_config_show,
            kind_available_images,
            kind_registry_create,
            kind_registry_connect,
            kind_registry_status,
            kind_node_exec,
            kind_node_logs,
            kind_node_inspect,
            kind_node_restart,
            kind_network_inspect,
            kind_port_mappings,
            kind_ingress_setup,
            kind_cluster_status,
            kind_images_list,
            kind_provider_info,
        )
        assert callable(register_kind_tools)
        assert callable(_kind_available)
        assert callable(_get_kind_version)
        assert callable(_run_kind)
        assert callable(_run_docker)
        assert callable(kind_detect)
        assert callable(kind_version)
        assert callable(kind_list_clusters)
        assert callable(kind_get_nodes)
        assert callable(kind_get_kubeconfig)
        assert callable(kind_export_logs)
        assert callable(kind_create_cluster)
        assert callable(kind_delete_cluster)
        assert callable(kind_delete_all_clusters)
        assert callable(kind_load_image)
        assert callable(kind_load_image_archive)
        assert callable(kind_build_node_image)
        assert callable(kind_cluster_info)
        assert callable(kind_node_labels)
        assert callable(kind_config_validate)
        assert callable(kind_config_generate)
        assert callable(kind_config_show)
        assert callable(kind_available_images)
        assert callable(kind_registry_create)
        assert callable(kind_registry_connect)
        assert callable(kind_registry_status)
        assert callable(kind_node_exec)
        assert callable(kind_node_logs)
        assert callable(kind_node_inspect)
        assert callable(kind_node_restart)
        assert callable(kind_network_inspect)
        assert callable(kind_port_mappings)
        assert callable(kind_ingress_setup)
        assert callable(kind_cluster_status)
        assert callable(kind_images_list)
        assert callable(kind_provider_info)

    @pytest.mark.unit
    def test_kind_available_when_installed(self):
        """Test _kind_available returns True when CLI is installed."""
        from kubectl_mcp_tool.tools.kind import _kind_available

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = _kind_available()
            assert result is True

    @pytest.mark.unit
    def test_kind_available_when_not_installed(self):
        """Test _kind_available returns False when CLI is not installed."""
        from kubectl_mcp_tool.tools.kind import _kind_available

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = _kind_available()
            assert result is False

    @pytest.mark.unit
    def test_get_kind_version(self):
        """Test _get_kind_version extracts version correctly."""
        from kubectl_mcp_tool.tools.kind import _get_kind_version

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="kind v0.23.0 go1.21.0 darwin/arm64"
            )
            result = _get_kind_version()
            assert result == "v0.23.0"

    @pytest.mark.unit
    def test_get_kind_version_not_installed(self):
        """Test _get_kind_version returns None when not installed."""
        from kubectl_mcp_tool.tools.kind import _get_kind_version

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = _get_kind_version()
            assert result is None

    @pytest.mark.unit
    def test_run_kind_not_available(self):
        """Test _run_kind returns error when CLI not available."""
        from kubectl_mcp_tool.tools.kind import _run_kind

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = _run_kind(["get", "clusters"])
            assert result["success"] is False
            assert "not available" in result["error"]

    @pytest.mark.unit
    def test_run_kind_success(self):
        """Test _run_kind returns success on successful command."""
        from kubectl_mcp_tool.tools.kind import _run_kind

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="test-cluster",
                stderr=""
            )
            result = _run_kind(["get", "clusters"])
            assert result["success"] is True
            assert result["output"] == "test-cluster"

    @pytest.mark.unit
    def test_run_kind_timeout(self):
        """Test _run_kind handles timeout."""
        from kubectl_mcp_tool.tools.kind import _run_kind

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),
                subprocess.TimeoutExpired(cmd="kind", timeout=300)
            ]
            result = _run_kind(["create", "cluster"])
            assert result["success"] is False
            assert "timed out" in result["error"]


class TestKindDetect:
    """Tests for kind_detect function."""

    @pytest.mark.unit
    def test_kind_detect_installed(self):
        """Test kind_detect when kind is installed."""
        from kubectl_mcp_tool.tools.kind import kind_detect

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="kind v0.23.0 go1.21.0 darwin/arm64"
            )
            result = kind_detect()
            assert result["installed"] is True
            assert result["cli_available"] is True
            assert result["version"] == "v0.23.0"
            assert result["install_instructions"] is None

    @pytest.mark.unit
    def test_kind_detect_not_installed(self):
        """Test kind_detect when kind is not installed."""
        from kubectl_mcp_tool.tools.kind import kind_detect

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = kind_detect()
            assert result["installed"] is False
            assert result["cli_available"] is False
            assert result["version"] is None
            assert result["install_instructions"] is not None


class TestKindListClusters:
    """Tests for kind_list_clusters function."""

    @pytest.mark.unit
    def test_kind_list_clusters_success(self):
        """Test kind_list_clusters returns cluster list."""
        from kubectl_mcp_tool.tools.kind import kind_list_clusters

        with patch("kubectl_mcp_tool.tools.kind._kind_available", return_value=True):
            with patch("kubectl_mcp_tool.tools.kind.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="dev-cluster\ntest-cluster",
                    stderr=""
                )
                result = kind_list_clusters()
                assert result["success"] is True
                assert result["total"] == 2
                assert "dev-cluster" in result["clusters"]
                assert "test-cluster" in result["clusters"]

    @pytest.mark.unit
    def test_kind_list_clusters_empty(self):
        """Test kind_list_clusters returns empty list."""
        from kubectl_mcp_tool.tools.kind import kind_list_clusters

        with patch("kubectl_mcp_tool.tools.kind._kind_available", return_value=True):
            with patch("kubectl_mcp_tool.tools.kind.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="",
                    stderr=""
                )
                result = kind_list_clusters()
                assert result["success"] is True
                assert result["total"] == 0


class TestKindGetNodes:
    """Tests for kind_get_nodes function."""

    @pytest.mark.unit
    def test_kind_get_nodes_success(self):
        """Test kind_get_nodes returns node list."""
        from kubectl_mcp_tool.tools.kind import kind_get_nodes

        with patch("kubectl_mcp_tool.tools.kind._kind_available", return_value=True):
            with patch("kubectl_mcp_tool.tools.kind.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="kind-control-plane\nkind-worker\nkind-worker2",
                    stderr=""
                )
                result = kind_get_nodes(name="kind")
                assert result["success"] is True
                assert result["total"] == 3
                assert "kind-control-plane" in result["nodes"]


class TestKindCreateCluster:
    """Tests for kind_create_cluster function."""

    @pytest.mark.unit
    def test_kind_create_cluster_basic(self):
        """Test kind_create_cluster with basic options."""
        from kubectl_mcp_tool.tools.kind import kind_create_cluster

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Creating cluster \"test\" ...",
                stderr=""
            )
            result = kind_create_cluster(name="test")
            assert result["success"] is True
            assert "created" in result["message"].lower()

    @pytest.mark.unit
    def test_kind_create_cluster_with_options(self):
        """Test kind_create_cluster with all options."""
        from kubectl_mcp_tool.tools.kind import kind_create_cluster

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Creating cluster \"prod\" ...",
                stderr=""
            )
            result = kind_create_cluster(
                name="prod",
                image="kindest/node:v1.29.0",
                wait="10m"
            )
            assert result["success"] is True


class TestKindDeleteCluster:
    """Tests for kind_delete_cluster function."""

    @pytest.mark.unit
    def test_kind_delete_cluster_success(self):
        """Test kind_delete_cluster deletes cluster."""
        from kubectl_mcp_tool.tools.kind import kind_delete_cluster

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Deleting cluster \"test\" ...",
                stderr=""
            )
            result = kind_delete_cluster(name="test")
            assert result["success"] is True
            assert "deleted" in result["message"].lower()


class TestKindDeleteAllClusters:
    """Tests for kind_delete_all_clusters function."""

    @pytest.mark.unit
    def test_kind_delete_all_clusters_success(self):
        """Test kind_delete_all_clusters deletes all clusters."""
        from kubectl_mcp_tool.tools.kind import kind_delete_all_clusters

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Deleted clusters: [\"test1\" \"test2\"]",
                stderr=""
            )
            result = kind_delete_all_clusters()
            assert result["success"] is True
            assert "deleted" in result["message"].lower()


class TestKindLoadImage:
    """Tests for kind_load_image function."""

    @pytest.mark.unit
    def test_kind_load_image_success(self):
        """Test kind_load_image loads images."""
        from kubectl_mcp_tool.tools.kind import kind_load_image

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Image loaded",
                stderr=""
            )
            result = kind_load_image(images=["myapp:latest"], name="test")
            assert result["success"] is True
            assert result["images"] == ["myapp:latest"]

    @pytest.mark.unit
    def test_kind_load_image_no_images(self):
        """Test kind_load_image with no images."""
        from kubectl_mcp_tool.tools.kind import kind_load_image

        result = kind_load_image(images=[], name="test")
        assert result["success"] is False
        assert "no images" in result["error"].lower()


class TestKindLoadImageArchive:
    """Tests for kind_load_image_archive function."""

    @pytest.mark.unit
    def test_kind_load_image_archive_file_not_found(self):
        """Test kind_load_image_archive with missing file."""
        from kubectl_mcp_tool.tools.kind import kind_load_image_archive

        result = kind_load_image_archive(archive="/nonexistent/file.tar", name="test")
        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestKindToolsRegistration:
    """Tests for kind tools registration."""

    @pytest.mark.unit
    def test_kind_tools_import(self):
        """Test that kind tools can be imported."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools
        assert callable(register_kind_tools)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_kind_tools_register(self, mock_all_kubernetes_apis):
        """Test that kind tools register correctly."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        tools = await server.server.list_tools()
        tool_names = {t.name for t in tools}

        kind_tools = [
            "kind_detect_tool",
            "kind_version_tool",
            "kind_list_clusters_tool",
            "kind_get_nodes_tool",
            "kind_get_kubeconfig_tool",
            "kind_export_logs_tool",
            "kind_cluster_info_tool",
            "kind_node_labels_tool",
            "kind_create_cluster_tool",
            "kind_delete_cluster_tool",
            "kind_delete_all_clusters_tool",
            "kind_load_image_tool",
            "kind_load_image_archive_tool",
            "kind_build_node_image_tool",
            "kind_set_kubeconfig_tool",
            "kind_config_validate_tool",
            "kind_config_generate_tool",
            "kind_config_show_tool",
            "kind_available_images_tool",
            "kind_registry_create_tool",
            "kind_registry_connect_tool",
            "kind_registry_status_tool",
            "kind_node_exec_tool",
            "kind_node_logs_tool",
            "kind_node_inspect_tool",
            "kind_node_restart_tool",
            "kind_network_inspect_tool",
            "kind_port_mappings_tool",
            "kind_ingress_setup_tool",
            "kind_cluster_status_tool",
            "kind_images_list_tool",
            "kind_provider_info_tool",
        ]
        for tool in kind_tools:
            assert tool in tool_names, f"kind tool '{tool}' not registered"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_kind_tool_count(self, mock_all_kubernetes_apis):
        """Test that correct number of kind tools are registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        tools = await server.server.list_tools()
        tool_names = {t.name for t in tools}
        kind_tools = [name for name in tool_names if name.startswith("kind_")]
        assert len(kind_tools) == 32, f"Expected 32 kind tools, got {len(kind_tools)}: {kind_tools}"

    @pytest.mark.unit
    def test_kind_non_destructive_mode(self, mock_all_kubernetes_apis):
        """Test that kind write operations are blocked in non-destructive mode."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test", disable_destructive=True)

        assert server.non_destructive is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_kind_tools_have_descriptions(self, mock_all_kubernetes_apis):
        """Test that all kind tools have descriptions."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            server = MCPServer(name="test")

        tools = await server.server.list_tools()
        kind_tools = [t for t in tools if t.name.startswith("kind_")]
        tools_without_description = [
            t.name for t in kind_tools
            if not t.description or len(t.description.strip()) == 0
        ]
        assert not tools_without_description, f"kind tools without descriptions: {tools_without_description}"


class TestKindNonDestructiveBlocking:
    """Tests for non-destructive mode blocking of kind write operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that kind_create_cluster_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_create_cluster_tool")
        result = tool.fn(name="test")
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that kind_delete_cluster_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_delete_cluster_tool")
        result = tool.fn(name="test")
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_all_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that kind_delete_all_clusters_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_delete_all_clusters_tool")
        result = tool.fn()
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_load_image_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that kind_load_image_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_load_image_tool")
        result = tool.fn(images="myapp:latest", name="test")
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_read_operations_allowed_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that read operations work in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_detect_tool")
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = tool.fn()
            result_dict = json.loads(result)
            assert "installed" in result_dict


class TestKindClusterInfo:
    """Tests for kind_cluster_info function."""

    @pytest.mark.unit
    def test_kind_cluster_info_cluster_not_found(self):
        """Test kind_cluster_info when cluster not found."""
        from kubectl_mcp_tool.tools.kind import kind_cluster_info

        with patch("kubectl_mcp_tool.tools.kind.kind_list_clusters") as mock_list:
            mock_list.return_value = {
                "success": True,
                "clusters": ["other-cluster"]
            }
            result = kind_cluster_info(name="nonexistent")
            assert result["success"] is False
            assert "not found" in result["error"].lower()

    @pytest.mark.unit
    def test_kind_cluster_info_success(self):
        """Test kind_cluster_info returns cluster info."""
        from kubectl_mcp_tool.tools.kind import kind_cluster_info

        with patch("kubectl_mcp_tool.tools.kind.kind_list_clusters") as mock_list:
            mock_list.return_value = {
                "success": True,
                "clusters": ["test-cluster"]
            }
            with patch("kubectl_mcp_tool.tools.kind.kind_get_nodes") as mock_nodes:
                mock_nodes.return_value = {
                    "success": True,
                    "nodes": ["test-cluster-control-plane"],
                    "total": 1
                }
                with patch("kubectl_mcp_tool.tools.kind.kind_get_kubeconfig") as mock_kubeconfig:
                    mock_kubeconfig.return_value = {
                        "success": True,
                        "kubeconfig": "apiVersion: v1\n..."
                    }
                    result = kind_cluster_info(name="test-cluster")
                    assert result["success"] is True
                    assert result["cluster"] == "test-cluster"
                    assert result["node_count"] == 1


class TestKindConfigValidate:
    """Tests for kind_config_validate function."""

    @pytest.mark.unit
    def test_kind_config_validate_file_not_found(self):
        """Test kind_config_validate with missing file."""
        from kubectl_mcp_tool.tools.kind import kind_config_validate

        result = kind_config_validate("/nonexistent/config.yaml")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.unit
    def test_kind_config_validate_valid_config(self, tmp_path):
        """Test kind_config_validate with valid config."""
        from kubectl_mcp_tool.tools.kind import kind_config_validate

        config_file = tmp_path / "kind.yaml"
        config_file.write_text("""
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
""")
        result = kind_config_validate(str(config_file))
        assert result["success"] is True
        assert result["valid"] is True
        assert result["config_summary"]["control_planes"] == 1
        assert result["config_summary"]["workers"] == 1

    @pytest.mark.unit
    def test_kind_config_validate_invalid_kind(self, tmp_path):
        """Test kind_config_validate with invalid kind field."""
        from kubectl_mcp_tool.tools.kind import kind_config_validate

        config_file = tmp_path / "kind.yaml"
        config_file.write_text("""
kind: Invalid
apiVersion: kind.x-k8s.io/v1alpha4
""")
        result = kind_config_validate(str(config_file))
        assert result["success"] is False
        assert len(result["errors"]) > 0


class TestKindConfigGenerate:
    """Tests for kind_config_generate function."""

    @pytest.mark.unit
    def test_kind_config_generate_default(self):
        """Test kind_config_generate with default options."""
        from kubectl_mcp_tool.tools.kind import kind_config_generate

        result = kind_config_generate()
        assert result["success"] is True
        assert "config" in result
        assert "kind: Cluster" in result["config"]
        assert result["summary"]["control_planes"] == 1
        assert result["summary"]["workers"] == 0

    @pytest.mark.unit
    def test_kind_config_generate_multi_node(self):
        """Test kind_config_generate with multiple nodes."""
        from kubectl_mcp_tool.tools.kind import kind_config_generate

        result = kind_config_generate(workers=2, control_planes=1)
        assert result["success"] is True
        assert result["summary"]["total_nodes"] == 3
        assert result["summary"]["workers"] == 2

    @pytest.mark.unit
    def test_kind_config_generate_with_ingress(self):
        """Test kind_config_generate with ingress enabled."""
        from kubectl_mcp_tool.tools.kind import kind_config_generate

        result = kind_config_generate(ingress=True)
        assert result["success"] is True
        assert result["summary"]["features"]["ingress"] is True
        assert "extraPortMappings" in result["config"]

    @pytest.mark.unit
    def test_kind_config_generate_with_registry(self):
        """Test kind_config_generate with registry enabled."""
        from kubectl_mcp_tool.tools.kind import kind_config_generate

        result = kind_config_generate(registry=True)
        assert result["success"] is True
        assert result["summary"]["features"]["registry"] is True
        assert "containerdConfigPatches" in result["config"]


class TestKindAvailableImages:
    """Tests for kind_available_images function."""

    @pytest.mark.unit
    def test_kind_available_images(self):
        """Test kind_available_images returns image list."""
        from kubectl_mcp_tool.tools.kind import kind_available_images

        result = kind_available_images()
        assert result["success"] is True
        assert "images" in result
        assert len(result["images"]) > 0
        assert result["latest"] is not None
        assert "kindest/node" in result["latest"]


class TestKindRegistryCreate:
    """Tests for kind_registry_create function."""

    @pytest.mark.unit
    def test_kind_registry_create_already_exists(self):
        """Test kind_registry_create when registry exists."""
        from kubectl_mcp_tool.tools.kind import kind_registry_create

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {"success": True, "output": "container_id"}
            result = kind_registry_create()
            assert result["success"] is True
            assert "already exists" in result["message"]

    @pytest.mark.unit
    def test_kind_registry_create_new(self):
        """Test kind_registry_create creates new registry."""
        from kubectl_mcp_tool.tools.kind import kind_registry_create

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.side_effect = [
                {"success": True, "output": ""},
                {"success": True, "output": ""},
                {"success": True, "output": ""},
                {"success": True, "output": ""}
            ]
            result = kind_registry_create()
            assert result["success"] is True
            assert result["port"] == 5001


class TestKindRegistryStatus:
    """Tests for kind_registry_status function."""

    @pytest.mark.unit
    def test_kind_registry_status_not_found(self):
        """Test kind_registry_status when registry not found."""
        from kubectl_mcp_tool.tools.kind import kind_registry_status

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {"success": False, "error": "not found"}
            result = kind_registry_status()
            assert result["success"] is False
            assert result["installed"] is False

    @pytest.mark.unit
    def test_kind_registry_status_running(self):
        """Test kind_registry_status when registry is running."""
        from kubectl_mcp_tool.tools.kind import kind_registry_status

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {
                "success": True,
                "output": json.dumps({
                    "State": {"Running": True, "Status": "running"},
                    "NetworkSettings": {
                        "Ports": {"5000/tcp": [{"HostPort": "5001"}]},
                        "Networks": {"kind": {}, "bridge": {}}
                    }
                })
            }
            result = kind_registry_status()
            assert result["success"] is True
            assert result["running"] is True
            assert result["connected_to_kind"] is True


class TestKindNodeExec:
    """Tests for kind_node_exec function."""

    @pytest.mark.unit
    def test_kind_node_exec_missing_node(self):
        """Test kind_node_exec with missing node."""
        from kubectl_mcp_tool.tools.kind import kind_node_exec

        result = kind_node_exec(node="", command="ls")
        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.unit
    def test_kind_node_exec_missing_command(self):
        """Test kind_node_exec with missing command."""
        from kubectl_mcp_tool.tools.kind import kind_node_exec

        result = kind_node_exec(node="kind-control-plane", command="")
        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.unit
    def test_kind_node_exec_success(self):
        """Test kind_node_exec succeeds."""
        from kubectl_mcp_tool.tools.kind import kind_node_exec

        with patch("kubectl_mcp_tool.tools.kind.kind_get_nodes") as mock_nodes:
            mock_nodes.return_value = {
                "success": True,
                "nodes": ["kind-control-plane"]
            }
            with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
                mock_docker.return_value = {"success": True, "output": "output"}
                result = kind_node_exec(node="kind-control-plane", command="ls")
                assert result["success"] is True
                assert result["output"] == "output"


class TestKindNodeLogs:
    """Tests for kind_node_logs function."""

    @pytest.mark.unit
    def test_kind_node_logs_missing_node(self):
        """Test kind_node_logs with missing node."""
        from kubectl_mcp_tool.tools.kind import kind_node_logs

        result = kind_node_logs(node="")
        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.unit
    def test_kind_node_logs_success(self):
        """Test kind_node_logs succeeds."""
        from kubectl_mcp_tool.tools.kind import kind_node_logs

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {"success": True, "output": "log output"}
            result = kind_node_logs(node="kind-control-plane")
            assert result["success"] is True
            assert "logs" in result


class TestKindNodeInspect:
    """Tests for kind_node_inspect function."""

    @pytest.mark.unit
    def test_kind_node_inspect_missing_node(self):
        """Test kind_node_inspect with missing node."""
        from kubectl_mcp_tool.tools.kind import kind_node_inspect

        result = kind_node_inspect(node="")
        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.unit
    def test_kind_node_inspect_success(self):
        """Test kind_node_inspect succeeds."""
        from kubectl_mcp_tool.tools.kind import kind_node_inspect

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {
                "success": True,
                "output": json.dumps({
                    "State": {"Running": True, "Status": "running", "StartedAt": "2024-01-01", "Pid": 1234},
                    "Config": {"Image": "kindest/node:v1.29.0", "Labels": {}},
                    "NetworkSettings": {"IPAddress": "172.18.0.2", "Networks": {"kind": {}}},
                    "HostConfig": {"PortBindings": {}},
                    "Mounts": []
                })
            }
            result = kind_node_inspect(node="kind-control-plane")
            assert result["success"] is True
            assert result["state"]["running"] is True


class TestKindNodeRestart:
    """Tests for kind_node_restart function."""

    @pytest.mark.unit
    def test_kind_node_restart_missing_node(self):
        """Test kind_node_restart with missing node."""
        from kubectl_mcp_tool.tools.kind import kind_node_restart

        result = kind_node_restart(node="")
        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.unit
    def test_kind_node_restart_success(self):
        """Test kind_node_restart succeeds."""
        from kubectl_mcp_tool.tools.kind import kind_node_restart

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {"success": True, "output": ""}
            result = kind_node_restart(node="kind-control-plane")
            assert result["success"] is True
            assert "restarted" in result["message"].lower()


class TestKindNetworkInspect:
    """Tests for kind_network_inspect function."""

    @pytest.mark.unit
    def test_kind_network_inspect_not_found(self):
        """Test kind_network_inspect when network not found."""
        from kubectl_mcp_tool.tools.kind import kind_network_inspect

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {"success": False, "error": "not found"}
            result = kind_network_inspect()
            assert result["success"] is False

    @pytest.mark.unit
    def test_kind_network_inspect_success(self):
        """Test kind_network_inspect succeeds."""
        from kubectl_mcp_tool.tools.kind import kind_network_inspect

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {
                "success": True,
                "output": json.dumps([{
                    "Name": "kind",
                    "Driver": "bridge",
                    "Scope": "local",
                    "IPAM": {"Config": [{"Subnet": "172.18.0.0/16", "Gateway": "172.18.0.1"}]},
                    "Containers": {
                        "abc123": {"Name": "kind-control-plane", "IPv4Address": "172.18.0.2/16", "MacAddress": "aa:bb:cc"}
                    }
                }])
            }
            result = kind_network_inspect()
            assert result["success"] is True
            assert result["subnet"] == "172.18.0.0/16"


class TestKindPortMappings:
    """Tests for kind_port_mappings function."""

    @pytest.mark.unit
    def test_kind_port_mappings_success(self):
        """Test kind_port_mappings returns mappings."""
        from kubectl_mcp_tool.tools.kind import kind_port_mappings

        with patch("kubectl_mcp_tool.tools.kind.kind_get_nodes") as mock_nodes:
            mock_nodes.return_value = {
                "success": True,
                "nodes": ["kind-control-plane"]
            }
            with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
                mock_docker.return_value = {
                    "success": True,
                    "output": json.dumps({
                        "80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "80"}]
                    })
                }
                result = kind_port_mappings()
                assert result["success"] is True
                assert result["has_mappings"] is True


class TestKindIngressSetup:
    """Tests for kind_ingress_setup function."""

    @pytest.mark.unit
    def test_kind_ingress_setup_invalid_type(self):
        """Test kind_ingress_setup with invalid type."""
        from kubectl_mcp_tool.tools.kind import kind_ingress_setup

        result = kind_ingress_setup(ingress_type="invalid")
        assert result["success"] is False
        assert "unsupported" in result["error"].lower()

    @pytest.mark.unit
    def test_kind_ingress_setup_cluster_not_found(self):
        """Test kind_ingress_setup when cluster not found."""
        from kubectl_mcp_tool.tools.kind import kind_ingress_setup

        with patch("kubectl_mcp_tool.tools.kind.kind_list_clusters") as mock_list:
            mock_list.return_value = {"success": True, "clusters": []}
            result = kind_ingress_setup(cluster="nonexistent")
            assert result["success"] is False


class TestKindClusterStatus:
    """Tests for kind_cluster_status function."""

    @pytest.mark.unit
    def test_kind_cluster_status_not_found(self):
        """Test kind_cluster_status when cluster not found."""
        from kubectl_mcp_tool.tools.kind import kind_cluster_status

        with patch("kubectl_mcp_tool.tools.kind.kind_list_clusters") as mock_list:
            mock_list.return_value = {"success": True, "clusters": []}
            result = kind_cluster_status(name="nonexistent")
            assert result["success"] is False
            assert "not found" in result["error"].lower()


class TestKindImagesList:
    """Tests for kind_images_list function."""

    @pytest.mark.unit
    def test_kind_images_list_no_nodes(self):
        """Test kind_images_list when no nodes."""
        from kubectl_mcp_tool.tools.kind import kind_images_list

        with patch("kubectl_mcp_tool.tools.kind.kind_get_nodes") as mock_nodes:
            mock_nodes.return_value = {"success": True, "nodes": []}
            result = kind_images_list()
            assert result["success"] is False


class TestKindProviderInfo:
    """Tests for kind_provider_info function."""

    @pytest.mark.unit
    def test_kind_provider_info_success(self):
        """Test kind_provider_info returns provider details."""
        from kubectl_mcp_tool.tools.kind import kind_provider_info

        with patch("kubectl_mcp_tool.tools.kind._run_docker") as mock_docker:
            mock_docker.return_value = {
                "success": True,
                "output": json.dumps({
                    "Client": {"Version": "24.0.0", "ApiVersion": "1.43", "Os": "darwin", "Arch": "arm64"},
                    "Server": {"Version": "24.0.0"}
                })
            }
            result = kind_provider_info()
            assert result["success"] is True
            assert result["provider"] == "docker"
            assert result["client_version"] == "24.0.0"


class TestRunDocker:
    """Tests for _run_docker helper function."""

    @pytest.mark.unit
    def test_run_docker_success(self):
        """Test _run_docker returns success."""
        from kubectl_mcp_tool.tools.kind import _run_docker

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="output",
                stderr=""
            )
            result = _run_docker(["ps"])
            assert result["success"] is True
            assert result["output"] == "output"

    @pytest.mark.unit
    def test_run_docker_not_available(self):
        """Test _run_docker when Docker not available."""
        from kubectl_mcp_tool.tools.kind import _run_docker

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = _run_docker(["ps"])
            assert result["success"] is False
            assert "not available" in result["error"].lower()

    @pytest.mark.unit
    def test_run_docker_timeout(self):
        """Test _run_docker handles timeout."""
        from kubectl_mcp_tool.tools.kind import _run_docker

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="docker", timeout=60)
            result = _run_docker(["ps"])
            assert result["success"] is False
            assert "timed out" in result["error"]


class TestNewKindNonDestructiveBlocking:
    """Tests for non-destructive mode blocking of new kind write operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_registry_create_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that kind_registry_create_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_registry_create_tool")
        result = tool.fn()
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_node_exec_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that kind_node_exec_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_node_exec_tool")
        result = tool.fn(node="test", command="ls")
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_node_restart_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that kind_node_restart_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_node_restart_tool")
        result = tool.fn(node="test")
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_ingress_setup_blocked_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that kind_ingress_setup_tool is blocked in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_ingress_setup_tool")
        result = tool.fn()
        result_dict = json.loads(result)
        assert result_dict["success"] is False
        assert "non-destructive" in result_dict["error"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_read_operations_allowed_in_non_destructive(self, mock_all_kubernetes_apis):
        """Test that new read operations work in non-destructive mode."""
        from kubectl_mcp_tool.tools.kind import register_kind_tools

        try:
            from fastmcp import FastMCP
        except ImportError:
            from mcp.server.fastmcp import FastMCP

        mcp = FastMCP(name="test")
        register_kind_tools(mcp, non_destructive=True)

        tool = await mcp.get_tool("kind_available_images_tool")
        result = tool.fn()
        result_dict = json.loads(result)
        assert result_dict["success"] is True
        assert "images" in result_dict
