---
name: k8s-helm
description: Manage Helm charts, releases, and repositories. Use for Helm installations, upgrades, rollbacks, chart development, and release management.
---

# Helm Chart Management

Comprehensive Helm v3 operations using kubectl-mcp-server's 16 Helm tools.

## Quick Reference

### Install Chart
```
install_helm_chart(
    name="my-release",
    chart="bitnami/nginx",
    namespace="web",
    values={"replicaCount": 3, "service.type": "LoadBalancer"}
)
```

### Upgrade Release
```
upgrade_helm_release(
    name="my-release",
    chart="bitnami/nginx",
    namespace="web",
    values={"replicaCount": 5}
)
```

### Rollback Release
```
rollback_helm_release(
    name="my-release",
    namespace="web",
    revision=1  # Specific revision, or 0 for previous
)
```

### Uninstall Release
```
uninstall_helm_chart(name="my-release", namespace="web")
```

## Release Management

### List Releases
```
list_helm_releases(namespace="web")
list_helm_releases()  # All namespaces
```

### Get Release Details
```
get_helm_release(name="my-release", namespace="web")
```

### Release History
```
get_helm_history(name="my-release", namespace="web")
```

### Get Release Values
```
get_helm_values(name="my-release", namespace="web")
```

### Get Release Manifest
```
get_helm_manifest(name="my-release", namespace="web")
```

## Repository Management

### Add Repository
```
add_helm_repo(name="bitnami", url="https://charts.bitnami.com/bitnami")
```

### List Repositories
```
list_helm_repos()
```

### Update Repositories
```
update_helm_repos()
```

### Search Charts
```
search_helm_charts(keyword="nginx")
search_helm_charts(keyword="postgres", repo="bitnami")
```

## Chart Development

### Template Chart (Dry Run)
```
template_helm_chart(
    name="my-release",
    chart="./my-chart",
    namespace="test",
    values={"key": "value"}
)
```

### Lint Chart
```
lint_helm_chart(chart="./my-chart")
```

### Package Chart
```
package_helm_chart(chart="./my-chart", destination="./packages")
```

## Common Workflows

### New Application Deployment
```
1. add_helm_repo(name="bitnami", url="...")
2. search_helm_charts(keyword="postgresql")
3. template_helm_chart(...)  # Preview
4. install_helm_chart(...)   # Deploy
5. get_helm_release(...)     # Verify
```

### Upgrade with Rollback Safety
```
1. get_helm_history(name, namespace)  # Note current revision
2. upgrade_helm_release(name, chart, namespace, values)
3. # If issues:
   rollback_helm_release(name, namespace, revision)
```

### Multi-Environment Deployment
```
# Development
install_helm_chart(
    name="app",
    chart="./charts/app",
    namespace="dev",
    values={"replicas": 1},
    context="development"
)

# Staging
install_helm_chart(
    name="app",
    chart="./charts/app",
    namespace="staging",
    values={"replicas": 2},
    context="staging"
)

# Production
install_helm_chart(
    name="app",
    chart="./charts/app",
    namespace="prod",
    values={"replicas": 5},
    context="production"
)
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

### Release Stuck in Pending
```
get_helm_release(name, namespace)
get_pods(namespace, label_selector="app.kubernetes.io/instance=<release>")
```

### Failed Installation
```
get_helm_history(name, namespace)  # Check status
get_events(namespace)              # Check events
uninstall_helm_chart(name, namespace)  # Clean up
```

### Values Not Applied
```
get_helm_values(name, namespace)  # Verify current values
template_helm_chart(...)          # Preview with new values
upgrade_helm_release(...)         # Apply
```

## Best Practices

1. **Always Template First**
   ```
   template_helm_chart(name, chart, namespace, values)
   # Review output before install
   ```

2. **Use Semantic Versioning**
   ```
   install_helm_chart(..., version="1.2.3")
   ```

3. **Store Values in Git**
   - `values-dev.yaml`
   - `values-staging.yaml`
   - `values-prod.yaml`

4. **Namespace Isolation**
   - One namespace per release
   - Easier cleanup and RBAC

## Related Skills
- [k8s-deploy](../k8s-deploy/SKILL.md) - Deployment strategies
- [k8s-gitops](../k8s-gitops/SKILL.md) - GitOps Helm releases
