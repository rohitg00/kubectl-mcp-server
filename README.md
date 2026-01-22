# Kubectl MCP Server

A Model Context Protocol (MCP) server for Kubernetes that enables AI assistants like Claude, Cursor, and others to interact with Kubernetes clusters through natural language.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![PyPI](https://img.shields.io/pypi/v/kubectl-mcp-tool?color=blue&label=PyPI)](https://pypi.org/project/kubectl-mcp-tool/)
[![npm](https://img.shields.io/npm/v/kubectl-mcp-server?color=green&label=npm)](https://www.npmjs.com/package/kubectl-mcp-server)
[![Docker](https://img.shields.io/docker/pulls/rohitghumare64/kubectl-mcp-server.svg)](https://hub.docker.com/r/rohitghumare64/kubectl-mcp-server)
[![Tests](https://img.shields.io/badge/tests-138%20passed-success)](https://github.com/rohitg00/kubectl-mcp-server)

## MCP Client Compatibility

Works with all MCP-compatible AI assistants:

| Client | Status | Client | Status |
|--------|--------|--------|--------|
| Claude Desktop | ✅ Native | Claude Code | ✅ Native |
| Cursor | ✅ Native | Windsurf | ✅ Native |
| GitHub Copilot | ✅ Native | OpenAI Codex | ✅ Native |
| Gemini CLI | ✅ Native | Goose | ✅ Native |
| Roo Code | ✅ Native | Kilo Code | ✅ Native |
| Amp | ✅ Native | Trae | ✅ Native |
| OpenCode | ✅ Native | Kiro CLI | ✅ Native |
| Antigravity | ✅ Native | Clawdbot | ✅ Native |
| Droid (Factory) | ✅ Native | Any MCP Client | ✅ Compatible |

## Live Demos

### Claude Desktop
![Claude MCP](./docs/claude/claude-mcp.gif)

### Cursor AI
![Cursor MCP](./docs/cursor/cursor-mcp.gif)

### Windsurf
![Windsurf MCP](./docs/windsurf/windsurf-mcp.gif)

## Features

### 121 MCP Tools for Complete Kubernetes Management

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
| **Helm Releases** | `helm_list`, `helm_status`, `helm_history`, `helm_get_values`, `helm_get_manifest`, `helm_get_notes`, `helm_get_hooks`, `helm_get_all` |
| **Helm Charts** | `helm_show_chart`, `helm_show_values`, `helm_show_readme`, `helm_show_crds`, `helm_show_all`, `helm_search_repo`, `helm_search_hub` |
| **Helm Repos** | `helm_repo_list`, `helm_repo_add`, `helm_repo_remove`, `helm_repo_update` |
| **Helm Operations** | `install_helm_chart`, `upgrade_helm_chart`, `uninstall_helm_chart`, `helm_rollback`, `helm_test`, `helm_template`, `helm_template_apply` |
| **Helm Development** | `helm_create`, `helm_lint`, `helm_package`, `helm_pull`, `helm_dependency_list`, `helm_dependency_update`, `helm_dependency_build`, `helm_version`, `helm_env` |
| **Context** | `get_current_context`, `switch_context`, `list_contexts`, `list_kubeconfig_contexts` |
| **Diagnostics** | `diagnose_pod_crash`, `detect_pending_pods`, `get_evicted_pods`, `compare_namespaces` |
| **Operations** | `kubectl_apply`, `kubectl_create`, `kubectl_describe`, `kubectl_patch`, `delete_resource`, `kubectl_cp`, `backup_resource`, `label_resource`, `annotate_resource`, `taint_node`, `wait_for_condition` |
| **Autoscaling** | `get_hpa`, `get_pdb` |
| **Cost Optimization** | `get_resource_recommendations`, `get_idle_resources`, `get_resource_quotas_usage`, `get_cost_analysis`, `get_overprovisioned_resources`, `get_resource_trends`, `get_namespace_cost_allocation`, `optimize_resource_requests` |
| **Advanced** | `kubectl_generic`, `kubectl_explain`, `get_api_resources`, `port_forward`, `get_resource_usage`, `node_management` |

### MCP Resources (FastMCP 3)

Access Kubernetes data as browsable resources:

| Resource URI | Description |
|--------------|-------------|
| `kubeconfig://contexts` | List all available kubectl contexts |
| `kubeconfig://current-context` | Get current active context |
| `namespace://current` | Get current namespace |
| `namespace://list` | List all namespaces |
| `cluster://info` | Get cluster information |
| `cluster://nodes` | Get detailed node information |
| `cluster://version` | Get Kubernetes version |
| `cluster://api-resources` | List available API resources |
| `manifest://deployments/{ns}/{name}` | Get deployment YAML |
| `manifest://services/{ns}/{name}` | Get service YAML |
| `manifest://pods/{ns}/{name}` | Get pod YAML |
| `manifest://configmaps/{ns}/{name}` | Get ConfigMap YAML |
| `manifest://secrets/{ns}/{name}` | Get secret YAML (data masked) |
| `manifest://ingresses/{ns}/{name}` | Get ingress YAML |

### MCP Prompts (FastMCP 3)

Pre-built workflow prompts for common Kubernetes operations:

| Prompt | Description |
|--------|-------------|
| `troubleshoot_workload` | Comprehensive troubleshooting guide for pods/deployments |
| `deploy_application` | Step-by-step deployment workflow |
| `security_audit` | Security scanning and RBAC analysis workflow |
| `cost_optimization` | Resource optimization and cost analysis workflow |
| `disaster_recovery` | Backup and recovery planning workflow |
| `debug_networking` | Network debugging for services and connectivity |
| `scale_application` | Scaling guide with HPA/VPA best practices |
| `upgrade_cluster` | Kubernetes cluster upgrade planning |

### Key Capabilities

- **Multi-Transport Support**: stdio, SSE, HTTP/streamable-http
- **AI Assistant Integration**: Claude Desktop, Claude Code, Cursor, Windsurf
- **Multi-Cluster**: Context switching between clusters
- **Security**: Non-destructive mode, secrets masking, RBAC validation
- **Diagnostics**: Pod crash analysis, network connectivity testing, DNS resolution checks
- **Helm v3**: Full Helm chart lifecycle management
- **Cost Optimization**: Resource recommendations, idle resource detection, usage analysis
- **FastMCP 3**: MCP Resources and Prompts for enhanced AI workflows

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

### GitHub Copilot (VS Code)

Add to VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "kubernetes": {
        "command": "npx",
        "args": ["-y", "kubectl-mcp-server"]
      }
    }
  }
}
```

### Goose

Add to `~/.config/goose/config.yaml`:

```yaml
extensions:
  kubernetes:
    command: npx
    args:
      - -y
      - kubectl-mcp-server
```

### Gemini CLI

Add to `~/.gemini/settings.json`:

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

### Roo Code / Kilo Code

Add to `~/.config/roo-code/mcp.json` or `~/.config/kilo-code/mcp.json`:

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

## Kubernetes Deployment

Deploy kubectl-mcp-server directly in your Kubernetes cluster for centralized access.

### kMCP Deployment (Recommended)

[kMCP](https://github.com/kagent-dev/kmcp) is a development platform and control plane for MCP servers. See [kMCP quickstart](https://kagent.dev/docs/kmcp/quickstart).

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

# Or deploy using our Docker image with the MCPServer manifest
kmcp deploy --file deploy/kmcp/kmcp.yaml --image rohitghumare64/kubectl-mcp-server:latest
```

### Standard Kubernetes Deployment

Deploy using kubectl/kustomize without kMCP:

```bash
# Using kustomize (recommended)
kubectl apply -k deploy/kubernetes/

# Or apply individual manifests
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/rbac.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml

# Access via port-forward
kubectl port-forward -n kubectl-mcp svc/kubectl-mcp-server 8000:8000
```

### MCPServer Custom Resource

For kMCP deployments, apply this MCPServer resource:

```yaml
apiVersion: kagent.dev/v1alpha1
kind: MCPServer
metadata:
  name: kubectl-mcp-server
spec:
  deployment:
    image: "rohitghumare64/kubectl-mcp-server:latest"
    port: 8000
  transportType: http
  httpTransport:
    targetPort: 8000
    path: /mcp
```

See [deploy/](deploy/) for full manifests and configuration options.

### kagent Integration (AI Agents)

[kagent](https://github.com/kagent-dev/kagent) is a Kubernetes-native AI agent framework (CNCF project). Register kubectl-mcp-server as a ToolServer to give your agents 121 K8s management tools.

```bash
# Install kagent
brew install kagent
kagent install --profile demo

# Register kubectl-mcp-server as a ToolServer
kubectl apply -f deploy/kagent/toolserver-stdio.yaml

# Open kagent dashboard and chat with your K8s agent
kagent dashboard
```

See [kagent quickstart](https://kagent.dev/docs/kagent/getting-started/quickstart) for full documentation.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AI Assistant  │────▶│   MCP Server     │────▶│  Kubernetes API │
│ (Claude/Cursor) │◀────│ (kubectl-mcp)    │◀────│    (kubectl)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

The MCP server implements the [Model Context Protocol](https://github.com/modelcontextprotocol/spec), translating natural language requests into kubectl operations.

### Modular Structure

```
kubectl_mcp_tool/
├── mcp_server.py          # Main server (FastMCP, transports)
├── tools/                  # 121 MCP tools organized by category
│   ├── pods.py            # Pod management & diagnostics
│   ├── deployments.py     # Deployments, StatefulSets, DaemonSets
│   ├── core.py            # Namespaces, ConfigMaps, Secrets
│   ├── cluster.py         # Context/cluster management
│   ├── networking.py      # Services, Ingress, NetworkPolicies
│   ├── storage.py         # PVCs, StorageClasses, PVs
│   ├── security.py        # RBAC, ServiceAccounts, PodSecurity
│   ├── helm.py            # Complete Helm v3 operations
│   ├── operations.py      # kubectl apply/patch/describe/etc
│   ├── diagnostics.py     # Metrics, namespace comparison
│   └── cost.py            # Resource optimization & cost analysis
├── resources/              # 8 MCP Resources for data exposure
├── prompts/                # 8 MCP Prompts for workflows
└── cli/                    # CLI interface
```

## Multi-Cluster Support

```bash
# List contexts
list_contexts

# Switch cluster
switch_context --context_name production

# Get context details
get_context_details --context_name staging
```

## Development & Testing

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage
pytest tests/ --cov=kubectl_mcp_tool --cov-report=html

# Run only unit tests
pytest tests/ -v -m unit
```

### Test Structure

```
tests/
├── __init__.py          # Test package
├── conftest.py          # Shared fixtures and mocks
├── test_tools.py        # Unit tests for 121 MCP tools
├── test_resources.py    # Tests for 8 MCP Resources
├── test_prompts.py      # Tests for 8 MCP Prompts
└── test_server.py       # Server initialization tests
```

**138 tests covering**: tool registration, resource exposure, prompt generation, server initialization, non-destructive mode, secret masking, error handling, and transport methods.

### Code Quality

```bash
# Format code
black kubectl_mcp_tool tests

# Sort imports
isort kubectl_mcp_tool tests

# Lint
flake8 kubectl_mcp_tool tests

# Type checking
mypy kubectl_mcp_tool
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
