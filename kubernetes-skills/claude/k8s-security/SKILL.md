---
name: k8s-security
description: Audit Kubernetes RBAC, enforce policies, and manage secrets. Use for security reviews, permission audits, policy enforcement with Kyverno/Gatekeeper, and secret management.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 10
  category: security
---

# Kubernetes Security

Security auditing, RBAC management, and policy enforcement using kubectl-mcp-server tools.

## When to Apply

Use this skill when:
- User mentions: "security", "RBAC", "permissions", "policy", "audit", "secrets"
- Operations: security review, permission check, policy enforcement
- Keywords: "who can", "access control", "compliance", "vulnerable"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check cluster-admin bindings first | CRITICAL | `get_cluster_role_bindings` |
| 2 | Audit secrets access permissions | CRITICAL | Review role rules |
| 3 | Verify network isolation | HIGH | `get_network_policies` |
| 4 | Check policy compliance | HIGH | `kyverno_*`, `gatekeeper_*` |
| 5 | Review pod security contexts | MEDIUM | `describe_pod` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List roles | `get_roles` | `get_roles(namespace)` |
| Cluster roles | `get_cluster_roles` | `get_cluster_roles()` |
| Role bindings | `get_role_bindings` | `get_role_bindings(namespace)` |
| Service accounts | `get_service_accounts` | `get_service_accounts(namespace)` |
| Kyverno policies | `kyverno_clusterpolicies_list_tool` | `kyverno_clusterpolicies_list_tool()` |

## RBAC Auditing

### List Roles and Bindings

```python
get_roles(namespace)
get_cluster_roles()
get_role_bindings(namespace)
get_cluster_role_bindings()
```

### Check Service Account Permissions

```python
get_service_accounts(namespace)
```

### Common RBAC Patterns

| Pattern | Risk Level | Check |
|---------|-----------|-------|
| cluster-admin binding | Critical | `get_cluster_role_bindings()` |
| Wildcard verbs (*) | High | Review role rules |
| secrets access | High | Check get/list on secrets |
| pod/exec | High | Allows container access |

See [RBAC-PATTERNS.md](RBAC-PATTERNS.md) for detailed patterns and remediation.

## Policy Enforcement

### Kyverno Policies

```python
kyverno_policies_list_tool(namespace)
kyverno_clusterpolicies_list_tool()
kyverno_policy_get_tool(name, namespace)
```

### OPA Gatekeeper

```python
gatekeeper_constraints_list_tool()
gatekeeper_constraint_get_tool(kind, name)
gatekeeper_templates_list_tool()
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
get_secrets(namespace)
```

### Secret Best Practices

1. Use external secret managers (Vault, AWS SM)
2. Encrypt secrets at rest (EncryptionConfiguration)
3. Limit secret access via RBAC
4. Rotate secrets regularly

## Network Policies

### List Policies

```python
get_network_policies(namespace)
```

### Cilium Network Policies

```python
cilium_policies_list_tool(namespace)
cilium_policy_get_tool(name, namespace)
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
   get_cluster_role_bindings()
   get_roles(namespace)
   ```

2. **Policy Compliance**
   ```python
   kyverno_clusterpolicies_list_tool()
   gatekeeper_constraints_list_tool()
   ```

3. **Network Isolation**
   ```python
   get_network_policies(namespace)
   cilium_endpoints_list_tool(namespace)
   ```

4. **Pod Security**
   ```python
   get_pods(namespace)
   describe_pod(name, namespace)
   ```

## Multi-Cluster Security

Audit across clusters:

```python
get_cluster_role_bindings(context="production")
get_cluster_role_bindings(context="staging")
```

## Automated Audit Script

For comprehensive security audit, see [scripts/audit-rbac.py](scripts/audit-rbac.py).

## Related Tools

- RBAC: `get_roles`, `get_cluster_roles`, `get_role_bindings`
- Policy: `kyverno_*`, `gatekeeper_*`
- Network: `get_network_policies`, `cilium_policies_*`
- Istio: `istio_authorizationpolicies_list_tool`, `istio_peerauthentications_list_tool`

## Related Skills

- [k8s-policy](../k8s-policy/SKILL.md) - Policy management
- [k8s-cilium](../k8s-cilium/SKILL.md) - Cilium network security
