# Kubernetes Context Management

Patterns for managing multiple cluster contexts.

## Understanding Contexts

A kubeconfig context combines:
- **Cluster**: API server URL and CA certificate
- **User**: Authentication credentials
- **Namespace**: Default namespace (optional)

## Context Naming Conventions

### By Environment

```
production-us-east-1
production-eu-west-1
staging-us-east-1
development
```

### By Purpose

```
management-cluster
workload-cluster-1
workload-cluster-2
monitoring-cluster
```

### By Team

```
team-a-dev
team-a-prod
team-b-dev
platform-admin
```

## MCP Commands

```python
# List all contexts
list_contexts_tool()

# View kubeconfig (sanitized)
kubeconfig_view()
```

## Context in Every Command

All kubectl-mcp-server tools accept `context` parameter:

```python
# Explicit context (recommended)
get_pods(namespace="default", context="production")
get_pods(namespace="default", context="staging")

# Current context (implicit)
get_pods(namespace="default")
```

## Multi-Cluster Patterns

### Compare Environments

```python
# Get deployments from both clusters
prod_deps = get_deployments(namespace="app", context="production")
staging_deps = get_deployments(namespace="app", context="staging")
```

### Cross-Cluster Secret Sync

```python
# Read secret from source
secret = get_secrets(namespace="app", context="source-cluster")

# Apply to target (via manifest)
apply_manifest(secret_yaml, namespace="app", context="target-cluster")
```

### Parallel Health Checks

```python
contexts = ["prod-1", "prod-2", "staging"]
for ctx in contexts:
    nodes = get_nodes(context=ctx)
    pods = get_pods(namespace="kube-system", context=ctx)
    # Report status
```

### Rolling Deployment Across Clusters

```python
# Deploy to staging first
install_helm_chart(name="app", chart="./app",
                   namespace="prod", context="staging")

# Verify
get_pods(namespace="prod", label_selector="app=myapp", context="staging")

# Deploy to production regions sequentially
for region in ["us-east", "us-west", "eu-west"]:
    install_helm_chart(name="app", chart="./app",
                       namespace="prod", context=f"production-{region}")
    # Wait for healthy
    get_pods(namespace="prod", context=f"production-{region}")
```

## Access Control Per Context

### Separate Kubeconfigs

```bash
# Different files per environment
export KUBECONFIG=~/.kube/production.yaml
export KUBECONFIG=~/.kube/development.yaml
```

### Service Account Per Cluster

```python
# Different SAs for different access levels
# Production: read-only SA
get_pods(namespace="app", context="production-readonly")

# Development: full access SA
apply_manifest(manifest, namespace="app", context="development-admin")
```

## Cluster API Management

For managing cluster lifecycle:

```python
# List CAPI-managed clusters
capi_clusters_list_tool(namespace="capi-system")

# Get workload cluster kubeconfig
kubeconfig = capi_cluster_kubeconfig_tool(
    name="workload-cluster-1",
    namespace="capi-system"
)

# Use the kubeconfig to access workload cluster
# (save to file, add to contexts)
```

## Federation Patterns

### Kubefed Resources

Cross-cluster resource propagation with KubeFed.

### Cluster Mesh (Cilium)

```python
# Check Cilium cluster mesh status
cilium_nodes_list_tool(context="cluster-1")
cilium_nodes_list_tool(context="cluster-2")
```

### Multi-Cluster Service Mesh (Istio)

```python
istio_proxy_status_tool(context="primary")
istio_proxy_status_tool(context="remote")
```

## Best Practices

1. **Always Use Explicit Context**
   ```python
   # Good: explicit
   get_pods(context="production")

   # Risky: implicit
   get_pods()  # Which cluster?
   ```

2. **Naming Convention**
   - Consistent format: `<env>-<region>`
   - Short but descriptive

3. **Read-Only for Production**
   - Default production context: read-only
   - Separate admin context for changes

4. **Audit Cross-Cluster Operations**
   - Log which clusters are accessed
   - Track who made changes

5. **Separate Credentials**
   - Different SAs per environment
   - Shorter token lifetimes for prod

## Troubleshooting

### Context Not Found

```python
list_contexts_tool()
# Verify context name is correct
```

### Authentication Failure

```python
# Check credentials
# Token expired?
# Certificate valid?
```

### Network Issues

```
# API server reachable?
# VPN connected?
# Firewall rules?
```
