---
name: k8s-networking
description: Kubernetes networking management for services, ingresses, endpoints, and network policies. Use when configuring connectivity, load balancing, or network isolation.
---

# Kubernetes Networking

Manage Kubernetes networking resources using kubectl-mcp-server's networking tools.

## Services

```python
# List services
get_services(namespace="default")

# Get service details
describe_service(name="my-service", namespace="default")

# Create service (ClusterIP)
create_service(
    name="my-service",
    namespace="default",
    selector={"app": "my-app"},
    ports=[{"port": 80, "targetPort": 8080}]
)

# Create LoadBalancer
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
# List endpoints (service backends)
get_endpoints(namespace="default")

# Check if service has backends
get_endpoints(namespace="default")
# Empty addresses = no pods matching selector
```

## Ingress

```python
# List ingresses
get_ingresses(namespace="default")

# Get ingress details
describe_ingress(name="my-ingress", namespace="default")

# Create ingress
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
# List network policies
get_network_policies(namespace="default")

# Get policy details
describe_network_policy(name="deny-all", namespace="default")

# Create deny-all policy
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

# Allow specific traffic
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
# Service not accessible?
get_endpoints(namespace="default")  # Check backends exist
get_network_policies(namespace="default")  # Check isolation

# DNS issues?
kubectl_exec(
    pod="debug-pod",
    namespace="default",
    command="nslookup my-service.default.svc.cluster.local"
)
```

## Related Skills

- [k8s-service-mesh](../k8s-service-mesh/SKILL.md) - Istio traffic management
- [k8s-cilium](../k8s-cilium/SKILL.md) - Cilium network policies
