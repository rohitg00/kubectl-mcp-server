---
name: k8s-certs
description: Kubernetes certificate management with cert-manager. Use when managing TLS certificates, configuring issuers, or troubleshooting certificate issues.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 9
  category: security
---

# Certificate Management with cert-manager

Manage TLS certificates using kubectl-mcp-server's cert-manager tools.

## When to Apply

Use this skill when:
- User mentions: "certificate", "cert-manager", "TLS", "SSL", "issuer", "Let's Encrypt"
- Operations: creating certificates, configuring issuers, debugging cert issues
- Keywords: "https", "secure", "encrypt", "renew", "expiring"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect cert-manager first | CRITICAL | `detect_certs` |
| 2 | Use staging issuer for testing | HIGH | Test with letsencrypt-staging |
| 3 | Check issuer before cert | HIGH | `list_cert_issuers` |
| 4 | Monitor certificate expiry | MEDIUM | `get_cert` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect cert-manager | `detect_certs` | `detect_certs()` |
| List certificates | `list_certs` | `list_certs(namespace)` |
| Get certificate | `get_cert` | `get_cert(name, namespace)` |
| List issuers | `list_cert_issuers` | `list_cert_issuers()` |

## Check Installation

```python
detect_certs()
```

## Certificates

### List Certificates

```python
list_certs(namespace="default")
```

### Get Certificate Details

```python
get_cert(
    name="my-tls",
    namespace="default"
)
```

### Create Certificate

```python
kubectl_apply(manifest="""
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: my-tls
  namespace: default
spec:
  secretName: my-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - app.example.com
  - www.example.com
""")
```

## Issuers

### List Issuers

```python
list_cert_issuers(namespace="default")

list_cert_issuers()
```

### Get Issuer Details

```python
get_cert_issuer(name="my-issuer", namespace="default")
get_cert_issuer(name="letsencrypt-prod")
```

### Create Let's Encrypt Issuer

```python
kubectl_apply(manifest="""
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-staging-key
    solvers:
    - http01:
        ingress:
          class: nginx
""")

kubectl_apply(manifest="""
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
    - http01:
        ingress:
          class: nginx
""")
```

### Create Self-Signed Issuer

```python
kubectl_apply(manifest="""
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: selfsigned
spec:
  selfSigned: {}
""")
```

## Certificate Requests

```python
list_cert_requests(namespace="default")

list_cert_requests(
    name="my-tls-xxxxx",
    namespace="default"
)
```

## Troubleshooting

### Certificate Not Ready

```python
get_cert(name, namespace)
list_cert_requests(namespace)
get_events(namespace)
```

### Issuer Not Ready

```python
get_cert_issuer(name)
get_events(namespace="cert-manager")
```

## Ingress Integration

```python
kubectl_apply(manifest="""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: app-tls
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

## Prerequisites

- **cert-manager**: Required for all certificate tools
  ```bash
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
  ```

## Related Skills

- [k8s-networking](../k8s-networking/SKILL.md) - Ingress configuration
- [k8s-security](../k8s-security/SKILL.md) - Security best practices
