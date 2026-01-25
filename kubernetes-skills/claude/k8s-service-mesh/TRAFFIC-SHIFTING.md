# Istio Traffic Shifting Patterns

Advanced traffic management with VirtualServices.

## Weight-Based Routing (Canary)

### Gradual Rollout

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 90
    - destination:
        host: reviews
        subset: v2
      weight: 10
```

### Progressive Weights

| Phase | v1 Weight | v2 Weight | Duration |
|-------|-----------|-----------|----------|
| Start | 100% | 0% | - |
| Canary | 90% | 10% | 1 hour |
| Expand | 75% | 25% | 2 hours |
| Half | 50% | 50% | 4 hours |
| Promote | 0% | 100% | - |

### MCP Commands

```python
# Apply weight change
apply_manifest(virtualservice_yaml, namespace)

# Verify
istio_virtualservice_get_tool(name, namespace)
```

## Header-Based Routing

### Beta Users

```yaml
http:
- match:
  - headers:
      x-user-type:
        exact: beta
  route:
  - destination:
      host: reviews
      subset: v2
- route:
  - destination:
      host: reviews
      subset: v1
```

### Internal Testing

```yaml
http:
- match:
  - headers:
      x-internal:
        exact: "true"
  route:
  - destination:
      host: reviews
      subset: canary
```

## Cookie-Based Routing

```yaml
http:
- match:
  - headers:
      cookie:
        regex: "^(.*?;)?(user=beta)(;.*)?$"
  route:
  - destination:
      host: reviews
      subset: v2
```

## Source-Based Routing

### By Service Identity

```yaml
http:
- match:
  - sourceLabels:
      app: productpage
      version: v2
  route:
  - destination:
      host: reviews
      subset: v2
```

## Mirroring (Shadow Traffic)

Test new version with production traffic:

```yaml
http:
- route:
  - destination:
      host: reviews
      subset: v1
  mirror:
    host: reviews
    subset: v2
  mirrorPercentage:
    value: 100.0
```

## Fault Injection

### Delay

```yaml
http:
- fault:
    delay:
      percentage:
        value: 10
      fixedDelay: 5s
  route:
  - destination:
      host: reviews
```

### Abort

```yaml
http:
- fault:
    abort:
      percentage:
        value: 10
      httpStatus: 500
  route:
  - destination:
      host: reviews
```

## Timeout and Retry

```yaml
http:
- timeout: 10s
  retries:
    attempts: 3
    perTryTimeout: 3s
    retryOn: 5xx,reset
  route:
  - destination:
      host: reviews
```

## DestinationRule for Subsets

Required companion to VirtualService:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews
spec:
  host: reviews
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
  - name: canary
    labels:
      version: canary
```

## Traffic Shifting Workflow

```python
# 1. Ensure DestinationRule exists
istio_destinationrules_list_tool(namespace)

# 2. Check current VirtualService
istio_virtualservice_get_tool(name, namespace)

# 3. Apply new weights
apply_manifest(updated_vs, namespace)

# 4. Verify change
istio_virtualservice_get_tool(name, namespace)

# 5. Monitor (with Kiali or Prometheus)
istio_analyze_tool(namespace)
```

## Rollback

Quick rollback to stable version:

```yaml
http:
- route:
  - destination:
      host: reviews
      subset: v1
    weight: 100
```

Apply immediately:
```python
apply_manifest(rollback_vs, namespace)
```
