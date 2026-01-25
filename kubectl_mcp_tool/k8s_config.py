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
    MCP_STATELESS_MODE: If "true", don't cache API clients (reload config each request)
    MCP_KUBECONFIG_WATCH: If "true", auto-detect kubeconfig file changes
"""

import os
import logging
import threading
import time
from typing import Optional, Any, List, Dict, Callable

logger = logging.getLogger("mcp-server")

_stateless_mode = os.environ.get("MCP_STATELESS_MODE", "").lower() in ("true", "1", "yes")
_kubeconfig_watcher: Optional["KubeconfigWatcher"] = None
_kubeconfig_last_mtime: Dict[str, float] = {}
_config_change_callbacks: List[Callable[[], None]] = []


class KubeconfigWatcher:
    """Watch kubeconfig files for changes and trigger reloads.

    This class monitors kubeconfig files and automatically invalidates
    cached configurations when changes are detected.
    """

    def __init__(self, check_interval: float = 5.0):
        """Initialize the kubeconfig watcher.

        Args:
            check_interval: How often to check for changes (seconds)
        """
        self._check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._watched_files: Dict[str, float] = {}
        self._lock = threading.Lock()

    def start(self):
        """Start watching for kubeconfig changes."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info("Kubeconfig watcher started")

    def stop(self):
        """Stop watching for kubeconfig changes."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("Kubeconfig watcher stopped")

    def add_file(self, filepath: str):
        """Add a file to watch.

        Args:
            filepath: Path to kubeconfig file
        """
        filepath = os.path.expanduser(filepath)
        if os.path.exists(filepath):
            with self._lock:
                self._watched_files[filepath] = os.path.getmtime(filepath)

    def _watch_loop(self):
        """Main watch loop - check for file changes periodically."""
        while self._running:
            try:
                self._check_files()
            except Exception as e:
                logger.debug(f"Kubeconfig watch error: {e}")
            time.sleep(self._check_interval)

    def _check_files(self):
        """Check all watched files for changes."""
        with self._lock:
            for filepath, last_mtime in list(self._watched_files.items()):
                try:
                    if not os.path.exists(filepath):
                        continue

                    current_mtime = os.path.getmtime(filepath)
                    if current_mtime != last_mtime:
                        self._watched_files[filepath] = current_mtime
                        logger.info(f"Kubeconfig changed: {filepath}")
                        self._on_config_changed()
                except Exception as e:
                    logger.debug(f"Error checking {filepath}: {e}")

    def _on_config_changed(self):
        """Handle kubeconfig file change - invalidate caches."""
        global _config_loaded
        _config_loaded = False

        if _HAS_PROVIDER:
            try:
                provider = get_provider()
                if hasattr(provider, 'invalidate_cache'):
                    provider.invalidate_cache()
            except Exception:
                pass

        for callback in _config_change_callbacks:
            try:
                callback()
            except Exception as e:
                logger.debug(f"Config change callback error: {e}")


def enable_kubeconfig_watch(check_interval: float = 5.0):
    """Enable automatic kubeconfig file watching.

    When enabled, the server will automatically detect changes to kubeconfig
    files and reload the configuration. This is useful when:
    - Cloud provider CLIs update credentials (aws, gcloud, az)
    - Users switch contexts using external tools
    - Kubeconfig files are mounted dynamically (e.g., in Kubernetes)

    Args:
        check_interval: How often to check for changes (seconds)

    Example:
        enable_kubeconfig_watch(check_interval=10.0)
    """
    global _kubeconfig_watcher

    if _kubeconfig_watcher is not None:
        return

    _kubeconfig_watcher = KubeconfigWatcher(check_interval=check_interval)
    kubeconfig_env = os.environ.get('KUBECONFIG', '~/.kube/config')
    for path in kubeconfig_env.split(os.pathsep):
        _kubeconfig_watcher.add_file(path)
    _kubeconfig_watcher.start()


def disable_kubeconfig_watch():
    """Disable kubeconfig file watching."""
    global _kubeconfig_watcher

    if _kubeconfig_watcher is not None:
        _kubeconfig_watcher.stop()
        _kubeconfig_watcher = None


def on_config_change(callback: Callable[[], None]):
    """Register a callback to be called when kubeconfig changes.

    Args:
        callback: Function to call when config changes
    """
    _config_change_callbacks.append(callback)


def is_stateless_mode() -> bool:
    """Check if stateless mode is enabled.

    In stateless mode, API clients are not cached and configuration
    is reloaded on each request. This is useful for:
    - Serverless environments (Lambda, Cloud Functions)
    - Environments where credentials may change frequently
    - Security-conscious deployments

    Returns:
        True if stateless mode is enabled
    """
    return _stateless_mode


def set_stateless_mode(enabled: bool):
    """Enable or disable stateless mode.

    Args:
        enabled: True to enable stateless mode
    """
    global _stateless_mode
    _stateless_mode = enabled
    if enabled:
        logger.info("Stateless mode enabled - API clients will not be cached")
    else:
        logger.info("Stateless mode disabled - API clients will be cached")

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

    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration")
        _config_loaded = True
        return True
    except ConfigException:
        logger.debug("Not running in-cluster, trying kubeconfig...")

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

    try:
        from kubernetes import config
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes configuration")
        _config_loaded = True
        return
    except ConfigException:
        pass

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


patch_kubernetes_config()


def _load_config_for_context(context: str = "") -> Any:
    """
    Load kubernetes config for a specific context and return ApiClient.

    Uses the provider module for caching when available, unless stateless
    mode is enabled.

    Args:
        context: Context name (empty for default)

    Returns:
        kubernetes.client.ApiClient configured for the context

    Raises:
        UnknownContextError: If context is not found (when provider available)
        RuntimeError: If config cannot be loaded
    """
    if not _stateless_mode and _HAS_PROVIDER:
        try:
            provider = get_provider()
            return provider.get_api_client(context)
        except UnknownContextError:
            raise
        except Exception as e:
            logger.warning(f"Provider failed, falling back to basic config: {e}")

    from kubernetes import client, config
    from kubernetes.config.config_exception import ConfigException

    try:
        config.load_incluster_config()
        return client.ApiClient()
    except ConfigException:
        pass

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


def _get_client(context: str, client_class):
    """Helper to create a configured Kubernetes API client."""
    from kubernetes import client
    try:
        api_client = _load_config_for_context(context)
        return client_class(api_client=api_client)
    except Exception as e:
        raise RuntimeError(f"Invalid kube-config. Context: {context or 'default'}. Error: {e}")


def get_k8s_client(context: str = ""):
    """Get a configured Kubernetes Core API client."""
    from kubernetes import client
    return _get_client(context, client.CoreV1Api)


def get_apps_client(context: str = ""):
    """Get a configured Kubernetes Apps API client."""
    from kubernetes import client
    return _get_client(context, client.AppsV1Api)


def get_rbac_client(context: str = ""):
    """Get a configured Kubernetes RBAC API client."""
    from kubernetes import client
    return _get_client(context, client.RbacAuthorizationV1Api)


def get_networking_client(context: str = ""):
    """Get a configured Kubernetes Networking API client."""
    from kubernetes import client
    return _get_client(context, client.NetworkingV1Api)


def get_storage_client(context: str = ""):
    """Get a configured Kubernetes Storage API client."""
    from kubernetes import client
    return _get_client(context, client.StorageV1Api)


def get_batch_client(context: str = ""):
    """Get a configured Kubernetes Batch API client."""
    from kubernetes import client
    return _get_client(context, client.BatchV1Api)


def get_autoscaling_client(context: str = ""):
    """Get a configured Kubernetes Autoscaling API client."""
    from kubernetes import client
    return _get_client(context, client.AutoscalingV1Api)


def get_policy_client(context: str = ""):
    """Get a configured Kubernetes Policy API client."""
    from kubernetes import client
    return _get_client(context, client.PolicyV1Api)


def get_custom_objects_client(context: str = ""):
    """Get a configured Kubernetes Custom Objects API client."""
    from kubernetes import client
    return _get_client(context, client.CustomObjectsApi)


def get_version_client(context: str = ""):
    """Get a configured Kubernetes Version API client."""
    from kubernetes import client
    return _get_client(context, client.VersionApi)


def get_admissionregistration_client(context: str = ""):
    """Get a configured Kubernetes Admission Registration API client."""
    from kubernetes import client
    return _get_client(context, client.AdmissionregistrationV1Api)


def get_apiextensions_client(context: str = ""):
    """Get a configured Kubernetes API Extensions client."""
    from kubernetes import client
    return _get_client(context, client.ApiextensionsV1Api)


def get_coordination_client(context: str = ""):
    """Get a configured Kubernetes Coordination API client."""
    from kubernetes import client
    return _get_client(context, client.CoordinationV1Api)


def get_events_client(context: str = ""):
    """Get a configured Kubernetes Events API client."""
    from kubernetes import client
    return _get_client(context, client.EventsV1Api)


def list_contexts() -> list:
    """List all available kubeconfig contexts."""
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
    """Get the current active context name."""
    if _HAS_PROVIDER:
        try:
            return provider_get_current_context()
        except Exception as e:
            logger.warning(f"Provider get_current_context failed: {e}")

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
    """Check if a context exists in kubeconfig."""
    contexts = list_contexts()
    return any(ctx["name"] == context for ctx in contexts)


def _get_kubectl_context_args(context: str = "") -> list:
    """Get kubectl command arguments for specifying a context."""
    if context and context.strip():
        return ["--context", context.strip()]
    return []


_BASE_EXPORTS = [
    "get_k8s_client", "get_apps_client", "get_rbac_client", "get_networking_client",
    "get_storage_client", "get_batch_client", "get_autoscaling_client", "get_policy_client",
    "get_custom_objects_client", "get_version_client", "get_admissionregistration_client",
    "get_apiextensions_client", "get_coordination_client", "get_events_client",
    "load_kubernetes_config", "patch_kubernetes_config",
    "list_contexts", "get_active_context", "context_exists",
    "enable_kubeconfig_watch", "disable_kubeconfig_watch", "on_config_change", "KubeconfigWatcher",
    "is_stateless_mode", "set_stateless_mode",
]

if _HAS_PROVIDER:
    __all__ = _BASE_EXPORTS + [
        "KubernetesProvider", "ProviderConfig", "ProviderType",
        "UnknownContextError", "get_provider", "validate_context",
    ]
else:
    __all__ = _BASE_EXPORTS
