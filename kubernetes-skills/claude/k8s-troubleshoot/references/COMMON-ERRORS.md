# Common Kubernetes Error Messages

Quick reference for error messages and their solutions.

## Pod Errors

### CrashLoopBackOff

**Meaning:** Container keeps crashing and restarting.

**Causes:**
- Application crash on startup
- Missing configuration or secrets
- Resource exhaustion (OOM)
- Failing health checks

**Fix:**
```python
get_pod_logs(name, namespace, previous=True)
describe_pod(name, namespace)
```

### ImagePullBackOff / ErrImagePull

**Meaning:** Cannot pull container image.

**Causes:**
- Image doesn't exist
- Private registry without credentials
- Network issues
- Rate limiting (Docker Hub)

**Fix:**
```python
describe_pod(name, namespace)
```

### OOMKilled (Exit Code 137)

**Meaning:** Container exceeded memory limit.

**Causes:**
- Memory limit too low
- Memory leak in application
- Large data processing

**Fix:**
```python
get_pod_metrics(name, namespace)
```

### Exit Code 1

**Meaning:** Application error.

**Fix:** Check application logs for stack trace.

### Exit Code 127

**Meaning:** Command not found.

**Fix:** Check container image has required binaries.

### Exit Code 128+N

**Meaning:** Container killed by signal N.

| Exit Code | Signal | Meaning |
|-----------|--------|---------|
| 130 | SIGINT (2) | Interrupt |
| 137 | SIGKILL (9) | Killed (OOM) |
| 143 | SIGTERM (15) | Terminated |

## Scheduling Errors

### 0/N nodes are available

**Causes:**
- Insufficient resources
- Node selector/affinity not matching
- Taints without tolerations
- All nodes cordoned

**Fix:**
```python
describe_pod(name, namespace)
get_nodes()
```

### PodExceedsFreeCPU / PodExceedsFreeMemory

**Fix:** Reduce resource requests or add capacity.

### NodeNotReady

**Fix:**
```python
describe_node(name)
```

## Storage Errors

### PersistentVolumeClaim not found

**Fix:** Create the PVC before the pod.

### Unable to attach or mount volumes

**Causes:**
- PV already attached elsewhere
- Storage class misconfigured
- Node has no access to storage

**Fix:**
```python
describe_pvc(name, namespace)
get_storage_classes()
```

## Network Errors

### Connection refused

**Causes:**
- Service not exposed on expected port
- Application not listening
- Firewall/NetworkPolicy blocking

**Fix:**
```python
get_endpoints(namespace)
get_network_policies(namespace)
```

### No route to host

**Causes:**
- Node network issues
- CNI problems

**Fix:** Check CNI pods in kube-system.

### DNS resolution failed

**Fix:**
```python
get_pods(namespace="kube-system", label_selector="k8s-app=kube-dns")
```

## RBAC Errors

### Forbidden: User cannot...

**Causes:**
- Missing Role/ClusterRole
- Missing RoleBinding/ClusterRoleBinding
- ServiceAccount not assigned

**Fix:**
```python
get_cluster_roles()
get_role_bindings(namespace)
```

## Admission Controller Errors

### Admission webhook denied

**Causes:**
- Policy violation (Kyverno/Gatekeeper)
- Webhook unavailable

**Fix:**
```python
kyverno_clusterpolicies_list_tool()
gatekeeper_constraints_list_tool()
```

## Resource Limit Errors

### Forbidden: exceeded quota

**Fix:**
```python
get_resource_quotas(namespace)
```

### LimitRange rejection

**Fix:** Adjust resource requests/limits to match LimitRange.

## Probe Failures

### Liveness probe failed

**Meaning:** Container will be restarted.

### Readiness probe failed

**Meaning:** Pod removed from service endpoints.

**Common causes:**
- Wrong port in probe config
- Application slow to start
- Dependencies unavailable

**Fix:**
```python
describe_pod(name, namespace)
get_pod_logs(name, namespace)
```

## Quick Lookup

| Error | First Tool |
|-------|------------|
| CrashLoopBackOff | `get_pod_logs(previous=True)` |
| ImagePullBackOff | `describe_pod` |
| Pending (scheduling) | `describe_pod`, `get_events` |
| PVC Pending | `describe_pvc` |
| Connection refused | `get_endpoints` |
| RBAC Forbidden | `get_role_bindings` |
