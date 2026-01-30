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
| 1 | Check namespace exists before operations | CRITICAL | `get_namespaces` |
| 2 | Never expose secrets in plain text | CRITICAL | Handle `get_secret` output carefully |
| 3 | Use labels for filtering | HIGH | `label_selector` parameter |
| 4 | Check events after changes | MEDIUM | `get_events` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List pods | `get_pods` | `get_pods(namespace="default")` |
| Describe pod | `describe_pod` | `describe_pod(name, namespace)` |
| Get logs | `get_pod_logs` | `get_pod_logs(name, namespace)` |
| List namespaces | `get_namespaces` | `get_namespaces()` |
| Get configmap | `get_configmap` | `get_configmap(name, namespace)` |
| List nodes | `get_nodes` | `get_nodes()` |

## Pods

```python
get_pods(namespace="default")
get_pods(namespace="kube-system", label_selector="app=nginx")

describe_pod(name="my-pod", namespace="default")

get_pod_logs(name="my-pod", namespace="default")
get_pod_logs(name="my-pod", namespace="default", previous=True)

delete_pod(name="my-pod", namespace="default")
```

## Namespaces

```python
get_namespaces()

create_namespace(name="my-namespace")

delete_namespace(name="my-namespace")
```

## ConfigMaps

```python
get_configmaps(namespace="default")

get_configmap(name="my-config", namespace="default")

create_configmap(
    name="app-config",
    namespace="default",
    data={"key": "value", "config.yaml": "setting: true"}
)
```

## Secrets

```python
get_secrets(namespace="default")

get_secret(name="my-secret", namespace="default")

create_secret(
    name="db-credentials",
    namespace="default",
    data={"username": "admin", "password": "secret123"}
)
```

## Nodes

```python
get_nodes()

describe_node(name="node-1")

get_nodes_summary()

cordon_node(name="node-1")
uncordon_node(name="node-1")

drain_node(name="node-1", ignore_daemonsets=True)
```

## Events

```python
get_events(namespace="default")

get_events(namespace="default", field_selector="involvedObject.name=my-pod")
```

## Multi-Cluster Support

All tools support `context` parameter:

```python
get_pods(namespace="default", context="production-cluster")
get_nodes(context="staging-cluster")
```

## Related Skills

- [k8s-troubleshoot](../k8s-troubleshoot/SKILL.md) - Debug failing pods
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl apply/patch/delete
