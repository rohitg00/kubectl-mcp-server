---
name: k8s-cost
description: Optimize Kubernetes costs through resource right-sizing, unused resource detection, and cluster efficiency analysis. Use for cost optimization, resource analysis, and capacity planning.
---

# Kubernetes Cost Optimization

Cost analysis and optimization using kubectl-mcp-server's cost tools.

## Quick Cost Analysis

### Get Cost Summary
```
get_namespace_cost(namespace)  # Namespace cost breakdown
get_cluster_cost()             # Cluster-wide cost summary
```

### Find Unused Resources
```
find_unused_resources(namespace)  # PVCs, ConfigMaps, Secrets
find_orphaned_pvcs(namespace)     # Unbound PVCs
```

### Resource Right-Sizing
```
get_resource_recommendations(namespace)  # CPU/memory suggestions
get_pod_metrics(name, namespace)         # Current usage
```

## Cost Optimization Workflow

### 1. Identify Overprovisioned Resources

```
# Get recommendations
get_resource_recommendations(namespace="production")

# Compare requests vs actual usage
get_pod_metrics(name, namespace)
get_resource_usage(namespace)
```

### 2. Find Idle Resources

```
# Unused PVCs (not mounted)
find_orphaned_pvcs(namespace)

# ConfigMaps/Secrets not referenced
find_unused_resources(namespace)
```

### 3. Analyze Node Utilization

```
get_nodes()
get_node_metrics()  # If metrics-server installed
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
```
get_resource_usage(namespace)
get_pod_metrics(name, namespace)
```

### Storage (PVCs)
```
get_pvc(namespace)
find_orphaned_pvcs(namespace)
```

### Network (LoadBalancers)
```
get_services(namespace)  # Filter type=LoadBalancer
# Each LB has fixed cloud cost
```

## Multi-Cluster Cost Analysis

Compare costs across clusters:
```
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
```
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
