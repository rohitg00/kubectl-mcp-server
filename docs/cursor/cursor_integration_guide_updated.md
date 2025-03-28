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
3. Scroll down to the "MCP" section
4. Click "Add new global MCP server"
5. Enter the following configuration in `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.minimal_wrapper"],
      "env": {
        "KUBECONFIG": "/path/to/your/.kube/config", 
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"
      }
    }
  }
}
```

Replace `/path/to/your/.kube/config` with the actual path to your kubeconfig file. 
On most systems, this is `~/.kube/config`.

Save this configuration to `~/.cursor/mcp.json` for global settings.

Note: This configuration uses the minimal wrapper approach which has better compatibility with different MCP SDK versions.

### 4. Test the Integration

You can test the integration by:

1. Start Cursor
2. Open a new file or project
3. Ask a Kubernetes-related question like:
   - "List all pods in the default namespace"
   - "What deployments are running in my cluster?"
   - "Show me the services in the kube-system namespace"

### 5. Automated Setup

For an automated setup, you can run the installation script:

```bash
bash install.sh
```

This script will:
1. Install all required dependencies
2. Create the correct configuration file for Cursor
3. Set up the environment variables properly
4. Verify kubectl access

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
