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
| 1 | Detect Istio installation first | CRITICAL | `istio_detect_tool` |
| 2 | Run analyze before changes | HIGH | `istio_analyze_tool` |
| 3 | Check proxy status for sync | HIGH | `istio_proxy_status_tool` |
| 4 | Verify sidecar injection | MEDIUM | `istio_sidecar_status_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect Istio | `istio_detect_tool` | `istio_detect_tool()` |
| Analyze config | `istio_analyze_tool` | `istio_analyze_tool(namespace)` |
| Proxy status | `istio_proxy_status_tool` | `istio_proxy_status_tool()` |
| List VirtualServices | `istio_virtualservices_list_tool` | `istio_virtualservices_list_tool(namespace)` |

## Quick Status Check

### Detect Istio Installation

```python
istio_detect_tool()
```

### Check Proxy Status

```python
istio_proxy_status_tool()
istio_sidecar_status_tool(namespace)
```

### Analyze Configuration

```python
istio_analyze_tool(namespace)
```

## Traffic Management

### VirtualServices

List and inspect:

```python
istio_virtualservices_list_tool(namespace)
istio_virtualservice_get_tool(name, namespace)
```

See [TRAFFIC-SHIFTING.md](TRAFFIC-SHIFTING.md) for canary and blue-green patterns.

### DestinationRules

```python
istio_destinationrules_list_tool(namespace)
```

### Gateways

```python
istio_gateways_list_tool(namespace)
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
istio_virtualservice_get_tool("my-service", namespace)
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
istio_peerauthentications_list_tool(namespace)
```

### AuthorizationPolicy

```python
istio_authorizationpolicies_list_tool(namespace)
```

## Observability

### Proxy Metrics

```python
istio_proxy_status_tool()
```

### Hubble (Cilium Integration)

If using Cilium with Istio:

```python
hubble_flows_query_tool(namespace)
cilium_endpoints_list_tool(namespace)
```

## Troubleshooting

### Sidecar Not Injected

```python
istio_sidecar_status_tool(namespace)
```

### Traffic Not Routing

```python
istio_analyze_tool(namespace)
istio_virtualservice_get_tool(name, namespace)
istio_destinationrules_list_tool(namespace)
istio_proxy_status_tool()
```

### mTLS Failures

```python
istio_peerauthentications_list_tool(namespace)
```

### Common Issues

| Symptom | Check | Resolution |
|---------|-------|------------|
| 503 errors | `istio_analyze_tool()` | Fix VirtualService/DestinationRule |
| No sidecar | `istio_sidecar_status_tool()` | Label namespace |
| Config not applied | `istio_proxy_status_tool()` | Wait for sync or restart pod |

## Multi-Cluster Service Mesh

Istio multi-cluster setup:

```python
istio_proxy_status_tool(context="primary")
istio_virtualservices_list_tool(namespace, context="primary")

istio_proxy_status_tool(context="remote")
```

## Prerequisites

- **Istio**: Required for all Istio tools
  ```bash
  istioctl install --set profile=demo
  ```

## Related Skills

- [k8s-deploy](../k8s-deploy/SKILL.md) - Deployment with traffic shifting
- [k8s-security](../k8s-security/SKILL.md) - Authorization policies
