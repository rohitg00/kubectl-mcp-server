---
name: k8s-security
description: Audit Kubernetes RBAC, enforce policies, and manage secrets. Use for security reviews, permission audits, policy enforcement with Kyverno/Gatekeeper, and secret management.
---

# Kubernetes Security

Security auditing, RBAC management, and policy enforcement using kubectl-mcp-server tools.

## RBAC Auditing

### List Roles and Bindings
```
get_roles(namespace)           # Namespace-scoped roles
get_cluster_roles()            # Cluster-wide roles
get_role_bindings(namespace)   # Namespace bindings
get_cluster_role_bindings()    # Cluster-wide bindings
```

### Check Service Account Permissions
```
get_service_accounts(namespace)
# Then examine role bindings for the SA
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
```
kyverno_policies_list_tool(namespace)
kyverno_clusterpolicies_list_tool()
kyverno_policy_get_tool(name, namespace)
```

### OPA Gatekeeper
```
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
```
get_secrets(namespace)  # Lists names only, not values
```

### Secret Best Practices
1. Use external secret managers (Vault, AWS SM)
2. Encrypt secrets at rest (EncryptionConfiguration)
3. Limit secret access via RBAC
4. Rotate secrets regularly

## Network Policies

### List Policies
```
get_network_policies(namespace)
```

### Cilium Network Policies
```
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
   ```
   get_cluster_role_bindings()  # Find cluster-admin users
   get_roles(namespace)         # Review namespace permissions
   ```

2. **Policy Compliance**
   ```
   kyverno_clusterpolicies_list_tool()  # Check policy coverage
   gatekeeper_constraints_list_tool()    # Check constraint status
   ```

3. **Network Isolation**
   ```
   get_network_policies(namespace)       # Verify policies exist
   cilium_endpoints_list_tool(namespace) # Check endpoint labels
   ```

4. **Pod Security**
   ```
   get_pods(namespace)
   describe_pod(name, namespace)  # Check securityContext
   ```

## Multi-Cluster Security

Audit across clusters:
```
# Production cluster
get_cluster_role_bindings(context="production")

# Staging cluster
get_cluster_role_bindings(context="staging")
```

## Automated Audit Script

For comprehensive security audit, see [scripts/audit-rbac.py](scripts/audit-rbac.py).

## Related Tools

- RBAC: `get_roles`, `get_cluster_roles`, `get_role_bindings`
- Policy: `kyverno_*`, `gatekeeper_*`
- Network: `get_network_policies`, `cilium_policies_*`
- Istio: `istio_authorizationpolicies_list_tool`, `istio_peerauthentications_list_tool`
