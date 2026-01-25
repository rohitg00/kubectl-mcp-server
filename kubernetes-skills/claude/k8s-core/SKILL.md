---
name: k8s-core
description: Core Kubernetes resource management for pods, namespaces, configmaps, secrets, and nodes. Use when listing, inspecting, or managing fundamental K8s objects.
---

# Core Kubernetes Resources

Manage fundamental Kubernetes objects using kubectl-mcp-server's core tools.

## Pods

```python
# List pods in namespace
get_pods(namespace="default")
get_pods(namespace="kube-system", label_selector="app=nginx")

# Get pod details
describe_pod(name="my-pod", namespace="default")

# Get logs
get_pod_logs(name="my-pod", namespace="default")
get_pod_logs(name="my-pod", namespace="default", previous=True)  # Previous container

# Delete pod
delete_pod(name="my-pod", namespace="default")
```

## Namespaces

```python
# List namespaces
get_namespaces()

# Create namespace
create_namespace(name="my-namespace")

# Delete namespace
delete_namespace(name="my-namespace")
```

## ConfigMaps

```python
# List configmaps
get_configmaps(namespace="default")

# Get specific configmap
get_configmap(name="my-config", namespace="default")

# Create configmap
create_configmap(
    name="app-config",
    namespace="default",
    data={"key": "value", "config.yaml": "setting: true"}
)
```

## Secrets

```python
# List secrets
get_secrets(namespace="default")

# Get secret (base64 encoded)
get_secret(name="my-secret", namespace="default")

# Create secret
create_secret(
    name="db-credentials",
    namespace="default",
    data={"username": "admin", "password": "secret123"}
)
```

## Nodes

```python
# List nodes
get_nodes()

# Get node details
describe_node(name="node-1")

# Get nodes summary (CPU, memory, pods)
get_nodes_summary()

# Cordon/uncordon
cordon_node(name="node-1")
uncordon_node(name="node-1")

# Drain node
drain_node(name="node-1", ignore_daemonsets=True)
```

## Events

```python
# Get events in namespace
get_events(namespace="default")

# Get events for specific resource
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
