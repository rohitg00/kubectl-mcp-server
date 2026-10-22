---
name: k8s-service-mesh
description: Manage Istio service mesh for traffic management, security, and observability. Use for traffic shifting, canary releases, mTLS, and service mesh troubleshooting.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 10
  category: networking
---

# Kubernetes Service Mesh (Istio)

Traffic management, security, and observability using kubectl-mcp-server's Istio/Kiali tools.

## When to Apply

Use this skill when:
- User mentions: "Istio", "service mesh", "mTLS", "VirtualService", "traffic shifting"
- Operations: traffic management, canary deployments, security policies
- Keywords: "sidecar", "proxy", "traffic split", "mutual TLS"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect Istio installation first | CRITICAL | `istio_detect` |
| 2 | Run analyze before changes | HIGH | `istio_analyze` |
| 3 | Check proxy status for sync | HIGH | `istio_proxy_status` |
| 4 | Verify sidecar injection | MEDIUM | `istio_sidecar_status` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect Istio | `istio_detect` | `istio_detect()` |
| Analyze config | `istio_analyze` | `istio_analyze(namespace)` |
| Proxy status | `istio_proxy_status` | `istio_proxy_status()` |
| List VirtualServices | `istio_virtualservices_list` | `istio_virtualservices_list(namespace)` |

## Quick Status Check

### Detect Istio Installation

```python
istio_detect()
```

### Check Proxy Status

```python
istio_proxy_status()
istio_sidecar_status(namespace)
```

### Analyze Configuration

```python
istio_analyze(namespace)
```

## Traffic Management

### VirtualServices

List and inspect:

```python
istio_virtualservices_list(namespace)
istio_virtualservice_get(name, namespace)
```

See [TRAFFIC-SHIFTING.md](TRAFFIC-SHIFTING.md) for canary and blue-green patterns.

### DestinationRules

```python
istio_destinationrules_list(namespace)
```

### Gateways

```python
istio_gateways_list(namespace)
```

## Traffic Shifting Patterns

### Canary Release (Weight-Based)

VirtualService for 90/10 split:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-service
spec:
  hosts:
  - my-service
  http:
  - route:
    - destination:
        host: my-service
        subset: stable
      weight: 90
    - destination:
        host: my-service
        subset: canary
      weight: 10
```

Apply and verify:

```python
kubectl_apply(vs_yaml, namespace)
istio_virtualservice_get("my-service", namespace)
```

### Header-Based Routing

Route beta users:

```yaml
http:
- match:
  - headers:
      x-user-type:
        exact: beta
  route:
  - destination:
      host: my-service
      subset: canary
- route:
  - destination:
      host: my-service
      subset: stable
```

## Security (mTLS)

See [MTLS.md](MTLS.md) for detailed mTLS configuration.

### PeerAuthentication (mTLS Mode)

```python
istio_peerauthentications_list(namespace)
```

### AuthorizationPolicy

```python
istio_authorizationpolicies_list(namespace)
```

## Observability

### Proxy Metrics

```python
istio_proxy_status()
```

### Hubble (Cilium Integration)

If using Cilium with Istio:

```python
get_hubble_flows(namespace)
cilium_list_endpoints(namespace)
```

## Troubleshooting

### Sidecar Not Injected

```python
istio_sidecar_status(namespace)
```

### Traffic Not Routing

```python
istio_analyze(namespace)
istio_virtualservice_get(name, namespace)
istio_destinationrules_list(namespace)
istio_proxy_status()
```

### mTLS Failures

```python
istio_peerauthentications_list(namespace)
```

### Common Issues

| Symptom | Check | Resolution |
|---------|-------|------------|
| 503 errors | `istio_analyze()` | Fix VirtualService/DestinationRule |
| No sidecar | `istio_sidecar_status()` | Label namespace |
| Config not applied | `istio_proxy_status()` | Wait for sync or restart pod |

## Multi-Cluster Service Mesh

Istio multi-cluster setup:

```python
istio_proxy_status(context="primary")
istio_virtualservices_list(namespace, context="primary")

istio_proxy_status(context="remote")
```

## Prerequisites

- **Istio**: Required for all Istio tools
  ```bash
  istioctl install --set profile=demo
  ```

## Related Skills

- [k8s-deploy](../k8s-deploy/SKILL.md) - Deployment with traffic shifting
- [k8s-security](../k8s-security/SKILL.md) - Authorization policies
