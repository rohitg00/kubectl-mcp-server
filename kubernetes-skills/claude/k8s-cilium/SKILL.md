---
name: k8s-cilium
description: Cilium and Hubble network observability for Kubernetes. Use when managing network policies, observing traffic flows, or troubleshooting connectivity with eBPF-based networking.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 8
  category: networking
---

# Cilium & Hubble Network Observability

Manage eBPF-based networking using kubectl-mcp-server's Cilium tools (8 tools).

## When to Apply

Use this skill when:
- User mentions: "Cilium", "Hubble", "eBPF", "network policy", "flow"
- Operations: network policy management, traffic observation, L7 filtering
- Keywords: "network security", "traffic flow", "dropped packets", "connectivity"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect Cilium installation first | CRITICAL | `detect_cilium` |
| 2 | Check agent status for health | HIGH | `cilium_get_status` |
| 3 | Use Hubble for flow debugging | HIGH | `get_hubble_flows` |
| 4 | Start with default deny | MEDIUM | CiliumNetworkPolicy |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect Cilium | `detect_cilium` | `detect_cilium()` |
| Agent status | `cilium_get_status` | `cilium_get_status()` |
| List policies | `cilium_list_policies` | `cilium_list_policies(namespace)` |
| Query flows | `get_hubble_flows` | `get_hubble_flows(namespace)` |

## Check Installation

```python
detect_cilium()
```

## Cilium Status

```python
cilium_get_status()
```

## Network Policies

### List Policies

```python
cilium_list_policies(namespace="default")
```

### Get Policy Details

```python
cilium_get_policy(name="allow-web", namespace="default")
```

### Create Cilium Network Policy

```python
kubectl_apply(manifest="""
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-web
  namespace: default
spec:
  endpointSelector:
    matchLabels:
      app: web
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
  egress:
  - toEndpoints:
    - matchLabels:
        app: database
    toPorts:
    - ports:
      - port: "5432"
        protocol: TCP
""")
```

## Endpoints

```python
cilium_list_endpoints(namespace="default")
```

## Identities

```python
cilium_list_identities()
```

## Nodes

```python
cilium_list_nodes()
```

## Hubble Flow Observability

```python
get_hubble_flows(
    namespace="default",
    pod="my-pod",
    last="5m"
)

get_hubble_flows(
    namespace="default",
    verdict="DROPPED"
)

get_hubble_flows(
    namespace="default",
    type="l7"
)
```

## Create L7 Policy

```python
kubectl_apply(manifest="""
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-policy
  namespace: default
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: "/api/v1/.*"
        - method: POST
          path: "/api/v1/users"
""")
```

## Cluster Mesh

```python
kubectl_apply(manifest="""
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-cross-cluster
spec:
  endpointSelector:
    matchLabels:
      app: shared-service
  ingress:
  - fromEntities:
    - cluster
    - remote-node
""")
```

## Troubleshooting Workflows

### Pod Can't Reach Service

```python
cilium_get_status()
cilium_list_endpoints(namespace)
cilium_list_policies(namespace)
get_hubble_flows(namespace, pod, verdict="DROPPED")
```

### Policy Not Working

```python
cilium_get_policy(name, namespace)
cilium_list_endpoints(namespace)
get_hubble_flows(namespace)
```

### Network Performance Issues

```python
cilium_get_status()
cilium_list_nodes()
get_hubble_flows(namespace, type="l7")
```

## Best Practices

1. **Start with default deny**: Create baseline deny-all policy
2. **Use labels consistently**: Policies rely on label selectors
3. **Monitor with Hubble**: Observe flows before/after policy changes
4. **Test in staging**: Verify policies don't break connectivity

## Prerequisites

- **Cilium**: Required for all Cilium tools
  ```bash
  cilium install
  ```

## Related Skills

- [k8s-networking](../k8s-networking/SKILL.md) - Standard K8s networking
- [k8s-security](../k8s-security/SKILL.md) - Security policies
- [k8s-service-mesh](../k8s-service-mesh/SKILL.md) - Istio service mesh
