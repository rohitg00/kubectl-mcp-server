---
name: k8s-cost
description: Optimize Kubernetes costs through resource right-sizing, unused resource detection, and cluster efficiency analysis. Use for cost optimization, resource analysis, and capacity planning.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 8
  category: observability
---

# Kubernetes Cost Optimization

Cost analysis and optimization using kubectl-mcp-server's cost tools.

## When to Apply

Use this skill when:
- User mentions: "cost", "savings", "optimize", "expensive", "budget"
- Operations: cost analysis, right-sizing, cleanup unused resources
- Keywords: "how much", "reduce", "efficiency", "waste", "overprovisioned"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Find and delete unused PVCs | CRITICAL | `find_orphaned_pvcs` |
| 2 | Right-size overprovisioned pods | HIGH | `get_resource_recommendations` |
| 3 | Identify idle LoadBalancers | HIGH | `get_services` |
| 4 | Scale down non-prod off-hours | MEDIUM | `scale_deployment` |
| 5 | Consolidate small namespaces | LOW | Analysis |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Namespace cost | `get_namespace_cost` | `get_namespace_cost(namespace)` |
| Cluster cost | `get_cluster_cost` | `get_cluster_cost()` |
| Unused PVCs | `find_orphaned_pvcs` | `find_orphaned_pvcs(namespace)` |
| Right-sizing | `get_resource_recommendations` | `get_resource_recommendations(namespace)` |

## Quick Cost Analysis

### Get Cost Summary

```python
get_namespace_cost(namespace)
get_cluster_cost()
```

### Find Unused Resources

```python
find_unused_resources(namespace)
find_orphaned_pvcs(namespace)
```

### Resource Right-Sizing

```python
get_resource_recommendations(namespace)
get_pod_metrics(name, namespace)
```

## Cost Optimization Workflow

### 1. Identify Overprovisioned Resources

```python
get_resource_recommendations(namespace="production")

get_pod_metrics(name, namespace)
get_resource_usage(namespace)
```

### 2. Find Idle Resources

```python
find_orphaned_pvcs(namespace)

find_unused_resources(namespace)
```

### 3. Analyze Node Utilization

```python
get_nodes()
get_node_metrics()
```

## Right-Sizing Guidelines

| Current State | Recommendation |
|--------------|----------------|
| CPU usage < 10% of request | Reduce request by 50% |
| CPU usage > 80% of request | Increase request by 25% |
| Memory < 50% of request | Reduce request |
| Memory near limit | Increase limit, monitor OOM |

## Cost by Resource Type

### Compute (Pods/Deployments)

```python
get_resource_usage(namespace)
get_pod_metrics(name, namespace)
```

### Storage (PVCs)

```python
get_pvc(namespace)
find_orphaned_pvcs(namespace)
```

### Network (LoadBalancers)

```python
get_services(namespace)
```

## Multi-Cluster Cost Analysis

Compare costs across clusters:

```python
get_cluster_cost(context="production")
get_cluster_cost(context="staging")
get_cluster_cost(context="development")
```

## Cost Reduction Actions

### Immediate Wins

1. **Delete unused PVCs**: `find_orphaned_pvcs()` then delete
2. **Right-size pods**: Apply `get_resource_recommendations()`
3. **Scale down dev/staging**: Off-hours scaling

### Medium-term Optimizations

1. **Use Spot/Preemptible nodes**: For fault-tolerant workloads
2. **Implement HPA**: Auto-scale based on demand
3. **Use KEDA**: Scale to zero for event-driven workloads

### Long-term Strategy

1. **Reserved instances**: For stable production workloads
2. **Multi-tenant clusters**: Consolidate small clusters
3. **Right-size node pools**: Match workload requirements

## Automated Analysis Script

For comprehensive cost analysis, see [scripts/find-overprovisioned.py](scripts/find-overprovisioned.py).

## KEDA for Cost Savings

Scale to zero with KEDA:

```python
keda_scaledobjects_list_tool(namespace)
keda_scaledobject_get_tool(name, namespace)
```

KEDA reduces costs by:
- Scaling pods to 0 when idle
- Event-driven scaling (queue depth, etc.)
- Cron-based scaling for predictable patterns

## Related Skills

- [k8s-autoscaling](../k8s-autoscaling/SKILL.md) - HPA, VPA, KEDA
- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Resource debugging
