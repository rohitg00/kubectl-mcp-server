---
name: k8s-vind
description: Manage vCluster (virtual Kubernetes clusters) instances using vind. Use when creating, managing, or operating lightweight virtual clusters for development, testing, or multi-tenancy.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 14
  category: development
---

# vCluster (vind) Management

Manage virtual Kubernetes clusters using kubectl-mcp-server's vind tools (14 tools).

vCluster enables running fully functional Kubernetes clusters as lightweight workloads inside a host cluster, combining multi-tenancy with strong isolation.

## When to Apply

Use this skill when:
- User mentions: "vCluster", "vind", "virtual cluster", "lightweight cluster"
- Operations: creating dev environments, multi-tenant isolation, ephemeral clusters
- Keywords: "virtual Kubernetes", "dev cluster", "pause cluster", "tenant isolation"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect vCluster CLI first | CRITICAL | `detect_ecosystem` |
| 2 | Check cluster status before operations | HIGH | `vind_status` |
| 3 | Connect before kubectl operations | HIGH | `vind_connect` |
| 4 | Pause unused clusters to save resources | MEDIUM | `vind_pause` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect vCluster | `detect_ecosystem` | `detect_ecosystem()` |
| List clusters | `vind_list_clusters` | `vind_list_clusters()` |
| Create cluster | `vind_create_cluster` | `vind_create_cluster(name)` |
| Connect to cluster | `vind_connect` | `vind_connect(name)` |

## Prerequisites

- **vCluster CLI**: Required for all vind tools
  ```bash
  curl -L -o vcluster "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)"
  chmod +x vcluster && sudo mv vcluster /usr/local/bin/
  ```

## Check Installation

```python
detect_ecosystem()
```

## List Clusters

```python
vind_list_clusters()
```

## Get Cluster Status

```python
vind_status(name="my-vcluster", namespace="vcluster")
```

## Get Kubeconfig

```python
vind_get_kubeconfig(name="my-vcluster", namespace="vcluster")
```

## View Logs

```python
vind_status(name="my-vcluster", namespace="vcluster", tail=100)
```

## Cluster Lifecycle

### Create Cluster

```python
vind_create_cluster(name="dev-cluster")

vind_create_cluster(
    name="dev-cluster",
    namespace="dev",
    kubernetes_version="v1.29.0",
    connect=True
)

vind_create_cluster(
    name="custom-cluster",
    set_values="sync.toHost.pods.enabled=true,sync.toHost.services.enabled=true"
)
```

### Delete Cluster

```python
vind_delete_cluster(name="dev-cluster")

vind_delete_cluster(
    name="dev-cluster",
    namespace="dev",
    delete_namespace=True
)
```

### Pause Cluster (Save Resources)

```python
vind_pause(name="dev-cluster")
```

### Resume Cluster

```python
vind_resume(name="dev-cluster")
```

## Connect/Disconnect

### Connect to Cluster

```python
vind_connect(name="dev-cluster")

vind_connect(
    name="dev-cluster",
    namespace="dev",
    kube_config="~/.kube/vcluster-config"
)
```

### Disconnect from Cluster

```python
vind_disconnect()
```

## Upgrade Cluster

```python
vind_upgrade(
    name="dev-cluster",
    kubernetes_version="v1.30.0"
)

vind_upgrade(
    name="dev-cluster",
    values_file="new-values.yaml"
)
```

## Describe Cluster

```python
vind_describe(name="dev-cluster")
```

## Platform UI

```python
vind_status()

vind_status(host="0.0.0.0", port=9898)
```

## Development Workflow

### Quick Dev Environment

```python
vind_create_cluster(name="dev", connect=True)

kubectl_apply(manifest="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: nginx:alpine
""")
```

### Multi-Tenant Setup

```python
vind_create_cluster(name="team-a", namespace="team-a-vcluster")
vind_create_cluster(name="team-b", namespace="team-b-vcluster")

vind_list_clusters()
```

### Resource Management

```python
vind_pause(name="dev")

vind_resume(name="dev")
```

## Docker-Specific Configuration

For vCluster in Docker (vind) deployments, use `--set` values:

```python
vind_create_cluster(
    name="docker-cluster",
    set_values="experimental.docker.network=my-network,experimental.docker.ports[0].containerPort=80"
)
```

## Troubleshooting

### Cluster Not Starting

```text
1. detect_ecosystem()
2. vind_status(name="my-cluster", tail=200)
3. vind_status(name="my-cluster")
```

### Connection Issues

```text
1. vind_disconnect()
2. vind_connect(name="my-cluster")
3. vind_get_kubeconfig(name="my-cluster")
```

### Resource Issues

```text
1. vind_pause(name="unused-cluster")
2. vind_delete_cluster(name="old-cluster", delete_namespace=True)
```

## CLI Installation

Install vCluster CLI:

```bash
curl -L -o vcluster "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)"
chmod +x vcluster
sudo mv vcluster /usr/local/bin/

vcluster version
```

## Related Skills

- [k8s-multicluster](../k8s-multicluster/SKILL.md) - Multi-cluster management
- [k8s-helm](../k8s-helm/SKILL.md) - Helm chart operations
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl operations
