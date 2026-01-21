# Kubectl MCP Server

A Model Context Protocol (MCP) server for Kubernetes that enables AI assistants like Claude, Cursor, and others to interact with Kubernetes clusters through natural language.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://github.com/modelcontextprotocol/modelcontextprotocol)
[![PyPI version](https://badge.fury.io/py/kubectl-mcp-tool.svg)](https://pypi.org/project/kubectl-mcp-tool/)
[![npm version](https://badge.fury.io/js/kubectl-mcp-server.svg)](https://www.npmjs.com/package/kubectl-mcp-server)
[![Docker](https://img.shields.io/docker/pulls/rohitghumare64/kubectl-mcp-server.svg)](https://hub.docker.com/r/rohitghumare64/kubectl-mcp-server)

## Live Demos

### Claude Desktop
![Claude MCP](./docs/claude/claude-mcp.gif)

### Cursor AI
![Cursor MCP](./docs/cursor/cursor-mcp.gif)

### Windsurf
![Windsurf MCP](./docs/windsurf/windsurf-mcp.gif)

## Features

### 72 MCP Tools for Complete Kubernetes Management

| Category | Tools |
|----------|-------|
| **Pods** | `get_pods`, `get_logs`, `get_pod_events`, `check_pod_health`, `exec_in_pod`, `cleanup_pods`, `get_pod_conditions`, `get_previous_logs` |
| **Deployments** | `get_deployments`, `create_deployment`, `scale_deployment`, `kubectl_rollout`, `restart_deployment` |
| **Workloads** | `get_statefulsets`, `get_daemonsets`, `get_jobs`, `get_replicasets` |
| **Services & Networking** | `get_services`, `get_ingress`, `get_endpoints`, `diagnose_network_connectivity`, `check_dns_resolution`, `trace_service_chain` |
| **Storage** | `get_persistent_volumes`, `get_pvcs`, `get_storage_classes` |
| **Config** | `get_configmaps`, `get_secrets`, `get_resource_quotas`, `get_limit_ranges` |
| **Cluster** | `get_nodes`, `get_namespaces`, `get_cluster_info`, `get_cluster_version`, `health_check`, `get_node_metrics`, `get_pod_metrics` |
| **RBAC & Security** | `get_rbac_roles`, `get_cluster_roles`, `get_service_accounts`, `audit_rbac_permissions`, `check_secrets_security`, `get_pod_security_info`, `get_admission_webhooks` |
| **CRDs** | `get_crds`, `get_priority_classes` |
| **Helm** | `install_helm_chart`, `upgrade_helm_chart`, `uninstall_helm_chart`, `helm_template`, `helm_template_apply` |
| **Context** | `get_current_context`, `switch_context`, `list_contexts`, `list_kubeconfig_contexts` |
| **Diagnostics** | `diagnose_pod_crash`, `detect_pending_pods`, `get_evicted_pods`, `compare_namespaces` |
| **Operations** | `kubectl_apply`, `kubectl_create`, `kubectl_describe`, `kubectl_patch`, `delete_resource`, `kubectl_cp`, `backup_resource`, `label_resource`, `annotate_resource`, `taint_node`, `wait_for_condition` |
| **Autoscaling** | `get_hpa`, `get_pdb` |
| **Advanced** | `kubectl_generic`, `kubectl_explain`, `get_api_resources`, `port_forward`, `get_resource_usage`, `node_management` |

### Key Capabilities

- **Multi-Transport Support**: stdio, SSE, HTTP/streamable-http
- **AI Assistant Integration**: Claude Desktop, Claude Code, Cursor, Windsurf
- **Multi-Cluster**: Context switching between clusters
- **Security**: Non-destructive mode, secrets masking, RBAC validation
- **Diagnostics**: Pod crash analysis, network connectivity testing, DNS resolution checks
- **Helm v3**: Full Helm chart lifecycle management

## Installation

### Prerequisites
- Python 3.9+
- kubectl CLI installed and configured
- Access to a Kubernetes cluster

### npm / npx (Recommended)

```bash
# Run directly without installation
npx kubectl-mcp-server

# Or install globally
npm install -g kubectl-mcp-server
```

### pip (Python)

```bash
pip install kubectl-mcp-tool
```

### Docker

```bash
# Pull the latest image
docker pull rohitghumare64/kubectl-mcp-server:latest

# Run with stdio transport
docker run -i -v $HOME/.kube:/root/.kube:ro rohitghumare64/kubectl-mcp-server:latest

# Run with SSE transport
docker run -p 8000:8000 -v $HOME/.kube:/root/.kube:ro rohitghumare64/kubectl-mcp-server:latest --transport sse
```

## Quick Start

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "kubectl-mcp-server"]
    }
  }
}
```

### Claude Code

Add to `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "kubectl-mcp-server"]
    }
  }
}
```

### Cursor AI

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "kubectl-mcp-server"]
    }
  }
}
```

### Windsurf

Add to `~/.config/windsurf/mcp.json`:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "kubectl-mcp-server"]
    }
  }
}
```

### Using Python Directly

If you prefer Python over npx:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.mcp_server"],
      "env": {
        "KUBECONFIG": "/path/to/.kube/config"
      }
    }
  }
}
```

## Transport Modes

```bash
# stdio (default) - for Claude Desktop, Cursor, etc.
python -m kubectl_mcp_tool.mcp_server

# SSE - Server-Sent Events
python -m kubectl_mcp_tool.mcp_server --transport sse --port 8000

# HTTP
python -m kubectl_mcp_tool.mcp_server --transport http --port 8000
```

### Options
- `--transport`: `stdio`, `sse`, `http`, `streamable-http` (default: `stdio`)
- `--host`: Host to bind (default: `0.0.0.0`)
- `--port`: Port for network transports (default: `8000`)
- `--non-destructive`: Block destructive operations (delete, apply, create)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `KUBECONFIG` | Path to kubeconfig file (default: `~/.kube/config`) |
| `MCP_DEBUG` | Set to `1` for verbose logging |
| `MCP_LOG_FILE` | Path to log file |

## Docker MCP Toolkit

Compatible with [Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/):

```bash
# Add server
docker mcp server add kubectl-mcp-server mcp/kubectl-mcp-server:latest

# Configure kubeconfig
docker mcp server configure kubectl-mcp-server --volume "$HOME/.kube:/root/.kube:ro"

# Enable and connect
docker mcp server enable kubectl-mcp-server
docker mcp client connect claude
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AI Assistant  │────▶│   MCP Server     │────▶│  Kubernetes API │
│ (Claude/Cursor) │◀────│ (kubectl-mcp)    │◀────│    (kubectl)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

The MCP server implements the [Model Context Protocol](https://github.com/modelcontextprotocol/spec), translating natural language requests into kubectl operations.

## Multi-Cluster Support

```bash
# List contexts
list_contexts

# Switch cluster
switch_context --context_name production

# Get context details
get_context_details --context_name staging
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [PyPI Package](https://pypi.org/project/kubectl-mcp-tool/)
- [npm Package](https://www.npmjs.com/package/kubectl-mcp-server)
- [Docker Hub](https://hub.docker.com/r/rohitghumare64/kubectl-mcp-server)
- [GitHub Issues](https://github.com/rohitg00/kubectl-mcp-server/issues)
