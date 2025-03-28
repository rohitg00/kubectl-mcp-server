#!/bin/bash
set -e

echo "Installing kubectl-mcp-tool..."

# Uninstall any previous versions first
pip uninstall -y kubectl-mcp-tool fastmcp mcp mcp-python || true

# Install the correct version of MCP SDK
pip install mcp>=1.5.0

# Create logs directory if it doesn't exist
mkdir -p logs

# Install kubectl-mcp-tool in development mode
pip install -e .

# Create directories for all supported AI assistants
mkdir -p ~/.cursor
mkdir -p ~/.cursor/logs
mkdir -p ~/.config/claude
mkdir -p ~/.config/windsurf

# Get absolute path to Python interpreter
PYTHON_PATH=$(which python)
echo "Using Python interpreter: $PYTHON_PATH"

# Get absolute path to kubectl config
KUBE_CONFIG="${KUBECONFIG:-$HOME/.kube/config}"
echo "Using Kubernetes config: $KUBE_CONFIG"

# Get absolute path to kubectl command
KUBECTL_PATH=$(which kubectl)
if [ -z "$KUBECTL_PATH" ]; then
  echo "WARNING: kubectl not found in PATH. Please install kubectl."
  KUBECTL_PATH="kubectl"
fi
echo "Using kubectl: $KUBECTL_PATH"

# Create a test configuration for Cursor MCP with absolute path and minimal wrapper
cat > ~/.cursor/mcp.json << EOF
{
  "mcpServers": {
    "kubernetes": {
      "command": "$PYTHON_PATH",
      "args": ["-m", "kubectl_mcp_tool.minimal_wrapper"],
      "env": {
        "KUBECONFIG": "$KUBE_CONFIG",
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$HOME/.pyenv/versions/3.10.0/bin"
      }
    }
  }
}
EOF

# Create a test configuration for Claude with absolute path
cat > ~/.config/claude/mcp.json << EOF
{
  "mcpServers": {
    "kubernetes": {
      "command": "$PYTHON_PATH",
      "args": ["-m", "kubectl_mcp_tool.cli.cli", "serve"],
      "env": {
        "KUBECONFIG": "$KUBE_CONFIG"
      }
    }
  }
}
EOF

# Create a test configuration for WindSurf with absolute path
cat > ~/.config/windsurf/mcp.json << EOF
{
  "mcpServers": {
    "kubernetes": {
      "command": "$PYTHON_PATH",
      "args": ["-m", "kubectl_mcp_tool.cli.cli", "serve"],
      "env": {
        "KUBECONFIG": "$KUBE_CONFIG"
      }
    }
  }
}
EOF

# Test that kubectl is working
echo "Testing kubectl access..."
if $KUBECTL_PATH version --client > /dev/null 2>&1; then
  echo "✅ kubectl is working correctly"
else
  echo "⚠️ kubectl test failed. You may need to set up kubernetes access."
fi

# Check if kubeconfig exists
if [ -f "$KUBE_CONFIG" ]; then
  echo "✅ Kubernetes config exists at $KUBE_CONFIG"
else
  echo "⚠️ Kubernetes config not found at $KUBE_CONFIG. You may need to set up kubernetes access."
fi

echo "Installation complete. Verify with: kubectl-mcp --help"
echo ""
echo "To start the MCP server, run: kubectl-mcp serve"
echo ""
echo "MCP configurations have been added for:"
echo " - Cursor: ~/.cursor/mcp.json (with minimal wrapper)"
echo " - Claude: ~/.config/claude/mcp.json"
echo " - WindSurf: ~/.config/windsurf/mcp.json"
echo ""
echo "If Cursor fails to connect, check the output of: python -m kubectl_mcp_tool.minimal_wrapper"
echo ""
echo "If you encounter any issues, check the documentation in the docs/ folder"
