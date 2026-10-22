---
name: k8s-networking
description: Kubernetes networking management for services, ingresses, endpoints, and network policies. Use when configuring connectivity, load balancing, or network isolation.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 5
  category: networking
---

# Kubernetes Networking

Manage Kubernetes networking resources using kubectl-mcp-server's networking tools.

> Requires the `security` toolset: start kubectl-mcp-server with `--toolsets default,security` (or `MCP_TOOLSETS=default,security`).

## When to Apply

Use this skill when:
- User mentions: "service", "ingress", "endpoint", "network policy", "load balancer"
- Operations: exposing applications, configuring routing, network isolation
- Keywords: "connectivity", "DNS", "traffic", "port", "firewall"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check endpoints before troubleshooting services | CRITICAL | `kubectl_get` |
| 2 | Verify service selector matches pod labels | HIGH | `kubectl_get`, `kubectl_get` |
| 3 | Review network policies for isolation | HIGH | `analyze_network_policies` |
| 4 | Test DNS resolution from within pods | MEDIUM | `exec_in_pod` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List services | `kubectl_get` | `kubectl_get(resource_type="services", namespace)` |
| Check backends | `kubectl_get` | `kubectl_get(resource_type="endpoints", namespace)` |
| List ingresses | `kubectl_get` | `kubectl_get(resource_type="ingress", namespace)` |
| Network policies | `analyze_network_policies` | `analyze_network_policies(namespace)` |

## Services

```python
kubectl_get(resource_type="services", namespace="default")

kubectl_describe(resource_type="service", name="my-service", namespace="default")

kubectl_apply(manifest="""
apiVersion: v1
kind: Service
metadata:
  name: my-service
  namespace: default
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
""")

kubectl_apply(manifest="""
apiVersion: v1
kind: Service
metadata:
  name: my-lb
  namespace: default
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - port: 443
    targetPort: 8443
""")
```

## Endpoints

```python
kubectl_get(resource_type="endpoints", namespace="default")
```

## Ingress

```python
kubectl_get(resource_type="ingress", namespace="default")

kubectl_describe(resource_type="ingress", name="my-ingress", namespace="default")

kubectl_apply(manifest="""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  namespace: default
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
""")
```

## Network Policies

```python
analyze_network_policies(namespace="default")

kubectl_describe(resource_type="networkpolicy", name="deny-all", namespace="default")

kubectl_apply(manifest="""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
""")

kubectl_apply(manifest="""
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: web
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 80
""")
```

## Troubleshooting Connectivity

```python
kubectl_get(resource_type="endpoints", namespace="default")

analyze_network_policies(namespace="default")

exec_in_pod(
    pod_name="debug-pod",
    namespace="default",
    command="nslookup my-service.default.svc.cluster.local"
)
```

## Related Skills

- [k8s-service-mesh](../k8s-service-mesh/SKILL.md) - Istio traffic management
- [k8s-cilium](../k8s-cilium/SKILL.md) - Cilium network policies
