---
name: k8s-gitops
description: Manage GitOps workflows with Flux and ArgoCD. Use for sync status, reconciliation, app management, source management, and GitOps troubleshooting.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 7
  category: gitops
---

# Kubernetes GitOps

GitOps workflows using Flux and ArgoCD with kubectl-mcp-server tools.

## When to Apply

Use this skill when:
- User mentions: "Flux", "ArgoCD", "GitOps", "sync", "reconcile"
- Operations: checking sync status, triggering reconciliation, drift detection
- Keywords: "out of sync", "deploy from git", "continuous delivery"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check source readiness before troubleshooting | CRITICAL | `flux_sources_list_tool` |
| 2 | Verify sync status before deployments | HIGH | `argocd_app_get_tool` |
| 3 | Reconcile after git changes | MEDIUM | `flux_reconcile_tool` |
| 4 | Suspend before manual changes | LOW | `flux_suspend_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List Flux kustomizations | `flux_kustomizations_list_tool` | `flux_kustomizations_list_tool(namespace)` |
| Reconcile Flux | `flux_reconcile_tool` | `flux_reconcile_tool(kind, name, namespace)` |
| List ArgoCD apps | `argocd_apps_list_tool` | `argocd_apps_list_tool(namespace)` |
| Sync ArgoCD | `argocd_sync_tool` | `argocd_sync_tool(name, namespace)` |

## Flux CD

### Check Flux Status

```python
flux_kustomizations_list_tool(namespace="flux-system")
flux_helmreleases_list_tool(namespace)
flux_sources_list_tool(namespace="flux-system")
```

### Reconcile Resources

```python
flux_reconcile_tool(
    kind="kustomization",
    name="my-app",
    namespace="flux-system"
)

flux_reconcile_tool(
    kind="helmrelease",
    name="my-chart",
    namespace="default"
)
```

### Suspend/Resume

```python
flux_suspend_tool(kind="kustomization", name="my-app", namespace="flux-system")

flux_resume_tool(kind="kustomization", name="my-app", namespace="flux-system")
```

See [FLUX.md](FLUX.md) for detailed Flux workflows.

## ArgoCD

### List Applications

```python
argocd_apps_list_tool(namespace="argocd")
```

### Get App Status

```python
argocd_app_get_tool(name="my-app", namespace="argocd")
```

### Sync Application

```python
argocd_sync_tool(name="my-app", namespace="argocd")
```

### Refresh App

```python
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

```python
flux_reconcile_tool(kind="kustomization", name="staging", namespace="flux-system")

flux_reconcile_tool(kind="kustomization", name="production", namespace="flux-system")
```

### With ArgoCD

```python
argocd_sync_tool(name="app-staging", namespace="argocd")

argocd_app_get_tool(name="app-staging", namespace="argocd")

argocd_sync_tool(name="app-production", namespace="argocd")
```

## Multi-Cluster GitOps

Manage GitOps across clusters:

```python
flux_kustomizations_list_tool(namespace="flux-system", context="cluster-1")
flux_kustomizations_list_tool(namespace="flux-system", context="cluster-2")

flux_reconcile_tool(
    kind="kustomization",
    name="apps",
    namespace="flux-system",
    context="production-cluster"
)
```

## Drift Detection

Compare live state with desired:

```python
argocd_app_get_tool(name="my-app", namespace="argocd")

flux_kustomizations_list_tool(namespace="flux-system")
```

## Prerequisites

- **Flux**: Required for Flux tools
  ```bash
  flux install
  ```
- **ArgoCD**: Required for ArgoCD tools
  ```bash
  kubectl create namespace argocd
  kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
  ```

## Related Skills

- [k8s-deploy](../k8s-deploy/SKILL.md) - Standard deployments
- [k8s-helm](../k8s-helm/SKILL.md) - Helm chart management
