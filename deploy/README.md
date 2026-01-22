# Kubernetes Deployment

This directory contains deployment manifests for running kubectl-mcp-server in Kubernetes.

## Deployment Options

### Option 1: kMCP (Recommended for MCP Ecosystem)

[kMCP](https://github.com/kagent-dev/kmcp) is a development platform and control plane for MCP servers that simplifies deployment to Kubernetes.

```bash
# Install kmcp CLI
curl -fsSL https://raw.githubusercontent.com/kagent-dev/kmcp/refs/heads/main/scripts/get-kmcp.sh | bash

# Install kmcp controller in your cluster
helm install kmcp-crds oci://ghcr.io/kagent-dev/kmcp/helm/kmcp-crds \
     --namespace kmcp-system --create-namespace
kmcp install

# Deploy kubectl-mcp-server using npx (easiest)
kmcp deploy package --deployment-name kubectl-mcp-server \
   --manager npx --args kubectl-mcp-server

# Or deploy using Docker image
kmcp deploy --file kmcp/kmcp.yaml --image rohitghumare64/kubectl-mcp-server:latest
```

See [kmcp/kmcp.yaml](kmcp/kmcp.yaml) for the MCPServer manifest.

### Option 2: Standard Kubernetes (kubectl/kustomize)

Deploy directly to Kubernetes without kMCP:

```bash
# Using kustomize (recommended)
kubectl apply -k kubernetes/

# Or apply individual manifests
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/rbac.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

### Option 3: Helm Chart

```bash
# Using Docker image directly with custom values
helm upgrade --install kubectl-mcp-server \
  --set image.repository=rohitghumare64/kubectl-mcp-server \
  --set image.tag=latest \
  --set service.port=8000 \
  ./helm  # Coming soon
```

## Directory Structure

```
deploy/
├── kmcp/                    # kMCP deployment manifests
│   └── kmcp.yaml           # MCPServer custom resource
├── kubernetes/              # Standard Kubernetes manifests
│   ├── namespace.yaml      # Namespace definition
│   ├── rbac.yaml           # ServiceAccount, ClusterRole, ClusterRoleBinding
│   ├── deployment.yaml     # Deployment with resource limits
│   ├── service.yaml        # ClusterIP and NodePort services
│   └── kustomization.yaml  # Kustomize configuration
└── README.md               # This file
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_DEBUG` | `0` | Set to `1` for verbose logging |
| `MCP_LOG_FILE` | - | Path to log file |

### Transport Modes

The deployment uses SSE transport by default. Modify the args in deployment.yaml:

```yaml
args:
  - "--transport"
  - "sse"      # Options: stdio, sse, http, streamable-http
  - "--port"
  - "8000"
```

### RBAC Permissions

The included RBAC configuration grants **read-only access** to most Kubernetes resources. For write operations (apply, delete, scale), you'll need to modify `rbac.yaml` to add write permissions.

## Accessing the Server

### Port Forward (Development)

```bash
kubectl port-forward -n kubectl-mcp svc/kubectl-mcp-server 8000:8000
```

### NodePort (Testing)

Access via `http://<node-ip>:30800`

### Ingress (Production)

Create an Ingress resource pointing to the `kubectl-mcp-server` service.

## Verify Deployment

```bash
# Check pods
kubectl get pods -n kubectl-mcp

# Check logs
kubectl logs -n kubectl-mcp -l app=kubectl-mcp-server

# Test health endpoint
kubectl port-forward -n kubectl-mcp svc/kubectl-mcp-server 8000:8000 &
curl http://localhost:8000/health
```

## Security Considerations

1. **RBAC**: The default configuration uses read-only permissions
2. **Non-destructive mode**: Add `--non-destructive` to args for extra safety
3. **Network Policies**: Consider adding NetworkPolicy to restrict access
4. **Secrets**: Secrets are masked in output by default
