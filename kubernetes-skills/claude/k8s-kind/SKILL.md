---
name: k8s-kind
description: Manage kind (Kubernetes IN Docker) local clusters. Use when creating, testing, or developing with local Kubernetes clusters in Docker containers.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 32
  category: development
---

# kind (Kubernetes IN Docker) Management

Manage local Kubernetes clusters using kubectl-mcp-server's kind tools (32 tools).

kind enables running local Kubernetes clusters using Docker container "nodes". It's ideal for local development, CI/CD testing, and testing across Kubernetes versions.

## When to Apply

Use this skill when:
- User mentions: "kind", "local cluster", "Kubernetes in Docker", "dev cluster"
- Operations: creating local clusters, loading images, CI/CD testing
- Keywords: "local development", "test cluster", "load image", "multi-node"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect kind CLI first | CRITICAL | `kind_detect_tool` |
| 2 | Generate config for complex setups | HIGH | `kind_config_generate_tool` |
| 3 | Load images after cluster creation | HIGH | `kind_load_image_tool` |
| 4 | Export logs for debugging | MEDIUM | `kind_export_logs_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect kind | `kind_detect_tool` | `kind_detect_tool()` |
| Create cluster | `kind_create_cluster_tool` | `kind_create_cluster_tool(name)` |
| Load image | `kind_load_image_tool` | `kind_load_image_tool(images, name)` |
| Get kubeconfig | `kind_get_kubeconfig_tool` | `kind_get_kubeconfig_tool(name)` |

## Prerequisites

- **kind CLI**: Required for all kind tools
  ```bash
  # macOS
  brew install kind
  # or download binary
  curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-$(uname)-amd64
  chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind
  ```
- **Docker**: Required (kind runs clusters in Docker containers)

## Check Installation

```python
kind_detect_tool()

kind_version_tool()

kind_provider_info_tool()
```

## List Clusters

```python
kind_list_clusters_tool()
```

## Get Cluster Information

```python
kind_cluster_info_tool(name="my-cluster")

kind_cluster_status_tool(name="my-cluster")

kind_get_nodes_tool(name="my-cluster")

kind_node_labels_tool(name="my-cluster")
```

## Configuration Management

### Generate Config

```python
kind_config_generate_tool()

kind_config_generate_tool(workers=2, control_planes=1)

kind_config_generate_tool(workers=2, ingress=True, registry=True)

kind_config_generate_tool(control_planes=3, workers=3)
```

### Validate Config

```python
kind_config_validate_tool(config_path="/path/to/kind.yaml")
```

### Show Running Config

```python
kind_config_show_tool(name="my-cluster")
```

### Available Images

```python
kind_available_images_tool()
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

## Local Registry Integration

### Create Registry

```python
kind_registry_create_tool()

kind_registry_create_tool(name="my-registry", port=5001)
```

### Connect Cluster to Registry

```python
kind_registry_connect_tool(cluster_name="my-cluster")
```

### Check Registry Status

```python
kind_registry_status_tool()
```

### Registry Workflow

```python
kind_registry_create_tool()

config = kind_config_generate_tool(registry=True)

kind_create_cluster_tool(name="dev", config="/tmp/kind.yaml")

kind_registry_connect_tool(cluster_name="dev")
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

### List Images on Cluster

```python
kind_images_list_tool(cluster="my-cluster")

kind_images_list_tool(cluster="my-cluster", node="my-cluster-worker")
```

## Node Management

### Inspect Node

```python
kind_node_inspect_tool(node="kind-control-plane")
```

### Get Node Logs

```python
kind_node_logs_tool(node="kind-control-plane")

kind_node_logs_tool(node="kind-control-plane", tail=200)
```

### Execute Command on Node

```python
kind_node_exec_tool(
    node="kind-control-plane",
    command="crictl images"
)

kind_node_exec_tool(
    node="kind-control-plane",
    command="journalctl -u kubelet --no-pager -n 50"
)
```

### Restart Node

```python
kind_node_restart_tool(node="kind-worker")
```

## Networking

### Inspect Network

```python
kind_network_inspect_tool()
```

### List Port Mappings

```python
kind_port_mappings_tool(cluster="my-cluster")
```

### Setup Ingress

```python
kind_ingress_setup_tool(cluster="my-cluster")

kind_ingress_setup_tool(cluster="my-cluster", ingress_type="contour")
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

### Development with Local Registry

```python
kind_registry_create_tool()

config = kind_config_generate_tool(workers=1, ingress=True, registry=True)

kind_create_cluster_tool(name="dev", config="/tmp/kind-config.yaml")

kind_registry_connect_tool(cluster_name="dev")

kind_ingress_setup_tool(cluster="dev")
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

### Cluster Health Check

```python
kind_cluster_status_tool(name="my-cluster")
```

### Node Issues

```python
kind_node_inspect_tool(node="kind-control-plane")

kind_node_logs_tool(node="kind-control-plane")

kind_node_exec_tool(
    node="kind-control-plane",
    command="crictl ps"
)

kind_node_restart_tool(node="kind-worker")
```

### Network Issues

```python
kind_network_inspect_tool()

kind_port_mappings_tool()
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

## Tool Reference

### Read-Only Tools (20)
| Tool | Description |
|------|-------------|
| `kind_detect_tool` | Detect CLI installation |
| `kind_version_tool` | Get CLI version |
| `kind_list_clusters_tool` | List all clusters |
| `kind_get_nodes_tool` | List nodes in cluster |
| `kind_get_kubeconfig_tool` | Get kubeconfig |
| `kind_export_logs_tool` | Export cluster logs |
| `kind_cluster_info_tool` | Get cluster info |
| `kind_node_labels_tool` | Get node labels |
| `kind_config_validate_tool` | Validate config file |
| `kind_config_generate_tool` | Generate config YAML |
| `kind_config_show_tool` | Show running config |
| `kind_available_images_tool` | List K8s versions |
| `kind_registry_status_tool` | Check registry status |
| `kind_node_logs_tool` | Get node logs |
| `kind_node_inspect_tool` | Inspect node details |
| `kind_network_inspect_tool` | Inspect Docker network |
| `kind_port_mappings_tool` | List port mappings |
| `kind_cluster_status_tool` | Get cluster health |
| `kind_images_list_tool` | List images on nodes |
| `kind_provider_info_tool` | Get provider info |

### Write Tools (12)
| Tool | Description |
|------|-------------|
| `kind_create_cluster_tool` | Create cluster |
| `kind_delete_cluster_tool` | Delete cluster |
| `kind_delete_all_clusters_tool` | Delete all clusters |
| `kind_load_image_tool` | Load Docker images |
| `kind_load_image_archive_tool` | Load from archive |
| `kind_build_node_image_tool` | Build node image |
| `kind_set_kubeconfig_tool` | Set kubeconfig context |
| `kind_registry_create_tool` | Create local registry |
| `kind_registry_connect_tool` | Connect to registry |
| `kind_node_exec_tool` | Execute on node |
| `kind_node_restart_tool` | Restart node |
| `kind_ingress_setup_tool` | Setup ingress |

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
