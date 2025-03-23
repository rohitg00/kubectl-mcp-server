# Integration Guide for kubectl-mcp-tool

This guide explains how to integrate the kubectl-mcp-tool with various AI assistants for natural language Kubernetes operations.

## Table of Contents

- [Cursor Integration](#cursor-integration)
- [Windsurf Integration](#windsurf-integration)
- [Claude Integration](#claude-integration)
- [General MCP Integration](#general-mcp-integration)

## Cursor Integration

### Prerequisites

- kubectl-mcp-tool installed
- Cursor AI assistant
- Python 3.9+

### Configuration Steps

1. **Install the kubectl-mcp-tool**:
   ```bash
   pip install kubectl-mcp-tool
   # Or install from source
   pip install -e /path/to/kubectl-mcp-server
   ```

2. **Open Cursor AI Assistant**:
   - Launch Cursor AI assistant
   - Navigate to Settings

3. **Configure the Tool**:
   - Go to the Tools section in Settings
   - Add a new tool with the following configuration:
     - **Tool Name**: `kubectl-mcp-tool`
     - **Command**: `python -m kubectl_mcp_tool.cli serve --transport stdio --cursor`
     - **Working Directory**: `/path/to/kubectl-mcp-server`

4. **Enable the Tool**:
   - Make sure the tool is enabled in Cursor
   - If the tool shows "Client closed" status, try restarting Cursor and the tool

### Using kubectl-mcp-tool with Cursor

Once configured, you can use natural language commands in Cursor:

- "Get all pods"
- "Show namespaces"
- "Switch to namespace kube-system"
- "What is my current namespace"

Example conversation:

```
User: Get all pods in the default namespace
Cursor: [Uses kubectl-mcp-tool]
Command: kubectl get pods -n default

Result:
NAME                     READY   STATUS    RESTARTS   AGE
nginx-pod               1/1     Running   0          1h
web-deployment-abc123   1/1     Running   0          45m
db-statefulset-0        1/1     Running   0          30m
```

### Troubleshooting Cursor Integration

If you encounter the "Client closed" status:

1. **Restart the Tool**:
   - Disable and re-enable the tool in Cursor settings
   - Restart Cursor

2. **Check Logs**:
   - Look for error messages in the following log files:
     - `simple_mcp_server.log`
     - `kubectl_mcp_tool_cli.log`

3. **Verify Command**:
   - Make sure the command is correct: `python -m kubectl_mcp_tool.cli serve --transport stdio --cursor`
   - Ensure the working directory is correct

4. **Test Directly**:
   - Run the command directly in a terminal to verify it works:
     ```bash
     python -m kubectl_mcp_tool.cli serve --cursor
     ```

## Windsurf Integration

### Prerequisites

- kubectl-mcp-tool installed
- Windsurf AI assistant
- Python 3.9+

### Configuration Steps

1. **Install the kubectl-mcp-tool**:
   ```bash
   pip install kubectl-mcp-tool
   # Or install from source
   pip install -e /path/to/kubectl-mcp-server
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

### Using kubectl-mcp-tool with Windsurf

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

### Troubleshooting Windsurf Integration

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

## Claude Integration

### Prerequisites

- kubectl-mcp-tool installed
- Claude AI access
- Python 3.9+

### Integration Steps

1. **Install the kubectl-mcp-tool**:
   ```bash
   pip install kubectl-mcp-tool
   # Or install from source
   pip install -e /path/to/kubectl-mcp-server
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
   - For Claude in Cursor, follow the [Cursor Integration](#cursor-integration) section

### Using kubectl-mcp-tool with Claude

Claude can interact with kubectl-mcp-tool using natural language commands. Here are some examples:

#### Example 1: Getting Pods

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

#### Example 2: Switching Namespaces

```
User: Switch to the kube-system namespace
Claude: I'll switch to the kube-system namespace.

[Claude uses kubectl-mcp-tool]
Command: kubectl config set-context --current --namespace kube-system

Result:
Switched to namespace kube-system
```

#### Example 3: Checking Current Namespace

```
User: What namespace am I currently in?
Claude: Let me check your current namespace.

[Claude uses kubectl-mcp-tool]
Command: kubectl config view --minify --output jsonpath={..namespace}

Result:
kube-system
```

### Troubleshooting Claude Integration

If Claude has trouble connecting to your kubectl-mcp-tool:

1. **Check Server Status**:
   - Verify that the MCP server is running
   - Check the server logs for errors

2. **Verify URL**:
   - If using the expose feature, make sure the URL is correct and accessible
   - Test the URL directly in a browser or with curl

## General MCP Integration

The kubectl-mcp-tool implements the Model Context Protocol (MCP) specification from [modelcontextprotocol.io](https://modelcontextprotocol.io/). This allows it to be integrated with any AI assistant that supports the MCP protocol.

### MCP Protocol Implementation

The kubectl-mcp-tool implements the following MCP methods:

- `mcp.initialize`: Initialize the MCP server
- `mcp.tools.list`: List available tools
- `mcp.tool.call`: Call a specific tool

### Available Tools

The kubectl-mcp-tool provides the following tools through the MCP interface:

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `process_natural_language` | Process natural language queries for kubectl operations | `query`: The natural language query to process |
| `get_pods` | Get all pods in a namespace | `namespace`: The namespace to get pods from (optional) |
| `get_namespaces` | Get all namespaces in the cluster | None |
| `switch_namespace` | Switch to a different namespace | `namespace`: The namespace to switch to |
| `get_current_namespace` | Get the current namespace | None |
| `get_deployments` | Get all deployments in a namespace | `namespace`: The namespace to get deployments from (optional) |

### Example MCP Requests

Here's an example of how to call the `process_natural_language` tool using the MCP protocol:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "mcp.tool.call",
  "params": {
    "name": "process_natural_language",
    "input": {
      "query": "get all pods"
    }
  }
}
```

And here's an example response:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "output": [
      {
        "type": "text",
        "text": "Command: kubectl get pods\n\nResult:\nNAME                     READY   STATUS    RESTARTS   AGE\nnginx-pod               1/1     Running   0          1h\nweb-deployment-abc123   1/1     Running   0          45m\ndb-statefulset-0        1/1     Running   0          30m"
      }
    ]
  }
}
```

### Advanced MCP Configuration

For advanced MCP configuration options, see the [MCP Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/).
