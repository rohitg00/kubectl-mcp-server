# ArgoCD Deep Dive

Detailed workflows for GitOps with ArgoCD.

## ArgoCD Resources

### Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/my-app
    targetRevision: HEAD
    path: deploy/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

### ApplicationSet

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - cluster: production
        url: https://prod.k8s.local
      - cluster: staging
        url: https://staging.k8s.local
  template:
    metadata:
      name: 'my-app-{{cluster}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/org/my-app
        path: 'deploy/{{cluster}}'
      destination:
        server: '{{url}}'
        namespace: my-app
```

## MCP Server Tools

```python
# List all applications
argocd_apps_list_tool(namespace="argocd")

# Get application details
argocd_app_get_tool(name="my-app", namespace="argocd")

# Sync application
argocd_sync_tool(name="my-app", namespace="argocd")

# Refresh application (fetch latest from git)
argocd_refresh_tool(name="my-app", namespace="argocd")
```

## Application States

| State | Meaning | Action |
|-------|---------|--------|
| Synced | Matches desired state | None |
| OutOfSync | Differs from git | Sync |
| Unknown | Cannot determine | Refresh |
| Missing | Resource deleted | Sync |

## Health States

| State | Meaning | Action |
|-------|---------|--------|
| Healthy | All resources ready | None |
| Progressing | Resources updating | Wait |
| Degraded | Resources failing | Debug |
| Suspended | Manually paused | Resume |
| Missing | App doesn't exist | Create |

## Common Workflows

### Check Application Status

```
1. argocd_apps_list_tool(namespace="argocd")
2. argocd_app_get_tool(name="my-app", namespace="argocd")
```

### Force Sync

```
argocd_refresh_tool(name="my-app", namespace="argocd")  # Refresh first
argocd_sync_tool(name="my-app", namespace="argocd")     # Then sync
```

### Sync with Prune

When resources are deleted from git:
```
argocd_sync_tool(name="my-app", namespace="argocd", prune=True)
```

## Multi-Cluster Deployment

ArgoCD can manage multiple clusters:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app-prod
spec:
  destination:
    server: https://prod-cluster.k8s.local  # External cluster
    namespace: production
```

## Troubleshooting

### OutOfSync

```
argocd_app_get_tool(name, namespace)
# Check diff between desired and live state
# May need manual sync or auto-sync enabled
```

### Sync Failed

```
argocd_app_get_tool(name, namespace)
get_events(namespace=target_namespace)
# Check:
# - RBAC permissions
# - Resource conflicts
# - Namespace exists
```

### Degraded Health

```
argocd_app_get_tool(name, namespace)
get_pods(namespace=target_namespace)
describe_pod(name, target_namespace)
```

## Sync Options

| Option | Purpose |
|--------|---------|
| Prune | Delete resources removed from git |
| SelfHeal | Auto-fix manual changes |
| CreateNamespace | Create target namespace |
| ApplyOutOfSyncOnly | Only sync changed resources |
| SkipDryRunOnMissingResource | Skip validation |
