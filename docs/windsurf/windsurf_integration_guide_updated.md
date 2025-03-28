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

### 3. Configure WindSurf

To configure WindSurf to use the kubectl-mcp-tool:

1. Open or create the MCP configuration file for WindSurf:
   - macOS: `~/.config/windsurf/mcp.json`
   - Windows: `%APPDATA%\WindSurf\mcp.json`
   - Linux: `~/.config/windsurf/mcp.json`

2. Add the following configuration:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.minimal_wrapper"],
      "env": {
        "KUBECONFIG": "/path/to/your/.kube/config"
      }
    }
  }
}
```

3. Replace `/path/to/your/.kube/config` with the actual path to your kubeconfig file (usually `~/.kube/config`)
4. Save the file and restart WindSurf.

Note: This configuration uses the minimal wrapper approach which has better compatibility with different MCP SDK versions.

### 4. Automated Setup

For an automated setup, you can run the installation script:

```bash
bash install.sh
```

This script will:
1. Install all required dependencies
2. Create the correct configuration file for WindSurf
3. Set up the environment variables properly
4. Verify kubectl access

### 5. Test the Integration

You can test the integration by:

1. Start WindSurf
2. Ask a Kubernetes-related question like:
   - "List all pods in the default namespace"
   - "What deployments are running in my cluster?"
   - "Show me the services in the kube-system namespace"

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
