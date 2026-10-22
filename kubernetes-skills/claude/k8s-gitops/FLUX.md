# Flux CD Deep Dive

Detailed workflows for GitOps with Flux.

## Flux Resources

### GitRepository Source

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/org/my-app
  ref:
    branch: main
  secretRef:
    name: git-credentials
```

### Kustomization

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 5m
  path: ./deploy/production
  prune: true
  sourceRef:
    kind: GitRepository
    name: my-app
  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: my-app
    namespace: production
```

### HelmRelease

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: my-app
  namespace: production
spec:
  interval: 5m
  chart:
    spec:
      chart: my-app
      version: "1.2.x"
      sourceRef:
        kind: HelmRepository
        name: my-charts
        namespace: flux-system
  values:
    replicas: 3
```

## MCP Server Tools

```python
# List sources (GitRepository, HelmRepository, etc.)
gitops_sources_list(namespace="flux-system")

# List Kustomizations
gitops_apps_list(namespace="flux-system")

# List HelmReleases
gitops_apps_list(namespace="production")

# Force reconciliation
gitops_app_sync(
    kind="kustomization",
    name="my-app",
    namespace="flux-system"
)

# Suspend reconciliation
kubectl_patch(
    resource_type="kustomization",
    name="my-app",
    namespace="flux-system",
    patch={"spec": {"suspend": true}}, patch_type="merge")

# Resume reconciliation
kubectl_patch(
    resource_type="kustomization",
    name="my-app",
    namespace="flux-system",
    patch={"spec": {"suspend": false}}, patch_type="merge")
```

## Common Workflows

### Check Sync Status

```
1. gitops_sources_list(namespace="flux-system")  # Source ready?
2. gitops_apps_list(namespace="flux-system")  # Applied?
3. gitops_apps_list(namespace="production")  # Helm ready?
```

### Force Sync

```
gitops_app_sync(kind="gitrepository", name="my-app", namespace="flux-system")
gitops_app_sync(kind="kustomization", name="my-app", namespace="flux-system")
```

### Pause for Maintenance

```
kubectl_patch(resource_type="kustomization", name="production", namespace="flux-system", patch={"spec": {"suspend": true}}, patch_type="merge")
# Do maintenance
kubectl_patch(resource_type="kustomization", name="production", namespace="flux-system", patch={"spec": {"suspend": false}}, patch_type="merge")
```

## Troubleshooting

### Source Not Ready

```
gitops_sources_list(namespace="flux-system")
# Check:
# - Git URL correct
# - Secret exists and has valid credentials
# - Network access to git server
```

### Kustomization Failed

```
gitops_apps_list(namespace="flux-system")
kubectl_get(resource_type="events", namespace="flux-system")
# Check:
# - Path exists in repo
# - Kustomization.yaml valid
# - Target namespace exists
```

### HelmRelease Failed

```
gitops_apps_list(namespace)
kubectl_get(resource_type="events", namespace)
# Check:
# - Chart exists in repo
# - Version exists
# - Values are valid
```

## Multi-Environment Setup

```
flux-system/
├── sources/
│   └── git-repository.yaml
├── clusters/
│   ├── production/
│   │   └── kustomization.yaml
│   └── staging/
│       └── kustomization.yaml
└── apps/
    ├── base/
    │   ├── deployment.yaml
    │   └── kustomization.yaml
    ├── production/
    │   └── kustomization.yaml
    └── staging/
        └── kustomization.yaml
```
