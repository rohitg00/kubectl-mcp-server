# Claude Integration Guide for kubectl-mcp-tool

This guide explains how to integrate the kubectl-mcp-tool with Claude AI for natural language Kubernetes operations.

## Prerequisites

- kubectl-mcp-tool installed
- Claude AI access
- Python 3.8+

## Integration Steps

1. **Install the kubectl-mcp-tool**:
   ```bash
   # Install from PyPI (recommended)
   pip install kubectl-mcp-tool
   
   # For a specific version
   pip install kubectl-mcp-tool==1.0.0
   
   # Or install in development mode from local repository
   pip install -e /path/to/kubectl-mcp-tool
   ```
   
   The package is available on PyPI: [https://pypi.org/project/kubectl-mcp-tool/1.0.0/](https://pypi.org/project/kubectl-mcp-tool/1.0.0/)

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
   - For Claude in Cursor, follow the [Cursor Integration Guide](../cursor/cursor_integration.md)

### Step 3: Configure Claude Desktop

To configure Claude Desktop to use the `kubectl-mcp-tool` MCP server:

1. Open or create the MCP configuration file at `~/.config/claude/mcp.json` (Windows: `%APPDATA%\Claude\mcp.json`)
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
4. Save the file and restart Claude Desktop.

Note: This configuration uses the minimal wrapper approach which has better compatibility with different MCP SDK versions.

### Step 4: Automated Setup

For an automated setup, you can run the installation script:

```bash
bash install.sh
```

This script will:
1. Install all required dependencies
2. Create the correct configuration file for Claude Desktop
3. Set up the environment variables properly
4. Verify kubectl access

### Step 5: Testing the Integration

You can test the integration by:

1. Start Claude Desktop
2. Ask a Kubernetes-related question like:
   - "List all pods in the default namespace"
   - "What deployments are running in my cluster?"
   - "Show me the services in the kube-system namespace"

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

For installation details, see the [Installation Guide](../INSTALLATION.md).
