---
name: k8s-core
description: Core Kubernetes resource management for pods, namespaces, configmaps, secrets, and nodes. Use when listing, inspecting, or managing fundamental K8s objects.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 17
  category: core
---

# Core Kubernetes Resources

Manage fundamental Kubernetes objects using kubectl-mcp-server's core tools.

## When to Apply

Use this skill when:
- User mentions: "pods", "namespaces", "configmaps", "secrets", "nodes", "events"
- Operations: listing resources, describing objects, creating/deleting resources
- Keywords: "show me", "list", "get", "describe", "create", "delete"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check namespace exists before operations | CRITICAL | `kubectl_get` |
| 2 | Never expose secrets in plain text | CRITICAL | Handle `kubectl_get` output carefully |
| 3 | Use labels for filtering | HIGH | `label_selector` parameter |
| 4 | Check events after changes | MEDIUM | `kubectl_get` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List pods | `kubectl_get` | `kubectl_get(resource_type="pods", namespace="default")` |
| Describe pod | `kubectl_describe` | `kubectl_describe(name, namespace)` |
| Get logs | `kubectl_logs` | `kubectl_logs(name, namespace)` |
| List namespaces | `kubectl_get` | `kubectl_get(resource_type="namespaces")` |
| Get configmap | `kubectl_get` | `kubectl_get(resource_type="configmaps", name, namespace)` |
| List nodes | `kubectl_get` | `kubectl_get(resource_type="nodes")` |

## Pods

```python
kubectl_get(resource_type="pods", namespace="default")
kubectl_get(resource_type="pods", namespace="kube-system", label_selector="app=nginx")

kubectl_describe(name="my-pod", namespace="default")

kubectl_logs(name="my-pod", namespace="default")
kubectl_logs(name="my-pod", namespace="default", previous=True)

delete_pod(name="my-pod", namespace="default")
```

## Namespaces

```python
kubectl_get(resource_type="namespaces")

create_namespace(name="my-namespace")

delete_namespace(name="my-namespace")
```

## ConfigMaps

```python
kubectl_get(resource_type="configmaps", namespace="default")

kubectl_get(resource_type="configmaps", name="my-config", namespace="default")

create_configmap(
    name="app-config",
    namespace="default",
    data={"key": "value", "config.yaml": "setting: true"}
)
```

## Secrets

```python
kubectl_get(resource_type="secrets", namespace="default")

kubectl_get(resource_type="secrets", name="my-secret", namespace="default")

create_secret(
    name="db-credentials",
    namespace="default",
    data={"username": "admin", "password": "secret123"}
)
```

## Nodes

```python
kubectl_get(resource_type="nodes")

kubectl_describe(name="node-1")

get_nodes_summary()

cordon_node(name="node-1")
uncordon_node(name="node-1")

drain_node(name="node-1", ignore_daemonsets=True)
```

## Events

```python
kubectl_get(resource_type="events", namespace="default")

kubectl_get(resource_type="events", namespace="default", field_selector="involvedObject.name=my-pod")
```

## Multi-Cluster Support

All tools support `context` parameter:

```python
kubectl_get(resource_type="pods", namespace="default", context="production-cluster")
kubectl_get(resource_type="nodes", context="staging-cluster")
```

## Related Skills

- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Debug failing pods
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl apply/patch/delete
