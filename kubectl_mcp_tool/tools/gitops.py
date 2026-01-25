"""GitOps toolset for kubectl-mcp-server (Flux and Argo CD)."""

import json
from typing import Dict, Any, List

try:
    from fastmcp import FastMCP
    from fastmcp.tools import ToolAnnotations
except ImportError:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations

from ..crd_detector import crd_exists, require_any_crd
from .utils import run_kubectl, get_resources


FLUX_KUSTOMIZATION_CRD = "kustomizations.kustomize.toolkit.fluxcd.io"
FLUX_HELMRELEASE_CRD = "helmreleases.helm.toolkit.fluxcd.io"
FLUX_GITREPO_CRD = "gitrepositories.source.toolkit.fluxcd.io"
FLUX_HELMREPO_CRD = "helmrepositories.source.toolkit.fluxcd.io"
ARGOCD_APP_CRD = "applications.argoproj.io"
ARGOCD_APPSET_CRD = "applicationsets.argoproj.io"


def gitops_apps_list(
    namespace: str = "",
    context: str = "",
    kind: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List GitOps applications from Flux or Argo CD.

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional, uses current context if not specified)
        kind: Filter by kind (Kustomization, HelmRelease, Application)
        label_selector: Label selector to filter resources

    Returns:
        List of GitOps applications with their status
    """
    apps = []

    if not kind or kind.lower() == "kustomization":
        if crd_exists(FLUX_KUSTOMIZATION_CRD, context):
            for item in get_resources("kustomizations.kustomize.toolkit.fluxcd.io", namespace, context, label_selector):
                status = item.get("status", {})
                conditions = status.get("conditions", [])
                ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
                apps.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "kind": "Kustomization",
                    "engine": "flux",
                    "ready": ready_cond.get("status") == "True",
                    "status": ready_cond.get("reason", "Unknown"),
                    "message": ready_cond.get("message", ""),
                    "source": item.get("spec", {}).get("sourceRef", {}),
                    "path": item.get("spec", {}).get("path", ""),
                    "last_applied": status.get("lastAppliedRevision", ""),
                })

    if not kind or kind.lower() == "helmrelease":
        if crd_exists(FLUX_HELMRELEASE_CRD, context):
            for item in get_resources("helmreleases.helm.toolkit.fluxcd.io", namespace, context, label_selector):
                status = item.get("status", {})
                conditions = status.get("conditions", [])
                ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
                apps.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "kind": "HelmRelease",
                    "engine": "flux",
                    "ready": ready_cond.get("status") == "True",
                    "status": ready_cond.get("reason", "Unknown"),
                    "message": ready_cond.get("message", ""),
                    "chart": item.get("spec", {}).get("chart", {}),
                    "version": status.get("lastAppliedRevision", ""),
                })

    if not kind or kind.lower() == "application":
        if crd_exists(ARGOCD_APP_CRD, context):
            for item in get_resources("applications.argoproj.io", namespace, context, label_selector):
                status = item.get("status", {})
                health = status.get("health", {})
                sync = status.get("sync", {})
                apps.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "kind": "Application",
                    "engine": "argocd",
                    "ready": health.get("status") == "Healthy" and sync.get("status") == "Synced",
                    "health": health.get("status", "Unknown"),
                    "sync_status": sync.get("status", "Unknown"),
                    "message": health.get("message", ""),
                    "source": item.get("spec", {}).get("source", {}),
                    "destination": item.get("spec", {}).get("destination", {}),
                })

    return {
        "context": context or "current",
        "total": len(apps),
        "applications": apps,
    }


def gitops_app_get(
    name: str,
    namespace: str,
    kind: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get details of a specific GitOps application.

    Args:
        name: Name of the application
        namespace: Namespace of the application
        kind: Kind of application (Kustomization, HelmRelease, Application)
        context: Kubernetes context to use (optional)

    Returns:
        Detailed application information
    """
    kind_map = {
        "kustomization": "kustomizations.kustomize.toolkit.fluxcd.io",
        "helmrelease": "helmreleases.helm.toolkit.fluxcd.io",
        "application": "applications.argoproj.io",
    }

    k8s_kind = kind_map.get(kind.lower())
    if not k8s_kind:
        return {"success": False, "error": f"Unknown kind: {kind}"}

    args = ["get", k8s_kind, name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "application": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def gitops_app_sync(
    name: str,
    namespace: str,
    kind: str,
    context: str = ""
) -> Dict[str, Any]:
    """Trigger sync/reconciliation for a GitOps application.

    Args:
        name: Name of the application
        namespace: Namespace of the application
        kind: Kind of application (Kustomization, HelmRelease for Flux)
        context: Kubernetes context to use (optional)

    Returns:
        Sync trigger result
    """
    kind_lower = kind.lower()

    if kind_lower == "kustomization":
        if not crd_exists(FLUX_KUSTOMIZATION_CRD, context):
            return {"success": False, "error": "Flux Kustomization CRD not installed"}

        annotation = "reconcile.fluxcd.io/requestedAt"
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        args = [
            "annotate", "kustomizations.kustomize.toolkit.fluxcd.io",
            name, "-n", namespace,
            f"{annotation}={timestamp}", "--overwrite"
        ]
        result = run_kubectl(args, context)

        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Triggered reconciliation for Kustomization {name}",
                "annotation": f"{annotation}={timestamp}",
            }
        return {"success": False, "error": result.get("error", "Failed to trigger sync")}

    elif kind_lower == "helmrelease":
        if not crd_exists(FLUX_HELMRELEASE_CRD, context):
            return {"success": False, "error": "Flux HelmRelease CRD not installed"}

        annotation = "reconcile.fluxcd.io/requestedAt"
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        args = [
            "annotate", "helmreleases.helm.toolkit.fluxcd.io",
            name, "-n", namespace,
            f"{annotation}={timestamp}", "--overwrite"
        ]
        result = run_kubectl(args, context)

        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Triggered reconciliation for HelmRelease {name}",
                "annotation": f"{annotation}={timestamp}",
            }
        return {"success": False, "error": result.get("error", "Failed to trigger sync")}

    elif kind_lower == "application":
        if not crd_exists(ARGOCD_APP_CRD, context):
            return {"success": False, "error": "ArgoCD Application CRD not installed"}

        annotation = "argocd.argoproj.io/refresh"
        args = [
            "annotate", "applications.argoproj.io",
            name, "-n", namespace,
            f"{annotation}=hard", "--overwrite"
        ]
        result = run_kubectl(args, context)

        if result["success"]:
            return {
                "success": True,
                "context": context or "current",
                "message": f"Triggered hard refresh for ArgoCD Application {name}",
            }
        return {"success": False, "error": result.get("error", "Failed to trigger sync")}

    return {"success": False, "error": f"Unknown kind: {kind}"}


def gitops_app_status(
    name: str,
    namespace: str,
    kind: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get sync status of a GitOps application.

    Args:
        name: Name of the application
        namespace: Namespace of the application
        kind: Kind of application (Kustomization, HelmRelease, Application)
        context: Kubernetes context to use (optional)

    Returns:
        Application status information
    """
    result = gitops_app_get(name, namespace, kind, context)
    if not result.get("success"):
        return result

    app = result["application"]
    status = app.get("status", {})
    kind_lower = kind.lower()

    if kind_lower in ("kustomization", "helmrelease"):
        conditions = status.get("conditions", [])
        ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
        reconciling_cond = next((c for c in conditions if c.get("type") == "Reconciling"), {})

        return {
            "success": True,
            "context": context or "current",
            "name": name,
            "namespace": namespace,
            "kind": kind,
            "ready": ready_cond.get("status") == "True",
            "reason": ready_cond.get("reason", "Unknown"),
            "message": ready_cond.get("message", ""),
            "reconciling": reconciling_cond.get("status") == "True",
            "last_applied_revision": status.get("lastAppliedRevision", ""),
            "last_attempted_revision": status.get("lastAttemptedRevision", ""),
            "observed_generation": status.get("observedGeneration"),
        }

    elif kind_lower == "application":
        health = status.get("health", {})
        sync = status.get("sync", {})
        operation = status.get("operationState", {})

        return {
            "success": True,
            "context": context or "current",
            "name": name,
            "namespace": namespace,
            "kind": kind,
            "health_status": health.get("status", "Unknown"),
            "health_message": health.get("message", ""),
            "sync_status": sync.get("status", "Unknown"),
            "sync_revision": sync.get("revision", ""),
            "operation_phase": operation.get("phase", ""),
            "operation_message": operation.get("message", ""),
        }

    return {"success": False, "error": f"Unknown kind: {kind}"}


def gitops_sources_list(
    namespace: str = "",
    context: str = "",
    kind: str = "",
    label_selector: str = ""
) -> Dict[str, Any]:
    """List Flux source resources (GitRepositories, HelmRepositories).

    Args:
        namespace: Filter by namespace (empty for all namespaces)
        context: Kubernetes context to use (optional)
        kind: Filter by kind (GitRepository, HelmRepository)
        label_selector: Label selector to filter resources

    Returns:
        List of source resources
    """
    sources = []

    if not kind or kind.lower() == "gitrepository":
        if crd_exists(FLUX_GITREPO_CRD, context):
            for item in get_resources("gitrepositories.source.toolkit.fluxcd.io", namespace, context, label_selector):
                status = item.get("status", {})
                conditions = status.get("conditions", [])
                ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
                artifact = status.get("artifact", {})
                sources.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "kind": "GitRepository",
                    "ready": ready_cond.get("status") == "True",
                    "status": ready_cond.get("reason", "Unknown"),
                    "url": item.get("spec", {}).get("url", ""),
                    "branch": item.get("spec", {}).get("ref", {}).get("branch", ""),
                    "revision": artifact.get("revision", ""),
                    "last_update": artifact.get("lastUpdateTime", ""),
                })

    if not kind or kind.lower() == "helmrepository":
        if crd_exists(FLUX_HELMREPO_CRD, context):
            for item in get_resources("helmrepositories.source.toolkit.fluxcd.io", namespace, context, label_selector):
                status = item.get("status", {})
                conditions = status.get("conditions", [])
                ready_cond = next((c for c in conditions if c.get("type") == "Ready"), {})
                artifact = status.get("artifact", {})
                sources.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "kind": "HelmRepository",
                    "ready": ready_cond.get("status") == "True",
                    "status": ready_cond.get("reason", "Unknown"),
                    "url": item.get("spec", {}).get("url", ""),
                    "revision": artifact.get("revision", ""),
                    "last_update": artifact.get("lastUpdateTime", ""),
                })

    return {
        "context": context or "current",
        "total": len(sources),
        "sources": sources,
    }


def gitops_source_get(
    name: str,
    namespace: str,
    kind: str,
    context: str = ""
) -> Dict[str, Any]:
    """Get details of a Flux source resource.

    Args:
        name: Name of the source
        namespace: Namespace of the source
        kind: Kind of source (GitRepository, HelmRepository)
        context: Kubernetes context to use (optional)

    Returns:
        Detailed source information
    """
    kind_map = {
        "gitrepository": "gitrepositories.source.toolkit.fluxcd.io",
        "helmrepository": "helmrepositories.source.toolkit.fluxcd.io",
    }

    k8s_kind = kind_map.get(kind.lower())
    if not k8s_kind:
        return {"success": False, "error": f"Unknown kind: {kind}"}

    args = ["get", k8s_kind, name, "-n", namespace, "-o", "json"]
    result = run_kubectl(args, context)

    if result["success"]:
        try:
            data = json.loads(result["output"])
            return {
                "success": True,
                "context": context or "current",
                "source": data,
            }
        except json.JSONDecodeError:
            return {"success": False, "error": "Failed to parse response"}

    return {"success": False, "error": result.get("error", "Unknown error")}


def gitops_detect_engine(context: str = "") -> Dict[str, Any]:
    """Detect which GitOps engines are installed in the cluster.

    Args:
        context: Kubernetes context to use (optional)

    Returns:
        Detection results for Flux and ArgoCD
    """
    flux_installed = any([
        crd_exists(FLUX_KUSTOMIZATION_CRD, context),
        crd_exists(FLUX_HELMRELEASE_CRD, context),
    ])

    argocd_installed = crd_exists(ARGOCD_APP_CRD, context)

    return {
        "context": context or "current",
        "flux": {
            "installed": flux_installed,
            "kustomizations": crd_exists(FLUX_KUSTOMIZATION_CRD, context),
            "helmreleases": crd_exists(FLUX_HELMRELEASE_CRD, context),
            "gitrepositories": crd_exists(FLUX_GITREPO_CRD, context),
            "helmrepositories": crd_exists(FLUX_HELMREPO_CRD, context),
        },
        "argocd": {
            "installed": argocd_installed,
            "applications": crd_exists(ARGOCD_APP_CRD, context),
            "applicationsets": crd_exists(ARGOCD_APPSET_CRD, context),
        },
    }


def register_gitops_tools(mcp: FastMCP, non_destructive: bool = False):
    """Register GitOps tools with the MCP server."""

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def gitops_apps_list_tool(
        namespace: str = "",
        context: str = "",
        kind: str = "",
        label_selector: str = ""
    ) -> str:
        """List GitOps applications from Flux or Argo CD."""
        return json.dumps(gitops_apps_list(namespace, context, kind, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def gitops_app_get_tool(
        name: str,
        namespace: str,
        kind: str,
        context: str = ""
    ) -> str:
        """Get details of a specific GitOps application."""
        return json.dumps(gitops_app_get(name, namespace, kind, context), indent=2)

    @mcp.tool()
    def gitops_app_sync_tool(
        name: str,
        namespace: str,
        kind: str,
        context: str = ""
    ) -> str:
        """Trigger sync/reconciliation for a GitOps application."""
        if non_destructive:
            return json.dumps({"success": False, "error": "Operation blocked: non-destructive mode"})
        return json.dumps(gitops_app_sync(name, namespace, kind, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def gitops_app_status_tool(
        name: str,
        namespace: str,
        kind: str,
        context: str = ""
    ) -> str:
        """Get sync status of a GitOps application."""
        return json.dumps(gitops_app_status(name, namespace, kind, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def gitops_sources_list_tool(
        namespace: str = "",
        context: str = "",
        kind: str = "",
        label_selector: str = ""
    ) -> str:
        """List Flux source resources (GitRepositories, HelmRepositories)."""
        return json.dumps(gitops_sources_list(namespace, context, kind, label_selector), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def gitops_source_get_tool(
        name: str,
        namespace: str,
        kind: str,
        context: str = ""
    ) -> str:
        """Get details of a Flux source resource."""
        return json.dumps(gitops_source_get(name, namespace, kind, context), indent=2)

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
    def gitops_detect_engine_tool(context: str = "") -> str:
        """Detect which GitOps engines are installed in the cluster."""
        return json.dumps(gitops_detect_engine(context), indent=2)
