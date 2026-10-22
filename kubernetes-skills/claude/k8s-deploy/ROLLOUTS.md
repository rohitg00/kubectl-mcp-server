# Argo Rollouts Deep Dive

Detailed workflows for progressive delivery with Argo Rollouts.

## Rollout Types

### Canary Strategy

Gradually shift traffic to the new version:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 5m}
      - setWeight: 25
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 75
      - pause: {duration: 5m}
```

### Blue-Green Strategy

Switch all traffic at once:

```yaml
strategy:
  blueGreen:
    activeService: my-app-active
    previewService: my-app-preview
    autoPromotionEnabled: false
    prePromotionAnalysis:
      templates:
      - templateName: success-rate
```

## Analysis Templates

### Success Rate Analysis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
  - name: success-rate
    interval: 30s
    count: 5
    successCondition: result[0] >= 0.95
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(http_requests_total{status=~"2.*",app="{{args.app}}"}[5m])) /
          sum(rate(http_requests_total{app="{{args.app}}"}[5m]))
```

## MCP Server Tools

```python
# List all rollouts
get_rollouts_list(namespace="production")

# Get rollout details and status
get_rollout(name="my-app", namespace="production")
get_rollout_status(name="my-app", namespace="production")

# Promote (advance canary)
promote_rollout(name="my-app", namespace="production")

# Abort (rollback)
abort_rollout(name="my-app", namespace="production")

# Retry failed rollout
retry_rollout(name="my-app", namespace="production")

# Restart rollout (new ReplicaSet)
restart_rollout(name="my-app", namespace="production")

# Check analysis runs
get_analysis_runs(namespace="production")
```

## Common Workflows

### Safe Canary Release

```
1. get_rollout_status(name, namespace)  # Check current state
2. # Update image in rollout manifest
3. kubectl_apply(rollout_yaml, namespace)
4. get_rollout_status(name, namespace)  # Watch progress
5. # If analysis fails: abort_rollout(name, namespace)
6. # If manual gate: promote_rollout(name, namespace)
```

### Emergency Rollback

```
abort_rollout(name, namespace)
# Immediately reverts to stable version
```

### Force Full Promotion

```
promote_rollout(name, namespace, full=True)
# Skips remaining steps
```

## Troubleshooting

### Rollout Stuck

```
get_rollout_status(name, namespace)
get_analysis_runs(namespace)
get_events(namespace)
```

### Analysis Failing

```
get_analysis_runs(namespace)
# Check Prometheus query in AnalysisTemplate
# Verify metrics are being collected
```
