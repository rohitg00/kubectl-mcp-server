"""Tests for Kubernetes provider kubeconfig handling."""

import os
from unittest.mock import MagicMock, patch

import pytest
import yaml
from kubernetes.config.config_exception import ConfigException


def _write_kubeconfig(path, context_name):
    """Write a minimal kubeconfig containing one context."""
    path.write_text(yaml.safe_dump({
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [{
            "name": f"{context_name}-cluster",
            "cluster": {"server": f"https://{context_name}.example.com"},
        }],
        "users": [{
            "name": f"{context_name}-user",
            "user": {"token": f"{context_name}-token"},
        }],
        "contexts": [{
            "name": context_name,
            "context": {
                "cluster": f"{context_name}-cluster",
                "user": f"{context_name}-user",
            },
        }],
        "current-context": context_name,
    }))


class TestProviderConfig:
    """Tests for provider configuration loaded from the environment."""

    @pytest.mark.unit
    def test_expands_each_path_in_kubeconfig_path_list(self, tmp_path, monkeypatch):
        """Each kubeconfig entry should expand user paths independently."""
        from kubectl_mcp_tool.providers import ProviderConfig

        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv(
            "KUBECONFIG",
            os.pathsep.join(["~/.kube/sit", "~/.kube/stg"]),
        )

        provider_config = ProviderConfig.from_env()

        assert provider_config.kubeconfig_path == os.pathsep.join([
            str(tmp_path / ".kube" / "sit"),
            str(tmp_path / ".kube" / "stg"),
        ])


class TestKubernetesProvider:
    """Tests for the multi-cluster kubeconfig provider."""

    @pytest.mark.unit
    def test_loads_contexts_from_multiple_kubeconfig_files(self, tmp_path):
        """A path list is valid when at least one kubeconfig file exists."""
        from kubectl_mcp_tool.providers import (
            KubernetesProvider,
            ProviderConfig,
            ProviderType,
        )

        first_path = tmp_path / "sit.config"
        second_path = tmp_path / "stg.config"
        first_path.touch()
        second_path.touch()
        path_list = os.pathsep.join([str(first_path), str(second_path)])
        contexts = [
            {
                "name": "sit",
                "context": {
                    "cluster": "sit-cluster",
                    "user": "sit-user",
                },
            },
            {
                "name": "stg",
                "context": {
                    "cluster": "stg-cluster",
                    "user": "stg-user",
                },
            },
        ]

        with patch(
            "kubernetes.config.load_incluster_config",
            side_effect=ConfigException("not in cluster"),
        ), patch(
            "kubernetes.config.list_kube_config_contexts",
            return_value=(contexts, contexts[0]),
        ) as mock_list_contexts:
            provider = KubernetesProvider(ProviderConfig(
                provider_type=ProviderType.KUBECONFIG,
                kubeconfig_path=path_list,
            ))

        assert [context.name for context in provider.list_contexts()] == ["sit", "stg"]
        mock_list_contexts.assert_called_with(config_file=path_list)

    @pytest.mark.unit
    def test_kubernetes_client_merges_contexts_from_path_list(self, tmp_path):
        """The official Kubernetes client should merge all configured files."""
        from kubernetes import config

        first_path = tmp_path / "sit.config"
        second_path = tmp_path / "stg.config"
        _write_kubeconfig(first_path, "sit")
        _write_kubeconfig(second_path, "stg")
        path_list = os.pathsep.join([str(first_path), str(second_path)])

        contexts, active = config.list_kube_config_contexts(config_file=path_list)

        # Both contexts from the two files are present after the client merges
        # the path list. Which file's current-context becomes active is an
        # internal detail of the Kubernetes client that has changed across
        # versions (first-file on v28.x, last-file on v35.x), so we only assert
        # that the active context is one of the merged contexts.
        assert [context["name"] for context in contexts] == ["sit", "stg"]
        assert active["name"] in ("sit", "stg")


class TestFallbackKubeconfigLoading:
    """Tests for kubeconfig loading when the enhanced provider is unavailable."""

    @pytest.mark.unit
    def test_loads_from_path_list_when_any_file_exists(self, tmp_path, monkeypatch):
        """Fallback loading should validate entries, then pass the full list."""
        from kubectl_mcp_tool import k8s_config

        existing_path = tmp_path / "sit.config"
        existing_path.touch()
        missing_path = tmp_path / "missing.config"
        path_list = os.pathsep.join([str(existing_path), str(missing_path)])
        api_client = MagicMock()

        monkeypatch.setenv("KUBECONFIG", path_list)
        monkeypatch.setattr(k8s_config, "_HAS_PROVIDER", False)

        with patch(
            "kubernetes.config.load_incluster_config",
            side_effect=ConfigException("not in cluster"),
        ), patch("kubernetes.config.load_kube_config") as mock_load_kube_config, patch(
            "kubernetes.client.ApiClient",
            return_value=api_client,
        ):
            result = k8s_config._load_config_for_context()

        assert result is api_client
        assert mock_load_kube_config.call_args.kwargs["config_file"] == path_list
        assert "client_configuration" in mock_load_kube_config.call_args.kwargs

    @pytest.mark.unit
    def test_rejects_path_list_when_all_files_are_missing(self, tmp_path, monkeypatch):
        """Fallback loading should still fail when no configured file exists."""
        from kubectl_mcp_tool import k8s_config

        path_list = os.pathsep.join([
            str(tmp_path / "missing-sit.config"),
            str(tmp_path / "missing-stg.config"),
        ])

        monkeypatch.setenv("KUBECONFIG", path_list)
        monkeypatch.setattr(k8s_config, "_HAS_PROVIDER", False)

        with patch(
            "kubernetes.config.load_incluster_config",
            side_effect=ConfigException("not in cluster"),
        ), pytest.raises(RuntimeError, match="kubeconfig not found"):
            k8s_config._load_config_for_context()
