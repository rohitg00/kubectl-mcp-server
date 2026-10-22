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

### Option 3: kagent Integration (AI Agents)

[kagent](https://github.com/kagent-dev/kagent) is a Kubernetes-native framework for building AI agents (CNCF project). Register kubectl-mcp-server as a ToolServer to give your agents 121 Kubernetes management tools.

```bash
# Install kagent
brew install kagent
# Or: curl https://raw.githubusercontent.com/kagent-dev/kagent/refs/heads/main/scripts/get-kagent | bash

# Install kagent to cluster with demo agents
export OPENAI_API_KEY="your-api-key"
kagent install --profile demo

# Register kubectl-mcp-server as a ToolServer (stdio - uses npx)
kubectl apply -f kagent/toolserver-stdio.yaml

# Or if kubectl-mcp-server is deployed in K8s (HTTP transport)
kubectl apply -f kagent/toolserver-http.yaml

# Optionally create a K8s admin agent
kubectl apply -f kagent/agent-k8s-admin.yaml

# Open kagent dashboard
kagent dashboard
```

See [kagent/](kagent/) for ToolServer manifests and example agents.

### Option 4: Helm Chart

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
├── kagent/                  # kagent AI agent integration
│   ├── toolserver-stdio.yaml   # ToolServer (stdio/npx transport)
│   ├── toolserver-http.yaml    # ToolServer (HTTP transport)
│   └── agent-k8s-admin.yaml    # Example K8s admin agent
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
| `MCP_ALLOW_UNAUTHENTICATED` | `false` | Required to listen on a pod IP without OAuth |
| `MCP_AUTH_ENABLED` / `MCP_AUTH_ISSUER` | - | OAuth 2.1 token validation (preferred over the flag above) |
| `MCP_SAFETY_MODE` | `normal` | `read-only`, `disable-destructive`, `confirm`, `normal` |

### Transport Modes

The deployment serves stateless Streamable HTTP at `/mcp` in read-only mode. Every request is
self-contained (MCP 2026-07-28), so you can scale replicas behind the Service without sticky
sessions. `sse` still works but is deprecated by the MCP spec.

```yaml
args:
  - "--transport"
  - "http"      # Options: stdio, http, streamable-http, sse (deprecated)
  - "--port"
  - "8000"
  - "--read-only"
```

### RBAC Permissions

The included RBAC configuration grants **read-only access** to most Kubernetes resources and **no access to Secrets**. For write operations (apply, delete, scale), add write permissions to `rbac.yaml` and drop `--read-only`.

## Accessing the Server

### Port Forward (Development)

```bash
kubectl port-forward -n kubectl-mcp svc/kubectl-mcp-server 8000:8000
```

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

1. **Authentication**: the manifest sets `MCP_ALLOW_UNAUTHENTICATED=true`. Any pod that can reach the Service acts with this ServiceAccount, so either add a NetworkPolicy that only admits your agent, or configure OAuth (`MCP_AUTH_ENABLED`, `MCP_AUTH_ISSUER`) and remove the flag
2. **RBAC**: read-only, without Secrets
3. **Safety mode**: `--read-only` hides every tool that changes state; use `--disable-destructive` or `--confirm-destructive` if you grant write RBAC
4. **Secrets**: Secret values in tool output are redacted (`MCP_MASK_SECRETS=false` disables)
