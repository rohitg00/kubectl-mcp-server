---
name: k8s-incident
description: Respond to Kubernetes incidents with runbooks and diagnostics. Use for outages, pod failures, node issues, network problems, and emergency response.
---

# Kubernetes Incident Response

Runbooks and diagnostic workflows for common Kubernetes incidents.

## Incident Triage

### Quick Health Check
```
1. get_nodes()                    # Node status
2. get_pods(namespace="kube-system")  # Control plane
3. get_events(namespace)          # Recent events
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
```
1. get_pod_logs(name, namespace, previous=True)
2. describe_pod(name, namespace)
3. get_events(namespace, field_selector="involvedObject.name=<pod>")
4. get_pod_metrics(name, namespace)
```

**Common Causes:**
- OOMKilled → Increase memory limits
- Exit code 1 → Application error in logs
- Exit code 137 → Killed by OOM or SIGKILL
- Exit code 143 → Graceful SIGTERM

### ImagePullBackOff
```
1. describe_pod(name, namespace)  # Check image name
2. get_secrets(namespace)         # Check imagePullSecrets
```

**Common Causes:**
- Wrong image name/tag
- Private registry, no imagePullSecret
- Registry rate limiting

### Pending Pod
```
1. describe_pod(name, namespace)
2. get_nodes()
3. get_events(namespace)
```

**Common Causes:**
- Insufficient resources
- Node selector mismatch
- Taints without tolerations
- PVC not bound

## Runbook: Node Issues

### Node NotReady
```
1. describe_node(name)
2. get_events(namespace="", field_selector="involvedObject.name=<node>")
3. node_logs_tool(name, "kubelet")
```

**Common Causes:**
- kubelet not running
- Network partition
- Disk pressure
- Memory pressure

### Node DiskPressure
```
1. describe_node(name)
2. get_pods(field_selector="spec.nodeName=<node>")
3. # Check large containers/logs
```

**Actions:**
- Clean up container logs
- Evict low-priority pods
- Expand node disk

## Runbook: Network Issues

### Service Not Accessible
```
1. get_services(namespace)
2. get_endpoints(namespace)        # Check backends
3. get_pods(namespace, label_selector="<service-selector>")
4. get_network_policies(namespace)
```

**Common Causes:**
- No matching pods (empty endpoints)
- Pods not ready
- NetworkPolicy blocking traffic

### DNS Resolution Failures
```
1. get_pods(namespace="kube-system", label_selector="k8s-app=kube-dns")
2. get_pod_logs("coredns-xxx", "kube-system")
```

### With Cilium
```
cilium_status_tool()
cilium_endpoints_list_tool(namespace)
hubble_flows_query_tool(namespace)
```

### With Istio
```
istio_analyze_tool(namespace)
istio_proxy_status_tool()
```

## Runbook: Storage Issues

### PVC Pending
```
1. describe_pvc(name, namespace)
2. get_storage_classes()
3. get_events(namespace)
```

**Common Causes:**
- No matching PV
- StorageClass not provisioning
- Quota exceeded

### Pod Stuck in ContainerCreating
```
1. describe_pod(name, namespace)
2. get_pvc(namespace)
3. get_events(namespace)
```

**Common Causes:**
- PVC not bound
- Volume mount error
- Image pull taking time

## Runbook: Control Plane Issues

### API Server Unavailable
```
1. get_pods(namespace="kube-system", label_selector="component=kube-apiserver")
2. get_events(namespace="kube-system")
```

### etcd Issues
```
1. get_pods(namespace="kube-system", label_selector="component=etcd")
2. get_pod_logs("etcd-xxx", "kube-system")
```

## Emergency Actions

### Cordon Node (Prevent Scheduling)
```
# Via kubectl (not in MCP tools yet)
# kubectl cordon <node>
```

### Drain Node (Evict Pods)
```
# Via kubectl
# kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
```

### Force Delete Pod
```
delete_pod(name, namespace, grace_period=0, force=True)
```

### Rollback Deployment
```
rollback_deployment(name, namespace, revision=0)  # Previous version
```

### Helm Rollback
```
rollback_helm_release(name, namespace, revision=1)
```

## Diagnostic Collection Script

For comprehensive incident diagnostics, see [scripts/collect-diagnostics.py](scripts/collect-diagnostics.py).

Collects:
- Pod logs and events
- Node conditions
- Resource usage
- Network policies
- Recent changes

## Multi-Cluster Incident Response

Check all clusters:
```
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
