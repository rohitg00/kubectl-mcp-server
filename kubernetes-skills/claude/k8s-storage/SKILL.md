---
name: k8s-storage
description: Kubernetes storage management for PVCs, storage classes, and persistent volumes. Use when provisioning storage, managing volumes, or troubleshooting storage issues.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 3
  category: storage
---

# Kubernetes Storage

Manage Kubernetes storage using kubectl-mcp-server's storage tools.

## When to Apply

Use this skill when:
- User mentions: "PVC", "PV", "storage class", "volume", "disk", "storage"
- Operations: provisioning storage, mounting volumes, expanding storage
- Keywords: "persist", "data", "backup storage", "volume claim"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Verify storage class exists before PVC | CRITICAL | `get_storage_classes` |
| 2 | Check PVC status before pod deployment | HIGH | `describe_pvc` |
| 3 | Review access modes for multi-pod access | MEDIUM | `get_pvcs` |
| 4 | Monitor PV reclaim policy | LOW | `get_persistent_volumes` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List PVCs | `get_pvcs` | `get_pvcs(namespace)` |
| PVC details | `describe_pvc` | `describe_pvc(name, namespace)` |
| Storage classes | `get_storage_classes` | `get_storage_classes()` |
| List PVs | `get_persistent_volumes` | `get_persistent_volumes()` |

## Persistent Volume Claims (PVCs)

```python
get_pvcs(namespace="default")

describe_pvc(name="my-pvc", namespace="default")

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

kubectl_delete(resource_type="pvc", name="my-pvc", namespace="default")
```

## Storage Classes

```python
get_storage_classes()

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
get_persistent_volumes()

describe_persistent_volume(name="pv-001")
```

## Volume Snapshots

```python
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
describe_pvc(name="my-pvc", namespace="default")

get_events(namespace="default")
describe_pod(name="my-pod", namespace="default")
```

## Related Skills

- [k8s-backup](../k8s-backup/SKILL.md) - Velero backup/restore
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl apply/patch
