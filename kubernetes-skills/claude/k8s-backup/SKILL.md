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
| 1 | Verify Velero installation first | CRITICAL | `detect_ecosystem` |
| 2 | Check backup location before create | HIGH | `list_backup_locations` |
| 3 | Wait for backup completion | HIGH | `get_backup` |
| 4 | Test restores to non-prod first | MEDIUM | `create_restore` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect Velero | `detect_ecosystem` | `detect_ecosystem()` |
| List backups | `list_backups` | `list_backups()` |
| Create backup | `create_backup` | `create_backup(name, namespaces)` |
| Restore | `create_restore` | `create_restore(name, backup_name)` |

## Check Velero Installation

```python
detect_ecosystem()

list_backup_locations()
```

## Create Backups

```python
create_backup(
    name="my-backup",
    namespaces=["default", "app-namespace"]
)

create_backup(
    name="app-backup",
    namespaces=["default"],
    label_selector="app=my-app"
)

create_backup(
    name="config-backup",
    namespaces=["default"],
    exclude_resources=["pods", "replicasets"]
)

create_backup(
    name="daily-backup",
    namespaces=["production"],
    ttl="720h"
)
```

## List and Describe Backups

```python
list_backups()

get_backup(name="my-backup")
```

## Restore from Backup

```python
create_restore(
    name="my-restore",
    backup_name="my-backup"
)

create_restore(
    name="my-restore",
    backup_name="my-backup",
    namespace_mappings={"old-ns": "new-ns"}
)

create_restore(
    name="config-restore",
    backup_name="my-backup",
    include_resources=["configmaps", "secrets"]
)

create_restore(
    name="partial-restore",
    backup_name="my-backup",
    exclude_resources=["persistentvolumeclaims"]
)
```

## List and Monitor Restores

```python
list_restores()

get_restore(name="my-restore")
```

## Scheduled Backups

```python
list_backup_schedules()

list_backup_schedules(name="daily-backup")

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
from datetime import datetime

create_backup(
    name=f"dr-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    namespaces=["production"]
)
get_backup(name="dr-backup-20260130-120000")
```

### Restore to New Cluster

```python
detect_ecosystem()
list_backups()
create_restore(
    name="dr-restore",
    backup_name="dr-backup-..."
)
get_restore(name="dr-restore")
```

## Prerequisites

- **Velero**: Required for all backup tools
  ```bash
  velero install --provider aws --bucket my-bucket --secret-file ./credentials
  ```

## Related Skills

- [k8s-multicluster](../k8s-multicluster/SKILL.md) - Multi-cluster operations
- [k8s-incident](../k8s-incident/SKILL.md) - Incident response
