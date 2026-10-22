---
name: k8s-gitops
description: Manage GitOps workflows with Flux and ArgoCD. Use for sync status, reconciliation, app management, source management, and GitOps troubleshooting.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 7
  category: gitops
---

# Kubernetes GitOps

GitOps workflows using Flux and ArgoCD with kubectl-mcp-server tools.

> Requires the `gitops` toolset: start kubectl-mcp-server with `--toolsets default,gitops` (or `MCP_TOOLSETS=default,gitops`). For deep work, the project-maintained MCP servers may fit better: Argo CD: https://github.com/argoproj-labs/mcp-for-argocd; Flux: https://fluxoperator.dev/mcp-server/.

## When to Apply

Use this skill when:
- User mentions: "Flux", "ArgoCD", "GitOps", "sync", "reconcile"
- Operations: checking sync status, triggering reconciliation, drift detection
- Keywords: "out of sync", "deploy from git", "continuous delivery"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check source readiness before troubleshooting | CRITICAL | `gitops_sources_list` |
| 2 | Verify sync status before deployments | HIGH | `gitops_app_get` |
| 3 | Reconcile after git changes | MEDIUM | `gitops_app_sync` |
| 4 | Suspend before manual changes | LOW | `kubectl_patch` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List Flux kustomizations | `gitops_apps_list` | `gitops_apps_list(namespace)` |
| Reconcile Flux | `gitops_app_sync` | `gitops_app_sync(kind, name, namespace)` |
| List ArgoCD apps | `gitops_apps_list` | `gitops_apps_list(namespace)` |
| Sync ArgoCD | `gitops_app_sync` | `gitops_app_sync(name, namespace)` |

## Flux CD

### Check Flux Status

```python
gitops_apps_list(namespace="flux-system")
gitops_apps_list(namespace)
gitops_sources_list(namespace="flux-system")
```

### Reconcile Resources

```python
gitops_app_sync(
    kind="kustomization",
    name="my-app",
    namespace="flux-system"
)

gitops_app_sync(
    kind="helmrelease",
    name="my-chart",
    namespace="default"
)
```

### Suspend/Resume

```python
kubectl_patch(resource_type="kustomization", name="my-app", namespace="flux-system", patch={"spec": {"suspend": true}}, patch_type="merge")

kubectl_patch(resource_type="kustomization", name="my-app", namespace="flux-system", patch={"spec": {"suspend": false}}, patch_type="merge")
```

See [FLUX.md](FLUX.md) for detailed Flux workflows.

## ArgoCD

### List Applications

```python
gitops_apps_list(namespace="argocd")
```

### Get App Status

```python
gitops_app_get(kind="application", name="my-app", namespace="argocd")
```

### Sync Application

```python
gitops_app_sync(kind="application", name="my-app", namespace="argocd")
```

### Refresh App

```python
gitops_app_sync(kind="application", name="my-app", namespace="argocd")
```

See [ARGOCD.md](ARGOCD.md) for detailed ArgoCD workflows.

## GitOps Troubleshooting

### Flux Not Syncing

| Symptom | Check | Resolution |
|---------|-------|------------|
| Source not ready | `gitops_sources_list()` | Check git credentials |
| Kustomization failed | `gitops_apps_list()` | Check manifest errors |
| HelmRelease failed | `gitops_apps_list()` | Check values, chart version |

### ArgoCD Out of Sync

| Symptom | Check | Resolution |
|---------|-------|------------|
| OutOfSync | `gitops_app_get()` | Manual sync or check auto-sync |
| Degraded | Check health status | Fix unhealthy resources |
| Unknown | Refresh app | `gitops_app_sync()` |

## Environment Promotion

### With Flux Kustomizations

```python
gitops_app_sync(kind="kustomization", name="staging", namespace="flux-system")

gitops_app_sync(kind="kustomization", name="production", namespace="flux-system")
```

### With ArgoCD

```python
gitops_app_sync(kind="application", name="app-staging", namespace="argocd")

gitops_app_get(kind="application", name="app-staging", namespace="argocd")

gitops_app_sync(kind="application", name="app-production", namespace="argocd")
```

## Multi-Cluster GitOps

Manage GitOps across clusters:

```python
gitops_apps_list(namespace="flux-system", context="cluster-1")
gitops_apps_list(namespace="flux-system", context="cluster-2")

gitops_app_sync(
    kind="kustomization",
    name="apps",
    namespace="flux-system",
    context="production-cluster"
)
```

## Drift Detection

Compare live state with desired:

```python
gitops_app_get(kind="application", name="my-app", namespace="argocd")

gitops_apps_list(namespace="flux-system")
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
