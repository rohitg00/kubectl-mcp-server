---
name: k8s-helm
description: Manage Helm charts, releases, and repositories. Use for Helm installations, upgrades, rollbacks, chart development, and release management.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 16
  category: workloads
---

# Helm Chart Management

Comprehensive Helm v3 operations using kubectl-mcp-server's 16 Helm tools.

## When to Apply

Use this skill when:
- User mentions: "helm", "chart", "release", "values", "repository"
- Operations: installing charts, upgrading releases, rollbacks
- Keywords: "package", "template", "lint", "repo add"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Template before install (dry run) | CRITICAL | `template_helm_chart` |
| 2 | Check existing releases first | CRITICAL | `list_helm_releases` |
| 3 | Lint charts before packaging | HIGH | `lint_helm_chart` |
| 4 | Note revision before upgrade | HIGH | `get_helm_history` |
| 5 | Verify values after upgrade | MEDIUM | `get_helm_values` |
| 6 | Update repos before search | LOW | `update_helm_repos` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Install chart | `install_helm_chart` | `install_helm_chart(name, chart, namespace)` |
| Upgrade release | `upgrade_helm_release` | `upgrade_helm_release(name, chart, namespace, values)` |
| Rollback | `rollback_helm_release` | `rollback_helm_release(name, namespace, revision)` |
| List releases | `list_helm_releases` | `list_helm_releases(namespace)` |
| Get values | `get_helm_values` | `get_helm_values(name, namespace)` |
| Template (dry run) | `template_helm_chart` | `template_helm_chart(name, chart, namespace)` |

## Install Chart

```python
install_helm_chart(
    name="my-release",
    chart="bitnami/nginx",
    namespace="web",
    values={"replicaCount": 3, "service.type": "LoadBalancer"}
)
```

## Upgrade Release

```python
upgrade_helm_release(
    name="my-release",
    chart="bitnami/nginx",
    namespace="web",
    values={"replicaCount": 5}
)
```

## Rollback Release

```python
rollback_helm_release(
    name="my-release",
    namespace="web",
    revision=1
)
```

## Uninstall Release

```python
uninstall_helm_chart(name="my-release", namespace="web")
```

## Release Management

### List Releases

```python
list_helm_releases(namespace="web")

list_helm_releases()
```

### Get Release Details

```python
get_helm_release(name="my-release", namespace="web")
```

### Release History

```python
get_helm_history(name="my-release", namespace="web")
```

### Get Release Values

```python
get_helm_values(name="my-release", namespace="web")
```

### Get Release Manifest

```python
get_helm_manifest(name="my-release", namespace="web")
```

## Repository Management

### Add Repository

```python
add_helm_repo(name="bitnami", url="https://charts.bitnami.com/bitnami")
```

### List Repositories

```python
list_helm_repos()
```

### Update Repositories

```python
update_helm_repos()
```

### Search Charts

```python
search_helm_charts(keyword="nginx")

search_helm_charts(keyword="postgres", repo="bitnami")
```

## Chart Development

### Template Chart (Dry Run)

```python
template_helm_chart(
    name="my-release",
    chart="./my-chart",
    namespace="test",
    values={"key": "value"}
)
```

### Lint Chart

```python
lint_helm_chart(chart="./my-chart")
```

### Package Chart

```python
package_helm_chart(chart="./my-chart", destination="./packages")
```

## Common Workflows

### New Application Deployment

```python
add_helm_repo(name="bitnami", url="...")

search_helm_charts(keyword="postgresql")

template_helm_chart(...)

install_helm_chart(...)

get_helm_release(...)
```

### Upgrade with Rollback Safety

```python
get_helm_history(name, namespace)

upgrade_helm_release(name, chart, namespace, values)

rollback_helm_release(name, namespace, revision)
```

### Multi-Environment Deployment

```python
install_helm_chart(
    name="app",
    chart="./charts/app",
    namespace="dev",
    values={"replicas": 1},
    context="development"
)

install_helm_chart(
    name="app",
    chart="./charts/app",
    namespace="staging",
    values={"replicas": 2},
    context="staging"
)

install_helm_chart(
    name="app",
    chart="./charts/app",
    namespace="prod",
    values={"replicas": 5},
    context="production"
)
```

## Chart Structure

See [references/CHART-STRUCTURE.md](references/CHART-STRUCTURE.md) for best practices on organizing Helm charts.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.

### Release Stuck in Pending

```python
get_helm_release(name, namespace)

get_pods(namespace, label_selector="app.kubernetes.io/instance=<release>")
```

### Failed Installation

```python
get_helm_history(name, namespace)

get_events(namespace)

uninstall_helm_chart(name, namespace)
```

### Values Not Applied

```python
get_helm_values(name, namespace)

template_helm_chart(...)

upgrade_helm_release(...)
```

## Scripts

See [scripts/lint-chart.sh](scripts/lint-chart.sh) for automated chart validation.

## Best Practices

1. **Always Template First**
   ```python
   template_helm_chart(name, chart, namespace, values)
   ```

2. **Use Semantic Versioning**
   ```python
   install_helm_chart(..., version="1.2.3")
   ```

3. **Store Values in Git**
   - `values-dev.yaml`
   - `values-staging.yaml`
   - `values-prod.yaml`

4. **Namespace Isolation**
   - One namespace per release
   - Easier cleanup and RBAC

## Prerequisites

- **Helm CLI**: Required for all Helm operations
  ```bash
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  ```

## Related Skills

- [k8s-deploy](../k8s-deploy/SKILL.md) - Deployment strategies
- [k8s-gitops](../k8s-gitops/SKILL.md) - GitOps Helm releases
