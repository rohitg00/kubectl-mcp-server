---
name: k8s-troubleshoot
description: Debug Kubernetes pods, nodes, and workloads. Use when pods are failing, containers crash, nodes are unhealthy, or users mention debugging, troubleshooting, or diagnosing Kubernetes issues.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 15
  category: observability
---

# Kubernetes Troubleshooting

Expert debugging and diagnostics for Kubernetes clusters using kubectl-mcp-server tools.

## When to Apply

Use this skill when:
- User mentions: "debug", "troubleshoot", "diagnose", "failing", "crash", "not starting", "broken"
- Pod states: Pending, CrashLoopBackOff, ImagePullBackOff, OOMKilled, Error, Unknown
- Node issues: NotReady, MemoryPressure, DiskPressure, NetworkUnavailable, PIDPressure
- Keywords: "logs", "events", "describe", "why isn't working", "stuck", "not responding"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check pod status first | CRITICAL | `get_pods`, `describe_pod` |
| 2 | View recent events | CRITICAL | `get_events` |
| 3 | Inspect logs (including previous) | HIGH | `get_pod_logs` |
| 4 | Check resource metrics | HIGH | `get_pod_metrics` |
| 5 | Verify endpoints | MEDIUM | `get_endpoints` |
| 6 | Review network policies | MEDIUM | `get_network_policies` |
| 7 | Examine node status | LOW | `get_nodes`, `describe_node` |

## Quick Reference

| Symptom | First Tool | Next Steps |
|---------|------------|------------|
| Pod Pending | `describe_pod` | Check events, node capacity, resource requests |
| CrashLoopBackOff | `get_pod_logs(previous=True)` | Check exit code, resources, liveness probes |
| ImagePullBackOff | `describe_pod` | Verify image name, registry auth, network |
| OOMKilled | `get_pod_metrics` | Increase memory limits, check for memory leaks |
| ContainerCreating | `describe_pod` | Check PVC binding, secrets, configmaps |
| Terminating (stuck) | `describe_pod` | Check finalizers, PDBs, preStop hooks |

## Diagnostic Workflows

### Pod Not Starting

```
1. get_pods(namespace, label_selector) - Get pod status
2. describe_pod(name, namespace) - See events and conditions
3. get_events(namespace, field_selector="involvedObject.name=<pod>") - Check events
4. get_pod_logs(name, namespace, previous=True) - For crash loops
```

### Common Pod States

| State | Likely Cause | Tools to Use |
|-------|-------------|--------------|
| Pending | Scheduling issues | `describe_pod`, `get_nodes`, `get_events` |
| ImagePullBackOff | Registry/auth | `describe_pod`, check image name |
| CrashLoopBackOff | App crash | `get_pod_logs(previous=True)` |
| OOMKilled | Memory limit | `get_pod_metrics`, adjust limits |
| ContainerCreating | Volume/network | `describe_pod`, `get_pvc` |

### Node Issues

```
1. get_nodes() - List nodes and status
2. describe_node(name) - See conditions and capacity
3. Check: Ready, MemoryPressure, DiskPressure, PIDPressure
4. node_logs_tool(name, "kubelet") - Kubelet logs
```

## Deep Debugging Workflows

### CrashLoopBackOff Investigation

```
1. get_pod_logs(name, namespace, previous=True) - See why it crashed
2. describe_pod(name, namespace) - Check resource limits, probes
3. get_pod_metrics(name, namespace) - Memory/CPU at crash time
4. If OOM: compare requests/limits to actual usage
5. If app error: check logs for stack trace
```

### Networking Issues

```
1. get_services(namespace) - Verify service exists
2. get_endpoints(namespace) - Check endpoint backends
3. If empty endpoints: pods don't match selector
4. get_network_policies(namespace) - Check traffic rules
5. For Cilium: cilium_endpoints_list_tool(), hubble_flows_query_tool()
```

### Storage Problems

```
1. get_pvc(namespace) - Check PVC status
2. describe_pvc(name, namespace) - See binding issues
3. get_storage_classes() - Verify provisioner exists
4. If Pending: check storage class, access modes
```

### DNS Resolution

```
1. kubectl_exec(pod, namespace, "nslookup kubernetes.default") - Test DNS
2. If fails: check coredns pods in kube-system
3. get_pods(namespace="kube-system", label_selector="k8s-app=kube-dns")
4. get_pod_logs(name="coredns-*", namespace="kube-system")
```

## Multi-Cluster Debugging

All tools support `context` parameter for targeting different clusters:

```python
get_pods(namespace="kube-system", context="production-cluster")
get_events(namespace="default", context="staging-cluster")
describe_pod(name="myapp-xyz", namespace="prod", context="prod-east")
```

## Diagnostic Scripts

For comprehensive diagnostics, run the bundled scripts:
- See [scripts/diagnose-pod.py](scripts/diagnose-pod.py) for automated pod analysis
- See [scripts/health-check.sh](scripts/health-check.sh) for cluster health checks

## Decision Tree

See [references/DECISION-TREE.md](references/DECISION-TREE.md) for visual troubleshooting flowcharts.

## Common Errors Reference

See [references/COMMON-ERRORS.md](references/COMMON-ERRORS.md) for error message explanations and fixes.

## Related Tools

### Core Diagnostics
- `get_pods`, `describe_pod`, `get_pod_logs`, `get_pod_metrics`
- `get_events`, `get_nodes`, `describe_node`
- `get_resource_usage`, `compare_namespaces`

### Advanced (Ecosystem)
- Cilium: `cilium_endpoints_list_tool`, `hubble_flows_query_tool`
- Istio: `istio_proxy_status_tool`, `istio_analyze_tool`

## Related Skills

- [k8s-diagnostics](../k8s-diagnostics/SKILL.md) - Metrics and health checks
- [k8s-incident](../k8s-incident/SKILL.md) - Emergency runbooks
- [k8s-networking](../k8s-networking/SKILL.md) - Network troubleshooting
