---
name: k8s-operations
description: kubectl operations for applying, patching, deleting, and executing commands on Kubernetes resources. Use when modifying resources, running commands in pods, or managing resource lifecycle.
---

# kubectl Operations

Execute kubectl commands using kubectl-mcp-server's operations tools.

## Apply Resources

```python
# Apply YAML manifest
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

# Apply from file
kubectl_apply(file_path="/path/to/manifest.yaml")

# Dry run
kubectl_apply(manifest="...", dry_run=True)
```

## Patch Resources

```python
# Strategic merge patch
kubectl_patch(
    resource_type="deployment",
    name="nginx",
    namespace="default",
    patch={"spec": {"replicas": 5}}
)

# JSON patch
kubectl_patch(
    resource_type="deployment",
    name="nginx",
    namespace="default",
    patch=[{"op": "replace", "path": "/spec/replicas", "value": 5}],
    patch_type="json"
)

# Merge patch
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
# Delete single resource
kubectl_delete(resource_type="pod", name="my-pod", namespace="default")

# Delete with label selector
kubectl_delete(
    resource_type="pods",
    namespace="default",
    label_selector="app=test"
)

# Force delete
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
# Run command in pod
kubectl_exec(
    pod="my-pod",
    namespace="default",
    command="ls -la /app"
)

# Specific container
kubectl_exec(
    pod="my-pod",
    namespace="default",
    container="sidecar",
    command="cat /etc/config/settings.yaml"
)

# Interactive debugging
kubectl_exec(
    pod="my-pod",
    namespace="default",
    command="sh -c 'curl -s localhost:8080/health'"
)
```

## Scale Resources

```python
# Scale deployment
scale_deployment(name="nginx", namespace="default", replicas=5)

# Scale to zero
scale_deployment(name="nginx", namespace="default", replicas=0)

# Scale statefulset
kubectl_scale(
    resource_type="statefulset",
    name="mysql",
    namespace="default",
    replicas=3
)
```

## Rollout Management

```python
# Check rollout status
kubectl_rollout_status(
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

# Rollout history
kubectl_rollout_history(
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

# Restart deployment
kubectl_rollout_restart(
    resource_type="deployment",
    name="nginx",
    namespace="default"
)

# Rollback
rollback_deployment(name="nginx", namespace="default", revision=1)
```

## Labels and Annotations

```python
# Add label
kubectl_label(
    resource_type="pod",
    name="my-pod",
    namespace="default",
    labels={"env": "production"}
)

# Add annotation
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
