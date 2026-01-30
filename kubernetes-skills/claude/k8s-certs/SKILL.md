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
| 1 | Detect cert-manager first | CRITICAL | `certmanager_detect_tool` |
| 2 | Use staging issuer for testing | HIGH | Test with letsencrypt-staging |
| 3 | Check issuer before cert | HIGH | `certmanager_clusterissuers_list_tool` |
| 4 | Monitor certificate expiry | MEDIUM | `certmanager_certificate_get_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Detect cert-manager | `certmanager_detect_tool` | `certmanager_detect_tool()` |
| List certificates | `certmanager_certificates_list_tool` | `certmanager_certificates_list_tool(namespace)` |
| Get certificate | `certmanager_certificate_get_tool` | `certmanager_certificate_get_tool(name, namespace)` |
| List issuers | `certmanager_clusterissuers_list_tool` | `certmanager_clusterissuers_list_tool()` |

## Check Installation

```python
certmanager_detect_tool()
```

## Certificates

### List Certificates

```python
certmanager_certificates_list_tool(namespace="default")
```

### Get Certificate Details

```python
certmanager_certificate_get_tool(
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
certmanager_issuers_list_tool(namespace="default")

certmanager_clusterissuers_list_tool()
```

### Get Issuer Details

```python
certmanager_issuer_get_tool(name="my-issuer", namespace="default")
certmanager_clusterissuer_get_tool(name="letsencrypt-prod")
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
certmanager_certificaterequests_list_tool(namespace="default")

certmanager_certificaterequest_get_tool(
    name="my-tls-xxxxx",
    namespace="default"
)
```

## Troubleshooting

### Certificate Not Ready

```python
certmanager_certificate_get_tool(name, namespace)
certmanager_certificaterequests_list_tool(namespace)
get_events(namespace)
```

### Issuer Not Ready

```python
certmanager_clusterissuer_get_tool(name)
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
