---
name: k8s-cli
description: kubectl-mcp-server CLI commands for tool discovery, direct invocation, and diagnostics. Use when exploring available tools, calling tools from command line, or checking server health.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 0
  category: tooling
---

# kubectl-mcp-server CLI

Command-line interface for kubectl-mcp-server operations.

## When to Apply

Use this skill when:
- User mentions: "CLI", "command line", "tool discovery", "server health"
- Operations: listing tools, calling tools directly, checking dependencies
- Keywords: "doctor", "tools list", "call", "grep", "info"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Run doctor to check dependencies | CRITICAL | `kubectl-mcp-server doctor` |
| 2 | Use tools -d for descriptions | HIGH | `kubectl-mcp-server tools -d` |
| 3 | Use grep for tool discovery | MEDIUM | `kubectl-mcp-server grep` |
| 4 | Use call for direct invocation | MEDIUM | `kubectl-mcp-server call` |

## Quick Reference

| Task | Command | Example |
|------|---------|---------|
| List tools | `tools -d` | `kubectl-mcp-server tools -d` |
| Search tools | `grep` | `kubectl-mcp-server grep "*pod*"` |
| Call tool | `call` | `kubectl-mcp-server call get_pods '{"namespace": "default"}'` |
| Check health | `doctor` | `kubectl-mcp-server doctor` |

## Server Commands

### Start Server

```bash
# stdio transport (for Claude Desktop)
kubectl-mcp-server serve

# HTTP transport (for remote clients)
kubectl-mcp-server serve --transport streamable-http --port 8000

# With debug logging
MCP_DEBUG=true kubectl-mcp-server serve
```

### Check Health

```bash
# Verify dependencies
kubectl-mcp-server doctor

# Shows:
# ✓ kubectl: found
# ✓ helm: found
# ✓ kubeconfig: valid
# ✓ cluster: connected
```

## Tool Discovery

### List Tools

```bash
# List all tools
kubectl-mcp-server tools

# List with descriptions
kubectl-mcp-server tools -d

# JSON output
kubectl-mcp-server tools --json
```

### Search Tools

```bash
# Search by pattern
kubectl-mcp-server grep "*pod*"
kubectl-mcp-server grep "*helm*"
kubectl-mcp-server grep "*velero*"

# Results show matching tool names
```

### Tool Schema

```bash
# Show tool parameters
kubectl-mcp-server tools get_pods
kubectl-mcp-server tools install_helm_chart

# Shows:
# - Description
# - Parameters (name, type, required)
# - Return type
```

## Direct Tool Invocation

### Call Tools

```bash
# Call with JSON arguments
kubectl-mcp-server call get_pods '{"namespace": "default"}'

# Call with stdin
echo '{"namespace": "kube-system"}' | kubectl-mcp-server call get_pods

# Call with no arguments
kubectl-mcp-server call get_namespaces '{}'
```

### Examples

```bash
# Get pods
kubectl-mcp-server call get_pods '{"namespace": "default"}'

# Describe pod
kubectl-mcp-server call describe_pod '{"name": "nginx-xxx", "namespace": "default"}'

# Get logs
kubectl-mcp-server call get_pod_logs '{"name": "nginx-xxx", "namespace": "default"}'

# Scale deployment
kubectl-mcp-server call scale_deployment '{"name": "nginx", "namespace": "default", "replicas": 3}'

# Install helm chart
kubectl-mcp-server call install_helm_chart '{
  "name": "my-release",
  "chart": "bitnami/nginx",
  "namespace": "default"
}'
```

## Context Management

```bash
# Show current context
kubectl-mcp-server context

# Switch context
kubectl-mcp-server context production

# List available contexts
kubectl-mcp-server call list_contexts_tool '{}'
```

## Server Info

```bash
# Show server information
kubectl-mcp-server info

# Shows:
# - Version
# - Tool count
# - Resource count
# - Prompt count
```

## MCP Resources

```bash
# List available resources
kubectl-mcp-server resources

# Resources:
# - cluster://status
# - namespaces://list
# - pods://{namespace}
# - deployments://{namespace}
# - services://{namespace}
# - events://{namespace}
# - nodes://list
# - contexts://list
```

## MCP Prompts

```bash
# List available prompts
kubectl-mcp-server prompts

# Prompts:
# - troubleshoot-pod
# - deploy-application
# - security-audit
# - cost-optimization
# - incident-response
# - helm-workflow
# - gitops-sync
# - multi-cluster-compare
```

## Environment Variables

```bash
# Core
export MCP_DEBUG=true           # Enable debug logging
export MCP_LOG_FILE=/var/log/mcp.log  # Log to file
export NO_COLOR=1               # Disable colors

# Browser (optional)
export MCP_BROWSER_ENABLED=true
export MCP_BROWSER_PROVIDER=browserbase
export BROWSERBASE_API_KEY=bb_...
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "kubectl": {
      "command": "kubectl-mcp-server",
      "args": ["serve"]
    }
  }
}
```

## Shell Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias kmcp='kubectl-mcp-server'
alias kmcp-tools='kubectl-mcp-server tools -d'
alias kmcp-call='kubectl-mcp-server call'
alias kmcp-grep='kubectl-mcp-server grep'
```

## Related Skills

- [k8s-core](../k8s-core/SKILL.md) - Core resource tools
- [k8s-diagnostics](../k8s-diagnostics/SKILL.md) - Diagnostic tools
