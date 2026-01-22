"""
Kubernetes configuration loader utility.

Handles both in-cluster and out-of-cluster (kubeconfig) configurations.

This module patches the kubernetes.config.load_kube_config function to
automatically try in-cluster config first when running inside a pod.
"""

import os
import logging

logger = logging.getLogger("mcp-server")

_config_loaded = False
_original_load_kube_config = None


def load_kubernetes_config():
    """Load Kubernetes configuration.

    Tries in-cluster config first (when running inside a pod),
    then falls back to kubeconfig file.

    Returns:
        bool: True if config loaded successfully, False otherwise
    """
    global _config_loaded

    if _config_loaded:
        return True

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


def get_k8s_client():
    """Get a configured Kubernetes API client.

    Returns:
        kubernetes.client.CoreV1Api: Configured Kubernetes client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.CoreV1Api()


def get_apps_client():
    """Get a configured Kubernetes Apps API client.

    Returns:
        kubernetes.client.AppsV1Api: Configured Apps API client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.AppsV1Api()


def get_rbac_client():
    """Get a configured Kubernetes RBAC API client.

    Returns:
        kubernetes.client.RbacAuthorizationV1Api: Configured RBAC client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.RbacAuthorizationV1Api()


def get_networking_client():
    """Get a configured Kubernetes Networking API client.

    Returns:
        kubernetes.client.NetworkingV1Api: Configured Networking client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.NetworkingV1Api()


def get_storage_client():
    """Get a configured Kubernetes Storage API client.

    Returns:
        kubernetes.client.StorageV1Api: Configured Storage client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.StorageV1Api()


def get_batch_client():
    """Get a configured Kubernetes Batch API client.

    Returns:
        kubernetes.client.BatchV1Api: Configured Batch client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.BatchV1Api()


def get_autoscaling_client():
    """Get a configured Kubernetes Autoscaling API client.

    Returns:
        kubernetes.client.AutoscalingV1Api: Configured Autoscaling client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.AutoscalingV1Api()


def get_policy_client():
    """Get a configured Kubernetes Policy API client.

    Returns:
        kubernetes.client.PolicyV1Api: Configured Policy client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.PolicyV1Api()


def get_custom_objects_client():
    """Get a configured Kubernetes Custom Objects API client.

    Returns:
        kubernetes.client.CustomObjectsApi: Configured Custom Objects client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.CustomObjectsApi()


def get_version_client():
    """Get a configured Kubernetes Version API client.

    Returns:
        kubernetes.client.VersionApi: Configured Version client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.VersionApi()


def get_admissionregistration_client():
    """Get a configured Kubernetes Admission Registration API client.

    Returns:
        kubernetes.client.AdmissionregistrationV1Api: Configured Admission client

    Raises:
        RuntimeError: If Kubernetes config cannot be loaded
    """
    from kubernetes import client

    if not load_kubernetes_config():
        raise RuntimeError("Invalid kube-config file. No configuration found.")

    return client.AdmissionregistrationV1Api()
