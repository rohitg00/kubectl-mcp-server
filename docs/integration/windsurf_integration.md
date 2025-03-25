# Windsurf Integration Guide for kubectl-mcp-tool

This guide explains how to integrate the kubectl-mcp-tool with Windsurf for natural language Kubernetes operations.

## Prerequisites

- kubectl-mcp-tool installed
- Windsurf AI assistant
- Python 3.8+

## Configuration Steps

1. **Install the kubectl-mcp-tool**:
   ```bash
   pip install -e /path/to/kubectl-mcp-tool
   ```

2. **Start the MCP server**:
   ```bash
   python -m kubectl_mcp_tool.cli serve --transport sse --port 8080
   ```

3. **Configure Windsurf**:
   - Open Windsurf AI assistant
   - Go to Settings > Tools
   - Add a new tool with the following configuration:
     - **Tool Name**: `kubectl-mcp-tool`
     - **URL**: `http://localhost:8080`
     - **Transport**: `SSE`

4. **Enable the Tool**:
   - Make sure the tool is enabled in Windsurf
   - If the tool shows as disconnected, check that the MCP server is running

## Using the Tool in Windsurf

Once configured, you can use natural language commands in Windsurf:

- "Get all pods"
- "Show namespaces"
- "Switch to namespace kube-system"
- "What is my current namespace"

Example conversation:

```
User: Get all pods in the default namespace
Windsurf: [Uses kubectl-mcp-tool]
Command: kubectl get pods -n default

Result:
NAME                     READY   STATUS    RESTARTS   AGE
nginx-pod               1/1     Running   0          1h
web-deployment-abc123   1/1     Running   0          45m
db-statefulset-0        1/1     Running   0          30m
```

## Troubleshooting

If you encounter connection issues:

1. **Check Server Status**:
   - Verify that the MCP server is running
   - Check the server logs for errors

2. **Verify Port**:
   - Make sure port 8080 is not being used by another application
   - If needed, specify a different port with the `--port` option

3. **Test Directly**:
   - Test the server directly using curl:
     ```bash
     curl -N http://localhost:8080/mcp
     ```

4. **Firewall Issues**:
   - Check if a firewall is blocking the connection
   - Ensure that localhost connections are allowed

## Advanced Configuration

For advanced configuration options, see the [Configuration Guide](./configuration.md).
