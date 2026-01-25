---
name: k8s-cilium
description: Cilium and Hubble network observability for Kubernetes. Use when managing network policies, observing traffic flows, or troubleshooting connectivity with eBPF-based networking.
---

# Cilium & Hubble Network Observability

Manage eBPF-based networking using kubectl-mcp-server's Cilium tools (8 tools).

## Check Installation

```python
cilium_detect_tool()
```

## Cilium Status

```python
# Get Cilium agent status
cilium_status_tool()

# Shows:
# - Cilium health
# - Cluster connectivity
# - Controller status
# - Proxy status
```

## Network Policies

### List Policies

```python
cilium_policies_list_tool(namespace="default")

# Shows CiliumNetworkPolicies and CiliumClusterwideNetworkPolicies
```

### Get Policy Details

```python
cilium_policy_get_tool(name="allow-web", namespace="default")

# Shows:
# - Ingress rules
# - Egress rules
# - Endpoint selector
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
# List Cilium endpoints
cilium_endpoints_list_tool(namespace="default")

# Shows:
# - Endpoint ID
# - Pod name
# - Identity
# - Policy status (ingress/egress enforcement)
```

## Identities

```python
# List Cilium identities
cilium_identities_list_tool()

# Identities are security groups based on labels
# Used for policy enforcement
```

## Nodes

```python
# List Cilium nodes
cilium_nodes_list_tool()

# Shows:
# - Node name
# - Cilium internal IP
# - Health status
# - Encryption status
```

## Hubble Flow Observability

```python
# Query network flows
hubble_flows_query_tool(
    namespace="default",
    pod="my-pod",
    last="5m"
)

# Filter by verdict
hubble_flows_query_tool(
    namespace="default",
    verdict="DROPPED"  # or FORWARDED, AUDIT
)

# Filter by type
hubble_flows_query_tool(
    namespace="default",
    type="l7"  # L7 (HTTP) flows
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
# For multi-cluster connectivity
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
1. cilium_status_tool()  # Check Cilium health
2. cilium_endpoints_list_tool(namespace)  # Check endpoint status
3. cilium_policies_list_tool(namespace)  # Check policies
4. hubble_flows_query_tool(namespace, pod, verdict="DROPPED")  # Find drops
5. # If policy dropping traffic, update policy
```

### Policy Not Working

```python
1. cilium_policy_get_tool(name, namespace)  # Verify policy spec
2. cilium_endpoints_list_tool(namespace)  # Check enforcement mode
3. hubble_flows_query_tool(namespace)  # Observe actual flows
4. # Check endpoint selector matches pods
```

### Network Performance Issues

```python
1. cilium_status_tool()  # Check agent status
2. cilium_nodes_list_tool()  # Check node health
3. hubble_flows_query_tool(namespace, type="l7")  # Check latency
```

## Best Practices

1. **Start with default deny**: Create baseline deny-all policy
2. **Use labels consistently**: Policies rely on label selectors
3. **Monitor with Hubble**: Observe flows before/after policy changes
4. **Test in staging**: Verify policies don't break connectivity

## Related Skills

- [k8s-networking](../k8s-networking/SKILL.md) - Standard K8s networking
- [k8s-security](../k8s-security/SKILL.md) - Security policies
- [k8s-service-mesh](../k8s-service-mesh/SKILL.md) - Istio service mesh
