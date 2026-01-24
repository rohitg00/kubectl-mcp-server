"""CRD Auto-Discovery Framework for kubectl-mcp-server.

Detects installed CRDs in the cluster and enables/disables toolsets accordingly.
"""

import subprocess
import json
from typing import Dict, List, Optional, Set
from functools import lru_cache
import time

from .k8s_config import _get_kubectl_context_args


CRD_GROUPS = {
    "flux": [
        "kustomizations.kustomize.toolkit.fluxcd.io",
        "helmreleases.helm.toolkit.fluxcd.io",
        "gitrepositories.source.toolkit.fluxcd.io",
        "helmrepositories.source.toolkit.fluxcd.io",
    ],
    "argocd": [
        "applications.argoproj.io",
        "applicationsets.argoproj.io",
        "appprojects.argoproj.io",
    ],
    "certmanager": [
        "certificates.cert-manager.io",
        "issuers.cert-manager.io",
        "clusterissuers.cert-manager.io",
        "certificaterequests.cert-manager.io",
        "orders.acme.cert-manager.io",
        "challenges.acme.cert-manager.io",
    ],
    "kyverno": [
        "clusterpolicies.kyverno.io",
        "policies.kyverno.io",
        "policyreports.wgpolicyk8s.io",
        "clusterpolicyreports.wgpolicyk8s.io",
    ],
    "gatekeeper": [
        "constrainttemplates.templates.gatekeeper.sh",
        "configs.config.gatekeeper.sh",
    ],
    "velero": [
        "backups.velero.io",
        "restores.velero.io",
        "schedules.velero.io",
        "backupstoragelocations.velero.io",
    ],
    "keda": [
        "scaledobjects.keda.sh",
        "scaledjobs.keda.sh",
        "triggerauthentications.keda.sh",
    ],
    "cilium": [
        "ciliumnetworkpolicies.cilium.io",
        "ciliumclusterwidenetworkpolicies.cilium.io",
        "ciliumendpoints.cilium.io",
    ],
    "istio": [
        "virtualservices.networking.istio.io",
        "destinationrules.networking.istio.io",
        "gateways.networking.istio.io",
    ],
    "argorollouts": [
        "rollouts.argoproj.io",
        "analysistemplates.argoproj.io",
    ],
    "kubevirt": [
        "virtualmachines.kubevirt.io",
        "virtualmachineinstances.kubevirt.io",
    ],
    "capi": [
        "clusters.cluster.x-k8s.io",
        "machines.cluster.x-k8s.io",
        "machinedeployments.cluster.x-k8s.io",
    ],
}


_crd_cache: Dict[str, Dict[str, bool]] = {}
_cache_timestamp: Dict[str, float] = {}
CACHE_TTL = 300


def _get_cluster_crds(context: str = "") -> Set[str]:
    """Get all CRDs installed in the cluster."""
    try:
        cmd = ["kubectl"] + _get_kubectl_context_args(context) + [
            "get", "crds", "-o", "jsonpath={.items[*].metadata.name}"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return set(result.stdout.split())
        return set()
    except Exception:
        return set()


def detect_crds(context: str = "", force_refresh: bool = False) -> Dict[str, bool]:
    """Detect which CRD groups are installed in the cluster.

    Args:
        context: Kubernetes context to use
        force_refresh: Force refresh the cache

    Returns:
        Dict mapping CRD group name to installed status
    """
    cache_key = context or "default"

    if not force_refresh and cache_key in _crd_cache:
        if time.time() - _cache_timestamp.get(cache_key, 0) < CACHE_TTL:
            return _crd_cache[cache_key]

    installed_crds = _get_cluster_crds(context)

    result = {}
    for group_name, crds in CRD_GROUPS.items():
        result[group_name] = any(crd in installed_crds for crd in crds)

    _crd_cache[cache_key] = result
    _cache_timestamp[cache_key] = time.time()

    return result


def crd_exists(crd_name: str, context: str = "") -> bool:
    """Check if a specific CRD exists in the cluster.

    Args:
        crd_name: Full CRD name (e.g., "certificates.cert-manager.io")
        context: Kubernetes context to use

    Returns:
        True if CRD exists, False otherwise
    """
    try:
        cmd = ["kubectl"] + _get_kubectl_context_args(context) + [
            "get", "crd", crd_name, "-o", "name"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False


def get_enabled_toolsets(context: str = "") -> List[str]:
    """Get list of toolsets that should be enabled based on detected CRDs.

    Args:
        context: Kubernetes context to use

    Returns:
        List of enabled toolset names
    """
    crds = detect_crds(context)
    enabled = []

    if crds.get("flux") or crds.get("argocd"):
        enabled.append("gitops")
    if crds.get("certmanager"):
        enabled.append("certs")
    if crds.get("kyverno") or crds.get("gatekeeper"):
        enabled.append("policy")
    if crds.get("velero"):
        enabled.append("backup")
    if crds.get("keda"):
        enabled.append("keda")
    if crds.get("cilium"):
        enabled.append("cilium")
    if crds.get("argorollouts"):
        enabled.append("rollouts")
    if crds.get("kubevirt"):
        enabled.append("kubevirt")
    if crds.get("capi"):
        enabled.append("capi")
    if crds.get("istio"):
        enabled.append("istio")

    return enabled


def get_crd_status_summary(context: str = "") -> Dict:
    """Get a summary of CRD detection status.

    Args:
        context: Kubernetes context to use

    Returns:
        Summary dict with detected CRDs and enabled toolsets
    """
    crds = detect_crds(context)
    enabled = get_enabled_toolsets(context)

    return {
        "context": context or "current",
        "crd_groups": crds,
        "enabled_toolsets": enabled,
        "total_groups_detected": sum(1 for v in crds.values() if v),
        "total_toolsets_enabled": len(enabled),
    }


class FeatureNotInstalledError(Exception):
    """Raised when required CRDs are not installed."""

    def __init__(self, toolset: str, required_crds: List[str]):
        self.toolset = toolset
        self.required_crds = required_crds
        super().__init__(
            f"{toolset} toolset requires one of these CRDs: {', '.join(required_crds)}. "
            f"Install the required operator to use this feature."
        )


def require_crd(crd_name: str, toolset: str, context: str = ""):
    """Check if a CRD exists and raise an error if not.

    Args:
        crd_name: CRD name to check
        toolset: Toolset name for error message
        context: Kubernetes context

    Raises:
        FeatureNotInstalledError: If CRD is not installed
    """
    if not crd_exists(crd_name, context):
        raise FeatureNotInstalledError(toolset, [crd_name])


def require_any_crd(crd_names: List[str], toolset: str, context: str = ""):
    """Check if any of the CRDs exist and raise an error if none are found.

    Args:
        crd_names: List of CRD names to check
        toolset: Toolset name for error message
        context: Kubernetes context

    Raises:
        FeatureNotInstalledError: If no CRDs are installed
    """
    for crd in crd_names:
        if crd_exists(crd, context):
            return
    raise FeatureNotInstalledError(toolset, crd_names)
