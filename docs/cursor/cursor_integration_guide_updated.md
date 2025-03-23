# Cursor Integration Guide for kubectl-mcp-tool

This guide provides step-by-step instructions for configuring Cursor to work with the kubectl-mcp-tool MCP server.

## Prerequisites

- Cursor installed on your machine
- kubectl-mcp-tool installed and configured
- Python 3.8+ installed

## Configuration Steps

### 1. Install the kubectl-mcp-tool

First, download and install the kubectl-mcp-tool:

```bash
# Clone the repository
git clone https://github.com/your-username/kubectl-mcp-tool.git

# Install dependencies
cd kubectl-mcp-tool
pip install -r requirements.txt
```

### 2. Start the MCP Server

The kubectl-mcp-tool MCP server uses stdio transport for Cursor compatibility:

```bash
python cursor_compatible_mcp_server.py
```

### 3. Configure Cursor

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

### 4. Test the Integration

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

## Remote Access (Optional)

If you need to access the kubectl-mcp-tool from a different machine, you can use the SSE transport mode and expose the port:

```bash
# Start the server with SSE transport
python -m kubectl_mcp_tool.cli serve --transport sse --port 8080

# Expose the port (requires additional setup)
# This would typically be done through a secure tunnel or VPN
```

Note: Remote access should be configured with proper security measures to prevent unauthorized access to your Kubernetes cluster.
