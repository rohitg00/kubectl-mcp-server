"""
Kubernetes configuration loader utility.

Handles both in-cluster and out-of-cluster (kubeconfig) configurations.
Supports multi-cluster operations with context targeting.

This module provides context-aware client creation for multi-cluster support.
All get_*_client() functions accept an optional 'context' parameter.

Environment Variables:
    MCP_K8S_PROVIDER: Provider type (kubeconfig, in-cluster, single)
    MCP_K8S_KUBECONFIG: Path to kubeconfig file
    MCP_K8S_CONTEXT: Default context for single provider
    MCP_K8S_QPS: API rate limit (default: 100)
    MCP_K8S_BURST: API burst limit (default: 200)
    MCP_K8S_TIMEOUT: Request timeout in seconds (default: 30)
"""

import os
import logging
from typing import Optional, Any, List, Dict

logger = logging.getLogger("mcp-server")

# Try to import provider module for enhanced features
try:
    from .providers import (
        KubernetesProvider,
        ProviderConfig,
        ProviderType,
        UnknownContextError,
        get_provider,
        get_context_names,
        get_current_context as provider_get_current_context,
        validate_context,
    )
    _HAS_PROVIDER = True
except ImportError:
    _HAS_PROVIDER = False
    logger.debug("Provider module not available, using basic config")

_config_loaded = False
_original_load_kube_config = None


def load_kubernetes_config(context: str = ""):
    """Load Kubernetes configuration.

    Tries in-cluster config first (when running inside a pod),
    then falls back to kubeconfig file.

    Args:
        context: Optional context name for kubeconfig provider

    Returns:
        bool: True if config loaded successfully, False otherwise
    """
    global _config_loaded

    from kubernetes import config
    from kubernetes.config.config_exception import ConfigException

    # Try in-cluster config first (for pods running in Kubernetes)
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration")
        _config_loaded = True
        return True
    except ConfigException:
        logger.debug("Not running in-cluster, trying kubeconfig...")

    # Fall back to kubeconfig file
    try:
        kubeconfig_path = os.environ.get('KUBECONFIG', '~/.kube/config')
        kubeconfig_path = os.path.expanduser(kubeconfig_path)

        if context:
            config.load_kube_config(config_file=kubeconfig_path, context=context)
            logger.info(f"Loaded kubeconfig context '{context}' from {kubeconfig_path}")
        else:
            config.load_kube_config(config_file=kubeconfig_path)
            logger.info(f"Loaded kubeconfig from {kubeconfig_path}")

        _config_loaded = True
        return True
    except ConfigException as e:
        logger.error(f"Failed to load Kubernetes config: {e}")
        return False


def _patched_load_kube_config(*args, **kwargs):
    """Patched version of load_kube_config that tries in-cluster first."""
    global _config_loaded, _original_load_kube_config

    if _config_loaded:
        return

    from kubernetes.config.config_exception import ConfigException

    # Try in-cluster config first
    try:
        from kubernetes import config
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration")
        _config_loaded = True
        return
    except ConfigException:
        pass

    # Fall back to original behavior
    if _original_load_kube_config:
        _original_load_kube_config(*args, **kwargs)
        _config_loaded = True


def patch_kubernetes_config():
    """Patch the kubernetes config module to support in-cluster config.

    This should be called early in the application startup.
    """
    global _original_load_kube_config

    try:
        from kubernetes import config

        if _original_load_kube_config is None:
            _original_load_kube_config = config.load_kube_config
            config.load_kube_config = _patched_load_kube_config
            logger.debug("Patched kubernetes.config.load_kube_config for in-cluster support")
    except ImportError:
        logger.debug("kubernetes package not available for patching")


# Auto-patch when this module is imported
patch_kubernetes_config()


def _load_config_for_context(context: str = "") -> Any:
    """
    Load kubernetes config for a specific context and return ApiClient.

    Uses the provider module for caching when available.

    Args:
        context: Context name (empty for default)

    Returns:
        kubernetes.client.ApiClient configured for the context

    Raises:
        UnknownContextError: If context is not found (when provider available)
        RuntimeError: If config cannot be loaded
    """
    # Use provider module if available (provides caching and validation)
    if _HAS_PROVIDER:
        try:
            provider = get_provider()
            return provider.get_api_client(context)
        except UnknownContextError:
            raise
        except Exception as e:
            logger.warning(f"Provider failed, falling back to basic config: {e}")

    # Fallback to basic config loading
    from kubernetes import client, config
    from kubernetes.config.config_exception import ConfigException

    # Try in-cluster first
    try:
        config.load_incluster_config()
        return client.ApiClient()
    except ConfigException:
        pass

    # Load kubeconfig with optional context
    kubeconfig_path = os.environ.get('KUBECONFIG', '~/.kube/config')
    kubeconfig_path = os.path.expanduser(kubeconfig_path)

    api_config = client.Configuration()

    if context:
        config.load_kube_config(
            config_file=kubeconfig_path,
            context=context,
            client_configuration=api_config
        )
    else:
        config.load_kube_config(
            config_file=kubeconfig_path,
            client_configuration=api_config
        )

    return client.ApiClient(configuration=api_config)


def get_k8s_client(context: str = ""):
    """Get a configured Kubernetes Core API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.CoreV1Api: Configured Kubernetes client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.CoreV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_apps_client(context: str = ""):
    """Get a configured Kubernetes Apps API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.AppsV1Api: Configured Apps API client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.AppsV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_rbac_client(context: str = ""):
    """Get a configured Kubernetes RBAC API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.RbacAuthorizationV1Api: Configured RBAC client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.RbacAuthorizationV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_networking_client(context: str = ""):
    """Get a configured Kubernetes Networking API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.NetworkingV1Api: Configured Networking client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.NetworkingV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_storage_client(context: str = ""):
    """Get a configured Kubernetes Storage API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.StorageV1Api: Configured Storage client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.StorageV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_batch_client(context: str = ""):
    """Get a configured Kubernetes Batch API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.BatchV1Api: Configured Batch client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.BatchV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_autoscaling_client(context: str = ""):
    """Get a configured Kubernetes Autoscaling API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.AutoscalingV1Api: Configured Autoscaling client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.AutoscalingV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_policy_client(context: str = ""):
    """Get a configured Kubernetes Policy API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.PolicyV1Api: Configured Policy client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.PolicyV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_custom_objects_client(context: str = ""):
    """Get a configured Kubernetes Custom Objects API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.CustomObjectsApi: Configured Custom Objects client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.CustomObjectsApi(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_version_client(context: str = ""):
    """Get a configured Kubernetes Version API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.VersionApi: Configured Version client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.VersionApi(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_admissionregistration_client(context: str = ""):
    """Get a configured Kubernetes Admission Registration API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.AdmissionregistrationV1Api: Configured Admission client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.AdmissionregistrationV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_apiextensions_client(context: str = ""):
    """Get a configured Kubernetes API Extensions client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.ApiextensionsV1Api: Configured API Extensions client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.ApiextensionsV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_coordination_client(context: str = ""):
    """Get a configured Kubernetes Coordination API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.CoordinationV1Api: Configured Coordination client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.CoordinationV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_events_client(context: str = ""):
    """Get a configured Kubernetes Events API client.

    Args:
        context: Optional context name for multi-cluster support

    Returns:
        kubernetes.client.EventsV1Api: Configured Events client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    try:
        api_client = _load_config_for_context(context)
        return client.EventsV1Api(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


# Utility functions for context management

def list_contexts() -> list:
    """
    List all available kubeconfig contexts.

    Returns:
        List of context dictionaries with name, cluster, user, namespace
    """
    # Use provider if available
    if _HAS_PROVIDER:
        try:
            provider = get_provider()
            contexts = provider.list_contexts()
            return [
                {
                    "name": ctx.name,
                    "cluster": ctx.cluster,
                    "user": ctx.user,
                    "namespace": ctx.namespace,
                    "active": ctx.is_active
                }
                for ctx in contexts
            ]
        except Exception as e:
            logger.warning(f"Provider list_contexts failed: {e}")

    # Fallback to direct kubeconfig reading
    from kubernetes import config

    try:
        kubeconfig_path = os.environ.get('KUBECONFIG', '~/.kube/config')
        kubeconfig_path = os.path.expanduser(kubeconfig_path)

        contexts, active = config.list_kube_config_contexts(config_file=kubeconfig_path)

        return [
            {
                "name": ctx.get("name"),
                "cluster": ctx.get("context", {}).get("cluster"),
                "user": ctx.get("context", {}).get("user"),
                "namespace": ctx.get("context", {}).get("namespace", "default"),
                "active": ctx.get("name") == (active.get("name") if active else None)
            }
            for ctx in contexts
        ]
    except Exception as e:
        logger.error(f"Error listing contexts: {e}")
        return []


def get_active_context() -> Optional[str]:
    """
    Get the current active context name.

    Returns:
        Active context name or None
    """
    # Use provider if available
    if _HAS_PROVIDER:
        try:
            return provider_get_current_context()
        except Exception as e:
            logger.warning(f"Provider get_current_context failed: {e}")

    # Fallback to direct kubeconfig reading
    from kubernetes import config

    try:
        kubeconfig_path = os.environ.get('KUBECONFIG', '~/.kube/config')
        kubeconfig_path = os.path.expanduser(kubeconfig_path)

        _, active = config.list_kube_config_contexts(config_file=kubeconfig_path)
        return active.get("name") if active else None
    except Exception as e:
        logger.error(f"Error getting active context: {e}")
        return None


def context_exists(context: str) -> bool:
    """
    Check if a context exists in kubeconfig.

    Args:
        context: Context name to check

    Returns:
        True if context exists
    """
    contexts = list_contexts()
    return any(ctx["name"] == context for ctx in contexts)


def _get_kubectl_context_args(context: str = "") -> list:
    """
    Get kubectl command arguments for specifying a context.

    This utility function returns the appropriate --context flag arguments
    for kubectl commands when targeting a specific cluster.

    Args:
        context: Context name (empty string for default context)

    Returns:
        List of command arguments, e.g., ["--context", "my-cluster"]
        or empty list if no context specified
    """
    if context and context.strip():
        return ["--context", context.strip()]
    return []


# Re-export provider types for convenience
if _HAS_PROVIDER:
    __all__ = [
        # Client functions
        "get_k8s_client",
        "get_apps_client",
        "get_rbac_client",
        "get_networking_client",
        "get_storage_client",
        "get_batch_client",
        "get_autoscaling_client",
        "get_policy_client",
        "get_custom_objects_client",
        "get_version_client",
        "get_admissionregistration_client",
        "get_apiextensions_client",
        "get_coordination_client",
        "get_events_client",
        # Config functions
        "load_kubernetes_config",
        "patch_kubernetes_config",
        # Context functions
        "list_contexts",
        "get_active_context",
        "context_exists",
        # Provider types (when available)
        "KubernetesProvider",
        "ProviderConfig",
        "ProviderType",
        "UnknownContextError",
        "get_provider",
        "validate_context",
    ]
else:
    __all__ = [
        "get_k8s_client",
        "get_apps_client",
        "get_rbac_client",
        "get_networking_client",
        "get_storage_client",
        "get_batch_client",
        "get_autoscaling_client",
        "get_policy_client",
        "get_custom_objects_client",
        "get_version_client",
        "get_admissionregistration_client",
        "get_apiextensions_client",
        "get_coordination_client",
        "get_events_client",
        "load_kubernetes_config",
        "patch_kubernetes_config",
        "list_contexts",
        "get_active_context",
        "context_exists",
    ]
