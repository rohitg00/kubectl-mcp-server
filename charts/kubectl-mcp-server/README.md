# kubectl-mcp-server Helm Chart

A Helm chart for deploying kubectl-mcp-server - a Model Context Protocol (MCP) server for Kubernetes with 220+ tools, 8 resources, and 8 prompts.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+

## Installation

```bash
# Add the repository (if published to a Helm repository)
helm repo add kubectl-mcp https://rohitg00.github.io/kubectl-mcp-server

# Install the chart
helm install kubectl-mcp kubectl-mcp/kubectl-mcp-server

# Or install from local directory
helm install kubectl-mcp ./charts/kubectl-mcp-server
```

## Configuration

### Common Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `rohitghumare64/kubectl-mcp-server` |
| `image.tag` | Image tag | Chart appVersion |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |

### MCP Server Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcp.transport` | Transport mode (streamable-http, stdio) | `streamable-http` |
| `mcp.port` | Server port | `8000` |
| `mcp.debug` | Enable debug logging | `false` |
| `mcp.logFile` | Log to file path | `""` |

### Safety Mode Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `safety.mode` | Safety mode (normal, read-only, disable-destructive) | `normal` |

Safety modes:
- `normal`: All operations allowed (default)
- `read-only`: All write operations blocked
- `disable-destructive`: Only delete operations blocked

### RBAC Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `rbac.create` | Create ClusterRole and ClusterRoleBinding | `true` |
| `rbac.scope` | Permission scope (cluster, namespace) | `cluster` |
| `rbac.namespaces` | Namespaces for namespace-scoped access | `[]` |

### Browser Tools Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `browser.enabled` | Enable browser automation tools | `false` |
| `browser.provider` | Cloud provider (local, browserbase, browseruse) | `local` |
| `browser.browserbase.apiKey` | Browserbase API key | `""` |
| `browser.browserbase.projectId` | Browserbase project ID | `""` |
| `browser.browseruse.apiKey` | Browser Use API key | `""` |

### Metrics Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `metrics.enabled` | Enable Prometheus metrics | `false` |
| `metrics.serviceMonitor.enabled` | Create ServiceMonitor | `false` |
| `metrics.serviceMonitor.interval` | Scrape interval | `30s` |

### Service Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8000` |

### Ingress Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `""` |
| `ingress.hosts` | Ingress hosts | See values.yaml |

### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `128Mi` |

### Pod Disruption Budget

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podDisruptionBudget.enabled` | Enable PDB | `false` |
| `podDisruptionBudget.minAvailable` | Minimum available pods | `1` |

## Examples

### Read-Only Mode

Deploy in read-only mode for safe cluster exploration:

```bash
helm install kubectl-mcp ./charts/kubectl-mcp-server \
  --set safety.mode=read-only
```

### With Browser Tools

Enable browser automation tools with Browserbase:

```bash
helm install kubectl-mcp ./charts/kubectl-mcp-server \
  --set browser.enabled=true \
  --set browser.provider=browserbase \
  --set browser.browserbase.apiKey=YOUR_API_KEY \
  --set browser.browserbase.projectId=YOUR_PROJECT_ID
```

### With Prometheus Metrics

Enable metrics and ServiceMonitor:

```bash
helm install kubectl-mcp ./charts/kubectl-mcp-server \
  --set metrics.enabled=true \
  --set metrics.serviceMonitor.enabled=true
```

### High Availability

Deploy with multiple replicas and PDB:

```bash
helm install kubectl-mcp ./charts/kubectl-mcp-server \
  --set replicaCount=3 \
  --set podDisruptionBudget.enabled=true \
  --set podDisruptionBudget.minAvailable=2
```

## Connecting to the MCP Server

After installation, use port-forward to access the server:

```bash
kubectl port-forward svc/kubectl-mcp-kubectl-mcp-server 8000:8000
```

Configure your MCP client to connect to:
```
http://localhost:8000/mcp
```

## Uninstallation

```bash
helm uninstall kubectl-mcp
```

## License

MIT License - see [LICENSE](https://github.com/rohitg00/kubectl-mcp-server/blob/main/LICENSE)
