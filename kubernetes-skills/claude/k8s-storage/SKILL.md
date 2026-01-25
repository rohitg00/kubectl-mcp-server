---
name: k8s-storage
description: Kubernetes storage management for PVCs, storage classes, and persistent volumes. Use when provisioning storage, managing volumes, or troubleshooting storage issues.
---

# Kubernetes Storage

Manage Kubernetes storage using kubectl-mcp-server's storage tools.

## Persistent Volume Claims (PVCs)

```python
# List PVCs
get_pvcs(namespace="default")

# Get PVC details
describe_pvc(name="my-pvc", namespace="default")

# Create PVC
kubectl_apply(manifest="""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
  namespace: default
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard
""")

# Delete PVC
kubectl_delete(resource_type="pvc", name="my-pvc", namespace="default")
```

## Storage Classes

```python
# List storage classes
get_storage_classes()

# Get default storage class
get_storage_classes()
# Look for: storageclass.kubernetes.io/is-default-class: "true"

# Create storage class
kubectl_apply(manifest="""
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-ssd
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
""")
```

## Persistent Volumes

```python
# List PVs
get_persistent_volumes()

# Get PV details
describe_persistent_volume(name="pv-001")

# Check PV status
# - Available: Ready to be bound
# - Bound: Claimed by a PVC
# - Released: PVC deleted, not yet reclaimed
# - Failed: Reclamation failed
```

## Volume Snapshots

```python
# Create volume snapshot
kubectl_apply(manifest="""
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: my-snapshot
  namespace: default
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: my-pvc
""")

# Restore from snapshot
kubectl_apply(manifest="""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-pvc
spec:
  dataSource:
    name: my-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
""")
```

## Troubleshooting Storage

```python
# PVC stuck in Pending?
describe_pvc(name="my-pvc", namespace="default")
# Check events for:
# - No matching storage class
# - Insufficient capacity
# - Volume binding mode

# Pod stuck waiting for volume?
get_events(namespace="default")
describe_pod(name="my-pod", namespace="default")
```

## Related Skills

- [k8s-backup](../k8s-backup/SKILL.md) - Velero backup/restore
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl apply/patch
