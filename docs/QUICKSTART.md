# Quick Start Guide: kubectl-mcp-tool

This guide will help you quickly set up kubectl-mcp-tool to work with AI assistants like Cursor, Claude, and WindSurf.

## 1. One-Step Installation

The simplest way to install and configure kubectl-mcp-tool is to use our installation script:

```bash
# Clone the repository
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server

# Run the installation script
bash install.sh
```

This script will:
- Install the required dependencies
- Set up configurations for Cursor, Claude, and WindSurf
- Configure environment variables correctly
- Test your Kubernetes connection

## 2. Manual Installation

If you prefer to install manually:

```bash
# Install the package
pip install mcp>=1.5.0
pip install -e .

# Create config directories
mkdir -p ~/.cursor
mkdir -p ~/.config/claude
mkdir -p ~/.config/windsurf
```

## 3. Configuration for AI Assistants

### Cursor

Create or edit `~/.cursor/mcp.json`:

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

### Claude Desktop

Create or edit `~/.config/claude/mcp.json`:

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

### WindSurf

Create or edit `~/.config/windsurf/mcp.json`:

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

> **Important**: Replace `/path/to/your/.kube/config` with the actual path to your kubeconfig file (usually `~/.kube/config`).

## 4. Testing Your Installation

To verify your installation is working:

1. Test the command line:
   ```bash
   kubectl-mcp --help
   ```

2. Test the MCP server directly:
   ```bash
   python -m kubectl_mcp_tool.minimal_wrapper
   ```
   
   It should start and wait for connections with no errors.

3. Open your AI assistant (Cursor, Claude, or WindSurf) and ask a Kubernetes-related question:
   - "List all pods in the default namespace"
   - "What deployments are running in my cluster?"
   - "Show me the services in the kube-system namespace"

## 5. Troubleshooting

If you encounter issues:

1. Check the logs:
   ```bash
   # For Cursor
   cat ~/.cursor/logs/kubectl_mcp_debug.log
   ```

2. Run the tool directly to see error messages:
   ```bash
   python -m kubectl_mcp_tool.minimal_wrapper
   ```

3. Verify kubectl is working from command line:
   ```bash
   kubectl get pods
   ```

4. Check if your configuration file has the correct paths:
   ```bash
   cat ~/.cursor/mcp.json
   ```

5. Try reinstalling the package:
   ```bash
   pip uninstall -y kubectl-mcp-tool
   pip install -e .
   ```

For more details, see the [Installation Guide](./INSTALLATION.md) and [Troubleshooting](./INSTALLATION.md#troubleshooting) sections. 