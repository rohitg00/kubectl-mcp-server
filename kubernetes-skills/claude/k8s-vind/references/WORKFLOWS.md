# vCluster Workflow Reference

Common vCluster patterns and workflows.

## Development Workflows

### Quick Development Environment

```python
vind_create_cluster_tool(name="dev", connect=True)

vind_connect_tool(name="dev")

kubectl_apply(manifest="""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
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
        image: myapp:dev
        imagePullPolicy: Never
""")
```

### Feature Branch Environment

```python
vind_create_cluster_tool(
    name=f"feature-{branch_name}",
    namespace=f"feature-{branch_name}"
)

vind_delete_cluster_tool(
    name=f"feature-{branch_name}",
    delete_namespace=True
)
```

## Multi-Tenancy Patterns

### Per-Team Clusters

```python
teams = ["frontend", "backend", "platform"]

for team in teams:
    vind_create_cluster_tool(
        name=f"{team}-dev",
        namespace=f"{team}-vcluster"
    )

vind_list_clusters_tool()
```

### Per-Environment Isolation

```python
vind_create_cluster_tool(name="staging", namespace="staging-vcluster")
vind_create_cluster_tool(name="qa", namespace="qa-vcluster")
vind_create_cluster_tool(name="integration", namespace="integration-vcluster")
```

## Resource Management

### Cost-Saving Workflow

```python
vind_pause_tool(name="dev-cluster")

vind_resume_tool(name="dev-cluster")
```

### Scheduled Pause (Nights/Weekends)

```python
clusters = ["dev", "staging", "qa"]

for cluster in clusters:
    vind_pause_tool(name=cluster)

for cluster in clusters:
    vind_resume_tool(name=cluster)
```

## CI/CD Integration

### Test Environment Lifecycle

```python
test_cluster = f"ci-test-{build_id}"
vind_create_cluster_tool(name=test_cluster, connect=True)

kubectl_apply(manifest=test_manifests)

vind_delete_cluster_tool(name=test_cluster, delete_namespace=True)
```

### PR Preview Environments

```python
def create_preview(pr_number):
    vind_create_cluster_tool(
        name=f"pr-{pr_number}",
        namespace=f"pr-{pr_number}",
        connect=True
    )
    return vind_get_kubeconfig_tool(name=f"pr-{pr_number}")

def cleanup_preview(pr_number):
    vind_delete_cluster_tool(
        name=f"pr-{pr_number}",
        delete_namespace=True
    )
```

## Cluster Upgrade Patterns

### Rolling Upgrade

```python
vind_status_tool(name="prod-vcluster")

vind_upgrade_tool(
    name="prod-vcluster",
    kubernetes_version="v1.30.0"
)

vind_status_tool(name="prod-vcluster")
```

### Blue-Green Upgrade

```python
vind_create_cluster_tool(
    name="new-prod",
    kubernetes_version="v1.30.0"
)

vind_connect_tool(name="new-prod")
kubectl_apply(manifest=production_workloads)

vind_delete_cluster_tool(name="old-prod")
```

## Troubleshooting Workflows

### Cluster Not Starting

```python
vind_detect_tool()

vind_logs_tool(name="my-cluster", tail=200)

vind_status_tool(name="my-cluster")

get_events(namespace="my-cluster-vcluster")
```

### Connection Issues

```python
vind_disconnect_tool()

vind_connect_tool(name="my-cluster")

kubeconfig = vind_get_kubeconfig_tool(name="my-cluster")
```

### Describe for Details

```python
vind_describe_tool(name="my-cluster")
```

## Configuration Patterns

### Sync Resources to Host

```python
vind_create_cluster_tool(
    name="sync-cluster",
    set_values="sync.toHost.pods.enabled=true,sync.toHost.services.enabled=true"
)
```

### Custom K8s Version

```python
vind_create_cluster_tool(
    name="k8s-129",
    kubernetes_version="v1.29.0"
)
```

### With Specific Distro

```python
vind_create_cluster_tool(
    name="k3s-cluster",
    set_values="controlPlane.distro=k3s"
)
```

## Platform UI

### Start UI for Management

```python
vind_platform_start_tool()

vind_platform_start_tool(host="0.0.0.0", port=9898)
```

## Comparison: vCluster vs Host Resources

| Feature | vCluster | Host Namespace |
|---------|----------|----------------|
| Isolation | Full API isolation | Shared API |
| CRDs | Independent CRDs | Shared CRDs |
| RBAC | Separate RBAC | Host RBAC |
| Resource usage | ~100MB overhead | None |
| Cluster admin | Full access | Limited |
