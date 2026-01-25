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
rollouts_list_tool(namespace="production")

# Get rollout details and status
rollout_get_tool(name="my-app", namespace="production")
rollout_status_tool(name="my-app", namespace="production")

# Promote (advance canary)
rollout_promote_tool(name="my-app", namespace="production")

# Abort (rollback)
rollout_abort_tool(name="my-app", namespace="production")

# Retry failed rollout
rollout_retry_tool(name="my-app", namespace="production")

# Restart rollout (new ReplicaSet)
rollout_restart_tool(name="my-app", namespace="production")

# Check analysis runs
analysis_runs_list_tool(namespace="production")
```

## Common Workflows

### Safe Canary Release

```
1. rollout_status_tool(name, namespace)  # Check current state
2. # Update image in rollout manifest
3. apply_manifest(rollout_yaml, namespace)
4. rollout_status_tool(name, namespace)  # Watch progress
5. # If analysis fails: rollout_abort_tool(name, namespace)
6. # If manual gate: rollout_promote_tool(name, namespace)
```

### Emergency Rollback

```
rollout_abort_tool(name, namespace)
# Immediately reverts to stable version
```

### Force Full Promotion

```
rollout_promote_tool(name, namespace, full=True)
# Skips remaining steps
```

## Troubleshooting

### Rollout Stuck

```
rollout_status_tool(name, namespace)
analysis_runs_list_tool(namespace)
get_events(namespace)
```

### Analysis Failing

```
analysis_runs_list_tool(namespace)
# Check Prometheus query in AnalysisTemplate
# Verify metrics are being collected
```
