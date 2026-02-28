"""Unit tests for dynamic CRD discovery and custom resource tools."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock


class TestCRDCategories:

    @pytest.mark.unit
    def test_all_categories_have_required_keys(self):
        from kubectl_mcp_tool.tools.custom_resources import CRD_CATEGORIES

        assert len(CRD_CATEGORIES) == 23
        for name, info in CRD_CATEGORIES.items():
            assert "description" in info, f"Category '{name}' missing 'description'"
            assert "patterns" in info, f"Category '{name}' missing 'patterns'"
            assert "known_crds" in info, f"Category '{name}' missing 'known_crds'"
            assert isinstance(info["patterns"], list)
            assert isinstance(info["known_crds"], dict)
            assert len(info["patterns"]) > 0, f"Category '{name}' has no patterns"

    @pytest.mark.unit
    def test_known_crds_have_rich_descriptions(self):
        from kubectl_mcp_tool.tools.custom_resources import CRD_CATEGORIES

        for cat_name, cat_info in CRD_CATEGORIES.items():
            for crd_name, desc in cat_info["known_crds"].items():
                assert len(desc) > 30, (
                    f"CRD '{crd_name}' in '{cat_name}' has a short description ({len(desc)} chars). "
                    f"Expected rich semantic description."
                )

    @pytest.mark.unit
    def test_expected_categories_present(self):
        from kubectl_mcp_tool.tools.custom_resources import CRD_CATEGORIES

        expected = [
            "databases", "messaging", "certificates", "networking",
            "service_mesh", "monitoring", "logging", "gitops",
            "progressive_delivery", "autoscaling", "storage",
            "security", "secrets_management", "virtualization",
            "ai_ml", "workflows", "cluster_management", "serverless",
            "dns", "chaos_engineering", "api_gateway",
            "container_registry", "identity",
        ]
        for cat in expected:
            assert cat in CRD_CATEGORIES, f"Expected category '{cat}' not found"


class TestClassifyCRD:

    @pytest.mark.unit
    def test_classify_known_crd(self):
        from kubectl_mcp_tool.tools.custom_resources import _classify_crd

        result = _classify_crd(
            "clusters.postgresql.cnpg.io", "postgresql.cnpg.io", "Cluster"
        )
        assert "databases" in result["categories"]
        assert result["description"] is not None
        assert "CloudNativePG" in result["description"]

    @pytest.mark.unit
    def test_classify_known_kafka(self):
        from kubectl_mcp_tool.tools.custom_resources import _classify_crd

        result = _classify_crd(
            "kafkas.kafka.strimzi.io", "kafka.strimzi.io", "Kafka"
        )
        assert "messaging" in result["categories"]
        assert "Strimzi" in result["description"]

    @pytest.mark.unit
    def test_classify_unknown_crd_by_pattern(self):
        from kubectl_mcp_tool.tools.custom_resources import _classify_crd

        result = _classify_crd(
            "mydatabases.example.com", "example.com", "MyDatabase"
        )
        assert "databases" in result["categories"]
        assert result["description"] is None

    @pytest.mark.unit
    def test_classify_completely_unknown_crd(self):
        from kubectl_mcp_tool.tools.custom_resources import _classify_crd

        result = _classify_crd(
            "widgets.internal.corp", "internal.corp", "Widget"
        )
        assert result["categories"] == ["other"]
        assert result["description"] is None

    @pytest.mark.unit
    def test_classify_monitoring(self):
        from kubectl_mcp_tool.tools.custom_resources import _classify_crd

        result = _classify_crd(
            "prometheuses.monitoring.coreos.com",
            "monitoring.coreos.com",
            "Prometheus",
        )
        assert "monitoring" in result["categories"]

    @pytest.mark.unit
    def test_classify_cert_manager(self):
        from kubectl_mcp_tool.tools.custom_resources import _classify_crd

        result = _classify_crd(
            "certificates.cert-manager.io",
            "cert-manager.io",
            "Certificate",
        )
        assert "certificates" in result["categories"]
        assert result["description"] is not None


def _make_mock_crd(name, group, kind, plural, scope="Namespaced", version="v1"):
    crd = MagicMock()
    crd.metadata.name = name
    crd.spec.group = group
    crd.spec.names.kind = kind
    crd.spec.names.plural = plural
    crd.spec.names.short_names = []
    crd.spec.scope = scope
    ver = MagicMock()
    ver.name = version
    ver.served = True
    ver.storage = True
    ver.schema = None
    crd.spec.versions = [ver]
    return crd


class TestDiscoverCRDs:

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_discover_crds_basic(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api

        crds = [
            _make_mock_crd(
                "clusters.postgresql.cnpg.io",
                "postgresql.cnpg.io", "Cluster", "clusters",
            ),
            _make_mock_crd(
                "kafkas.kafka.strimzi.io",
                "kafka.strimzi.io", "Kafka", "kafkas",
            ),
            _make_mock_crd(
                "widgets.internal.corp",
                "internal.corp", "Widget", "widgets",
            ),
        ]
        mock_api.list_custom_resource_definition.return_value = MagicMock(items=crds)

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("discover_crds", {"category": "", "context": ""})
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["totalCRDs"] == 3
        assert "databases" in data["categories"]
        assert "messaging" in data["categories"]

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_discover_crds_filter_category(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api

        crds = [
            _make_mock_crd(
                "clusters.postgresql.cnpg.io",
                "postgresql.cnpg.io", "Cluster", "clusters",
            ),
            _make_mock_crd(
                "kafkas.kafka.strimzi.io",
                "kafka.strimzi.io", "Kafka", "kafkas",
            ),
        ]
        mock_api.list_custom_resource_definition.return_value = MagicMock(items=crds)

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("discover_crds", {"category": "databases", "context": ""})
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert "databases" in data["categories"]
        assert "messaging" not in data["categories"]

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_discover_crds_error(self, mock_get_client):
        mock_get_client.side_effect = Exception("connection refused")

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("discover_crds", {"category": "", "context": ""})
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is False
        assert "connection refused" in data["error"]


class TestSearchCRDs:

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_search_databases(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api

        crds = [
            _make_mock_crd(
                "clusters.postgresql.cnpg.io",
                "postgresql.cnpg.io", "Cluster", "clusters",
            ),
            _make_mock_crd(
                "kafkas.kafka.strimzi.io",
                "kafka.strimzi.io", "Kafka", "kafkas",
            ),
        ]
        mock_api.list_custom_resource_definition.return_value = MagicMock(items=crds)

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("search_crds", {"query": "databases", "context": ""})
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["count"] >= 1
        names = [r["name"] for r in data["results"]]
        assert "clusters.postgresql.cnpg.io" in names

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_search_kafka(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api

        crds = [
            _make_mock_crd(
                "kafkas.kafka.strimzi.io",
                "kafka.strimzi.io", "Kafka", "kafkas",
            ),
        ]
        mock_api.list_custom_resource_definition.return_value = MagicMock(items=crds)

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("search_crds", {"query": "kafka", "context": ""})
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["count"] == 1
        assert data["results"][0]["name"] == "kafkas.kafka.strimzi.io"

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_search_no_results(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api
        mock_api.list_custom_resource_definition.return_value = MagicMock(items=[])

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("search_crds", {"query": "nonexistent", "context": ""})
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["count"] == 0


class TestListCustomResources:

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_custom_objects_client")
    def test_list_namespaced(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api
        mock_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "metadata": {
                        "name": "my-db",
                        "namespace": "default",
                        "creationTimestamp": "2026-01-01T00:00:00Z",
                        "labels": {"app": "postgres"},
                    },
                    "status": {"phase": "Running", "conditions": []},
                    "spec": {"instances": 3},
                }
            ]
        }

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("list_custom_resources", {
                "group": "postgresql.cnpg.io",
                "version": "v1",
                "plural": "clusters",
                "namespace": "default",
                "label_selector": "",
                "limit": 100,
                "context": "",
            })
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["count"] == 1
        assert data["items"][0]["name"] == "my-db"
        assert data["items"][0]["replicas"] == 3

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_custom_objects_client")
    def test_list_cluster_scoped(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api
        mock_api.list_cluster_custom_object.return_value = {"items": []}

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("list_custom_resources", {
                "group": "example.io",
                "version": "v1",
                "plural": "widgets",
                "namespace": "",
                "label_selector": "",
                "limit": 100,
                "context": "",
            })
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["count"] == 0
        mock_api.list_cluster_custom_object.assert_called_once()

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_custom_objects_client")
    def test_list_404_error(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api
        mock_api.list_cluster_custom_object.side_effect = Exception("404 not found")

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("list_custom_resources", {
                "group": "missing.io",
                "version": "v1",
                "plural": "things",
                "namespace": "",
                "label_selector": "",
                "limit": 100,
                "context": "",
            })
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is False
        assert "not found" in data["error"].lower()
        assert "hint" in data


class TestGetCustomResource:

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_custom_objects_client")
    def test_get_namespaced(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api
        mock_api.get_namespaced_custom_object.return_value = {
            "metadata": {
                "name": "my-db",
                "namespace": "default",
                "uid": "abc-123",
                "creationTimestamp": "2026-01-01T00:00:00Z",
                "labels": {},
                "annotations": {"custom/note": "test"},
                "ownerReferences": [],
            },
            "spec": {"instances": 3, "storage": {"size": "10Gi"}},
            "status": {"phase": "Running"},
        }

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("get_custom_resource", {
                "group": "postgresql.cnpg.io",
                "version": "v1",
                "plural": "clusters",
                "name": "my-db",
                "namespace": "default",
                "context": "",
            })
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["metadata"]["name"] == "my-db"
        assert data["spec"]["instances"] == 3

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_custom_objects_client")
    def test_get_not_found(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api
        mock_api.get_namespaced_custom_object.side_effect = Exception("404 not found")

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("get_custom_resource", {
                "group": "postgresql.cnpg.io",
                "version": "v1",
                "plural": "clusters",
                "name": "missing",
                "namespace": "default",
                "context": "",
            })
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is False
        assert "not found" in data["error"].lower()


class TestDescribeCRD:

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_describe_crd(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api

        mock_crd = MagicMock()
        mock_crd.metadata.name = "clusters.postgresql.cnpg.io"
        mock_crd.spec.group = "postgresql.cnpg.io"
        mock_crd.spec.names.kind = "Cluster"
        mock_crd.spec.names.plural = "clusters"
        mock_crd.spec.names.singular = "cluster"
        mock_crd.spec.scope = "Namespaced"
        mock_crd.spec.names.short_names = ["pg"]

        ver = MagicMock()
        ver.name = "v1"
        ver.served = True
        ver.storage = True
        ver.schema = None
        mock_crd.spec.versions = [ver]

        mock_api.read_custom_resource_definition.return_value = mock_crd

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("describe_crd", {
                "crd_name": "clusters.postgresql.cnpg.io",
                "context": "",
            })
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is True
        assert data["crd"]["kind"] == "Cluster"
        assert "databases" in data["crd"]["categories"]
        assert data["crd"]["description"] is not None

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_describe_crd_not_found(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api
        mock_api.read_custom_resource_definition.side_effect = Exception("404 not found")

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("describe_crd", {
                "crd_name": "missing.example.io",
                "context": "",
            })
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["success"] is False
        assert "not found" in data["error"].lower()
        assert "hint" in data


class TestDetectCRDs:

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_detect_available(self, mock_get_client):
        mock_api = MagicMock()
        mock_get_client.return_value = mock_api
        mock_api.list_custom_resource_definition.return_value = MagicMock(
            items=[MagicMock()]
        )

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("detect_crds", {"context": ""})
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["installed"] is True
        assert data["available"] is True
        assert data["hasCRDs"] is True

    @pytest.mark.unit
    @patch("kubectl_mcp_tool.tools.custom_resources.get_apiextensions_client")
    def test_detect_unavailable(self, mock_get_client):
        mock_get_client.side_effect = Exception("connection refused")

        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools
        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        result = asyncio.run(
            server.call_tool("detect_crds", {"context": ""})
        )
        import json
        data = json.loads(result.content[0].text)
        assert data["installed"] is False
        assert data["available"] is False


class TestToolRegistration:

    @pytest.mark.unit
    def test_six_tools_registered(self):
        from fastmcp import FastMCP
        from kubectl_mcp_tool.tools.custom_resources import register_custom_resource_tools

        server = FastMCP(name="test")
        register_custom_resource_tools(server, False)

        tools = asyncio.run(server.list_tools())
        tool_names = [t.name for t in tools]
        expected = [
            "discover_crds",
            "search_crds",
            "list_custom_resources",
            "get_custom_resource",
            "describe_crd",
            "detect_crds",
        ]
        for name in expected:
            assert name in tool_names, f"Tool '{name}' not registered"
        assert len(tool_names) == 6

    @pytest.mark.unit
    def test_import_from_init(self):
        from kubectl_mcp_tool.tools import register_custom_resource_tools
        assert callable(register_custom_resource_tools)

    @pytest.mark.unit
    def test_import_module(self):
        from kubectl_mcp_tool.tools.custom_resources import (
            register_custom_resource_tools,
            CRD_CATEGORIES,
            _classify_crd,
        )
        assert callable(register_custom_resource_tools)
        assert callable(_classify_crd)
        assert isinstance(CRD_CATEGORIES, dict)
