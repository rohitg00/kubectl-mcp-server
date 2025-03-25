# Claude Integration Guide for kubectl-mcp-tool

This guide explains how to integrate the kubectl-mcp-tool with Claude AI for natural language Kubernetes operations.

## Prerequisites

- kubectl-mcp-tool installed
- Claude AI access
- Python 3.8+

## Integration Steps

1. **Install the kubectl-mcp-tool**:
   ```bash
   pip install -e /path/to/kubectl-mcp-tool
   ```

2. **Start the MCP server**:
   ```bash
   python -m kubectl_mcp_tool.cli serve --transport sse --port 8080
   ```

3. **Expose the MCP server** (optional, if Claude needs to access it remotely):
   ```bash
   python -m kubectl_mcp_tool.cli expose 8080
   ```

4. **Configure Claude**:
   - When using Claude in a web interface or API, you can provide the URL of your MCP server
   - For Claude in Cursor, follow the [Cursor Integration Guide](./cursor_integration.md)

## Using kubectl-mcp-tool with Claude

Claude can interact with kubectl-mcp-tool using natural language commands. Here are some examples:

### Example 1: Getting Pods

```
User: Get all pods in the default namespace
Claude: Let me check the pods in the default namespace for you.

[Claude uses kubectl-mcp-tool]
Command: kubectl get pods -n default

Result:
NAME                     READY   STATUS    RESTARTS   AGE
nginx-pod               1/1     Running   0          1h
web-deployment-abc123   1/1     Running   0          45m
db-statefulset-0        1/1     Running   0          30m
```

### Example 2: Switching Namespaces

```
User: Switch to the kube-system namespace
Claude: I'll switch to the kube-system namespace.

[Claude uses kubectl-mcp-tool]
Command: kubectl config set-context --current --namespace kube-system

Result:
Switched to namespace kube-system
```

### Example 3: Checking Current Namespace

```
User: What namespace am I currently in?
Claude: Let me check your current namespace.

[Claude uses kubectl-mcp-tool]
Command: kubectl config view --minify --output jsonpath={..namespace}

Result:
kube-system
```

## Troubleshooting

If Claude has trouble connecting to your kubectl-mcp-tool:

1. **Check Server Status**:
   - Verify that the MCP server is running
   - Check the server logs for errors

2. **Verify URL**:
   - If using the expose feature, make sure the URL is correct and accessible
   - Test the URL directly in a browser or with curl

3. **Authentication**:
   - If your Kubernetes cluster requires authentication, make sure the kubectl-mcp-tool has the necessary credentials

4. **Permissions**:
   - Ensure that Claude has permission to access your MCP server
   - Check firewall settings if necessary

## Advanced Configuration

For advanced configuration options, see the [Configuration Guide](./configuration.md).
