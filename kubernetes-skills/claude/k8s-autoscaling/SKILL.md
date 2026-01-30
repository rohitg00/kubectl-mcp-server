---
name: k8s-autoscaling
description: Configure Kubernetes autoscaling with HPA, VPA, and KEDA. Use for horizontal/vertical pod autoscaling, event-driven scaling, and capacity management.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 7
  category: scaling
---

# Kubernetes Autoscaling

Comprehensive autoscaling using HPA, VPA, and KEDA with kubectl-mcp-server tools.

## When to Apply

Use this skill when:
- User mentions: "HPA", "VPA", "KEDA", "autoscale", "scale to zero"
- Operations: configuring autoscaling, checking scaling status
- Keywords: "scale automatically", "event-driven", "right-size"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Verify metrics-server for HPA | CRITICAL | `get_resource_metrics` |
| 2 | Set resource requests before HPA | CRITICAL | `describe_pod` |
| 3 | Use KEDA for scale-to-zero | HIGH | `keda_scaledobjects_list_tool` |
| 4 | Check VPA recommendations | MEDIUM | `get_resource_recommendations` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List KEDA ScaledObjects | `keda_scaledobjects_list_tool` | `keda_scaledobjects_list_tool(namespace)` |
| Get ScaledObject | `keda_scaledobject_get_tool` | `keda_scaledobject_get_tool(name, namespace)` |
| List ScaledJobs | `keda_scaledjobs_list_tool` | `keda_scaledjobs_list_tool(namespace)` |
| Check KEDA | `keda_detect_tool` | `keda_detect_tool()` |

## HPA (Horizontal Pod Autoscaler)

Basic CPU-based scaling:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Apply and verify:

```python
kubectl_apply(hpa_yaml, namespace)
get_hpa(namespace)
```

## VPA (Vertical Pod Autoscaler)

Right-size resource requests:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: "Auto"
```

## KEDA (Event-Driven Autoscaling)

### Detect KEDA Installation

```python
keda_detect_tool()
```

### List ScaledObjects

```python
keda_scaledobjects_list_tool(namespace)
keda_scaledobject_get_tool(name, namespace)
```

### List ScaledJobs

```python
keda_scaledjobs_list_tool(namespace)
```

### Trigger Authentication

```python
keda_triggerauths_list_tool(namespace)
keda_triggerauth_get_tool(name, namespace)
```

### KEDA-Managed HPAs

```python
keda_hpa_list_tool(namespace)
```

See [KEDA-TRIGGERS.md](KEDA-TRIGGERS.md) for trigger configurations.

## Common KEDA Triggers

### Queue-Based Scaling (AWS SQS)

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: sqs-scaler
spec:
  scaleTargetRef:
    name: queue-processor
  minReplicaCount: 0
  maxReplicaCount: 100
  triggers:
  - type: aws-sqs-queue
    metadata:
      queueURL: https://sqs.region.amazonaws.com/...
      queueLength: "5"
```

### Cron-Based Scaling

```yaml
triggers:
- type: cron
  metadata:
    timezone: America/New_York
    start: 0 8 * * 1-5
    end: 0 18 * * 1-5
    desiredReplicas: "10"
```

### Prometheus Metrics

```yaml
triggers:
- type: prometheus
  metadata:
    serverAddress: http://prometheus:9090
    metricName: http_requests_total
    query: sum(rate(http_requests_total{app="myapp"}[2m]))
    threshold: "100"
```

## Scaling Strategies

| Strategy | Tool | Use Case |
|----------|------|----------|
| CPU/Memory | HPA | Steady traffic patterns |
| Custom metrics | HPA v2 | Business metrics |
| Event-driven | KEDA | Queue processing, cron |
| Vertical | VPA | Right-size requests |
| Scale to zero | KEDA | Cost savings, idle workloads |

## Cost-Optimized Autoscaling

### Scale to Zero with KEDA

Reduce costs for idle workloads:

```python
keda_scaledobjects_list_tool(namespace)
```

### Right-Size with VPA

Get recommendations and apply:

```python
get_resource_recommendations(namespace)
```

## Troubleshooting

### HPA Not Scaling

```python
get_hpa(namespace)
get_pod_metrics(name, namespace)
describe_pod(name, namespace)
```

### KEDA Not Triggering

```python
keda_scaledobject_get_tool(name, namespace)
get_events(namespace)
```

### Common Issues

| Symptom | Check | Resolution |
|---------|-------|------------|
| HPA unknown | Metrics server | Install metrics-server |
| KEDA no scale | Trigger auth | Check TriggerAuthentication |
| VPA not updating | Update mode | Set updateMode: Auto |
| Scale down slow | Stabilization | Adjust stabilizationWindowSeconds |

## Best Practices

1. **Always Set Resource Requests** - HPA requires requests to calculate utilization
2. **Use Multiple Metrics** - Combine CPU + custom metrics for accuracy
3. **Stabilization Windows** - Prevent flapping with scaleDown stabilization
4. **Scale to Zero Carefully** - Consider cold start time

## Related Skills

- [k8s-cost](../k8s-cost/SKILL.md) - Cost optimization
- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Debug scaling issues
