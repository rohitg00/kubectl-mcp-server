---
name: k8s-rollouts
description: Progressive delivery with Argo Rollouts and Flagger. Use when implementing canary deployments, blue-green deployments, or traffic shifting strategies.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 13
  category: delivery
---

# Progressive Delivery with Argo Rollouts & Flagger

Manage progressive deployments using kubectl-mcp-server's rollout tools (11 tools).

> Requires the `rollouts` toolset: start kubectl-mcp-server with `--toolsets default,rollouts` (or `MCP_TOOLSETS=default,rollouts`).

## When to Apply

Use this skill when:
- User mentions: "canary", "blue-green", "progressive delivery", "Argo Rollouts", "Flagger"
- Operations: rolling out new versions, traffic splitting, automated rollbacks
- Keywords: "gradual rollout", "traffic shift", "analysis run", "promote", "abort"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect Argo Rollouts installation first | CRITICAL | `detect_ecosystem` |
| 2 | Check rollout status before promoting | HIGH | `get_rollout_status` |
| 3 | Monitor analysis runs for failures | HIGH | `get_analysis_runs` |
| 4 | Abort immediately on critical failures | CRITICAL | `abort_rollout` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect Argo Rollouts | `detect_ecosystem` | `detect_ecosystem()` |
| List rollouts | `get_rollouts_list` | `get_rollouts_list(namespace)` |
| Get rollout status | `get_rollout_status` | `get_rollout_status(name, namespace)` |
| Promote rollout | `promote_rollout` | `promote_rollout(name, namespace)` |

## Check Installation

```python
detect_ecosystem()
```

## Argo Rollouts

### List Rollouts

```python
get_rollouts_list(namespace="default")

# Shows:
# - Rollout name
# - Strategy (canary/blueGreen)
# - Status
# - Desired/Ready replicas
```

### Get Rollout Details

```python
get_rollout(name="my-rollout", namespace="default")

# Shows:
# - Spec (strategy, steps)
# - Status (phase, conditions)
# - Current step
```

### Check Rollout Status

```python
get_rollout_status(name="my-rollout", namespace="default")

# Returns detailed status with:
# - Current step index
# - Canary weight
# - Stable/canary replicasets
```

### Promote Rollout

```python
# Promote to next step
promote_rollout(name="my-rollout", namespace="default")

# Full promote (skip remaining steps)
promote_rollout(name="my-rollout", namespace="default", full=True)
```

### Abort Rollout

```python
abort_rollout(name="my-rollout", namespace="default")
# Reverts to stable version
```

### Retry Rollout

```python
retry_rollout(name="my-rollout", namespace="default")
# Retry failed rollout
```

### Restart Rollout

```python
restart_rollout(name="my-rollout", namespace="default")
# Triggers new rollout with same spec
```

### Analysis Runs

```python
# List analysis runs
get_analysis_runs(namespace="default")

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
get_flagger_canaries(namespace="default")

# Shows:
# - Canary name
# - Status (Initialized, Progressing, Succeeded, Failed)
# - Weight
```

### Get Canary Details

```python
get_flagger_canary(name="my-canary", namespace="default")
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
1. get_rollouts_list(namespace)
2. # Update image in rollout
3. get_rollout_status(name, namespace)  # Monitor progress
4. promote_rollout(name, namespace)  # Promote when ready
5. # Or: abort_rollout(name, namespace) if issues
```

### Blue-Green Deployment
```python
1. get_rollout(name, namespace)  # Check current state
2. # Update image
3. get_rollout_status(name, namespace)  # Wait for preview ready
4. # Test preview service
5. promote_rollout(name, namespace)  # Switch traffic
```

## Troubleshooting

### Rollout Stuck

```python
1. get_rollout_status(name, namespace)  # Check current step
2. get_analysis_runs(namespace)  # Check analysis
3. kubectl_get(resource_type="events", namespace)  # Check events
4. # If analysis failing:
   abort_rollout(name, namespace)
```

### Canary Failing Analysis

```python
1. get_analysis_runs(namespace)
2. # Check metrics source (Prometheus, etc.)
3. # Verify threshold configuration
4. retry_rollout(name, namespace)  # Retry if transient
```

## Related Skills

- [k8s-deploy](../k8s-deploy/SKILL.md) - Standard deployments
- [k8s-service-mesh](../k8s-service-mesh/SKILL.md) - Traffic management with Istio
