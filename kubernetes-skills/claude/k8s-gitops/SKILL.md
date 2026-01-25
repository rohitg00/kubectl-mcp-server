---
name: k8s-gitops
description: Manage GitOps workflows with Flux and ArgoCD. Use for sync status, reconciliation, app management, source management, and GitOps troubleshooting.
---

# Kubernetes GitOps

GitOps workflows using Flux and ArgoCD with kubectl-mcp-server tools.

## Flux CD

### Check Flux Status
```
flux_kustomizations_list_tool(namespace="flux-system")
flux_helmreleases_list_tool(namespace)
flux_sources_list_tool(namespace="flux-system")
```

### Reconcile Resources
```
# Force sync
flux_reconcile_tool(
    kind="kustomization",
    name="my-app",
    namespace="flux-system"
)

# Reconcile Helm release
flux_reconcile_tool(
    kind="helmrelease",
    name="my-chart",
    namespace="default"
)
```

### Suspend/Resume
```
# Pause reconciliation
flux_suspend_tool(kind="kustomization", name="my-app", namespace="flux-system")

# Resume
flux_resume_tool(kind="kustomization", name="my-app", namespace="flux-system")
```

See [FLUX.md](FLUX.md) for detailed Flux workflows.

## ArgoCD

### List Applications
```
argocd_apps_list_tool(namespace="argocd")
```

### Get App Status
```
argocd_app_get_tool(name="my-app", namespace="argocd")
```

### Sync Application
```
argocd_sync_tool(name="my-app", namespace="argocd")
```

### Refresh App
```
argocd_refresh_tool(name="my-app", namespace="argocd")
```

See [ARGOCD.md](ARGOCD.md) for detailed ArgoCD workflows.

## GitOps Troubleshooting

### Flux Not Syncing

| Symptom | Check | Resolution |
|---------|-------|------------|
| Source not ready | `flux_sources_list_tool()` | Check git credentials |
| Kustomization failed | `flux_kustomizations_list_tool()` | Check manifest errors |
| HelmRelease failed | `flux_helmreleases_list_tool()` | Check values, chart version |

### ArgoCD Out of Sync

| Symptom | Check | Resolution |
|---------|-------|------------|
| OutOfSync | `argocd_app_get_tool()` | Manual sync or check auto-sync |
| Degraded | Check health status | Fix unhealthy resources |
| Unknown | Refresh app | `argocd_refresh_tool()` |

## Environment Promotion

### With Flux Kustomizations
```
# Promote from staging to production
1. flux_reconcile_tool(kind="kustomization", name="staging", namespace="flux-system")
2. Verify staging is healthy
3. Update production overlay in git
4. flux_reconcile_tool(kind="kustomization", name="production", namespace="flux-system")
```

### With ArgoCD
```
# Sync staging first
argocd_sync_tool(name="app-staging", namespace="argocd")

# Verify health
argocd_app_get_tool(name="app-staging", namespace="argocd")

# Promote to production
argocd_sync_tool(name="app-production", namespace="argocd")
```

## Multi-Cluster GitOps

Manage GitOps across clusters:
```
# Check Flux in all clusters
flux_kustomizations_list_tool(namespace="flux-system", context="cluster-1")
flux_kustomizations_list_tool(namespace="flux-system", context="cluster-2")

# Sync specific cluster
flux_reconcile_tool(
    kind="kustomization",
    name="apps",
    namespace="flux-system",
    context="production-cluster"
)
```

## Drift Detection

Compare live state with desired:
```
# ArgoCD shows drift automatically
argocd_app_get_tool(name="my-app", namespace="argocd")

# For Flux, check last applied revision
flux_kustomizations_list_tool(namespace="flux-system")
```

## Related Skills
- [k8s-deploy](../k8s-deploy/SKILL.md) - Standard deployments
- [k8s-helm](../k8s-helm/SKILL.md) - Helm chart management
