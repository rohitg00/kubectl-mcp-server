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
| 1 | Detect vCluster CLI first | CRITICAL | `vind_detect_tool` |
| 2 | Check cluster status before operations | HIGH | `vind_status_tool` |
| 3 | Connect before kubectl operations | HIGH | `vind_connect_tool` |
| 4 | Pause unused clusters to save resources | MEDIUM | `vind_pause_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect vCluster | `vind_detect_tool` | `vind_detect_tool()` |
| List clusters | `vind_list_clusters_tool` | `vind_list_clusters_tool()` |
| Create cluster | `vind_create_cluster_tool` | `vind_create_cluster_tool(name)` |
| Connect to cluster | `vind_connect_tool` | `vind_connect_tool(name)` |

## Prerequisites

- **vCluster CLI**: Required for all vind tools
  ```bash
  curl -L -o vcluster "https://github.com/loft-sh/vcluster/releases/latest/download/vcluster-$(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)"
  chmod +x vcluster && sudo mv vcluster /usr/local/bin/
  ```

## Check Installation

```python
vind_detect_tool()
```

## List Clusters

```python
vind_list_clusters_tool()
```

## Get Cluster Status

```python
vind_status_tool(name="my-vcluster", namespace="vcluster")
```

## Get Kubeconfig

```python
vind_get_kubeconfig_tool(name="my-vcluster", namespace="vcluster")
```

## View Logs

```python
vind_logs_tool(name="my-vcluster", namespace="vcluster", tail=100)
```

## Cluster Lifecycle

### Create Cluster

```python
vind_create_cluster_tool(name="dev-cluster")

vind_create_cluster_tool(
    name="dev-cluster",
    namespace="dev",
    kubernetes_version="v1.29.0",
    connect=True
)

vind_create_cluster_tool(
    name="custom-cluster",
    set_values="sync.toHost.pods.enabled=true,sync.toHost.services.enabled=true"
)
```

### Delete Cluster

```python
vind_delete_cluster_tool(name="dev-cluster")

vind_delete_cluster_tool(
    name="dev-cluster",
    namespace="dev",
    delete_namespace=True
)
```

### Pause Cluster (Save Resources)

```python
vind_pause_tool(name="dev-cluster")
```

### Resume Cluster

```python
vind_resume_tool(name="dev-cluster")
```

## Connect/Disconnect

### Connect to Cluster

```python
vind_connect_tool(name="dev-cluster")

vind_connect_tool(
    name="dev-cluster",
    namespace="dev",
    kube_config="~/.kube/vcluster-config"
)
```

### Disconnect from Cluster

```python
vind_disconnect_tool()
```

## Upgrade Cluster

```python
vind_upgrade_tool(
    name="dev-cluster",
    kubernetes_version="v1.30.0"
)

vind_upgrade_tool(
    name="dev-cluster",
    values_file="new-values.yaml"
)
```

## Describe Cluster

```python
vind_describe_tool(name="dev-cluster")
```

## Platform UI

```python
vind_platform_start_tool()

vind_platform_start_tool(host="0.0.0.0", port=9898)
```

## Development Workflow

### Quick Dev Environment

```python
vind_create_cluster_tool(name="dev", connect=True)

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
vind_create_cluster_tool(name="team-a", namespace="team-a-vcluster")
vind_create_cluster_tool(name="team-b", namespace="team-b-vcluster")

vind_list_clusters_tool()
```

### Resource Management

```python
vind_pause_tool(name="dev")

vind_resume_tool(name="dev")
```

## Docker-Specific Configuration

For vCluster in Docker (vind) deployments, use `--set` values:

```python
vind_create_cluster_tool(
    name="docker-cluster",
    set_values="experimental.docker.network=my-network,experimental.docker.ports[0].containerPort=80"
)
```

## Troubleshooting

### Cluster Not Starting

```text
1. vind_detect_tool()
2. vind_logs_tool(name="my-cluster", tail=200)
3. vind_status_tool(name="my-cluster")
```

### Connection Issues

```text
1. vind_disconnect_tool()
2. vind_connect_tool(name="my-cluster")
3. vind_get_kubeconfig_tool(name="my-cluster")
```

### Resource Issues

```text
1. vind_pause_tool(name="unused-cluster")
2. vind_delete_cluster_tool(name="old-cluster", delete_namespace=True)
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
