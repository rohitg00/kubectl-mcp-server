---
name: k8s-troubleshoot
description: Debug Kubernetes pods, nodes, and workloads. Use when pods are failing, containers crash, nodes are unhealthy, or users mention debugging, troubleshooting, or diagnosing Kubernetes issues.
---

# Kubernetes Troubleshooting

Expert debugging and diagnostics for Kubernetes clusters using kubectl-mcp-server tools.

## Quick Diagnostics

### Pod Not Starting
1. Get pod status: `get_pods(namespace, label_selector)`
2. Describe pod: `describe_pod(name, namespace)`
3. Check events: `get_events(namespace, field_selector="involvedObject.name=<pod>")`
4. View logs: `get_pod_logs(name, namespace, previous=True)` for crash loops

### Common Pod States

| State | Likely Cause | Tools to Use |
|-------|-------------|--------------|
| Pending | Scheduling issues | `describe_pod`, `get_nodes`, `get_events` |
| ImagePullBackOff | Registry/auth | `describe_pod`, check image name |
| CrashLoopBackOff | App crash | `get_pod_logs(previous=True)` |
| OOMKilled | Memory limit | `get_pod_metrics`, adjust limits |
| ContainerCreating | Volume/network | `describe_pod`, `get_pvc` |

### Node Issues
1. List nodes: `get_nodes()`
2. Node details: `describe_node(name)`
3. Node conditions: Check Ready, MemoryPressure, DiskPressure
4. Node logs: `node_logs_tool(name, "kubelet")`

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

## Multi-Cluster Debugging

All tools support `context` parameter for targeting different clusters:
```
get_pods(namespace="kube-system", context="production-cluster")
get_events(namespace="default", context="staging-cluster")
```

## Diagnostic Scripts

For comprehensive diagnostics, run the bundled script:
- See [scripts/diagnose-pod.py](scripts/diagnose-pod.py) for automated pod analysis

## Related Tools

### Core Diagnostics
- `get_pods`, `describe_pod`, `get_pod_logs`, `get_pod_metrics`
- `get_events`, `get_nodes`, `describe_node`
- `get_resource_usage`, `compare_namespaces`

### Advanced (Ecosystem)
- Cilium: `cilium_endpoints_list_tool`, `hubble_flows_query_tool`
- Istio: `istio_proxy_status_tool`, `istio_analyze_tool`
