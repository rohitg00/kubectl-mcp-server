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
| 1 | Detect Cilium installation first | CRITICAL | `cilium_detect_tool` |
| 2 | Check agent status for health | HIGH | `cilium_status_tool` |
| 3 | Use Hubble for flow debugging | HIGH | `hubble_flows_query_tool` |
| 4 | Start with default deny | MEDIUM | CiliumNetworkPolicy |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect Cilium | `cilium_detect_tool` | `cilium_detect_tool()` |
| Agent status | `cilium_status_tool` | `cilium_status_tool()` |
| List policies | `cilium_policies_list_tool` | `cilium_policies_list_tool(namespace)` |
| Query flows | `hubble_flows_query_tool` | `hubble_flows_query_tool(namespace)` |

## Check Installation

```python
cilium_detect_tool()
```

## Cilium Status

```python
cilium_status_tool()
```

## Network Policies

### List Policies

```python
cilium_policies_list_tool(namespace="default")
```

### Get Policy Details

```python
cilium_policy_get_tool(name="allow-web", namespace="default")
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
cilium_endpoints_list_tool(namespace="default")
```

## Identities

```python
cilium_identities_list_tool()
```

## Nodes

```python
cilium_nodes_list_tool()
```

## Hubble Flow Observability

```python
hubble_flows_query_tool(
    namespace="default",
    pod="my-pod",
    last="5m"
)

hubble_flows_query_tool(
    namespace="default",
    verdict="DROPPED"
)

hubble_flows_query_tool(
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
cilium_status_tool()
cilium_endpoints_list_tool(namespace)
cilium_policies_list_tool(namespace)
hubble_flows_query_tool(namespace, pod, verdict="DROPPED")
```

### Policy Not Working

```python
cilium_policy_get_tool(name, namespace)
cilium_endpoints_list_tool(namespace)
hubble_flows_query_tool(namespace)
```

### Network Performance Issues

```python
cilium_status_tool()
cilium_nodes_list_tool()
hubble_flows_query_tool(namespace, type="l7")
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
