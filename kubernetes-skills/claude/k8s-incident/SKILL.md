---
name: k8s-incident
description: Respond to Kubernetes incidents with runbooks and diagnostics. Use for outages, pod failures, node issues, network problems, and emergency response.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 15
  category: observability
---

# Kubernetes Incident Response

Runbooks and diagnostic workflows for common Kubernetes incidents.

## When to Apply

Use this skill when:
- User mentions: "incident", "outage", "emergency", "down", "not working"
- Operations: emergency response, production issues, service degradation
- Keywords: "urgent", "broken", "fix", "restore", "recover"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check control plane first | CRITICAL | `kubectl_get(resource_type="pods", namespace="kube-system")` |
| 2 | Assess node health | CRITICAL | `kubectl_get` |
| 3 | Gather events before changes | HIGH | `kubectl_get` |
| 4 | Document timeline | HIGH | Manual notes |
| 5 | Rollback if safe | MEDIUM | `kubectl_rollout` |

## Quick Reference

| Incident | First Tool | Next Steps |
|----------|------------|------------|
| Pod failure | `kubectl_logs(previous=True)` | `kubectl_describe`, `kubectl_get` |
| Node down | `kubectl_describe` | Check kubelet logs |
| Service unreachable | `kubectl_get` | `analyze_network_policies` |
| Control plane | `kubectl_get(resource_type="pods", namespace="kube-system")` | Check API server logs |

## Incident Triage

### Quick Health Check

```python
kubectl_get(resource_type="nodes")
kubectl_get(resource_type="pods", namespace="kube-system")
kubectl_get(resource_type="events", namespace)
```

### Severity Assessment

| Indicator | Severity | Action |
|-----------|----------|--------|
| Multiple nodes NotReady | Critical | Escalate immediately |
| kube-system pods failing | Critical | Control plane issue |
| Single pod CrashLoop | Medium | Debug pod |
| High latency | Medium | Check resources |

## Runbook: Pod Failures

### CrashLoopBackOff

```python
kubectl_logs(name, namespace, previous=True)
kubectl_describe(name, namespace)
kubectl_get(resource_type="events", namespace, field_selector="involvedObject.name=<pod>")
kubectl_top(name, namespace)
```

**Common Causes:**
- OOMKilled → Increase memory limits
- Exit code 1 → Application error in logs
- Exit code 137 → Killed by OOM or SIGKILL
- Exit code 143 → Graceful SIGTERM

### ImagePullBackOff

```python
kubectl_describe(name, namespace)
kubectl_get(resource_type="secrets", namespace)
```

### Pending Pod

```python
kubectl_describe(name, namespace)
kubectl_get(resource_type="nodes")
kubectl_get(resource_type="events", namespace)
```

## Runbook: Node Issues

### Node NotReady

```python
kubectl_describe(name)
kubectl_get(resource_type="events", namespace="", field_selector="involvedObject.name=<node>")
node_logs(name, "kubelet")
```

### Node DiskPressure

```python
kubectl_describe(name)
kubectl_get(resource_type="pods", field_selector="spec.nodeName=<node>")
```

## Runbook: Network Issues

### Service Not Accessible

```python
kubectl_get(resource_type="services", namespace)
kubectl_get(resource_type="endpoints", namespace)
kubectl_get(resource_type="pods", namespace, label_selector="<service-selector>")
analyze_network_policies(namespace)
```

### DNS Resolution Failures

```python
kubectl_get(resource_type="pods", namespace="kube-system", label_selector="k8s-app=kube-dns")
kubectl_logs("coredns-xxx", "kube-system")
```

### With Cilium

```python
cilium_get_status()
cilium_list_endpoints(namespace)
get_hubble_flows(namespace)
```

### With Istio

```python
istio_analyze(namespace)
istio_proxy_status()
```

## Runbook: Storage Issues

### PVC Pending

```python
kubectl_describe(name, namespace)
kubectl_get(resource_type="storageclasses")
kubectl_get(resource_type="events", namespace)
```

### Pod Stuck in ContainerCreating

```python
kubectl_describe(name, namespace)
kubectl_get(resource_type="pvc", namespace)
kubectl_get(resource_type="events", namespace)
```

## Runbook: Control Plane Issues

### API Server Unavailable

```python
kubectl_get(resource_type="pods", namespace="kube-system", label_selector="component=kube-apiserver")
kubectl_get(resource_type="events", namespace="kube-system")
```

### etcd Issues

```python
kubectl_get(resource_type="pods", namespace="kube-system", label_selector="component=etcd")
kubectl_logs("etcd-xxx", "kube-system")
```

## Emergency Actions

### Force Delete Pod

```python
delete_pod(name, namespace, grace_period=0, force=True)
```

### Rollback Deployment

```python
kubectl_rollout(name, namespace, revision=0)
```

### Helm Rollback

```python
helm_rollback(name, namespace, revision=1)
```

## Diagnostic Collection Script

For comprehensive incident diagnostics, see [scripts/collect-diagnostics.py](scripts/collect-diagnostics.py).

## Multi-Cluster Incident Response

Check all clusters:

```python
for context in ["prod-1", "prod-2", "staging"]:
    kubectl_get(resource_type="nodes", context=context)
    kubectl_get(resource_type="pods", namespace="kube-system", context=context)
    kubectl_get(resource_type="events", namespace="kube-system", context=context)
```

## Post-Incident

### Document Timeline

1. When did the incident start?
2. What was the impact?
3. What was the root cause?
4. What fixed it?

### Prevent Recurrence

- Add monitoring/alerting
- Improve resource limits
- Add readiness probes
- Document runbook

## Related Skills

- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Detailed debugging
- [k8s-security](../k8s-security/SKILL.md) - Security incidents
