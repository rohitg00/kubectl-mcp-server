import os
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from functools import lru_cache

logger = logging.getLogger("mcp-server")


class ProviderType(Enum):
    """Kubernetes provider types."""
    KUBECONFIG = "kubeconfig"
    IN_CLUSTER = "in-cluster"
    SINGLE = "single"


class UnknownContextError(Exception):
    """Raised when a requested context is not found."""
    def __init__(self, context: str, available: List[str] = None):
        self.context = context
        self.available = available or []
        msg = f"Context '{context}' not found"
        if self.available:
            msg += f". Available contexts: {', '.join(self.available)}"
        super().__init__(msg)


class ProviderError(Exception):
    """Raised when provider configuration is invalid."""
    pass


@dataclass
class ProviderConfig:
    """Configuration for Kubernetes provider."""
    provider_type: ProviderType = ProviderType.KUBECONFIG
    kubeconfig_path: str = ""
    context: str = ""
    qps: float = 100.0
    burst: int = 200
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        """Create config from environment variables."""
        provider_str = os.environ.get("MCP_K8S_PROVIDER", "kubeconfig").lower()

        try:
            provider_type = ProviderType(provider_str)
        except ValueError:
            logger.warning(f"Unknown provider type '{provider_str}', using kubeconfig")
            provider_type = ProviderType.KUBECONFIG

        kubeconfig_path = os.environ.get(
            "MCP_K8S_KUBECONFIG",
            os.environ.get("KUBECONFIG", "~/.kube/config")
        )
        kubeconfig_path = os.path.expanduser(kubeconfig_path)

        return cls(
            provider_type=provider_type,
            kubeconfig_path=kubeconfig_path,
            context=os.environ.get("MCP_K8S_CONTEXT", ""),
            qps=float(os.environ.get("MCP_K8S_QPS", "100")),
            burst=int(os.environ.get("MCP_K8S_BURST", "200")),
            timeout=int(os.environ.get("MCP_K8S_TIMEOUT", "30")),
        )


@dataclass
class ContextInfo:
    """Information about a kubeconfig context."""
    name: str
    cluster: str
    user: str
    namespace: str = "default"
    is_active: bool = False


class KubernetesProvider:
    """
    Multi-cluster Kubernetes provider.

    Manages connections to multiple Kubernetes clusters based on
    kubeconfig contexts or in-cluster configuration.
    """

    _instance: Optional["KubernetesProvider"] = None

    def __init__(self, config: Optional[ProviderConfig] = None):
        """Initialize provider with configuration."""
        self.config = config or ProviderConfig.from_env()
        self._api_clients: Dict[str, Any] = {}
        self._in_cluster = False
        self._contexts_cache: Optional[List[ContextInfo]] = None
        self._active_context: Optional[str] = None

        self._initialize()

    @classmethod
    def get_instance(cls) -> "KubernetesProvider":
        """Get singleton provider instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)."""
        cls._instance = None

    def _initialize(self):
        """Initialize the provider based on type."""
        if self.config.provider_type == ProviderType.IN_CLUSTER:
            self._initialize_in_cluster()
        elif self.config.provider_type == ProviderType.SINGLE:
            self._initialize_single()
        else:
            self._initialize_kubeconfig()

    def _initialize_in_cluster(self):
        """Initialize for in-cluster provider."""
        from kubernetes import config
        from kubernetes.config.config_exception import ConfigException

        try:
            config.load_incluster_config()
            self._in_cluster = True
            self._active_context = "in-cluster"
            logger.info("Initialized in-cluster Kubernetes provider")
        except ConfigException as e:
            raise ProviderError(f"Failed to load in-cluster config: {e}")

    def _initialize_single(self):
        """Initialize for single-context provider."""
        if not self.config.context:
            raise ProviderError("MCP_K8S_CONTEXT must be set for 'single' provider")

        from kubernetes import config

        try:
            config.load_kube_config(
                config_file=self.config.kubeconfig_path,
                context=self.config.context
            )
            self._active_context = self.config.context
            logger.info(f"Initialized single-context provider: {self.config.context}")
        except Exception as e:
            raise ProviderError(f"Failed to load context '{self.config.context}': {e}")

    def _initialize_kubeconfig(self):
        """Initialize for multi-cluster kubeconfig provider."""
        from kubernetes import config

        try:
            contexts, active = config.list_kube_config_contexts(
                config_file=self.config.kubeconfig_path
            )

            if active:
                self._active_context = active.get("name")

            self._contexts_cache = [
                ContextInfo(
                    name=ctx.get("name", ""),
                    cluster=ctx.get("context", {}).get("cluster", ""),
                    user=ctx.get("context", {}).get("user", ""),
                    namespace=ctx.get("context", {}).get("namespace", "default"),
                    is_active=ctx.get("name") == self._active_context
                )
                for ctx in contexts
            ]

            logger.info(
                f"Initialized kubeconfig provider with {len(self._contexts_cache)} contexts, "
                f"active: {self._active_context}"
            )
        except Exception as e:
            logger.warning(f"Failed to list contexts: {e}")
            self._contexts_cache = []

    def list_contexts(self) -> List[ContextInfo]:
        """
        List all available contexts.

        Returns:
            List of ContextInfo objects
        """
        if self._in_cluster:
            return [ContextInfo(
                name="in-cluster",
                cluster="in-cluster",
                user="service-account",
                namespace="default",
                is_active=True
            )]

        if self.config.provider_type == ProviderType.SINGLE:
            from kubernetes import config
            try:
                contexts, _ = config.list_kube_config_contexts(
                    config_file=self.config.kubeconfig_path
                )
                for ctx in contexts:
                    if ctx.get("name") == self.config.context:
                        return [ContextInfo(
                            name=ctx.get("name", ""),
                            cluster=ctx.get("context", {}).get("cluster", ""),
                            user=ctx.get("context", {}).get("user", ""),
                            namespace=ctx.get("context", {}).get("namespace", "default"),
                            is_active=True
                        )]
            except Exception:
                pass
            return []

        self._refresh_contexts_cache()
        return self._contexts_cache or []

    def _refresh_contexts_cache(self):
        """Refresh the contexts cache from kubeconfig."""
        if self._in_cluster or self.config.provider_type == ProviderType.SINGLE:
            return

        from kubernetes import config
        try:
            contexts, active = config.list_kube_config_contexts(
                config_file=self.config.kubeconfig_path
            )
            self._active_context = active.get("name") if active else None
            self._contexts_cache = [
                ContextInfo(
                    name=ctx.get("name", ""),
                    cluster=ctx.get("context", {}).get("cluster", ""),
                    user=ctx.get("context", {}).get("user", ""),
                    namespace=ctx.get("context", {}).get("namespace", "default"),
                    is_active=ctx.get("name") == self._active_context
                )
                for ctx in contexts
            ]
        except Exception as e:
            logger.warning(f"Failed to refresh contexts: {e}")

    def get_current_context(self) -> Optional[str]:
        """Get the current active context name."""
        if self._in_cluster:
            return "in-cluster"
        return self._active_context

    def _get_context_names(self) -> List[str]:
        """Get list of available context names."""
        contexts = self.list_contexts()
        return [ctx.name for ctx in contexts]

    def validate_context(self, context: str) -> str:
        """
        Validate and resolve a context name.

        Args:
            context: Context name (empty string uses default)

        Returns:
            Resolved context name

        Raises:
            UnknownContextError: If context is not found
        """
        if self._in_cluster:
            return "in-cluster"

        if self.config.provider_type == ProviderType.SINGLE:
            if context and context != self.config.context:
                raise UnknownContextError(
                    context,
                    [self.config.context]
                )
            return self.config.context

        if not context:
            return self._active_context or ""

        available = self._get_context_names()
        if context not in available:
            raise UnknownContextError(context, available)

        return context

    def get_api_client(self, context: str = "") -> Any:
        """
        Get an API client configuration for a specific context.

        Args:
            context: Context name (empty uses default)

        Returns:
            kubernetes.client.ApiClient configured for the context
        """
        from kubernetes import client, config

        resolved_context = self.validate_context(context)

        if resolved_context in self._api_clients:
            return self._api_clients[resolved_context]

        if self._in_cluster:
            api_client = client.ApiClient()
        else:
            api_config = client.Configuration()
            config.load_kube_config(
                config_file=self.config.kubeconfig_path,
                context=resolved_context,
                client_configuration=api_config
            )
            api_client = client.ApiClient(configuration=api_config)

        self._api_clients[resolved_context] = api_client

        return api_client

    def clear_client_cache(self, context: str = ""):
        """Clear cached API client(s)."""
        if context:
            self._api_clients.pop(context, None)
        else:
            self._api_clients.clear()


def get_provider() -> KubernetesProvider:
    """Get the global Kubernetes provider instance."""
    return KubernetesProvider.get_instance()


def get_context_names() -> List[str]:
    """Get list of available context names."""
    provider = get_provider()
    return [ctx.name for ctx in provider.list_contexts()]


def get_current_context() -> Optional[str]:
    """Get the current active context name."""
    return get_provider().get_current_context()


def validate_context(context: str) -> str:
    """Validate and resolve a context name."""
    return get_provider().validate_context(context)
