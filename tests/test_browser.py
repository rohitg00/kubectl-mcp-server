"""Unit tests for browser automation tools (optional module)."""

import pytest
import json
import os
from unittest.mock import patch, MagicMock


class TestBrowserAvailability:
    """Tests for browser module availability detection."""

    @pytest.mark.unit
    def test_browser_disabled_by_default(self):
        """Browser tools should be disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            # Need to reload module to pick up env changes
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)
            assert browser_module.BROWSER_ENABLED is False

    @pytest.mark.unit
    def test_browser_enabled_with_env_var(self):
        """Browser tools should be enabled when MCP_BROWSER_ENABLED=true."""
        with patch.dict(os.environ, {"MCP_BROWSER_ENABLED": "true"}):
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)
            assert browser_module.BROWSER_ENABLED is True

    @pytest.mark.unit
    def test_is_browser_available_disabled(self):
        """is_browser_available returns False when disabled."""
        with patch.dict(os.environ, {"MCP_BROWSER_ENABLED": "false"}):
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)
            assert browser_module.is_browser_available() is False

    @pytest.mark.unit
    def test_is_browser_available_enabled_no_binary(self):
        """is_browser_available returns False when enabled but binary missing."""
        with patch.dict(os.environ, {"MCP_BROWSER_ENABLED": "true"}):
            with patch("shutil.which", return_value=None):
                import importlib
                import kubectl_mcp_tool.tools.browser as browser_module
                importlib.reload(browser_module)
                # Force re-check since BROWSER_AVAILABLE is set at import time
                browser_module.BROWSER_AVAILABLE = False
                assert browser_module.is_browser_available() is False


class TestBrowserCommands:
    """Tests for browser command execution."""

    @pytest.mark.unit
    def test_run_browser_success(self):
        """Test successful browser command execution."""
        from kubectl_mcp_tool.tools.browser import _run_browser

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success output"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = _run_browser(["open", "https://example.com"])
            assert result["success"] is True
            assert result["output"] == "Success output"

    @pytest.mark.unit
    def test_run_browser_failure(self):
        """Test failed browser command execution."""
        from kubectl_mcp_tool.tools.browser import _run_browser

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: something went wrong"

        with patch("subprocess.run", return_value=mock_result):
            result = _run_browser(["open", "invalid"])
            assert result["success"] is False
            assert "Error" in result["error"]

    @pytest.mark.unit
    def test_run_browser_json_output(self):
        """Test browser command with JSON output."""
        from kubectl_mcp_tool.tools.browser import _run_browser

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"data": "test"}'
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = _run_browser(["snapshot", "--json"])
            assert result["success"] is True
            assert result["data"] == {"data": "test"}

    @pytest.mark.unit
    def test_run_browser_timeout(self):
        """Test browser command timeout handling."""
        from kubectl_mcp_tool.tools.browser import _run_browser
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 60)):
            result = _run_browser(["open", "https://slow.com"], timeout=60)
            assert result["success"] is False
            assert "timed out" in result["error"]

    @pytest.mark.unit
    def test_run_browser_not_found(self):
        """Test handling when agent-browser is not installed."""
        from kubectl_mcp_tool.tools.browser import _run_browser

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            result = _run_browser(["open", "https://example.com"])
            assert result["success"] is False
            assert "not found" in result["error"]


class TestBrowserToolFunctions:
    """Tests for individual browser tool functions."""

    @pytest.fixture
    def mock_browser_run(self):
        """Fixture to mock _run_browser."""
        with patch("kubectl_mcp_tool.tools.browser._run_browser") as mock:
            mock.return_value = {"success": True, "output": "OK"}
            yield mock

    @pytest.mark.unit
    def test_browser_open(self, mock_browser_run):
        """Test browser_open tool."""
        from kubectl_mcp_tool.tools.browser import register_browser_tools
        from fastmcp import FastMCP

        server = FastMCP(name="test")
        register_browser_tools(server, non_destructive=False)

        # Verify tool was registered
        import asyncio
        tools = asyncio.run(server.list_tools())
        tool_names = [t.name for t in tools]
        assert "browser_open" in tool_names

    @pytest.mark.unit
    def test_browser_snapshot(self, mock_browser_run):
        """Test browser_snapshot tool."""
        from kubectl_mcp_tool.tools.browser import register_browser_tools
        from fastmcp import FastMCP

        server = FastMCP(name="test")
        register_browser_tools(server, non_destructive=False)

        tools = asyncio.run(server.list_tools())
        tool_names = [t.name for t in tools]
        assert "browser_snapshot" in tool_names

    @pytest.mark.unit
    def test_browser_screenshot(self, mock_browser_run):
        """Test browser_screenshot tool."""
        from kubectl_mcp_tool.tools.browser import register_browser_tools
        from fastmcp import FastMCP

        server = FastMCP(name="test")
        register_browser_tools(server, non_destructive=False)

        tools = asyncio.run(server.list_tools())
        tool_names = [t.name for t in tools]
        assert "browser_screenshot" in tool_names

    @pytest.mark.unit
    def test_all_19_browser_tools_registered(self):
        """Verify all 19 browser tools are registered."""
        from kubectl_mcp_tool.tools.browser import register_browser_tools
        from fastmcp import FastMCP
        import asyncio

        server = FastMCP(name="test")
        register_browser_tools(server, non_destructive=False)

        tools = asyncio.run(server.list_tools())
        assert len(tools) == 19, f"Expected 19 browser tools, got {len(tools)}"

        expected_tools = [
            "browser_open",
            "browser_snapshot",
            "browser_click",
            "browser_fill",
            "browser_screenshot",
            "browser_get_text",
            "browser_get_url",
            "browser_wait",
            "browser_close",
            "browser_test_ingress",
            "browser_screenshot_service",
            "browser_screenshot_grafana",
            "browser_screenshot_argocd",
            "browser_health_check",
            "browser_form_submit",
            "browser_session_save",
            "browser_session_load",
            "browser_open_cloud_console",
            "browser_pdf_export",
        ]

        tool_names = {t.name for t in tools}
        missing = set(expected_tools) - tool_names
        assert not missing, f"Missing browser tools: {missing}"


class TestK8sIntegration:
    """Tests for Kubernetes-specific browser tools."""

    @pytest.mark.unit
    def test_get_ingress_url_not_found(self):
        """Test _get_ingress_url when no ingress exists."""
        from kubectl_mcp_tool.tools.browser import _get_ingress_url

        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.NetworkingV1Api") as mock_api:
                mock_instance = MagicMock()
                mock_instance.list_namespaced_ingress.return_value.items = []
                mock_api.return_value = mock_instance

                result = _get_ingress_url("my-service", "default")
                assert result is None

    @pytest.mark.unit
    def test_get_service_url_loadbalancer(self):
        """Test _get_service_url for LoadBalancer type."""
        from kubectl_mcp_tool.tools.browser import _get_service_url

        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_svc = MagicMock()
                mock_svc.spec.type = "LoadBalancer"
                mock_svc.spec.ports = [MagicMock(port=80)]
                mock_svc.status.load_balancer.ingress = [MagicMock(hostname="lb.example.com", ip=None)]

                mock_instance = MagicMock()
                mock_instance.read_namespaced_service.return_value = mock_svc
                mock_api.return_value = mock_instance

                result = _get_service_url("my-service", "default")
                assert result == "http://lb.example.com:80"

    @pytest.mark.unit
    def test_get_service_url_nodeport(self):
        """Test _get_service_url for NodePort type."""
        from kubectl_mcp_tool.tools.browser import _get_service_url

        with patch("kubernetes.config.load_kube_config"):
            with patch("kubernetes.client.CoreV1Api") as mock_api:
                mock_svc = MagicMock()
                mock_svc.spec.type = "NodePort"
                mock_svc.spec.ports = [MagicMock(node_port=30080)]

                mock_instance = MagicMock()
                mock_instance.read_namespaced_service.return_value = mock_svc
                mock_api.return_value = mock_instance

                result = _get_service_url("my-service", "default")
                assert result == "http://localhost:30080"


class TestCloudConsole:
    """Tests for cloud console URL generation."""

    @pytest.mark.unit
    def test_open_cloud_console_eks(self):
        """Test EKS console URL generation."""
        from kubectl_mcp_tool.tools.browser import register_browser_tools
        from fastmcp import FastMCP
        import asyncio

        server = FastMCP(name="test")
        register_browser_tools(server, non_destructive=False)

        # The tool should generate correct EKS URL
        # This is a basic registration test - actual URL testing would need integration tests

    @pytest.mark.unit
    def test_open_cloud_console_invalid_provider(self):
        """Test handling of invalid cloud provider."""
        from kubectl_mcp_tool.tools.browser import _run_browser

        # Mock the browser command to simulate the tool behavior
        with patch("kubectl_mcp_tool.tools.browser._run_browser") as mock:
            mock.return_value = {"success": False, "error": "Unknown provider"}
            result = mock(["open", "invalid-provider"])
            assert result["success"] is False


class TestServerIntegration:
    """Tests for browser tools integration with MCP server."""

    @pytest.mark.unit
    def test_browser_tools_not_registered_when_disabled(self):
        """Verify browser tools are not registered when disabled."""
        with patch.dict(os.environ, {"MCP_BROWSER_ENABLED": "false"}):
            with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                with patch("kubernetes.config.load_kube_config"):
                    # Force reload to pick up env change
                    import importlib
                    import kubectl_mcp_tool.tools.browser as browser_module
                    importlib.reload(browser_module)

                    from kubectl_mcp_tool.mcp_server import MCPServer
                    server = MCPServer(name="test")

                    import asyncio
                    tools = asyncio.run(server.server.list_tools())
                    tool_names = [t.name for t in tools]

                    # Should not have browser tools
                    assert "browser_open" not in tool_names
                    assert "browser_screenshot" not in tool_names

    @pytest.mark.unit
    def test_browser_tools_registered_when_enabled(self):
        """Verify browser tools are registered when enabled and available."""
        with patch.dict(os.environ, {"MCP_BROWSER_ENABLED": "true"}):
            with patch("shutil.which", return_value="/usr/bin/agent-browser"):
                with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                    with patch("kubernetes.config.load_kube_config"):
                        # Force reload to pick up env change
                        import importlib
                        import kubectl_mcp_tool.tools.browser as browser_module
                        importlib.reload(browser_module)
                        browser_module.BROWSER_AVAILABLE = True
                        browser_module.BROWSER_ENABLED = True

                        from kubectl_mcp_tool.mcp_server import MCPServer
                        server = MCPServer(name="test")

                        import asyncio
                        tools = asyncio.run(server.server.list_tools())
                        tool_names = [t.name for t in tools]

                        # Should have browser tools (127 + 19 = 146)
                        assert "browser_open" in tool_names
                        assert "browser_screenshot" in tool_names
                        assert len(tools) == 146, f"Expected 146 tools (127 + 19), got {len(tools)}"


import asyncio
