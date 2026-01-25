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
flux_sources_list_tool(namespace="flux-system")

# List Kustomizations
flux_kustomizations_list_tool(namespace="flux-system")

# List HelmReleases
flux_helmreleases_list_tool(namespace="production")

# Force reconciliation
flux_reconcile_tool(
    kind="kustomization",
    name="my-app",
    namespace="flux-system"
)

# Suspend reconciliation
flux_suspend_tool(
    kind="kustomization",
    name="my-app",
    namespace="flux-system"
)

# Resume reconciliation
flux_resume_tool(
    kind="kustomization",
    name="my-app",
    namespace="flux-system"
)
```

## Common Workflows

### Check Sync Status

```
1. flux_sources_list_tool(namespace="flux-system")  # Source ready?
2. flux_kustomizations_list_tool(namespace="flux-system")  # Applied?
3. flux_helmreleases_list_tool(namespace="production")  # Helm ready?
```

### Force Sync

```
flux_reconcile_tool(kind="gitrepository", name="my-app", namespace="flux-system")
flux_reconcile_tool(kind="kustomization", name="my-app", namespace="flux-system")
```

### Pause for Maintenance

```
flux_suspend_tool(kind="kustomization", name="production", namespace="flux-system")
# Do maintenance
flux_resume_tool(kind="kustomization", name="production", namespace="flux-system")
```

## Troubleshooting

### Source Not Ready

```
flux_sources_list_tool(namespace="flux-system")
# Check:
# - Git URL correct
# - Secret exists and has valid credentials
# - Network access to git server
```

### Kustomization Failed

```
flux_kustomizations_list_tool(namespace="flux-system")
get_events(namespace="flux-system")
# Check:
# - Path exists in repo
# - Kustomization.yaml valid
# - Target namespace exists
```

### HelmRelease Failed

```
flux_helmreleases_list_tool(namespace)
get_events(namespace)
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
