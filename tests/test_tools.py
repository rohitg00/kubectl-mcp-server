import ast
import asyncio
import pathlib
import subprocess
from unittest.mock import patch

import pytest
from fastmcp import Client

from kubectl_mcp_tool.mcp_server import MCPServer
from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode
from kubectl_mcp_tool.toolsets import DEFAULT_TOOLSETS, TOOL_TOOLSET, TOOLSETS, _BY_TOOLSET, resolve_toolsets

TOOLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "kubectl_mcp_tool" / "tools"
DEFAULT_TOOLS = {t for ts in DEFAULT_TOOLSETS for t in _BY_TOOLSET[ts]}


@pytest.fixture(autouse=True)
def reset_safety():
    set_safety_mode(SafetyMode.NORMAL)
    yield
    set_safety_mode(SafetyMode.NORMAL)


def make_server(**kwargs) -> MCPServer:
    with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
        return MCPServer(name="test", **kwargs)


def listed(server) -> set:
    return {t.name for t in asyncio.run(server.server.list_tools())}


def decorated_tools() -> set:
    names = set()
    for path in TOOLS_DIR.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "tool" for d in node.decorator_list
            ):
                names.add(node.name)
    return names


def call(server, name, args):
    async def run():
        async with Client(server.server, mode="2026-07-28") as client:
            return await client.call_tool(name, args, raise_on_error=False)
    return asyncio.run(run())


def ok(stdout="ok"):
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


class TestToolsets:
    def test_every_tool_is_assigned_to_exactly_one_toolset(self):
        assert decorated_tools() == set(TOOL_TOOLSET)
        assert len(TOOL_TOOLSET) == sum(len(v) for v in _BY_TOOLSET.values())

    def test_default_registers_only_core_and_helm(self):
        server = make_server()
        assert listed(server) == DEFAULT_TOOLS
        assert len(DEFAULT_TOOLS) <= 30

    def test_all_registers_every_tool(self):
        assert listed(make_server(toolsets="all")) == set(TOOL_TOOLSET)

    def test_disabled_toolsets_are_not_registered(self):
        server = make_server(toolsets="default,gitops")
        names = listed(server)
        assert "gitops_app_sync" in names and "list_certs" not in names
        assert asyncio.run(server.server.get_tool("list_certs")) is None

    def test_resolve_toolsets(self):
        assert resolve_toolsets(None) == DEFAULT_TOOLSETS
        assert resolve_toolsets("all") == set(TOOLSETS)
        assert resolve_toolsets("core") == {"core"}
        with pytest.raises(ValueError, match="Unknown toolset"):
            resolve_toolsets("default,nope")

    def test_instructions_point_to_official_servers(self):
        text = make_server().server.instructions
        assert "argoproj-labs/mcp-for-argocd" in text and "kyverno-mcp" in text
        assert "gitops" in text and "--toolsets" in text

    def test_call_tool_proxy_still_runs_guards(self):
        server = make_server(toolsets="all", tool_search=True)
        with patch("kubectl_mcp_tool.tools.utils.subprocess.run") as run:
            result = call(server, "call_tool", {"name": "kubectl_get", "arguments": {"resource_type": "--kubeconfig=/tmp/x"}})
        assert result.is_error and not run.called

    def test_tool_search_lists_defaults_plus_discovery_tools(self):
        server = make_server(toolsets="all", tool_search=True)
        assert listed(server) == DEFAULT_TOOLS | {"search_tools", "call_tool"}

    def test_all_tools_have_descriptions_and_annotations(self):
        for tool in asyncio.run(make_server(toolsets="all").server.list_tools()):
            assert tool.description and tool.description.strip(), tool.name
            assert tool.annotations is not None and tool.annotations.read_only_hint is not None, tool.name


class TestCoreTools:
    def run_tool(self, name, args, stdout="ok"):
        server = make_server()
        with patch("kubectl_mcp_tool.tools.utils.subprocess.run", return_value=ok(stdout)) as run:
            result = call(server, name, args)
        return result, run.call_args[0][0] if run.called else None

    def test_kubectl_get_builds_command(self):
        result, cmd = self.run_tool("kubectl_get", {
            "resource_type": "pods", "namespace": "web", "label_selector": "app=api",
            "field_selector": "status.phase=Running", "output": "wide", "sort_by": ".metadata.name",
        })
        assert cmd == ["kubectl", "get", "pods", "-n", "web", "-l", "app=api", "--field-selector",
                       "status.phase=Running", "--sort-by", ".metadata.name", "-o", "wide"]
        assert result.structured_content["success"] is True

    def test_kubectl_get_custom_resource_all_namespaces(self):
        _, cmd = self.run_tool("kubectl_get", {"resource_type": "certificates.cert-manager.io", "all_namespaces": True})
        assert cmd == ["kubectl", "get", "certificates.cert-manager.io", "--all-namespaces"]

    def test_kubectl_get_rejects_unknown_output(self):
        result, cmd = self.run_tool("kubectl_get", {"resource_type": "pods", "output": "go-template={{.}}"})
        assert cmd is None and result.structured_content["success"] is False

    def test_kubectl_get_truncates_large_output(self):
        result, _ = self.run_tool("kubectl_get", {"resource_type": "pods"}, stdout="x" * 70_000)
        assert result.structured_content["truncated"] is True
        assert len(result.structured_content["output"]) == 60_000

    def test_kubectl_logs_previous_and_since(self):
        _, cmd = self.run_tool("kubectl_logs", {"pod_name": "deployment/web", "namespace": "prod", "previous": True, "since": "10m"})
        assert cmd == ["kubectl", "logs", "deployment/web", "-n", "prod", "--tail=200", "--previous", "--since=10m"]

    def test_kubectl_logs_rejects_bad_since(self):
        result, cmd = self.run_tool("kubectl_logs", {"pod_name": "web", "since": "yesterday"})
        assert cmd is None and result.structured_content["success"] is False

    def test_kubectl_top_nodes(self):
        _, cmd = self.run_tool("kubectl_top", {"resource": "nodes", "sort_by": "cpu"})
        assert cmd == ["kubectl", "top", "nodes", "--sort-by", "cpu"]

    def test_kubectl_scale(self):
        _, cmd = self.run_tool("kubectl_scale", {"resource_type": "statefulset", "name": "db", "replicas": 3})
        assert cmd == ["kubectl", "scale", "statefulset/db", "--replicas=3", "-n", "default"]

    def test_kubectl_scale_blocked_in_read_only(self):
        server = make_server(read_only=True)
        with patch("kubectl_mcp_tool.tools.utils.subprocess.run") as run:
            result = call(server, "kubectl_scale", {"resource_type": "deployment", "name": "web", "replicas": 1})
        assert result.is_error and not run.called

    def test_kubectl_scale_to_zero_blocked_when_destructive_disabled(self):
        server = make_server(disable_destructive=True)
        with patch("kubectl_mcp_tool.tools.utils.subprocess.run") as run:
            result = call(server, "kubectl_scale", {"resource_type": "deployment", "name": "web", "replicas": 0})
        assert result.structured_content["success"] is False and not run.called

    def test_detect_ecosystem_maps_operators_to_toolsets(self):
        server = make_server(toolsets="default,gitops")
        crds = {"flux": True, "argocd": False, "certmanager": True}
        with patch("kubectl_mcp_tool.tools.kubectl.detect_crds", return_value=crds), \
                patch("kubectl_mcp_tool.tools.kubectl.shutil.which", return_value=None):
            data = call(server, "detect_ecosystem", {}).structured_content
        assert data["installed_operators"] == ["certmanager", "flux"]
        assert data["toolsets"]["gitops"]["enabled"] is True
        assert data["toolsets"]["certs"]["enabled"] is False
        assert any("mcp-for-argocd" in s for s in data["toolsets"]["gitops"]["official_mcp_servers"])


class TestHelmTools:
    def run_helm(self, name, args, stdout="[]"):
        server = make_server(toolsets="default,helm_dev")
        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_helm_availability", return_value=True), \
                patch("kubectl_mcp_tool.tools.helm.subprocess.run", return_value=ok(stdout)) as run:
            result = call(server, name, args)
        return result, run.call_args[0][0] if run.called else None

    def test_helm_list_works_on_helm_3_and_4(self):
        _, cmd = self.run_helm("helm_list", {"all_namespaces": True})
        assert "--all" not in cmd
        assert {"--deployed", "--failed", "--pending", "--superseded", "--uninstalled", "--uninstalling"} <= set(cmd)

    def test_helm_get_values(self):
        _, cmd = self.run_helm("helm_get", {"release_name": "web", "namespace": "apps", "all_values": True}, stdout="a: 1")
        assert cmd == ["helm", "get", "values", "web", "-n", "apps", "--output", "yaml", "--all"]

    def test_helm_get_manifest_revision(self):
        _, cmd = self.run_helm("helm_get", {"release_name": "web", "what": "manifest", "revision": 2})
        assert cmd == ["helm", "get", "manifest", "web", "-n", "default", "--revision", "2"]

    def test_helm_get_rejects_unknown_section(self):
        result, cmd = self.run_helm("helm_get", {"release_name": "web", "what": "secrets"})
        assert cmd is None and result.structured_content["success"] is False

    def test_helm_show(self):
        _, cmd = self.run_helm("helm_show", {"chart": "bitnami/nginx", "what": "readme", "version": "1.2.3"})
        assert cmd == ["helm", "show", "readme", "bitnami/nginx", "--version", "1.2.3"]
