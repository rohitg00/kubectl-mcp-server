---
name: k8s-storage
description: Kubernetes storage management for PVCs, storage classes, and persistent volumes. Use when provisioning storage, managing volumes, or troubleshooting storage issues.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 4
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
| 1 | Verify storage class exists before PVC | CRITICAL | `kubectl_get` |
| 2 | Check PVC status before pod deployment | HIGH | `kubectl_describe` |
| 3 | Review access modes for multi-pod access | MEDIUM | `kubectl_get` |
| 4 | Monitor PV reclaim policy | LOW | `kubectl_get` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List PVCs | `kubectl_get` | `kubectl_get(resource_type="pvc", namespace)` |
| PVC details | `kubectl_describe` | `kubectl_describe(name, namespace)` |
| Storage classes | `kubectl_get` | `kubectl_get(resource_type="storageclasses")` |
| List PVs | `kubectl_get` | `kubectl_get(resource_type="pv")` |

## Persistent Volume Claims (PVCs)

```python
kubectl_get(resource_type="pvc", namespace="default")

kubectl_describe(resource_type="pvc", name="my-pvc", namespace="default")

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

delete_resource(resource_type="pvc", name="my-pvc", namespace="default")
```

## Storage Classes

```python
kubectl_get(resource_type="storageclasses")

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
kubectl_get(resource_type="pv")

kubectl_describe(resource_type="pv", name="pv-001")
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
kubectl_describe(resource_type="pvc", name="my-pvc", namespace="default")

kubectl_get(resource_type="events", namespace="default")
kubectl_describe(resource_type="pod", name="my-pod", namespace="default")
```

## Related Skills

- [k8s-backup](../k8s-backup/SKILL.md) - Velero backup/restore
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl apply/patch
