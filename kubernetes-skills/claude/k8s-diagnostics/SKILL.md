---
name: k8s-diagnostics
description: Kubernetes diagnostics for metrics, health checks, resource comparisons, and cluster analysis. Use when analyzing cluster health, comparing environments, or gathering diagnostic data.
---

# Kubernetes Diagnostics

Analyze cluster health and compare resources using kubectl-mcp-server's diagnostic tools.

## Resource Metrics

```python
# Get pod metrics (requires metrics-server)
get_resource_metrics(namespace="default")

# Get node metrics
get_node_metrics()

# Top pods by CPU
get_top_pods(namespace="default", sort_by="cpu")

# Top pods by memory
get_top_pods(namespace="default", sort_by="memory")
```

## Cluster Health Check

```python
# Comprehensive health check
cluster_health_check()
# Returns:
# - API server status
# - etcd health
# - Node status
# - System pods status
# - Resource pressure

# Quick status
get_cluster_info()
```

## Compare Environments

```python
# Compare namespaces
compare_namespaces(
    namespace1="staging",
    namespace2="production",
    resource_type="deployment"
)
# Shows differences in:
# - Image versions
# - Replica counts
# - Resource limits
# - Environment variables

# Compare across clusters
compare_namespaces(
    namespace1="default",
    namespace2="default",
    resource_type="deployment",
    context1="staging-cluster",
    context2="prod-cluster"
)
```

## API Discovery

```python
# Get API versions
get_api_versions()

# Check if CRD exists
check_crd_exists(crd_name="certificates.cert-manager.io")

# List all CRDs
list_crds()
```

## Resource Analysis

```python
# Get nodes summary
get_nodes_summary()
# Returns:
# - Node name, status
# - CPU/memory capacity
# - CPU/memory allocatable
# - Pod count
# - Conditions

# View kubeconfig (sanitized)
kubeconfig_view()

# List contexts
list_contexts_tool()
```

## Diagnostic Workflows

### Cluster Overview
```python
1. cluster_health_check()      # Overall health
2. get_nodes_summary()         # Node capacity
3. get_events(namespace="")    # Cluster-wide events
4. list_crds()                 # Installed operators
```

### Pre-deployment Check
```python
1. get_resource_metrics(namespace)  # Current usage
2. get_nodes_summary()              # Available capacity
3. compare_namespaces(staging, prod, "deployment")  # Diff check
```

### Post-incident Analysis
```python
1. get_events(namespace)       # Recent events
2. get_pod_logs(name, namespace, previous=True)  # Crash logs
3. get_resource_metrics(namespace)  # Resource pressure
4. describe_node(name)         # Node conditions
```

## Related Skills

- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Debug issues
- [k8s-cost](../k8s-cost/SKILL.md) - Cost analysis
- [k8s-incident](../k8s-incident/SKILL.md) - Incident response
