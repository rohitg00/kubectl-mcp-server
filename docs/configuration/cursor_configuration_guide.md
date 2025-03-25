# Cursor Configuration Guide for kubectl-mcp-tool

This guide provides step-by-step instructions for configuring Cursor to work with the kubectl-mcp-tool MCP server.

## Prerequisites

- Cursor installed on your machine
- kubectl-mcp-tool installed and configured
- Python 3.8+ installed

## Configuration Steps

### 1. Start the MCP Server

First, start the kubectl-mcp-tool MCP server with Cursor compatibility mode:

```bash
python cursor_compatible_mcp_server.py
```

This will start the server using stdio transport, which is compatible with Cursor's MCP implementation.

### 2. Configure Cursor

1. Open Cursor and go to Settings
2. Navigate to the "AI & Copilot" section
3. Scroll down to "Tools" or "Extensions"
4. Click "Add Tool" or "Add Custom Tool"
5. Enter the following configuration:

```json
{
  "name": "kubectl-mcp-tool",
  "description": "Kubernetes operations using natural language",
  "command": "python /path/to/kubectl-mcp-tool/cursor_compatible_mcp_server.py",
  "transport": "stdio"
}
```

Replace `/path/to/kubectl-mcp-tool/` with the actual path to your kubectl-mcp-tool installation.

### 3. Test the Integration

1. Open a new chat in Cursor
2. Type a natural language kubectl command, such as:
   - "Get all pods in the default namespace"
   - "Show me all deployments"
   - "Switch to the kube-system namespace"

3. Cursor should execute the command using the kubectl-mcp-tool and display the results

## Example Commands

Here are some example natural language commands you can use:

- "Get all pods"
- "Show namespaces"
- "Switch to namespace kube-system"
- "Get deployments in namespace default"
- "Describe pod nginx-pod"
- "Scale deployment nginx to 3 replicas"
- "Get logs from pod web-deployment-abc123"

## Troubleshooting

### Common Issues

1. **"Client closed" error**:
   - Make sure the MCP server is running before sending commands
   - Check that the path in the Cursor configuration is correct
   - Verify that the server is running in Cursor compatibility mode

2. **Mock data is shown instead of real kubectl output**:
   - Ensure you have a running Kubernetes cluster (e.g., minikube)
   - Check that kubectl is properly configured on your system
   - Verify that you have the necessary permissions to execute kubectl commands

3. **Server not responding**:
   - Check the server logs for errors (cursor_mcp_debug.log)
   - Restart the MCP server
   - Verify that no other process is using the same port

### Logs

The MCP server creates log files that can help diagnose issues:

- `cursor_mcp_server.log`: General server logs
- `cursor_mcp_debug.log`: Detailed debug logs including protocol messages
