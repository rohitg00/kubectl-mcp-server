# Windsurf Integration Guide for kubectl-mcp-tool

This guide provides step-by-step instructions for configuring Windsurf to work with the kubectl-mcp-tool MCP server.

## Prerequisites

- Windsurf installed on your machine
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

### 2. Start the MCP Server with SSE Transport

For Windsurf integration, you need to start the kubectl-mcp-tool MCP server with SSE (Server-Sent Events) transport:

```bash
python -m kubectl_mcp_tool.cli serve --transport sse --port 8080
```

### 3. Configure Windsurf

1. Open Windsurf and go to Settings
2. Navigate to the "Tools" or "Extensions" section
3. Click "Add Tool" or "Add Custom Tool"
4. Enter the following configuration:

```json
{
  "Servers": {
    "mcp-server-kubectl-mcp-tool": {
      "name": "kubectl-mcp-tool", 
      "description": "Kubernetes operations using natural language",
      "command": "python3 windsurf_compatible_mcp_server.py",
      "transport": "sse"
    }
  }
}
```

Note: The MCP server will be started automatically by Windsurf using the command specified in the configuration.

### 4. Test the Integration

1. Open a new chat in Windsurf
2. Type a natural language kubectl command, such as:
   - "Get all pods in the default namespace"
   - "Show me all deployments"
   - "Switch to the kube-system namespace"

3. Windsurf should execute the command using the kubectl-mcp-tool and display the results

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

1. **Connection refused errors**:
   - Make sure the MCP server is running before sending commands
   - Check that the endpoint URL in the Windsurf configuration is correct
   - Verify that your public endpoint is properly forwarding to your local server

2. **Mock data is shown instead of real kubectl output**:
   - Ensure you have a running Kubernetes cluster (e.g., minikube)
   - Check that kubectl is properly configured on your system
   - Verify that you have the necessary permissions to execute kubectl commands

3. **Server not responding**:
   - Check the server logs for errors
   - Verify that the port (8080) is not being used by another application
   - Try restarting the MCP server

### Logs

The MCP server creates log files that can help diagnose issues:

- `mcp_server.log`: General server logs
- `mcp_debug.log`: Detailed debug logs including protocol messages

## Secure Remote Access

For production use, consider these security measures when exposing your kubectl-mcp-tool:

1. **Use HTTPS**: Always use HTTPS for your public endpoint
2. **Implement Authentication**: Add an authentication layer to your proxy
3. **Restrict Access**: Limit access to specific IP addresses
4. **Use a VPN**: Consider running your service within a VPN

Note: Exposing kubectl operations to the internet carries security risks. Ensure proper security measures are in place before doing so.
