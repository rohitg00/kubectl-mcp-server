# Cursor Configuration Guide for kubectl-mcp-tool

This guide explains how to configure Cursor AI assistant to work with the kubectl-mcp-tool for natural language Kubernetes operations.

## Prerequisites

- kubectl-mcp-tool installed
- Cursor AI assistant
- Python 3.8+

## Configuration Steps

1. **Install the kubectl-mcp-tool**:
   ```bash
   pip install -e /path/to/kubectl-mcp-tool
   ```

2. **Open Cursor AI Assistant**:
   - Launch Cursor AI assistant
   - Navigate to Settings

3. **Configure the Tool**:
   - Go to the Tools section in Settings
   - Add a new tool with the following configuration:
     - **Tool Name**: `kubectl-mcp-tool`
     - **Command**: `python -m kubectl_mcp_tool.cli serve --transport stdio --cursor`
     - **Working Directory**: `/path/to/kubectl-mcp-tool`

   ![Cursor Configuration](../screenshots/cursor_config.png)

4. **Enable the Tool**:
   - Make sure the tool is enabled in Cursor
   - If the tool shows "Client closed" status, try restarting Cursor and the tool

## Troubleshooting

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

## Using the Tool in Cursor

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

## Verifying Tool Registration

To verify that the tool is properly registered with Cursor, you can run the test script:

```bash
python test_cursor_tool_registration.py
```

This script will test the tool registration and functionality, ensuring that all required tools are available and working correctly.
