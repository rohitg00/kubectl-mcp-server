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
| 1 | Check control plane first | CRITICAL | `get_pods(namespace="kube-system")` |
| 2 | Assess node health | CRITICAL | `get_nodes` |
| 3 | Gather events before changes | HIGH | `get_events` |
| 4 | Document timeline | HIGH | Manual notes |
| 5 | Rollback if safe | MEDIUM | `kubectl_rollout` |

## Quick Reference

| Incident | First Tool | Next Steps |
|----------|------------|------------|
| Pod failure | `get_logs(previous=True)` | `kubectl_describe`, `get_events` |
| Node down | `kubectl_describe` | Check kubelet logs |
| Service unreachable | `get_endpoints` | `analyze_network_policies` |
| Control plane | `get_pods(namespace="kube-system")` | Check API server logs |

## Incident Triage

### Quick Health Check

```python
get_nodes()
get_pods(namespace="kube-system")
get_events(namespace)
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
get_logs(name, namespace, previous=True)
kubectl_describe(name, namespace)
get_events(namespace, field_selector="involvedObject.name=<pod>")
get_pod_metrics(name, namespace)
```

**Common Causes:**
- OOMKilled → Increase memory limits
- Exit code 1 → Application error in logs
- Exit code 137 → Killed by OOM or SIGKILL
- Exit code 143 → Graceful SIGTERM

### ImagePullBackOff

```python
kubectl_describe(name, namespace)
get_secrets(namespace)
```

### Pending Pod

```python
kubectl_describe(name, namespace)
get_nodes()
get_events(namespace)
```

## Runbook: Node Issues

### Node NotReady

```python
kubectl_describe(name)
get_events(namespace="", field_selector="involvedObject.name=<node>")
node_logs(name, "kubelet")
```

### Node DiskPressure

```python
kubectl_describe(name)
get_pods(field_selector="spec.nodeName=<node>")
```

## Runbook: Network Issues

### Service Not Accessible

```python
get_services(namespace)
get_endpoints(namespace)
get_pods(namespace, label_selector="<service-selector>")
analyze_network_policies(namespace)
```

### DNS Resolution Failures

```python
get_pods(namespace="kube-system", label_selector="k8s-app=kube-dns")
get_logs("coredns-xxx", "kube-system")
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
get_storage_classes()
get_events(namespace)
```

### Pod Stuck in ContainerCreating

```python
kubectl_describe(name, namespace)
get_pvcs(namespace)
get_events(namespace)
```

## Runbook: Control Plane Issues

### API Server Unavailable

```python
get_pods(namespace="kube-system", label_selector="component=kube-apiserver")
get_events(namespace="kube-system")
```

### etcd Issues

```python
get_pods(namespace="kube-system", label_selector="component=etcd")
get_logs("etcd-xxx", "kube-system")
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
    get_nodes(context=context)
    get_pods(namespace="kube-system", context=context)
    get_events(namespace="kube-system", context=context)
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
