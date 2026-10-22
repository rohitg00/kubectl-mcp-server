---
name: k8s-security
description: Audit Kubernetes RBAC, enforce policies, and manage secrets. Use for security reviews, permission audits, policy enforcement with Kyverno/Gatekeeper, and secret management.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 10
  category: security
---

# Kubernetes Security

Security auditing, RBAC management, and policy enforcement using kubectl-mcp-server tools.

> Requires the `cilium`, `istio`, `policy`, `security` toolsets: start kubectl-mcp-server with `--toolsets default,cilium,istio,policy,security` (or `MCP_TOOLSETS=default,cilium,istio,policy,security`). For deep work, the project-maintained MCP servers may fit better: Kyverno: https://github.com/nirmata/kyverno-mcp.

## When to Apply

Use this skill when:
- User mentions: "security", "RBAC", "permissions", "policy", "audit", "secrets"
- Operations: security review, permission check, policy enforcement
- Keywords: "who can", "access control", "compliance", "vulnerable"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check cluster-admin bindings first | CRITICAL | `kubectl_get` |
| 2 | Audit secrets access permissions | CRITICAL | Review role rules |
| 3 | Verify network isolation | HIGH | `analyze_network_policies` |
| 4 | Check policy compliance | HIGH | `kyverno_*`, `gatekeeper_*` |
| 5 | Review pod security contexts | MEDIUM | `kubectl_describe` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List roles | `kubectl_get` | `kubectl_get(resource_type="roles", namespace)` |
| Cluster roles | `kubectl_get` | `kubectl_get(resource_type="clusterroles")` |
| Role bindings | `kubectl_get` | `kubectl_get(resource_type="roles", namespace)` |
| Service accounts | `kubectl_get` | `kubectl_get(resource_type="serviceaccounts", namespace)` |
| Kyverno policies | `get_policy_list` | `get_policy_list()` |

## RBAC Auditing

### List Roles and Bindings

```python
kubectl_get(resource_type="roles", namespace)
kubectl_get(resource_type="clusterroles")
kubectl_get(resource_type="roles", namespace)
kubectl_get(resource_type="clusterroles")
```

### Check Service Account Permissions

```python
kubectl_get(resource_type="serviceaccounts", namespace)
```

### Common RBAC Patterns

| Pattern | Risk Level | Check |
|---------|-----------|-------|
| cluster-admin binding | Critical | `kubectl_get(resource_type="clusterroles")` |
| Wildcard verbs (*) | High | Review role rules |
| secrets access | High | Check get/list on secrets |
| pod/exec | High | Allows container access |

See [RBAC-PATTERNS.md](RBAC-PATTERNS.md) for detailed patterns and remediation.

## Policy Enforcement

### Kyverno Policies

```python
get_policy_list(namespace)
get_policy_list()
get_policy(name, namespace)
```

### OPA Gatekeeper

```python
get_policy_list()
get_policy(kind, name)
get_policy_list()
```

### Common Policies to Enforce

| Policy | Purpose |
|--------|---------|
| Disallow privileged | Prevent root containers |
| Require resource limits | Prevent resource exhaustion |
| Restrict host namespaces | Isolate from node |
| Require labels | Ensure metadata |
| Allowed registries | Control image sources |

## Secret Management

### List Secrets

```python
kubectl_get(resource_type="secrets", namespace)
```

### Secret Best Practices

1. Use external secret managers (Vault, AWS SM)
2. Encrypt secrets at rest (EncryptionConfiguration)
3. Limit secret access via RBAC
4. Rotate secrets regularly

## Network Policies

### List Policies

```python
analyze_network_policies(namespace)
```

### Cilium Network Policies

```python
cilium_list_policies(namespace)
cilium_get_policy(name, namespace)
```

### Default Deny Template

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

## Security Scanning Workflow

1. **RBAC Audit**
   ```python
   kubectl_get(resource_type="clusterroles")
   kubectl_get(resource_type="roles", namespace)
   ```

2. **Policy Compliance**
   ```python
   get_policy_list()
   get_policy_list()
   ```

3. **Network Isolation**
   ```python
   analyze_network_policies(namespace)
   cilium_list_endpoints(namespace)
   ```

4. **Pod Security**
   ```python
   kubectl_get(resource_type="pods", namespace)
   kubectl_describe(name, namespace)
   ```

## Multi-Cluster Security

Audit across clusters:

```python
kubectl_get(resource_type="clusterroles", context="production")
kubectl_get(resource_type="clusterroles", context="staging")
```

## Automated Audit Script

For comprehensive security audit, see [scripts/audit-rbac.py](scripts/audit-rbac.py).

## Related Tools

- RBAC: `kubectl_get`, `kubectl_get`, `kubectl_get`
- Policy: `kyverno_*`, `gatekeeper_*`
- Network: `analyze_network_policies`, `cilium_policies_*`
- Istio: `istio_authorizationpolicies_list`, `istio_peerauthentications_list`

## Related Skills

- [k8s-policy](../k8s-policy/SKILL.md) - Policy management
- [k8s-cilium](../k8s-cilium/SKILL.md) - Cilium network security
