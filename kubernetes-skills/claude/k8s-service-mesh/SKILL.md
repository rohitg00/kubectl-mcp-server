---
name: k8s-service-mesh
description: Manage Istio service mesh for traffic management, security, and observability. Use for traffic shifting, canary releases, mTLS, and service mesh troubleshooting.
---

# Kubernetes Service Mesh (Istio)

Traffic management, security, and observability using kubectl-mcp-server's Istio/Kiali tools.

## Quick Status Check

### Detect Istio Installation
```
istio_detect_tool()
```

### Check Proxy Status
```
istio_proxy_status_tool()  # All proxies
istio_sidecar_status_tool(namespace)  # Namespace injection status
```

### Analyze Configuration
```
istio_analyze_tool(namespace)  # Find configuration issues
```

## Traffic Management

### VirtualServices

List and inspect:
```
istio_virtualservices_list_tool(namespace)
istio_virtualservice_get_tool(name, namespace)
```

See [TRAFFIC-SHIFTING.md](TRAFFIC-SHIFTING.md) for canary and blue-green patterns.

### DestinationRules
```
istio_destinationrules_list_tool(namespace)
```

### Gateways
```
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
```
apply_manifest(vs_yaml, namespace)
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
```
istio_peerauthentications_list_tool(namespace)
```

Modes:
- `STRICT`: Require mTLS
- `PERMISSIVE`: Accept both
- `DISABLE`: No mTLS

### AuthorizationPolicy
```
istio_authorizationpolicies_list_tool(namespace)
```

Example deny-all policy:
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: my-namespace
spec:
  {}  # Empty spec = deny all
```

## Observability

### With Kiali
If Kiali is installed:
- Access Kiali dashboard for service graph
- Traffic flow visualization
- Configuration validation

### Proxy Metrics
```
# Check proxy sync status
istio_proxy_status_tool()
```

### Hubble (Cilium Integration)
If using Cilium with Istio:
```
hubble_flows_query_tool(namespace)
cilium_endpoints_list_tool(namespace)
```

## Troubleshooting

### Sidecar Not Injected
```
istio_sidecar_status_tool(namespace)
# Check namespace label: istio-injection=enabled
```

### Traffic Not Routing
```
1. istio_analyze_tool(namespace)  # Find issues
2. istio_virtualservice_get_tool(name, namespace)  # Check VS
3. istio_destinationrules_list_tool(namespace)  # Check DR
4. istio_proxy_status_tool()  # Check proxy sync
```

### mTLS Failures
```
1. istio_peerauthentications_list_tool(namespace)
2. Check mode matches between services
3. Verify certificates are valid
```

### Common Issues

| Symptom | Check | Resolution |
|---------|-------|------------|
| 503 errors | `istio_analyze_tool()` | Fix VirtualService/DestinationRule |
| No sidecar | `istio_sidecar_status_tool()` | Label namespace |
| Config not applied | `istio_proxy_status_tool()` | Wait for sync or restart pod |

## Multi-Cluster Service Mesh

Istio multi-cluster setup:
```
# Primary cluster
istio_proxy_status_tool(context="primary")
istio_virtualservices_list_tool(namespace, context="primary")

# Remote cluster
istio_proxy_status_tool(context="remote")
```

## Related Skills
- [k8s-deploy](../k8s-deploy/SKILL.md) - Deployment with traffic shifting
- [k8s-security](../k8s-security/SKILL.md) - Authorization policies
