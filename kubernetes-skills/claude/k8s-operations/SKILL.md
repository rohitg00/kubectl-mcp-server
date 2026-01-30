---
name: k8s-operations
description: kubectl operations for applying, patching, deleting, and executing commands on Kubernetes resources. Use when modifying resources, running commands in pods, or managing resource lifecycle.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 14
  category: operations
---

# kubectl Operations

Execute kubectl commands using kubectl-mcp-server's operations tools.

## When to Apply

Use this skill when:
- User mentions: "apply", "patch", "delete", "exec", "scale", "rollout"
- Operations: modifying resources, running commands, scaling workloads
- Keywords: "update", "change", "modify", "run command", "restart"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Dry run before apply in production | CRITICAL | `kubectl_apply(dry_run=True)` |
| 2 | Check current state before patching | HIGH | `describe_*` tools |
| 3 | Avoid force delete unless necessary | HIGH | `kubectl_delete` |
| 4 | Verify rollout status after changes | MEDIUM | `kubectl_rollout_status` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Apply manifest | `kubectl_apply` | `kubectl_apply(manifest=yaml)` |
| Patch resource | `kubectl_patch` | `kubectl_patch(type, name, namespace, patch)` |
| Delete resource | `kubectl_delete` | `kubectl_delete(type, name, namespace)` |
| Exec command | `kubectl_exec` | `kubectl_exec(pod, namespace, command)` |
| Scale deployment | `scale_deployment` | `scale_deployment(name, namespace, replicas)` |

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

kubectl_apply(file_path="/path/to/manifest.yaml")

kubectl_apply(manifest="...", dry_run=True)
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
kubectl_delete(resource_type="pod", name="my-pod", namespace="default")

kubectl_delete(
    resource_type="pods",
    namespace="default",
    label_selector="app=test"
)

kubectl_delete(
    resource_type="pod",
    name="stuck-pod",
    namespace="default",
    force=True,
    grace_period=0
)
```

## Execute Commands

```python
kubectl_exec(
    pod="my-pod",
    namespace="default",
    command="ls -la /app"
)

kubectl_exec(
    pod="my-pod",
    namespace="default",
    container="sidecar",
    command="cat /etc/config/settings.yaml"
)

kubectl_exec(
    pod="my-pod",
    namespace="default",
    command="sh -c 'curl -s localhost:8080/health'"
)
```

## Scale Resources

```python
scale_deployment(name="nginx", namespace="default", replicas=5)

scale_deployment(name="nginx", namespace="default", replicas=0)

kubectl_scale(
    resource_type="statefulset",
    name="mysql",
    namespace="default",
    replicas=3
)
```

## Rollout Management

```python
kubectl_rollout_status(
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

kubectl_rollout_history(
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

kubectl_rollout_restart(
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

rollback_deployment(name="nginx", namespace="default", revision=1)
```

## Labels and Annotations

```python
kubectl_label(
    resource_type="pod",
    name="my-pod",
    namespace="default",
    labels={"env": "production"}
)

kubectl_annotate(
    resource_type="deployment",
    name="nginx",
    namespace="default",
    annotations={"description": "Main web server"}
)
```

## Related Skills

- [k8s-deploy](../k8s-deploy/SKILL.md) - Deployment strategies
- [k8s-helm](../k8s-helm/SKILL.md) - Helm operations
