# Claude Code Integration Guide

This guide explains how to use kubectl-mcp-server with [Claude Code](https://docs.anthropic.com/en/docs/claude-code), Anthropic's CLI tool for coding with Claude.

## Prerequisites

1. **Install kubectl-mcp-tool**:
   ```bash
   pip install kubectl-mcp-tool
   ```

2. **Install Claude Code**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

3. **Verify kubectl is configured**:
   ```bash
   kubectl cluster-info
   ```

## Configuration Methods

### Method 1: Using the MCP Configuration File

Create or edit the MCP configuration file at `~/.config/claude-code/mcp.json` (or `%APPDATA%\claude-code\mcp.json` on Windows):

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.mcp_server"],
      "env": {
        "KUBECONFIG": "/path/to/your/.kube/config"
      }
    }
  }
}
```

### Method 2: Using Environment Variables

Set the following environment variables before running Claude Code:

```bash
export KUBECONFIG="$HOME/.kube/config"
export MCP_LOG_FILE="/tmp/kubectl-mcp.log"
export MCP_DEBUG="1"
```

### Method 3: Project-Level Configuration

Create a `.mcp.json` file in your project root:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.mcp_server"],
      "env": {
        "KUBECONFIG": "${HOME}/.kube/config"
      }
    }
  }
}
```

## Using with Claude Code

Once configured, you can use natural language to interact with your Kubernetes cluster:

```bash
# Start Claude Code in your project
claude-code

# Then ask questions like:
# "List all pods in the default namespace"
# "Show me the deployments in production"
# "Get logs from the nginx pod"
# "Scale the web deployment to 3 replicas"
```

## Available Tools

The kubectl-mcp-server provides the following tools to Claude Code:

### Core Operations
- `get_pods` - List pods in a namespace or all namespaces
- `get_namespaces` - List all namespaces
- `get_services` - List services
- `get_deployments` - List deployments
- `get_nodes` - List cluster nodes
- `get_configmaps` - List ConfigMaps
- `get_secrets` - List Secrets (metadata only)

### Context Management (Multi-Cluster Support)
- `list_contexts` - List all available kubeconfig contexts
- `get_current_context` - Get the current context
- `switch_context` - Switch to a different context
- `get_context_details` - Get details about a specific context
- `set_namespace_for_context` - Set default namespace for a context
- `get_cluster_info` - Get cluster information

### Helm Operations
- `install_helm_chart` - Install a Helm chart
- `upgrade_helm_chart` - Upgrade a Helm release
- `uninstall_helm_chart` - Uninstall a Helm release

### Monitoring & Diagnostics
- `health_check` - Check cluster health
- `get_resource_usage` - Get resource usage (kubectl top)
- `get_events` - Get cluster events
- `get_pod_events` - Get events for a specific pod
- `check_pod_health` - Check pod health status
- `get_logs` - Get pod logs

### Resource Management
- `create_deployment` - Create a new deployment
- `scale_deployment` - Scale a deployment
- `delete_resource` - Delete a resource
- `port_forward` - Forward a local port to a pod

### RBAC & Security
- `get_rbac_roles` - List RBAC roles
- `get_cluster_roles` - List cluster roles

### Reference
- `kubectl_explain` - Explain a Kubernetes resource
- `get_api_resources` - List API resources

## Troubleshooting

### Server Not Starting

1. **Check Python path**:
   ```bash
   which python
   python -m kubectl_mcp_tool.mcp_server --help
   ```

2. **Verify installation**:
   ```bash
   pip show kubectl-mcp-tool
   ```

3. **Check logs**:
   Set `MCP_DEBUG=1` and `MCP_LOG_FILE=/tmp/mcp.log` to enable debug logging.

### Connection Issues

1. **Verify kubectl works**:
   ```bash
   kubectl get pods
   ```

2. **Check kubeconfig path**:
   ```bash
   echo $KUBECONFIG
   cat ~/.kube/config
   ```

### Tool Execution Errors

If tools return errors, check:
- Cluster connectivity
- RBAC permissions for your user
- Namespace existence
- Resource names are correct

## Example Session

```
User: What pods are running in the kube-system namespace?

Claude: I'll check the pods in the kube-system namespace for you.

[Uses get_pods tool with namespace="kube-system"]

Here are the pods running in kube-system:
- coredns-5d78c9869d-abcde (Running)
- etcd-master (Running)
- kube-apiserver-master (Running)
- kube-controller-manager-master (Running)
- kube-proxy-xyz123 (Running)
- kube-scheduler-master (Running)

User: Can you switch to my production cluster?

Claude: I'll list the available contexts and switch to the production one.

[Uses list_contexts tool]
[Uses switch_context tool with context_name="production"]

Done! I've switched to the production cluster context.
```

## Security Considerations

- The MCP server has access to your kubeconfig and can perform any kubectl operation
- Use RBAC to limit what operations can be performed
- Consider using a service account with limited permissions for the MCP server
- Never expose the MCP server to untrusted networks

## See Also

- [Claude Desktop Integration](./claude_integration.md)
- [Installation Guide](../INSTALLATION.md)
- [Quick Start](../QUICKSTART.md)
