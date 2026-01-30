# Deployment Strategies Reference

Comparison of Kubernetes deployment strategies and when to use each.

## Strategy Comparison

| Strategy | Downtime | Risk | Rollback | Resource Cost | Best For |
|----------|----------|------|----------|---------------|----------|
| Rolling | None | Medium | Fast | 1.25-1.5x | Most apps |
| Recreate | Yes | Low | Manual | 1x | Stateful apps |
| Blue-Green | None | Low | Instant | 2x | Critical apps |
| Canary | None | Lowest | Instant | 1.1-1.5x | High-traffic apps |

## Rolling Update (Default)

**How it works:**
1. New pods created incrementally
2. Old pods terminated as new become ready
3. Controlled by `maxSurge` and `maxUnavailable`

**Configuration:**
```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
```

**Pros:**
- Zero downtime
- Low resource overhead
- Built into Kubernetes

**Cons:**
- Both versions run simultaneously
- No easy rollback mid-update
- Session affinity issues possible

**When to use:**
- Standard stateless applications
- Services that tolerate version mixing

## Recreate Strategy

**How it works:**
1. All existing pods terminated
2. New pods created after termination
3. Brief downtime during switch

**Configuration:**
```yaml
spec:
  strategy:
    type: Recreate
```

**Pros:**
- Clean switch between versions
- No version mixing
- Lower resource cost

**Cons:**
- Causes downtime
- Slower rollout

**When to use:**
- Applications that cannot run multiple versions
- Databases or stateful applications
- Development environments

## Blue-Green Deployment

**How it works:**
1. Deploy new version alongside old (green environment)
2. Run tests against green environment
3. Switch traffic instantly via service selector
4. Keep blue available for instant rollback

**With Argo Rollouts:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    blueGreen:
      activeService: myapp-active
      previewService: myapp-preview
      autoPromotionEnabled: false
```

**Pros:**
- Instant rollback
- Zero downtime
- Full testing before switch

**Cons:**
- 2x resource cost
- More complex setup

**When to use:**
- Critical production services
- Applications requiring instant rollback
- Compliance requirements

## Canary Deployment

**How it works:**
1. Deploy new version to small percentage
2. Gradually increase traffic
3. Monitor for errors
4. Auto-rollback on failures

**With Argo Rollouts:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 5m}
      - setWeight: 30
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
```

**Pros:**
- Lowest risk
- Real user testing
- Automatic rollback

**Cons:**
- Slower rollout
- Complex monitoring needed
- Version mixing during rollout

**When to use:**
- High-traffic applications
- Risk-sensitive deployments
- A/B testing requirements

## Traffic Shifting Methods

### Service Selector (Basic)

```yaml
apiVersion: v1
kind: Service
spec:
  selector:
    app: myapp
    version: v2  # Change to switch traffic
```

### Istio VirtualService

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
spec:
  http:
  - route:
    - destination:
        host: myapp
        subset: v1
      weight: 90
    - destination:
        host: myapp
        subset: v2
      weight: 10
```

### Argo Rollouts (Recommended)

Handles traffic shifting automatically based on analysis.

## Decision Flow

```
Need instant rollback?
├── Yes → Blue-Green
└── No
    └── High-risk deployment?
        ├── Yes → Canary
        └── No
            └── Stateful app?
                ├── Yes → Recreate
                └── No → Rolling Update
```

## MCP Server Tools by Strategy

| Strategy | Primary Tools |
|----------|--------------|
| Rolling | `set_deployment_image`, `rollout_status` |
| Recreate | `kubectl_apply`, `get_pods` |
| Blue-Green | `rollout_promote_tool`, `rollout_abort_tool` |
| Canary | `rollout_status_tool`, `rollout_promote_tool`, `analysis_runs_list_tool` |
