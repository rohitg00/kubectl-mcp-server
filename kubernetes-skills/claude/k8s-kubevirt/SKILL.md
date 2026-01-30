---
name: k8s-kubevirt
description: Virtual machine management with KubeVirt on Kubernetes. Use when creating, managing, or troubleshooting VMs running on Kubernetes clusters.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 13
  category: virtualization
---

# KubeVirt VM Management

Manage virtual machines on Kubernetes using kubectl-mcp-server's KubeVirt tools (13 tools).

## When to Apply

Use this skill when:
- User mentions: "KubeVirt", "virtual machine", "VM", "VirtualMachineInstance", "VMI"
- Operations: starting/stopping VMs, live migration, managing VM lifecycle
- Keywords: "VM on Kubernetes", "virtualization", "data volume", "instance type"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect KubeVirt installation first | CRITICAL | `kubevirt_detect_tool` |
| 2 | Check VM status before operations | HIGH | `kubevirt_vm_get_tool` |
| 3 | List VMIs for running VMs | HIGH | `kubevirt_vmis_list_tool` |
| 4 | Use instance types for consistency | MEDIUM | `kubevirt_instancetypes_list_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect KubeVirt | `kubevirt_detect_tool` | `kubevirt_detect_tool()` |
| List VMs | `kubevirt_vms_list_tool` | `kubevirt_vms_list_tool(namespace)` |
| Start VM | `kubevirt_vm_start_tool` | `kubevirt_vm_start_tool(name, namespace)` |
| Live migrate VM | `kubevirt_vm_migrate_tool` | `kubevirt_vm_migrate_tool(name, namespace)` |

## Check Installation

```python
kubevirt_detect_tool()
```

## List VMs

```python
# List VirtualMachines
kubevirt_vms_list_tool(namespace="default")

# List VirtualMachineInstances (running VMs)
kubevirt_vmis_list_tool(namespace="default")
```

## Get VM Details

```python
# Get VM definition
kubevirt_vm_get_tool(name="my-vm", namespace="default")

# Shows:
# - Spec (CPU, memory, disks)
# - Running status
# - Conditions
```

## VM Lifecycle

### Start VM

```python
kubevirt_vm_start_tool(name="my-vm", namespace="default")
```

### Stop VM

```python
kubevirt_vm_stop_tool(name="my-vm", namespace="default")
```

### Restart VM

```python
kubevirt_vm_restart_tool(name="my-vm", namespace="default")
```

### Pause/Unpause VM

```python
# Pause (freeze CPU)
kubevirt_vm_pause_tool(name="my-vm", namespace="default")

# Unpause
kubevirt_vm_unpause_tool(name="my-vm", namespace="default")
```

## Live Migration

```python
# Migrate VM to another node
kubevirt_vm_migrate_tool(name="my-vm", namespace="default")

# Check migration status
kubevirt_vmis_list_tool(namespace="default")
# Look for: migrationState
```

## Instance Types

```python
# List available instance types
kubevirt_instancetypes_list_tool()

# Instance types define:
# - CPU count
# - Memory size
# - GPU allocation
```

## Data Volumes

```python
# List data volumes (persistent VM disks)
kubevirt_datavolumes_list_tool(namespace="default")

# List data sources (golden images)
kubevirt_datasources_list_tool(namespace="default")
```

## Create VM

```python
kubectl_apply(manifest="""
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: my-vm
  namespace: default
spec:
  running: true
  template:
    metadata:
      labels:
        kubevirt.io/vm: my-vm
    spec:
      domain:
        cpu:
          cores: 2
        memory:
          guest: 4Gi
        devices:
          disks:
          - name: rootdisk
            disk:
              bus: virtio
          - name: cloudinitdisk
            disk:
              bus: virtio
      volumes:
      - name: rootdisk
        containerDisk:
          image: quay.io/kubevirt/fedora-cloud-container-disk-demo
      - name: cloudinitdisk
        cloudInitNoCloud:
          userData: |
            #cloud-config
            password: fedora
            chpasswd: { expire: False }
""")
```

## Create VM with DataVolume

```python
kubectl_apply(manifest="""
apiVersion: kubevirt.io/v1
kind: VirtualMachine
metadata:
  name: vm-with-pvc
  namespace: default
spec:
  running: true
  dataVolumeTemplates:
  - metadata:
      name: vm-with-pvc-disk
    spec:
      source:
        http:
          url: https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2
      storage:
        accessModes:
        - ReadWriteOnce
        resources:
          requests:
            storage: 10Gi
  template:
    spec:
      domain:
        cpu:
          cores: 2
        memory:
          guest: 4Gi
        devices:
          disks:
          - name: rootdisk
            disk:
              bus: virtio
      volumes:
      - name: rootdisk
        dataVolume:
          name: vm-with-pvc-disk
""")
```

## Troubleshooting

### VM Not Starting

```python
1. kubevirt_vm_get_tool(name, namespace)  # Check status/conditions
2. kubevirt_vmis_list_tool(namespace)  # Check VMI exists
3. get_events(namespace)  # Check events
4. get_pods(namespace, label_selector="kubevirt.io/vm=<name>")  # Check virt-launcher
```

### Migration Failed

```python
1. kubevirt_vmis_list_tool(namespace)  # Check migrationState
2. get_events(namespace)  # Check events
3. # Common issues:
   # - No suitable target node
   # - Insufficient resources
   # - Shared storage required
```

## Related Skills

- [k8s-storage](../k8s-storage/SKILL.md) - Persistent storage
- [k8s-operations](../k8s-operations/SKILL.md) - kubectl operations
