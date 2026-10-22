---
name: k8s-diagnostics
description: Kubernetes diagnostics for metrics, health checks, resource comparisons, and cluster analysis. Use when analyzing cluster health, comparing environments, or gathering diagnostic data.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 10
  category: observability
---

# Kubernetes Diagnostics

Analyze cluster health and compare resources using kubectl-mcp-server's diagnostic tools.

> Requires the `diagnostics`, `multicluster` toolsets: start kubectl-mcp-server with `--toolsets default,diagnostics,multicluster` (or `MCP_TOOLSETS=default,diagnostics,multicluster`).

## When to Apply

Use this skill when:
- User mentions: "metrics", "health check", "compare", "analysis", "capacity"
- Operations: cluster health assessment, environment comparison, resource analysis
- Keywords: "how much", "usage", "difference between", "capacity planning"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check metrics-server before using metrics | CRITICAL | `kubectl_top` |
| 2 | Run health check before deployments | HIGH | `health_check` |
| 3 | Compare staging vs prod before release | MEDIUM | `compare_namespaces` |
| 4 | Document baseline metrics | LOW | `get_nodes_summary` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Cluster health | `health_check` | `health_check()` |
| Pod metrics | `kubectl_top` | `kubectl_top(namespace)` |
| Node summary | `get_nodes_summary` | `get_nodes_summary()` |
| Compare envs | `compare_namespaces` | `compare_namespaces(ns1, ns2, type)` |
| List CRDs | `kubectl_get` | `kubectl_get(resource_type="crds")` |

## Resource Metrics

```python
kubectl_top(namespace="default")

kubectl_top(resource="nodes")

kubectl_top(resource="pods", namespace="default", sort_by="cpu")

kubectl_top(resource="pods", namespace="default", sort_by="memory")
```

## Cluster Health Check

```python
health_check()

health_check()
```

## Compare Environments

```python
compare_namespaces(
    namespace1="staging",
    namespace2="production",
    resource_type="deployment"
)

kubectl_get(resource_type="deployments", namespace="default", context="staging-cluster")
kubectl_get(resource_type="deployments", namespace="default", context="prod-cluster")
```

## API Discovery

```python
get_api_resources()

kubectl_get(resource_type="crds", name="certificates.cert-manager.io")

kubectl_get(resource_type="crds")
```

## Resource Analysis

```python
get_nodes_summary()

kubeconfig_view()

list_contexts()
```

## Diagnostic Workflows

### Cluster Overview

```python
health_check()
get_nodes_summary()
kubectl_get(resource_type="events", namespace="")
kubectl_get(resource_type="crds")
```

### Pre-deployment Check

```python
kubectl_top(namespace="production")
get_nodes_summary()
compare_namespaces(namespace1="staging", namespace2="prod", resource_type="deployment")
```

### Post-incident Analysis

```python
kubectl_get(resource_type="events", namespace)
kubectl_logs(name, namespace, previous=True)
kubectl_top(namespace)
kubectl_describe(name)
```

## Related Skills

- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Debug issues
- [k8s-cost](../k8s-cost/SKILL.md) - Cost analysis
- [k8s-incident](../k8s-incident/SKILL.md) - Incident response
