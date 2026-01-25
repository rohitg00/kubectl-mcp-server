# RBAC Patterns and Anti-Patterns

Security patterns for Kubernetes RBAC configuration.

## Dangerous Patterns (Anti-Patterns)

### 1. Cluster-Admin for Everyone

```yaml
# DANGEROUS: Gives full cluster access
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-everyone
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: Group
  name: system:authenticated
```

**Detection:**
```
get_cluster_role_bindings()
# Look for cluster-admin bindings to groups/users
```

### 2. Wildcard Verbs

```yaml
# DANGEROUS: Allows all actions
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
```

**Detection:**
```
get_cluster_roles()
get_roles(namespace)
# Check for * in verbs
```

### 3. Secrets Access

```yaml
# RISKY: Can read all secrets
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
```

**Detection:**
```
get_cluster_roles()
# Check for secrets access
```

### 4. Pod Exec Access

```yaml
# RISKY: Can execute in containers
rules:
- apiGroups: [""]
  resources: ["pods/exec"]
  verbs: ["create"]
```

## Secure Patterns

### 1. Read-Only Viewer

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: namespace-viewer
rules:
- apiGroups: ["", "apps", "batch"]
  resources: ["pods", "deployments", "jobs", "services"]
  verbs: ["get", "list", "watch"]
```

### 2. Developer Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
rules:
# Read most resources
- apiGroups: ["", "apps"]
  resources: ["pods", "deployments", "services", "configmaps"]
  verbs: ["get", "list", "watch"]
# Manage deployments
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["create", "update", "patch", "delete"]
# Read logs
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
# Port-forward for debugging
- apiGroups: [""]
  resources: ["pods/portforward"]
  verbs: ["create"]
```

### 3. CI/CD Service Account

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ci-deployer
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "update", "patch"]
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "create", "update"]
  resourceNames: ["app-config", "app-secrets"]  # Specific resources only
```

### 4. Namespace Admin (Not Cluster)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: namespace-admin
  namespace: my-namespace
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin  # Built-in admin (not cluster-admin)
subjects:
- kind: User
  name: team-lead
```

## Audit Checklist

### Using MCP Tools

```python
# 1. Check cluster-admin bindings
get_cluster_role_bindings()
# Flag: Any non-system bindings to cluster-admin

# 2. Review cluster roles
get_cluster_roles()
# Flag: Custom roles with wildcard access

# 3. Check namespace roles
for ns in namespaces:
    get_roles(namespace=ns)
    get_role_bindings(namespace=ns)
# Flag: Overly permissive custom roles

# 4. Review service accounts
get_service_accounts(namespace)
# Flag: Default SA used by workloads
```

### What to Look For

| Finding | Risk | Remediation |
|---------|------|-------------|
| cluster-admin to users | Critical | Create scoped roles |
| * verbs | High | Specify exact verbs |
| secrets access | High | Limit to specific secrets |
| pods/exec | Medium | Restrict to specific namespaces |
| Default SA with roles | Medium | Create dedicated SAs |

## Best Practices

1. **Principle of Least Privilege**
   - Only grant what's needed
   - Use namespace roles, not cluster roles

2. **Dedicated Service Accounts**
   - Don't use default SA
   - One SA per workload type

3. **Resource Names**
   - Limit to specific resources when possible
   - `resourceNames: ["specific-secret"]`

4. **Audit Regularly**
   - Review bindings monthly
   - Check for orphaned roles

5. **Namespace Isolation**
   - Different teams = different namespaces
   - RoleBindings per namespace
