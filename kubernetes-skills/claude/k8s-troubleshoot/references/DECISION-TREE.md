# Troubleshooting Decision Trees

Visual flowcharts for diagnosing Kubernetes issues.

## Pod Not Running

```
Pod Status?
├── Pending
│   ├── Events show "Insufficient cpu/memory"
│   │   └── Scale cluster or reduce requests
│   ├── Events show "no nodes available"
│   │   └── Check node taints, affinity rules
│   ├── Events show "PersistentVolumeClaim not found"
│   │   └── Create PVC or check storage class
│   └── No events
│       └── Check scheduler pods in kube-system
│
├── CrashLoopBackOff
│   ├── get_pod_logs(previous=True)
│   ├── Exit Code 137 (OOMKilled)
│   │   └── Increase memory limits
│   ├── Exit Code 1 (App Error)
│   │   └── Check application logs, config
│   └── Exit Code 127 (Command Not Found)
│       └── Check entrypoint/command in spec
│
├── ImagePullBackOff
│   ├── "unauthorized"
│   │   └── Create/update imagePullSecrets
│   ├── "not found"
│   │   └── Verify image name and tag
│   └── "timeout"
│       └── Check network, registry availability
│
├── ContainerCreating (stuck)
│   ├── Volume issues
│   │   └── Check PVC status, storage class
│   ├── ConfigMap/Secret not found
│   │   └── Create missing resources
│   └── Network issues
│       └── Check CNI pods
│
└── Running but not ready
    ├── Readiness probe failing
    │   └── Check probe config, app health
    └── Init containers not complete
        └── Check init container logs
```

## Service Not Accessible

```
Service unreachable?
├── get_endpoints(namespace) empty?
│   ├── Yes
│   │   ├── Pods exist with matching labels?
│   │   │   ├── No → Fix selector labels
│   │   │   └── Yes → Pods not ready
│   │   │       └── Fix pod readiness
│   │   └── Service selector correct?
│   │       └── Update service spec
│   └── No (endpoints exist)
│       ├── Check NetworkPolicy
│       │   └── get_network_policies(namespace)
│       ├── Check Service type
│       │   ├── ClusterIP → Only internal access
│       │   ├── NodePort → Access via node:port
│       │   └── LoadBalancer → Check cloud LB
│       └── DNS resolution working?
│           └── Test from inside pod
```

## Node Issues

```
Node Not Ready?
├── describe_node(name)
├── Conditions show:
│   ├── MemoryPressure
│   │   └── Eviction happening, free memory
│   ├── DiskPressure
│   │   └── Clean up images, logs
│   ├── PIDPressure
│   │   └── Kill zombie processes
│   └── NetworkUnavailable
│       └── Check CNI, kubelet
├── Kubelet not running?
│   └── Check systemctl status kubelet
└── Node cordoned?
    └── kubectl uncordon node
```

## Storage Issues

```
PVC Pending?
├── describe_pvc(name, namespace)
├── Events show:
│   ├── "no persistent volumes available"
│   │   ├── Dynamic provisioning enabled?
│   │   │   └── Check StorageClass exists
│   │   └── Static PV exists with matching spec?
│   │       └── Check access modes, capacity
│   ├── "waiting for first consumer"
│   │   └── Normal with WaitForFirstConsumer
│   └── "provisioning failed"
│       └── Check storage backend, quotas
```

## Deployment Not Progressing

```
Deployment stuck?
├── rollout_status(name, namespace)
├── Shows "waiting for rollout to finish"
│   ├── New pods starting?
│   │   ├── No → Check pod issues above
│   │   └── Yes but failing
│   │       └── Check pod logs
│   ├── Old pods not terminating?
│   │   ├── Check finalizers
│   │   └── Check PDBs (PodDisruptionBudget)
│   └── Deadline exceeded?
│       └── Increase progressDeadlineSeconds
```

## Quick Commands Reference

| Issue | First Command |
|-------|--------------|
| Pod not starting | `describe_pod(name, namespace)` |
| Logs needed | `get_pod_logs(name, namespace, previous=True)` |
| Events check | `get_events(namespace)` |
| Node issues | `describe_node(name)` |
| Service debug | `get_endpoints(namespace)` |
| Storage issues | `describe_pvc(name, namespace)` |
