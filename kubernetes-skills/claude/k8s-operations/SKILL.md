---
name: k8s-operations
description: kubectl operations for applying, patching, deleting, and executing commands on Kubernetes resources. Use when modifying resources, running commands in pods, or managing resource lifecycle.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 10
  category: operations
---

# kubectl Operations

Execute kubectl commands using kubectl-mcp-server's operations tools.

> Requires the `ops` toolset: start kubectl-mcp-server with `--toolsets default,ops` (or `MCP_TOOLSETS=default,ops`).

## When to Apply

Use this skill when:
- User mentions: "apply", "patch", "delete", "exec", "scale", "rollout"
- Operations: modifying resources, running commands, scaling workloads
- Keywords: "update", "change", "modify", "run command", "restart"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Compare with live state before apply in production | CRITICAL | `kubectl_get(resource_type, name, output="yaml")` |
| 2 | Check current state before patching | HIGH | `kubectl_describe` |
| 3 | Avoid force delete unless necessary | HIGH | `delete_resource` |
| 4 | Verify rollout status after changes | MEDIUM | `kubectl_rollout` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Apply manifest | `kubectl_apply` | `kubectl_apply(manifest=yaml)` |
| Patch resource | `kubectl_patch` | `kubectl_patch(type, name, namespace, patch)` |
| Delete resource | `delete_resource` | `delete_resource(type, name, namespace)` |
| Exec command | `exec_in_pod` | `exec_in_pod(pod, namespace, command)` |
| Scale deployment | `kubectl_scale` | `kubectl_scale(resource_type="deployment", name, namespace, replicas)` |

## Apply Resources

```python
kubectl_apply(manifest="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
""")

```

## Patch Resources

```python
kubectl_patch(
    resource_type="deployment",
    name="nginx",
    namespace="default",
    patch={"spec": {"replicas": 5}}
)

kubectl_patch(
    resource_type="deployment",
    name="nginx",
    namespace="default",
    patch=[{"op": "replace", "path": "/spec/replicas", "value": 5}],
    patch_type="json"
)

kubectl_patch(
    resource_type="service",
    name="my-svc",
    namespace="default",
    patch={"metadata": {"annotations": {"key": "value"}}},
    patch_type="merge"
)
```

## Delete Resources

```python
delete_resource(resource_type="pod", name="my-pod", namespace="default")

delete_resource(resource_type="deployment", name="old-app", namespace="default")
```

## Execute Commands

```python
exec_in_pod(
    pod_name="my-pod",
    namespace="default",
    command="ls -la /app"
)

exec_in_pod(
    pod_name="my-pod",
    namespace="default",
    container="sidecar",
    command="cat /etc/config/settings.yaml"
)

exec_in_pod(
    pod_name="my-pod",
    namespace="default",
    command="sh -c 'curl -s localhost:8080/health'"
)
```

## Scale Resources

```python
kubectl_scale(resource_type="deployment", name="nginx", namespace="default", replicas=5)

kubectl_scale(resource_type="deployment", name="nginx", namespace="default", replicas=0)

kubectl_scale(
    resource_type="statefulset",
    name="mysql",
    namespace="default",
    replicas=3
)
```

## Rollout Management

```python
kubectl_rollout(action="status",
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

kubectl_rollout(action="history",
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

kubectl_rollout(action="restart",
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

kubectl_rollout(action="undo", resource_type="deployment", name="nginx", namespace="default")
```

## Labels and Annotations

```python
label_resource(
    resource_type="pod",
    name="my-pod",
    namespace="default",
    labels={"env": "production"}
)

annotate_resource(
    resource_type="deployment",
    name="nginx",
    namespace="default",
    annotations={"description": "Main web server"}
)
```

## Related Skills

- [k8s-deploy](../k8s-deploy/SKILL.md) - Deployment strategies
- [k8s-helm](../k8s-helm/SKILL.md) - Helm operations
