# kubectl-mcp-server Documentation

Welcome to the kubectl-mcp-server documentation. This tool implements the Model Context Protocol (MCP) for Kubernetes operations, enabling natural language processing for kubectl commands and integration with AI assistants.

## Documentation Sections

### Integration Guides

- [Cursor Integration](integration/cursor_integration.md) - How to integrate with Cursor AI
- [Windsurf Integration](integration/windsurf_integration.md) - How to integrate with Windsurf

### Feature Documentation

- [Context Switching](features/context_switching_usage.md) - How to use the context switching feature
- [Log Analysis](features/log_analysis_features.md) - How to use the log analysis features

### Configuration Guides

- [Cursor Configuration](configuration/cursor_configuration.md) - How to configure Cursor for kubectl-mcp-server
- [Windsurf Configuration](configuration/windsurf_config.json) - Configuration example for Windsurf

## Quick Start

To get started quickly with kubectl-mcp-server:

1. Install the tool:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

2. Start the server for your preferred AI assistant:
   ```bash
   # For Cursor
   ./cursor_server.py
   
   # For Windsurf
   ./windsurf_server.py
   ```

3. Configure your AI assistant according to the relevant integration guide.

4. Start using natural language commands with kubectl!

## Example Usage

Once configured, you can use natural language to interact with your Kubernetes cluster:

- "Get all pods across all namespaces"
- "Show nodes in the cluster"
- "Scale deployment nginx to 3 replicas"
- "Describe pod metrics-server in kube-system namespace"
- "Analyze logs for pod nginx for errors"

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.
