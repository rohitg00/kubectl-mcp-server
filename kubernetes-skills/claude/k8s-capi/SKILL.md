---
name: k8s-capi
description: Cluster API lifecycle management for provisioning, scaling, and upgrading Kubernetes clusters. Use when managing cluster infrastructure or multi-cluster operations.
---

# Cluster API Lifecycle Management

Manage Kubernetes clusters using kubectl-mcp-server's Cluster API tools (11 tools).

## Check Installation

```python
capi_detect_tool()
```

## List Clusters

```python
# List all CAPI clusters
capi_clusters_list_tool(namespace="default")

# Shows:
# - Cluster name
# - Phase (Provisioning, Provisioned, Deleting)
# - Infrastructure ready
# - Control plane ready
```

## Get Cluster Details

```python
capi_cluster_get_tool(name="my-cluster", namespace="default")

# Shows:
# - Spec (control plane, infrastructure)
# - Status (phase, conditions)
# - Network configuration
```

## Get Cluster Kubeconfig

```python
# Get kubeconfig for workload cluster
capi_cluster_kubeconfig_tool(name="my-cluster", namespace="default")

# Returns kubeconfig to access the cluster
```

## Machines

### List Machines

```python
capi_machines_list_tool(namespace="default")

# Shows:
# - Machine name
# - Cluster
# - Phase (Running, Provisioning, Failed)
# - Provider ID
# - Version
```

### Get Machine Details

```python
capi_machine_get_tool(name="my-cluster-md-0-xxx", namespace="default")
```

## Machine Deployments

### List Machine Deployments

```python
capi_machinedeployments_list_tool(namespace="default")

# Shows:
# - Deployment name
# - Cluster
# - Replicas (ready/total)
# - Version
```

### Scale Machine Deployment

```python
# Scale worker nodes
capi_machinedeployment_scale_tool(
    name="my-cluster-md-0",
    namespace="default",
    replicas=5
)
```

## Machine Sets

```python
capi_machinesets_list_tool(namespace="default")
```

## Machine Health Checks

```python
capi_machinehealthchecks_list_tool(namespace="default")

# Health checks automatically remediate unhealthy machines
```

## Cluster Classes

```python
# List cluster templates
capi_clusterclasses_list_tool(namespace="default")

# ClusterClasses define reusable cluster configurations
```

## Create Cluster

```python
kubectl_apply(manifest="""
apiVersion: cluster.x-k8s.io/v1beta1
kind: Cluster
metadata:
  name: my-cluster
  namespace: default
spec:
  clusterNetwork:
    pods:
      cidrBlocks:
      - 192.168.0.0/16
    services:
      cidrBlocks:
      - 10.96.0.0/12
  controlPlaneRef:
    apiVersion: controlplane.cluster.x-k8s.io/v1beta1
    kind: KubeadmControlPlane
    name: my-cluster-control-plane
  infrastructureRef:
    apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
    kind: AWSCluster
    name: my-cluster
""")
```

## Create Machine Deployment

```python
kubectl_apply(manifest="""
apiVersion: cluster.x-k8s.io/v1beta1
kind: MachineDeployment
metadata:
  name: my-cluster-md-0
  namespace: default
spec:
  clusterName: my-cluster
  replicas: 3
  selector:
    matchLabels:
      cluster.x-k8s.io/cluster-name: my-cluster
  template:
    spec:
      clusterName: my-cluster
      version: v1.28.0
      bootstrap:
        configRef:
          apiVersion: bootstrap.cluster.x-k8s.io/v1beta1
          kind: KubeadmConfigTemplate
          name: my-cluster-md-0
      infrastructureRef:
        apiVersion: infrastructure.cluster.x-k8s.io/v1beta1
        kind: AWSMachineTemplate
        name: my-cluster-md-0
""")
```

## Cluster Lifecycle Workflows

### Provision New Cluster
```python
1. kubectl_apply(cluster_manifest)
2. capi_clusters_list_tool(namespace)  # Wait for Provisioned
3. capi_cluster_kubeconfig_tool(name, namespace)  # Get access
```

### Scale Workers
```python
1. capi_machinedeployments_list_tool(namespace)
2. capi_machinedeployment_scale_tool(name, namespace, replicas)
3. capi_machines_list_tool(namespace)  # Monitor
```

### Upgrade Cluster
```python
1. # Update control plane version
2. # Update machine deployment version
3. capi_machines_list_tool(namespace)  # Monitor rollout
```

## Troubleshooting

### Cluster Stuck Provisioning

```python
1. capi_cluster_get_tool(name, namespace)  # Check conditions
2. capi_machines_list_tool(namespace)  # Check machine status
3. get_events(namespace)  # Check events
4. # Check infrastructure provider logs
```

### Machine Failed

```python
1. capi_machine_get_tool(name, namespace)
2. get_events(namespace)
3. # Common issues:
   # - Cloud provider quota
   # - Invalid machine template
   # - Network issues
```

## Related Skills

- [k8s-multicluster](../k8s-multicluster/SKILL.md) - Multi-cluster operations
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl operations
