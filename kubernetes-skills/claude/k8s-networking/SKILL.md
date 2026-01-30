---
name: k8s-networking
description: Kubernetes networking management for services, ingresses, endpoints, and network policies. Use when configuring connectivity, load balancing, or network isolation.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 8
  category: networking
---

# Kubernetes Networking

Manage Kubernetes networking resources using kubectl-mcp-server's networking tools.

## When to Apply

Use this skill when:
- User mentions: "service", "ingress", "endpoint", "network policy", "load balancer"
- Operations: exposing applications, configuring routing, network isolation
- Keywords: "connectivity", "DNS", "traffic", "port", "firewall"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check endpoints before troubleshooting services | CRITICAL | `get_endpoints` |
| 2 | Verify service selector matches pod labels | HIGH | `get_services`, `get_pods` |
| 3 | Review network policies for isolation | HIGH | `get_network_policies` |
| 4 | Test DNS resolution from within pods | MEDIUM | `kubectl_exec` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List services | `get_services` | `get_services(namespace)` |
| Check backends | `get_endpoints` | `get_endpoints(namespace)` |
| List ingresses | `get_ingresses` | `get_ingresses(namespace)` |
| Network policies | `get_network_policies` | `get_network_policies(namespace)` |

## Services

```python
get_services(namespace="default")

describe_service(name="my-service", namespace="default")

create_service(
    name="my-service",
    namespace="default",
    selector={"app": "my-app"},
    ports=[{"port": 80, "targetPort": 8080}]
)

create_service(
    name="my-lb",
    namespace="default",
    type="LoadBalancer",
    selector={"app": "my-app"},
    ports=[{"port": 443, "targetPort": 8443}]
)
```

## Endpoints

```python
get_endpoints(namespace="default")
```

## Ingress

```python
get_ingresses(namespace="default")

describe_ingress(name="my-ingress", namespace="default")

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
get_network_policies(namespace="default")

describe_network_policy(name="deny-all", namespace="default")

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
get_endpoints(namespace="default")

get_network_policies(namespace="default")

kubectl_exec(
    pod="debug-pod",
    namespace="default",
    command="nslookup my-service.default.svc.cluster.local"
)
```

## Related Skills

- [k8s-service-mesh](../k8s-service-mesh/SKILL.md) - Istio traffic management
- [k8s-cilium](../k8s-cilium/SKILL.md) - Cilium network policies
