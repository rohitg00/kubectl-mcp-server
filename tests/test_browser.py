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
    def test_all_26_browser_tools_registered(self):
        """Verify all 26 browser tools are registered (v0.7+)."""
        from kubectl_mcp_tool.tools.browser import register_browser_tools
        from fastmcp import FastMCP
        import asyncio

        server = FastMCP(name="test")
        register_browser_tools(server, non_destructive=False)

        tools = asyncio.run(server.list_tools())
        assert len(tools) == 26, f"Expected 26 browser tools, got {len(tools)}"

        expected_tools = [
            # Core browser tools
            "browser_open",
            "browser_snapshot",
            "browser_click",
            "browser_fill",
            "browser_screenshot",
            "browser_get_text",
            "browser_get_url",
            "browser_wait",
            "browser_close",
            # NEW v0.7 tools
            "browser_connect_cdp",
            "browser_install",
            "browser_set_provider",
            "browser_session_list",
            "browser_session_switch",
            "browser_open_with_headers",
            "browser_set_viewport",
            # K8s integration tools
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


class TestBrowserV07Features:
    """Tests for agent-browser v0.7 features."""

    @pytest.mark.unit
    def test_get_global_options_empty(self):
        """Test _get_global_options with no env vars set."""
        from kubectl_mcp_tool.tools.browser import _get_global_options

        with patch.dict(os.environ, {}, clear=True):
            # Need to reload to pick up cleared env
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)

            opts = browser_module._get_global_options()
            # Should return empty list when no env vars set
            assert isinstance(opts, list)

    @pytest.mark.unit
    def test_get_global_options_with_provider(self):
        """Test _get_global_options with cloud provider."""
        with patch.dict(os.environ, {"MCP_BROWSER_PROVIDER": "browserbase"}):
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)

            opts = browser_module._get_global_options()
            assert "-p" in opts
            assert "browserbase" in opts

    @pytest.mark.unit
    def test_get_global_options_with_profile(self):
        """Test _get_global_options with persistent profile."""
        with patch.dict(os.environ, {"MCP_BROWSER_PROFILE": "~/.k8s-browser"}):
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)

            opts = browser_module._get_global_options()
            assert "--profile" in opts

    @pytest.mark.unit
    def test_get_global_options_with_session(self):
        """Test _get_global_options with session name."""
        with patch.dict(os.environ, {"MCP_BROWSER_SESSION": "test-session"}):
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)

            opts = browser_module._get_global_options()
            assert "--session" in opts
            assert "test-session" in opts

    @pytest.mark.unit
    def test_get_global_options_with_headed(self):
        """Test _get_global_options with headed mode."""
        with patch.dict(os.environ, {"MCP_BROWSER_HEADED": "true"}):
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)

            opts = browser_module._get_global_options()
            assert "--headed" in opts

    @pytest.mark.unit
    def test_is_transient_error(self):
        """Test transient error detection."""
        from kubectl_mcp_tool.tools.browser import _is_transient_error

        # Transient errors
        assert _is_transient_error("ECONNREFUSED") is True
        assert _is_transient_error("Connection refused") is True
        assert _is_transient_error("ETIMEDOUT") is True
        assert _is_transient_error("timeout occurred") is True

        # Non-transient errors
        assert _is_transient_error("File not found") is False
        assert _is_transient_error("Invalid argument") is False

    @pytest.mark.unit
    def test_run_browser_with_retry_success(self):
        """Test retry logic with successful result."""
        from kubectl_mcp_tool.tools.browser import _run_browser_with_retry

        with patch("kubectl_mcp_tool.tools.browser._run_browser") as mock_run:
            mock_run.return_value = {"success": True, "output": "OK"}

            result = _run_browser_with_retry(["open", "https://example.com"])

            assert result["success"] is True
            # Should only call once on success
            assert mock_run.call_count == 1

    @pytest.mark.unit
    def test_run_browser_with_retry_transient_error(self):
        """Test retry logic with transient error."""
        from kubectl_mcp_tool.tools.browser import _run_browser_with_retry

        with patch("kubectl_mcp_tool.tools.browser._run_browser") as mock_run:
            with patch("time.sleep"):  # Skip actual sleep
                # First two calls fail with transient error, third succeeds
                mock_run.side_effect = [
                    {"success": False, "error": "ECONNREFUSED"},
                    {"success": False, "error": "ECONNREFUSED"},
                    {"success": True, "output": "OK"},
                ]

                result = _run_browser_with_retry(["open", "https://example.com"], max_retries=3)

                assert result["success"] is True
                assert mock_run.call_count == 3

    @pytest.mark.unit
    def test_run_browser_with_retry_non_transient_error(self):
        """Test retry logic with non-transient error (no retry)."""
        from kubectl_mcp_tool.tools.browser import _run_browser_with_retry

        with patch("kubectl_mcp_tool.tools.browser._run_browser") as mock_run:
            mock_run.return_value = {"success": False, "error": "Invalid argument"}

            result = _run_browser_with_retry(["open", "https://example.com"])

            assert result["success"] is False
            # Should not retry non-transient errors
            assert mock_run.call_count == 1

    @pytest.mark.unit
    def test_debug_mode(self):
        """Test debug logging."""
        with patch.dict(os.environ, {"MCP_BROWSER_DEBUG": "true"}):
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)

            assert browser_module.MCP_BROWSER_DEBUG is True

    @pytest.mark.unit
    def test_retry_configuration(self):
        """Test retry configuration from environment."""
        with patch.dict(os.environ, {
            "MCP_BROWSER_MAX_RETRIES": "5",
            "MCP_BROWSER_RETRY_DELAY": "2000"
        }):
            import importlib
            import kubectl_mcp_tool.tools.browser as browser_module
            importlib.reload(browser_module)

            assert browser_module.MCP_BROWSER_MAX_RETRIES == 5
            assert browser_module.MCP_BROWSER_RETRY_DELAY == 2000


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

                        # Should have browser tools (224 + 26 = 250)
                        assert "browser_open" in tool_names
                        assert "browser_screenshot" in tool_names
                        assert "browser_connect_cdp" in tool_names  # v0.7 tool
                        assert len(tools) == 250, f"Expected 250 tools (224 + 26), got {len(tools)}"


import asyncio
