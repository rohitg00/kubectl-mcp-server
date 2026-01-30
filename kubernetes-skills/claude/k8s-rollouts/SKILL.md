---
name: k8s-rollouts
description: Progressive delivery with Argo Rollouts and Flagger. Use when implementing canary deployments, blue-green deployments, or traffic shifting strategies.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 11
  category: delivery
---

# Progressive Delivery with Argo Rollouts & Flagger

Manage progressive deployments using kubectl-mcp-server's rollout tools (11 tools).

## When to Apply

Use this skill when:
- User mentions: "canary", "blue-green", "progressive delivery", "Argo Rollouts", "Flagger"
- Operations: rolling out new versions, traffic splitting, automated rollbacks
- Keywords: "gradual rollout", "traffic shift", "analysis run", "promote", "abort"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect Argo Rollouts installation first | CRITICAL | `rollouts_detect_tool` |
| 2 | Check rollout status before promoting | HIGH | `rollout_status_tool` |
| 3 | Monitor analysis runs for failures | HIGH | `analysis_runs_list_tool` |
| 4 | Abort immediately on critical failures | CRITICAL | `rollout_abort_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect Argo Rollouts | `rollouts_detect_tool` | `rollouts_detect_tool()` |
| List rollouts | `rollouts_list_tool` | `rollouts_list_tool(namespace)` |
| Get rollout status | `rollout_status_tool` | `rollout_status_tool(name, namespace)` |
| Promote rollout | `rollout_promote_tool` | `rollout_promote_tool(name, namespace)` |

## Check Installation

```python
rollouts_detect_tool()
```

## Argo Rollouts

### List Rollouts

```python
rollouts_list_tool(namespace="default")

# Shows:
# - Rollout name
# - Strategy (canary/blueGreen)
# - Status
# - Desired/Ready replicas
```

### Get Rollout Details

```python
rollout_get_tool(name="my-rollout", namespace="default")

# Shows:
# - Spec (strategy, steps)
# - Status (phase, conditions)
# - Current step
```

### Check Rollout Status

```python
rollout_status_tool(name="my-rollout", namespace="default")

# Returns detailed status with:
# - Current step index
# - Canary weight
# - Stable/canary replicasets
```

### Promote Rollout

```python
# Promote to next step
rollout_promote_tool(name="my-rollout", namespace="default")

# Full promote (skip remaining steps)
rollout_promote_tool(name="my-rollout", namespace="default", full=True)
```

### Abort Rollout

```python
rollout_abort_tool(name="my-rollout", namespace="default")
# Reverts to stable version
```

### Retry Rollout

```python
rollout_retry_tool(name="my-rollout", namespace="default")
# Retry failed rollout
```

### Restart Rollout

```python
rollout_restart_tool(name="my-rollout", namespace="default")
# Triggers new rollout with same spec
```

### Analysis Runs

```python
# List analysis runs
analysis_runs_list_tool(namespace="default")

# Analysis runs verify rollout health:
# - Prometheus metrics
# - Web hooks
# - Custom jobs
```

## Create Canary Rollout

```python
kubectl_apply(manifest="""
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-rollout
  namespace: default
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 1m}
      - setWeight: 40
      - pause: {duration: 1m}
      - setWeight: 60
      - pause: {duration: 1m}
      - setWeight: 80
      - pause: {duration: 1m}
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
        image: my-app:v2
        ports:
        - containerPort: 8080
""")
```

## Create Blue-Green Rollout

```python
kubectl_apply(manifest="""
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-rollout
  namespace: default
spec:
  replicas: 3
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      autoPromotionEnabled: false
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
        image: my-app:v2
""")
```

## Flagger

### List Canaries

```python
flagger_canaries_list_tool(namespace="default")

# Shows:
# - Canary name
# - Status (Initialized, Progressing, Succeeded, Failed)
# - Weight
```

### Get Canary Details

```python
flagger_canary_get_tool(name="my-canary", namespace="default")
```

## Create Flagger Canary

```python
kubectl_apply(manifest="""
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: my-canary
  namespace: default
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  service:
    port: 80
  analysis:
    interval: 30s
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      threshold: 99
      interval: 1m
    - name: request-duration
      threshold: 500
      interval: 1m
""")
```

## Progressive Delivery Workflows

### Canary Deployment
```python
1. rollouts_list_tool(namespace)
2. # Update image in rollout
3. rollout_status_tool(name, namespace)  # Monitor progress
4. rollout_promote_tool(name, namespace)  # Promote when ready
5. # Or: rollout_abort_tool(name, namespace) if issues
```

### Blue-Green Deployment
```python
1. rollout_get_tool(name, namespace)  # Check current state
2. # Update image
3. rollout_status_tool(name, namespace)  # Wait for preview ready
4. # Test preview service
5. rollout_promote_tool(name, namespace)  # Switch traffic
```

## Troubleshooting

### Rollout Stuck

```python
1. rollout_status_tool(name, namespace)  # Check current step
2. analysis_runs_list_tool(namespace)  # Check analysis
3. get_events(namespace)  # Check events
4. # If analysis failing:
   rollout_abort_tool(name, namespace)
```

### Canary Failing Analysis

```python
1. analysis_runs_list_tool(namespace)
2. # Check metrics source (Prometheus, etc.)
3. # Verify threshold configuration
4. rollout_retry_tool(name, namespace)  # Retry if transient
```

## Related Skills

- [k8s-deploy](../k8s-deploy/SKILL.md) - Standard deployments
- [k8s-service-mesh](../k8s-service-mesh/SKILL.md) - Traffic management with Istio
