---
name: k8s-multicluster
description: Manage multiple Kubernetes clusters, switch contexts, and perform cross-cluster operations. Use when working with multiple clusters, comparing environments, or managing cluster lifecycle.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 15
  category: multicluster
---

# Multi-Cluster Kubernetes Management

Cross-cluster operations and context management using kubectl-mcp-server's multi-cluster support.

## When to Apply

Use this skill when:
- User mentions: "cluster", "context", "multi-cluster", "cross-cluster"
- Operations: switching contexts, comparing clusters, federated deployments
- Keywords: "different environment", "production vs staging", "all clusters"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Always specify context for prod | CRITICAL | `context` parameter |
| 2 | List contexts before switching | HIGH | `list_contexts` |
| 3 | Compare before promoting | MEDIUM | `compare_namespaces` |
| 4 | Use naming conventions | LOW | `prod-*`, `staging-*` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List contexts | `list_contexts` | `list_contexts()` |
| View kubeconfig | `kubeconfig_view` | `kubeconfig_view()` |
| List CAPI clusters | `capi_list_clusters` | `capi_list_clusters(namespace)` |
| Get CAPI kubeconfig | `capi_get_cluster_kubeconfig` | `capi_get_cluster_kubeconfig(name, namespace)` |

## Context Management

### List Available Contexts

```python
list_contexts()
```

### View Current Context

```python
kubeconfig_view()
```

### Switch Context

CLI: `kubectl-mcp-server context <context-name>`

## Cross-Cluster Operations

All kubectl-mcp-server tools support the `context` parameter:

```python
kubectl_get(resource_type="pods", namespace="default", context="production-cluster")

kubectl_get(resource_type="pods", namespace="default", context="staging-cluster")
```

## Common Multi-Cluster Patterns

### Compare Environments

```python
compare_namespaces(
    namespace1="production",
    namespace2="staging",
    resource_type="deployment",
    context="production-cluster"
)
```

### Parallel Queries

Query multiple clusters simultaneously:

```python
kubectl_get(resource_type="pods", namespace="app", context="prod-us-east")
kubectl_get(resource_type="pods", namespace="app", context="prod-eu-west")

kubectl_get(resource_type="pods", namespace="app", context="development")
```

### Cross-Cluster Health Check

```python
for context in ["prod-1", "prod-2", "staging"]:
    kubectl_get(resource_type="nodes", context=context)
    kubectl_get(resource_type="pods", namespace="kube-system", context=context)
```

## Cluster API (CAPI) Management

For managing cluster lifecycle:

### List Managed Clusters

```python
capi_list_clusters(namespace="capi-system")
```

### Get Cluster Details

```python
capi_get_cluster(name="prod-cluster", namespace="capi-system")
```

### Get Workload Cluster Kubeconfig

```python
capi_get_cluster_kubeconfig(name="prod-cluster", namespace="capi-system")
```

### Machine Management

```python
capi_list_machines(namespace="capi-system")
capi_list_machinedeployments(namespace="capi-system")
```

### Scale Cluster

```python
capi_scale_machinedeployment(
    name="prod-cluster-md-0",
    namespace="capi-system",
    replicas=5
)
```

See [CONTEXT-SWITCHING.md](CONTEXT-SWITCHING.md) for detailed patterns.

## Multi-Cluster Helm

Deploy charts to specific clusters:

```python
install_helm_chart(
    name="nginx",
    chart="bitnami/nginx",
    namespace="web",
    context="production-cluster"
)

helm_list(
    namespace="web",
    context="staging-cluster"
)
```

## Multi-Cluster GitOps

### Flux Across Clusters

```python
gitops_apps_list(
    namespace="flux-system",
    context="cluster-1"
)

gitops_app_sync(
    kind="kustomization",
    name="apps",
    namespace="flux-system",
    context="cluster-2"
)
```

### ArgoCD Across Clusters

```python
gitops_apps_list(namespace="argocd", context="management-cluster")
```

## Federation Patterns

### Secret Synchronization

```python
kubectl_get(resource_type="secrets", namespace="app", context="source-cluster")

kubectl_apply(secret_manifest, namespace="app", context="target-cluster")
```

### Cross-Cluster Service Discovery

With Cilium ClusterMesh or Istio multi-cluster:

```python
cilium_list_nodes(context="cluster-1")
istio_proxy_status(context="cluster-2")
```

## Best Practices

1. **Naming Convention**: Use descriptive context names (`prod-us-east-1`, `staging-eu-west-1`)
2. **Access Control**: Different kubeconfigs per environment
3. **Always Specify Context**: Avoid accidental cross-cluster operations
4. **Cluster Groups**: Organize by purpose (`prod-*`, `staging-*`, `dev-*`)

## Related Skills

- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Debug across clusters
- [k8s-gitops](../k8s-gitops/SKILL.md) - GitOps multi-cluster
- [k8s-capi](../k8s-capi/SKILL.md) - Cluster API management
