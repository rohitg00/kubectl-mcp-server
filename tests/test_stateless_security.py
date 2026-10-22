import json
import os
import subprocess
from unittest.mock import patch

import pytest
import yaml
from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from fastmcp.exceptions import ToolError

from kubectl_mcp_tool.mcp_server import (
    MCPServer,
    NetworkExposureError,
    ensure_network_exposure_allowed,
    is_loopback_host,
    main,
)
from kubectl_mcp_tool.middleware import reject_option_injection
from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode
from kubectl_mcp_tool.tools.operations import validate_generic_command
from kubectl_mcp_tool.utils.helpers import REDACTED, mask_secrets, redact_secrets

SECRET_YAML = """apiVersion: v1
kind: Secret
metadata:
  name: db
  annotations:
    kubectl.kubernetes.io/last-applied-configuration: '{"data":{"password":"aHVudGVyMg=="},"kind":"Secret"}'
data:
  password: aHVudGVyMg==
type: Opaque
"""


@pytest.fixture(autouse=True)
def reset_safety():
    set_safety_mode(SafetyMode.NORMAL)
    yield
    set_safety_mode(SafetyMode.NORMAL)


def make_server(**kwargs) -> MCPServer:
    with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
        return MCPServer(name="test", **kwargs)


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


async def accept_all(message, response_type, params, context):
    return ElicitResult(action="accept", content={k: True for k in params.requested_schema["properties"]})


async def decline(message, response_type, params, context):
    return ElicitResult(action="decline")


class TestSecretRedaction:
    def test_yaml_secret_values_and_last_applied_are_redacted(self):
        out = yaml.safe_load(mask_secrets(SECRET_YAML))
        assert out["data"] == {"password": REDACTED}
        assert out["metadata"]["annotations"]["kubectl.kubernetes.io/last-applied-configuration"] == REDACTED
        assert out["type"] == "Opaque"

    def test_raw_api_secret_list_items_are_redacted(self):
        raw = json.dumps({"kind": "SecretList", "items": [{"metadata": {"name": "a"}, "data": {"k": "dg=="}}]})
        assert json.loads(mask_secrets(raw))["items"][0]["data"] == {"k": REDACTED}

    def test_secret_embedded_in_structured_result(self):
        out = redact_secrets({"success": True, "yaml": SECRET_YAML})
        assert "aHVudGVyMg==" not in out["yaml"]

    def test_non_secret_output_is_untouched(self):
        text = "apiVersion: v1\nkind: ConfigMap\ndata:\n  key: value\n  password: notmasked\n"
        assert mask_secrets(text) == text
        assert mask_secrets("Secret rotation finished") == "Secret rotation finished"

    def test_tokens_are_masked(self):
        jwt = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJzeXN0ZW06YWRtaW4ifQ.c2lnbmF0dXJl"
        assert jwt not in mask_secrets(f"token: {jwt}")
        assert "abcdefghijklmnopqrstuvwxyz" not in mask_secrets("Authorization: Bearer abcdefghijklmnopqrstuvwxyz")


class TestOptionInjection:
    @pytest.mark.parametrize("args", [
        {"name": "--server=https://attacker.example"},
        {"chart": "--post-renderer=/bin/sh"},
        {"labels": {"--overwrite": "x"}},
        {"contexts": ["ok", "-x"]},
    ])
    def test_flag_like_values_are_rejected(self, args):
        with pytest.raises(ToolError):
            reject_option_injection(args)

    def test_free_text_and_normal_values_pass(self):
        reject_option_injection({"manifest": "---\nkind: Pod", "name": "nginx", "command": ["ls", "-la"], "replicas": 3})


class TestKubectlGeneric:
    @pytest.mark.parametrize("cmd", ["get pods -A", "describe pod x", "auth can-i list pods", "config get-contexts", "get secrets"])
    def test_safe_reads_allowed(self, cmd):
        assert validate_generic_command(cmd.split()) is None

    @pytest.mark.parametrize("cmd", [
        "get pods --server=https://attacker.example",
        "get pods -shttps://attacker.example",
        "get pods --kubeconfig=/tmp/evil",
        "get --raw /api/v1/secrets",
        "config use-context prod",
        "config view --flatten",
        "get secret db -o jsonpath={.data.password}",
        "get pods,secrets -oyaml",
        "delete pod x",
        "auth reconcile -f x",
    ])
    def test_unsafe_commands_blocked(self, cmd):
        assert validate_generic_command(cmd.split()) is not None


class TestNetworkExposure:
    @pytest.mark.parametrize("host", ["127.0.0.1", "127.0.0.5", "localhost", "::1", "[::1]"])
    def test_loopback(self, host):
        assert is_loopback_host(host)
        ensure_network_exposure_allowed(host, auth_enabled=False, allow_unauthenticated=False)

    def test_public_bind_requires_auth_or_opt_in(self):
        with pytest.raises(NetworkExposureError):
            ensure_network_exposure_allowed("0.0.0.0", auth_enabled=False, allow_unauthenticated=False)
        ensure_network_exposure_allowed("0.0.0.0", auth_enabled=True, allow_unauthenticated=False)
        ensure_network_exposure_allowed("0.0.0.0", auth_enabled=False, allow_unauthenticated=True)

    def test_cli_refuses_public_http_without_auth(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MCP_ALLOW_UNAUTHENTICATED", None)
            with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
                assert main(["serve", "--transport", "http", "--host", "0.0.0.0"]) == 2

    def test_invalid_safety_mode_fails_closed(self):
        with patch.dict(os.environ, {"MCP_SAFETY_MODE": "readonly"}):
            with pytest.raises(ValueError, match="Invalid safety mode"):
                make_server()

    def test_safety_mode_from_env(self):
        with patch.dict(os.environ, {"MCP_SAFETY_MODE": "read-only"}):
            make_server()
        from kubectl_mcp_tool.safety import get_safety_mode
        assert get_safety_mode() == SafetyMode.READ_ONLY


@pytest.mark.asyncio
class TestBothProtocolEras:
    @pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
    async def test_list_and_call(self, mode):
        server = make_server()
        async with Client(server.server, mode=mode) as client:
            assert (client.protocol_version == "2026-07-28") == (mode == "2026-07-28")
            tools = await client.list_tools()
            assert len(tools) > 250
            with patch("kubectl_mcp_tool.tools.operations.subprocess.run", return_value=completed(SECRET_YAML)):
                result = await client.call_tool("backup_resource", {"resource_type": "secret", "name": "db", "namespace": "default"})
        assert "aHVudGVyMg==" not in json.dumps(result.structured_content)
        assert all("aHVudGVyMg==" not in getattr(c, "text", "") for c in result.content)

    async def test_read_only_hides_and_blocks_writes(self):
        server = make_server(read_only=True)
        async with Client(server.server, mode="2026-07-28") as client:
            names = {t.name for t in await client.list_tools()}
            assert "get_pods" in names and "delete_resource" not in names
            with pytest.raises(Exception, match="read-only|Unknown tool|not found"):
                await client.call_tool("delete_resource", {"resource_type": "pod", "name": "x"})

    async def test_option_injection_blocked_end_to_end(self):
        server = make_server()
        async with Client(server.server, mode="2026-07-28") as client:
            with patch("kubectl_mcp_tool.tools.operations.subprocess.run") as run:
                with pytest.raises(ToolError, match="must not start with"):
                    await client.call_tool("kubectl_describe", {"resource_type": "pod", "name": "--server=https://attacker.example"})
                run.assert_not_called()

    @pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
    async def test_confirm_mode_accept(self, mode):
        server = make_server(confirm_destructive=True)
        async with Client(server.server, mode=mode, elicitation_handler=accept_all) as client:
            with patch("kubectl_mcp_tool.tools.operations.subprocess.run", return_value=completed("deleted")) as run:
                result = await client.call_tool("delete_resource", {"resource_type": "pod", "name": "nginx"})
        assert result.structured_content["success"] is True
        assert run.call_args[0][0][-5:] == ["delete", "pod", "nginx", "-n", "default"]

    @pytest.mark.parametrize("mode", ["2026-07-28", "legacy"])
    async def test_confirm_mode_decline(self, mode):
        server = make_server(confirm_destructive=True)
        async with Client(server.server, mode=mode, elicitation_handler=decline) as client:
            with patch("kubectl_mcp_tool.tools.operations.subprocess.run") as run:
                result = await client.call_tool("delete_resource", {"resource_type": "pod", "name": "nginx"})
                run.assert_not_called()
        assert "cancelled" in result.structured_content["error"].lower()
