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
| 2 | List contexts before switching | HIGH | `list_contexts_tool` |
| 3 | Compare before promoting | MEDIUM | `compare_namespaces` |
| 4 | Use naming conventions | LOW | `prod-*`, `staging-*` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List contexts | `list_contexts_tool` | `list_contexts_tool()` |
| View kubeconfig | `kubeconfig_view` | `kubeconfig_view()` |
| List CAPI clusters | `capi_clusters_list_tool` | `capi_clusters_list_tool(namespace)` |
| Get CAPI kubeconfig | `capi_cluster_kubeconfig_tool` | `capi_cluster_kubeconfig_tool(name, namespace)` |

## Context Management

### List Available Contexts

```python
list_contexts_tool()
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
get_pods(namespace="default", context="production-cluster")

get_pods(namespace="default", context="staging-cluster")
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
get_pods(namespace="app", context="prod-us-east")
get_pods(namespace="app", context="prod-eu-west")

get_pods(namespace="app", context="development")
```

### Cross-Cluster Health Check

```python
for context in ["prod-1", "prod-2", "staging"]:
    get_nodes(context=context)
    get_pods(namespace="kube-system", context=context)
```

## Cluster API (CAPI) Management

For managing cluster lifecycle:

### List Managed Clusters

```python
capi_clusters_list_tool(namespace="capi-system")
```

### Get Cluster Details

```python
capi_cluster_get_tool(name="prod-cluster", namespace="capi-system")
```

### Get Workload Cluster Kubeconfig

```python
capi_cluster_kubeconfig_tool(name="prod-cluster", namespace="capi-system")
```

### Machine Management

```python
capi_machines_list_tool(namespace="capi-system")
capi_machinedeployments_list_tool(namespace="capi-system")
```

### Scale Cluster

```python
capi_machinedeployment_scale_tool(
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

list_helm_releases(
    namespace="web",
    context="staging-cluster"
)
```

## Multi-Cluster GitOps

### Flux Across Clusters

```python
flux_kustomizations_list_tool(
    namespace="flux-system",
    context="cluster-1"
)

flux_reconcile_tool(
    kind="kustomization",
    name="apps",
    namespace="flux-system",
    context="cluster-2"
)
```

### ArgoCD Across Clusters

```python
argocd_apps_list_tool(namespace="argocd", context="management-cluster")
```

## Federation Patterns

### Secret Synchronization

```python
get_secrets(namespace="app", context="source-cluster")

kubectl_apply(secret_manifest, namespace="app", context="target-cluster")
```

### Cross-Cluster Service Discovery

With Cilium ClusterMesh or Istio multi-cluster:

```python
cilium_nodes_list_tool(context="cluster-1")
istio_proxy_status_tool(context="cluster-2")
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
