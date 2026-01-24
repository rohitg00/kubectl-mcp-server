"""Unit tests for the enhanced CLI module."""

import pytest
import os
import sys
import json
from unittest.mock import patch, MagicMock
from io import StringIO


class TestCliErrors:
    """Tests for CLI error handling module."""

    @pytest.mark.unit
    def test_error_code_values(self):
        """Test ErrorCode enum values."""
        from kubectl_mcp_tool.cli.errors import ErrorCode

        assert ErrorCode.SUCCESS == 0
        assert ErrorCode.CLIENT_ERROR == 1
        assert ErrorCode.SERVER_ERROR == 2
        assert ErrorCode.K8S_ERROR == 3
        assert ErrorCode.BROWSER_ERROR == 4
        assert ErrorCode.NETWORK_ERROR == 5

    @pytest.mark.unit
    def test_cli_error_dataclass(self):
        """Test CliError dataclass."""
        from kubectl_mcp_tool.cli.errors import CliError, ErrorCode

        error = CliError(
            code=ErrorCode.CLIENT_ERROR,
            type="TEST_ERROR",
            message="Test message",
            details="Test details",
            suggestion="Test suggestion"
        )

        assert error.code == ErrorCode.CLIENT_ERROR
        assert error.type == "TEST_ERROR"
        assert error.message == "Test message"
        assert error.details == "Test details"
        assert error.suggestion == "Test suggestion"

    @pytest.mark.unit
    def test_format_cli_error(self):
        """Test format_cli_error function."""
        from kubectl_mcp_tool.cli.errors import CliError, ErrorCode, format_cli_error

        error = CliError(
            code=ErrorCode.CLIENT_ERROR,
            type="TEST_ERROR",
            message="Something went wrong",
            details="More info here",
            suggestion="Try this instead"
        )

        formatted = format_cli_error(error)

        assert "Error [TEST_ERROR]: Something went wrong" in formatted
        assert "Details: More info here" in formatted
        assert "Suggestion: Try this instead" in formatted

    @pytest.mark.unit
    def test_tool_not_found_error(self):
        """Test tool_not_found_error factory."""
        from kubectl_mcp_tool.cli.errors import tool_not_found_error, ErrorCode

        error = tool_not_found_error("nonexistent_tool", ["get_pods", "list_namespaces"])

        assert error.code == ErrorCode.CLIENT_ERROR
        assert error.type == "TOOL_NOT_FOUND"
        assert "nonexistent_tool" in error.message
        assert "get_pods" in error.details

    @pytest.mark.unit
    def test_invalid_json_error(self):
        """Test invalid_json_error factory."""
        from kubectl_mcp_tool.cli.errors import invalid_json_error, ErrorCode

        error = invalid_json_error("{invalid json}", "Expecting value")

        assert error.code == ErrorCode.CLIENT_ERROR
        assert error.type == "INVALID_JSON"
        assert "Expecting value" in error.details

    @pytest.mark.unit
    def test_unknown_subcommand_error(self):
        """Test unknown_subcommand_error factory with suggestions."""
        from kubectl_mcp_tool.cli.errors import unknown_subcommand_error

        # Test known alias
        error = unknown_subcommand_error("run")
        assert "call" in error.suggestion

        # Test unknown command
        error = unknown_subcommand_error("unknown")
        assert "help" in error.suggestion.lower()

    @pytest.mark.unit
    def test_browser_not_found_error(self):
        """Test browser_not_found_error factory."""
        from kubectl_mcp_tool.cli.errors import browser_not_found_error, ErrorCode

        error = browser_not_found_error()

        assert error.code == ErrorCode.BROWSER_ERROR
        assert "agent-browser" in error.message
        assert "npm install" in error.suggestion


class TestCliOutput:
    """Tests for CLI output formatting module."""

    @pytest.mark.unit
    def test_should_colorize_respects_no_color(self):
        """Test that NO_COLOR env var disables colors."""
        from kubectl_mcp_tool.cli.output import should_colorize

        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            assert should_colorize() is False

    @pytest.mark.unit
    def test_format_tools_list_json(self):
        """Test format_tools_list with JSON output."""
        from kubectl_mcp_tool.cli.output import format_tools_list

        tools = [
            {"name": "get_pods", "description": "Get pods", "category": "pods"},
            {"name": "list_namespaces", "description": "List namespaces", "category": "core"},
        ]

        result = format_tools_list(tools, as_json=True)
        parsed = json.loads(result)

        assert len(parsed) == 2
        assert parsed[0]["name"] == "get_pods"

    @pytest.mark.unit
    def test_format_tools_list_text(self):
        """Test format_tools_list with text output."""
        from kubectl_mcp_tool.cli.output import format_tools_list

        tools = [
            {"name": "get_pods", "description": "Get pods", "category": "pods"},
        ]

        # Disable colors for predictable output
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            result = format_tools_list(tools, with_descriptions=True)

        assert "get_pods" in result
        assert "Get pods" in result

    @pytest.mark.unit
    def test_format_tool_schema(self):
        """Test format_tool_schema function."""
        from kubectl_mcp_tool.cli.output import format_tool_schema

        tool = {
            "name": "get_pods",
            "description": "Get pods in a namespace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "namespace": {"type": "string", "description": "Namespace name"}
                },
                "required": ["namespace"]
            }
        }

        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            result = format_tool_schema(tool)

        assert "get_pods" in result
        assert "Get pods in a namespace" in result
        assert "namespace" in result
        assert "required" in result

    @pytest.mark.unit
    def test_format_server_info(self):
        """Test format_server_info function."""
        from kubectl_mcp_tool.cli.output import format_server_info

        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            result = format_server_info(
                version="1.14.0",
                tool_count=127,
                resource_count=8,
                prompt_count=8,
                context="minikube"
            )

        assert "1.14.0" in result
        assert "127" in result
        assert "minikube" in result

    @pytest.mark.unit
    def test_format_doctor_results(self):
        """Test format_doctor_results function."""
        from kubectl_mcp_tool.cli.output import format_doctor_results

        checks = [
            {"name": "kubectl", "status": "ok", "version": "v1.28.0"},
            {"name": "helm", "status": "warning", "details": "Not installed"},
            {"name": "kubernetes", "status": "error", "details": "Connection failed"},
        ]

        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            result = format_doctor_results(checks)

        assert "kubectl" in result
        assert "v1.28.0" in result
        assert "Some checks failed" in result


class TestCliCommands:
    """Tests for CLI command handlers."""

    @pytest.mark.unit
    def test_main_help(self):
        """Test that --help works."""
        from kubectl_mcp_tool.cli.cli import main

        with patch.object(sys, 'argv', ['kubectl-mcp-server', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 0 for --help
            assert exc_info.value.code == 0

    @pytest.mark.unit
    def test_get_tool_category(self):
        """Test tool category detection."""
        from kubectl_mcp_tool.cli.cli import _get_tool_category

        assert _get_tool_category("get_pods") == "pods"
        assert _get_tool_category("list_deployments") == "deployments"
        assert _get_tool_category("helm_install") == "helm"
        assert _get_tool_category("browser_open") == "browser"
        assert _get_tool_category("unknown_tool") == "other"

    @pytest.mark.unit
    def test_cmd_doctor_checks_kubectl(self):
        """Test that doctor command checks for kubectl."""
        from kubectl_mcp_tool.cli.cli import cmd_doctor

        args = MagicMock()
        args.json = True

        # Mock shutil.which to simulate kubectl present
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: f"/usr/bin/{x}" if x == "kubectl" else None

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout='{"clientVersion": {"gitVersion": "v1.28.0"}}'
                )

                with patch("kubectl_mcp_tool.cli.cli.format_doctor_results") as mock_format:
                    mock_format.return_value = "{}"
                    cmd_doctor(args)

                # Should have called shutil.which for kubectl
                mock_which.assert_any_call("kubectl")


class TestCliIntegration:
    """Integration tests for CLI module."""

    @pytest.mark.unit
    def test_cli_module_imports(self):
        """Test that all CLI modules can be imported."""
        from kubectl_mcp_tool.cli import (
            main,
            CliError,
            ErrorCode,
            format_cli_error,
            format_tools_list,
            format_server_info,
        )

        assert main is not None
        assert CliError is not None
        assert ErrorCode is not None

    @pytest.mark.unit
    def test_error_str_representation(self):
        """Test CliError __str__ method."""
        from kubectl_mcp_tool.cli.errors import CliError, ErrorCode

        error = CliError(
            code=ErrorCode.CLIENT_ERROR,
            type="TEST",
            message="Test message"
        )

        assert "TEST" in str(error)
        assert "Test message" in str(error)
