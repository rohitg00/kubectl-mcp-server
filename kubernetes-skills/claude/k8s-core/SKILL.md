---
name: k8s-core
description: Core Kubernetes resource management for pods, namespaces, configmaps, secrets, and nodes. Use when listing, inspecting, or managing fundamental K8s objects.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 8
  category: core
---

# Core Kubernetes Resources

Manage fundamental Kubernetes objects using kubectl-mcp-server's core tools.

> Requires the `diagnostics`, `ops` toolsets: start kubectl-mcp-server with `--toolsets default,diagnostics,ops` (or `MCP_TOOLSETS=default,diagnostics,ops`).

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

kubectl_describe(resource_type="pod", name="my-pod", namespace="default")

kubectl_logs(pod_name="my-pod", namespace="default")
kubectl_logs(pod_name="my-pod", namespace="default", previous=True)

delete_resource(resource_type="pod", name="my-pod", namespace="default")
```

## Namespaces

```python
kubectl_get(resource_type="namespaces")

kubectl_create(resource_type="namespace", name="my-namespace")

delete_resource(resource_type="namespace", name="my-namespace")
```

## ConfigMaps

```python
kubectl_get(resource_type="configmaps", namespace="default")

kubectl_get(resource_type="configmaps", name="my-config", namespace="default")

kubectl_apply(manifest="""
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  key: value
  config.yaml: "setting: true"
""")
```

## Secrets

```python
kubectl_get(resource_type="secrets", namespace="default")

kubectl_get(resource_type="secrets", name="my-secret", namespace="default")

kubectl_apply(manifest="""
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: default
stringData:
  username: <username>
  password: <password>
""")
```

## Nodes

```python
kubectl_get(resource_type="nodes")

kubectl_describe(resource_type="node", name="node-1")

get_nodes_summary()

node_management(action="cordon", node_name="node-1")
node_management(action="uncordon", node_name="node-1")

node_management(action="drain", node_name="node-1")
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
