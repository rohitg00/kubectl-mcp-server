---
name: k8s-kind
description: Manage kind (Kubernetes IN Docker) local clusters. Use when creating, testing, or developing with local Kubernetes clusters in Docker containers.
---

# kind (Kubernetes IN Docker) Management

Manage local Kubernetes clusters using kubectl-mcp-server's kind tools (15 tools).

kind enables running local Kubernetes clusters using Docker container "nodes". It's ideal for local development, CI/CD testing, and testing across Kubernetes versions.

## Check Installation

```python
kind_detect_tool()

kind_version_tool()
```

## List Clusters

```python
kind_list_clusters_tool()
```

## Get Cluster Information

```python
kind_cluster_info_tool(name="my-cluster")

kind_get_nodes_tool(name="my-cluster")

kind_node_labels_tool(name="my-cluster")
```

## Get Kubeconfig

```python
kind_get_kubeconfig_tool(name="my-cluster")

kind_get_kubeconfig_tool(name="my-cluster", internal=True)
```

## Export Logs

```python
kind_export_logs_tool(name="my-cluster")

kind_export_logs_tool(name="my-cluster", output_dir="/tmp/kind-logs")
```

## Cluster Lifecycle

### Create Cluster

```python
kind_create_cluster_tool()

kind_create_cluster_tool(name="dev-cluster")

kind_create_cluster_tool(
    name="v129-cluster",
    image="kindest/node:v1.29.0"
)

kind_create_cluster_tool(
    name="multi-node",
    config="kind-config.yaml"
)
```

### Multi-Node Config Example

Create a file `kind-config.yaml`:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
- role: worker
- role: worker
```

### Delete Cluster

```python
kind_delete_cluster_tool(name="dev-cluster")

kind_delete_all_clusters_tool()
```

## Image Loading (Key Feature!)

The ability to load local Docker images directly into kind clusters is one of its most powerful features for local development.

### Load Docker Images

```python
kind_load_image_tool(images="myapp:latest", name="my-cluster")

kind_load_image_tool(
    images="myapp:latest,mydb:latest,myweb:v1",
    name="my-cluster"
)
```

### Load from Archive

```python
kind_load_image_archive_tool(
    archive="/path/to/images.tar",
    name="my-cluster"
)
```

## Advanced: Build Node Image

Build custom node images from Kubernetes source:

```python
kind_build_node_image_tool()

kind_build_node_image_tool(
    image="my-custom-node:v1.30.0",
    kube_root="/path/to/kubernetes"
)
```

## Update Kubeconfig

```python
kind_set_kubeconfig_tool(name="my-cluster")
```

## Development Workflow

### Quick Local Development

```python
kind_create_cluster_tool(name="dev")

kind_load_image_tool(images="myapp:dev", name="dev")

kubectl_apply(manifest="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        image: myapp:dev
        imagePullPolicy: Never
""")
```

### CI/CD Testing

```python
kind_create_cluster_tool(
    name="ci-test",
    image="kindest/node:v1.29.0",
    wait="3m"
)

kind_load_image_tool(images="test-image:ci", name="ci-test")

kind_delete_cluster_tool(name="ci-test")
```

### Version Testing

```python
kind_create_cluster_tool(name="v128", image="kindest/node:v1.28.0")
kind_create_cluster_tool(name="v129", image="kindest/node:v1.29.0")
kind_create_cluster_tool(name="v130", image="kindest/node:v1.30.0")

kind_list_clusters_tool()
```

## Troubleshooting

### Cluster Creation Issues

```python
kind_create_cluster_tool(name="debug", retain=True)

kind_export_logs_tool(name="debug")

kind_get_nodes_tool(name="debug")
```

### Node Issues

```python
kind_node_labels_tool(name="my-cluster")

kind_export_logs_tool(name="my-cluster")
```

### Cleanup

```python
kind_delete_cluster_tool(name="broken-cluster")

kind_delete_all_clusters_tool()
```

## CLI Installation

Install kind CLI:

```bash
# macOS (Apple Silicon)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-darwin-arm64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# macOS (Intel)
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-darwin-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verify
kind version
```

## kind vs vind (vCluster)

| Feature | kind | vind (vCluster) |
|---------|------|-----------------|
| Purpose | Local dev/CI clusters | Virtual clusters in existing K8s |
| Isolation | Full clusters in Docker | Virtual namespaces with isolation |
| Resource Usage | Higher (full cluster) | Lower (shares host cluster) |
| Best For | Local testing, CI/CD | Multi-tenancy, dev environments |
| Requires | Docker | Existing K8s cluster |

## Related Skills

- [k8s-vind](../k8s-vind/SKILL.md) - vCluster management
- [k8s-multicluster](../k8s-multicluster/SKILL.md) - Multi-cluster management
- [k8s-helm](../k8s-helm/SKILL.md) - Helm chart operations
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl operations
