---
name: k8s-backup
description: Kubernetes backup and restore with Velero. Use when creating backups, restoring applications, managing disaster recovery, or migrating workloads between clusters.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 11
  category: backup
---

# Kubernetes Backup with Velero

Manage backups and restores using kubectl-mcp-server's Velero tools.

## When to Apply

Use this skill when:
- User mentions: "backup", "restore", "Velero", "disaster recovery", "DR"
- Operations: creating backups, restoring namespaces, migration
- Keywords: "protect", "recover", "migrate", "snapshot"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Verify Velero installation first | CRITICAL | `velero_detect_tool` |
| 2 | Check backup location before create | HIGH | `velero_backup_locations_list_tool` |
| 3 | Wait for backup completion | HIGH | `velero_backup_get_tool` |
| 4 | Test restores to non-prod first | MEDIUM | `velero_restore_create_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect Velero | `velero_detect_tool` | `velero_detect_tool()` |
| List backups | `velero_backups_list_tool` | `velero_backups_list_tool()` |
| Create backup | `velero_backup_create_tool` | `velero_backup_create_tool(name, namespaces)` |
| Restore | `velero_restore_create_tool` | `velero_restore_create_tool(name, backup_name)` |

## Check Velero Installation

```python
velero_detect_tool()

velero_backup_locations_list_tool()
```

## Create Backups

```python
velero_backup_create_tool(
    name="my-backup",
    namespaces=["default", "app-namespace"]
)

velero_backup_create_tool(
    name="app-backup",
    namespaces=["default"],
    label_selector="app=my-app"
)

velero_backup_create_tool(
    name="config-backup",
    namespaces=["default"],
    exclude_resources=["pods", "replicasets"]
)

velero_backup_create_tool(
    name="daily-backup",
    namespaces=["production"],
    ttl="720h"
)
```

## List and Describe Backups

```python
velero_backups_list_tool()

velero_backup_get_tool(name="my-backup")
```

## Restore from Backup

```python
velero_restore_create_tool(
    name="my-restore",
    backup_name="my-backup"
)

velero_restore_create_tool(
    name="my-restore",
    backup_name="my-backup",
    namespace_mappings={"old-ns": "new-ns"}
)

velero_restore_create_tool(
    name="config-restore",
    backup_name="my-backup",
    include_resources=["configmaps", "secrets"]
)

velero_restore_create_tool(
    name="partial-restore",
    backup_name="my-backup",
    exclude_resources=["persistentvolumeclaims"]
)
```

## List and Monitor Restores

```python
velero_restores_list_tool()

velero_restore_get_tool(name="my-restore")
```

## Scheduled Backups

```python
velero_schedules_list_tool()

velero_schedule_get_tool(name="daily-backup")

kubectl_apply(manifest="""
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces:
    - production
    ttl: 720h
""")
```

## Disaster Recovery Workflow

### Create DR Backup

```python
velero_backup_create_tool(
    name="dr-backup-$(date)",
    namespaces=["production"]
)
velero_backup_get_tool(name="dr-backup-...")
```

### Restore to New Cluster

```python
velero_detect_tool()
velero_backups_list_tool()
velero_restore_create_tool(
    name="dr-restore",
    backup_name="dr-backup-..."
)
velero_restore_get_tool(name="dr-restore")
```

## Prerequisites

- **Velero**: Required for all backup tools
  ```bash
  velero install --provider aws --bucket my-bucket --secret-file ./credentials
  ```

## Related Skills

- [k8s-multicluster](../k8s-multicluster/SKILL.md) - Multi-cluster operations
- [k8s-incident](../k8s-incident/SKILL.md) - Incident response
