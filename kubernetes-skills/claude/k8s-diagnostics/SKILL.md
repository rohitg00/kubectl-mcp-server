---
name: k8s-diagnostics
description: Kubernetes diagnostics for metrics, health checks, resource comparisons, and cluster analysis. Use when analyzing cluster health, comparing environments, or gathering diagnostic data.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 10
  category: observability
---

# Kubernetes Diagnostics

Analyze cluster health and compare resources using kubectl-mcp-server's diagnostic tools.

## When to Apply

Use this skill when:
- User mentions: "metrics", "health check", "compare", "analysis", "capacity"
- Operations: cluster health assessment, environment comparison, resource analysis
- Keywords: "how much", "usage", "difference between", "capacity planning"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check metrics-server before using metrics | CRITICAL | `get_resource_metrics` |
| 2 | Run health check before deployments | HIGH | `cluster_health_check` |
| 3 | Compare staging vs prod before release | MEDIUM | `compare_namespaces` |
| 4 | Document baseline metrics | LOW | `get_nodes_summary` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Cluster health | `cluster_health_check` | `cluster_health_check()` |
| Pod metrics | `get_resource_metrics` | `get_resource_metrics(namespace)` |
| Node summary | `get_nodes_summary` | `get_nodes_summary()` |
| Compare envs | `compare_namespaces` | `compare_namespaces(ns1, ns2, type)` |
| List CRDs | `list_crds` | `list_crds()` |

## Resource Metrics

```python
get_resource_metrics(namespace="default")

get_node_metrics()

get_top_pods(namespace="default", sort_by="cpu")

get_top_pods(namespace="default", sort_by="memory")
```

## Cluster Health Check

```python
cluster_health_check()

get_cluster_info()
```

## Compare Environments

```python
compare_namespaces(
    namespace1="staging",
    namespace2="production",
    resource_type="deployment"
)

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
get_api_versions()

check_crd_exists(crd_name="certificates.cert-manager.io")

list_crds()
```

## Resource Analysis

```python
get_nodes_summary()

kubeconfig_view()

list_contexts_tool()
```

## Diagnostic Workflows

### Cluster Overview

```python
cluster_health_check()
get_nodes_summary()
get_events(namespace="")
list_crds()
```

### Pre-deployment Check

```python
get_resource_metrics(namespace="production")
get_nodes_summary()
compare_namespaces(namespace1="staging", namespace2="prod", resource_type="deployment")
```

### Post-incident Analysis

```python
get_events(namespace)
get_pod_logs(name, namespace, previous=True)
get_resource_metrics(namespace)
describe_node(name)
```

## Related Skills

- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Debug issues
- [k8s-cost](../k8s-cost/SKILL.md) - Cost analysis
- [k8s-incident](../k8s-incident/SKILL.md) - Incident response
