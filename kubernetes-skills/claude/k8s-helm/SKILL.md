---
name: k8s-helm
description: Manage Helm charts, releases, and repositories. Use for Helm installations, upgrades, rollbacks, chart development, and release management.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 18
  category: workloads
---

# Helm Chart Management

Comprehensive Helm v3 operations using kubectl-mcp-server's 16 Helm tools.

> Requires the `helm_dev` toolset: start kubectl-mcp-server with `--toolsets default,helm_dev` (or `MCP_TOOLSETS=default,helm_dev`).

## When to Apply

Use this skill when:
- User mentions: "helm", "chart", "release", "values", "repository"
- Operations: installing charts, upgrading releases, rollbacks
- Keywords: "package", "template", "lint", "repo add"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Template before install (dry run) | CRITICAL | `helm_template` |
| 2 | Check existing releases first | CRITICAL | `helm_list` |
| 3 | Lint charts before packaging | HIGH | `helm_lint` |
| 4 | Note revision before upgrade | HIGH | `helm_history` |
| 5 | Verify values after upgrade | MEDIUM | `helm_get` |
| 6 | Update repos before search | LOW | `helm_repo_update` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Install chart | `install_helm_chart` | `install_helm_chart(name, chart, namespace)` |
| Upgrade release | `upgrade_helm_chart` | `upgrade_helm_chart(name, chart, namespace, values)` |
| Rollback | `helm_rollback` | `helm_rollback(name, namespace, revision)` |
| List releases | `helm_list` | `helm_list(namespace)` |
| Get values | `helm_get` | `helm_get(name, namespace)` |
| Template (dry run) | `helm_template` | `helm_template(name, chart, namespace)` |

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
upgrade_helm_chart(
    name="my-release",
    chart="bitnami/nginx",
    namespace="web",
    values={"replicaCount": 5}
)
```

## Rollback Release

```python
helm_rollback(
    release_name="my-release",
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
helm_list(namespace="web")

helm_list()
```

### Get Release Details

```python
helm_status(release_name="my-release", namespace="web")
```

### Release History

```python
helm_history(release_name="my-release", namespace="web")
```

### Get Release Values

```python
helm_get(release_name="my-release", namespace="web")
```

### Get Release Manifest

```python
helm_get(what="manifest", release_name="my-release", namespace="web")
```

## Repository Management

### Add Repository

```python
helm_repo_add(name="bitnami", url="https://charts.bitnami.com/bitnami")
```

### List Repositories

```python
helm_repo_list()
```

### Update Repositories

```python
helm_repo_update()
```

### Search Charts

```python
helm_search_repo(keyword="nginx")

helm_search_repo(keyword="bitnami/postgres")
```

## Chart Development

### Template Chart (Dry Run)

```python
helm_template(
    name="my-release",
    chart="./my-chart",
    namespace="test",
    values={"key": "value"}
)
```

### Lint Chart

```python
helm_lint(chart_path="./my-chart")
```

### Package Chart

```python
helm_package(chart_path="./my-chart", destination="./packages")
```

## Common Workflows

### New Application Deployment

```python
helm_repo_add(name="bitnami", url="...")

helm_search_repo(keyword="postgresql")

helm_template(...)

install_helm_chart(...)

helm_status(...)
```

### Upgrade with Rollback Safety

```python
helm_history(name, namespace)

upgrade_helm_chart(name, chart, namespace, values)

helm_rollback(name, namespace, revision)
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
helm_status(name, namespace)

kubectl_get(resource_type="pods", namespace, label_selector="app.kubernetes.io/instance=<release>")
```

### Failed Installation

```python
helm_history(name, namespace)

kubectl_get(resource_type="events", namespace)

uninstall_helm_chart(name, namespace)
```

### Values Not Applied

```python
helm_get(name, namespace)

helm_template(...)

upgrade_helm_chart(...)
```

## Scripts

See [scripts/lint-chart.sh](scripts/lint-chart.sh) for automated chart validation.

## Best Practices

1. **Always Template First**
   ```python
   helm_template(name, chart, namespace, values)
   ```

2. **Use Semantic Versioning**
   ```python
   helm_show(chart="bitnami/nginx", what="chart", version="1.2.3")
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
