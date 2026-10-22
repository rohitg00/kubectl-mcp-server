# kubectl-mcp-server Helm Chart

Deploys kubectl-mcp-server, a stateless Model Context Protocol server for Kubernetes (MCP 2026-07-28, with automatic fallback for older clients). Streamable HTTP is served at `/mcp`; every request is self-contained, so replicas scale behind a plain Service without sticky sessions.

## Prerequisites

- Kubernetes 1.25+
- Helm 3.8+

## Installation

The chart refuses to render without an authentication decision, because the server acts with its ServiceAccount's permissions for anyone who can reach it.

```bash
# With OAuth 2.1 (recommended)
helm install kubectl-mcp ./charts/kubectl-mcp-server \
  --set auth.enabled=true \
  --set auth.issuer=https://idp.example.com \
  --set auth.resourceUrl=https://kubectl-mcp.example.com/mcp

# Without OAuth, when a NetworkPolicy or service mesh already restricts callers
helm install kubectl-mcp ./charts/kubectl-mcp-server \
  --set mcp.allowUnauthenticated=true
```

## Configuration

### MCP server

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcp.transport` | `http` (stateless Streamable HTTP) or `sse` (deprecated) | `http` |
| `mcp.port` | Container port | `8000` |
| `mcp.allowUnauthenticated` | Serve without OAuth | `false` |
| `mcp.requestStateKeySecret` | Secret with key `request-state-key` (>= 32 bytes) shared by replicas; needed for `safety.mode=confirm` with more than one replica | `""` |
| `mcp.debug` | Debug logging | `false` |
| `mcp.logFile` | Log file path | `""` |

### Authentication

| Parameter | Description | Default |
|-----------|-------------|---------|
| `auth.enabled` | Validate OAuth 2.1 bearer tokens (JWT via JWKS) | `false` |
| `auth.issuer` | Authorization server URL (required when enabled) | `""` |
| `auth.jwksUri` | JWKS endpoint | derived from issuer |
| `auth.audience` | Expected token audience | `kubectl-mcp-server` |
| `auth.requiredScopes` | Comma-separated scopes every token must carry | `mcp:tools` |
| `auth.resourceUrl` | Public URL advertised in RFC 9728 metadata | `""` |

Tokens carrying `mcp:tools` or `mcp:admin` can call every tool. Set `auth.requiredScopes=mcp:read` to issue narrower tokens: read-only tools then need `mcp:read` and tools that change state need `mcp:write`.

### Safety and RBAC

| Parameter | Description | Default |
|-----------|-------------|---------|
| `safety.mode` | `read-only`, `disable-destructive`, `confirm`, `normal` | `read-only` |
| `rbac.create` | Create ClusterRole and ClusterRoleBinding | `true` |
| `rbac.secrets` | Grant Secret access (read; write/delete outside read-only mode) | `false` |

`safety.mode` drives both the server and the ClusterRole: `read-only` hides every tool that changes state and grants only read verbs; `disable-destructive` adds create/update/patch; `confirm` and `normal` add delete. In `confirm` mode the user approves each destructive call (multi round-trip on 2026-07-28 clients, elicitation on older ones).

Secret values in tool output are redacted regardless of RBAC. Set `extraEnv` with `MCP_MASK_SECRETS=false` to disable.

### Service, ingress, scaling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Replicas (stateless, any count works) | `1` |
| `autoscaling.enabled` | HorizontalPodAutoscaler | `false` |
| `podDisruptionBudget.enabled` | PodDisruptionBudget | `false` |
| `service.type` / `service.port` | Service | `ClusterIP` / `8000` |
| `ingress.enabled` | Ingress | `false` |
| `metrics.serviceMonitor.enabled` | Prometheus ServiceMonitor for `/metrics` | `false` |
| `image.repository` / `image.tag` | Image | `rohitghumare64/kubectl-mcp-server` / appVersion |

The pod runs as UID 10001 with a read-only root filesystem; `/tmp` and `/home/mcp` are `emptyDir` volumes.

## Examples

Write access with per-call confirmation, three replicas:

```bash
kubectl create secret generic kubectl-mcp-rsk --from-literal=request-state-key="$(openssl rand -hex 32)"
helm install kubectl-mcp ./charts/kubectl-mcp-server \
  --set auth.enabled=true --set auth.issuer=https://idp.example.com \
  --set safety.mode=confirm \
  --set replicaCount=3 --set mcp.requestStateKeySecret=kubectl-mcp-rsk
```

## Connecting

```bash
kubectl port-forward svc/kubectl-mcp-kubectl-mcp-server 8000:8000
```

MCP endpoint: `http://localhost:8000/mcp`. Health: `/health`. Metrics: `/metrics`.

## Uninstallation

```bash
helm uninstall kubectl-mcp
```

## License

MIT License - see [LICENSE](https://github.com/rohitg00/kubectl-mcp-server/blob/main/LICENSE)
