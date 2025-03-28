# Installation Guide for kubectl-mcp-tool

This document provides detailed instructions for installing the kubectl-mcp-tool, a Kubernetes command-line tool that implements the Model Context Protocol (MCP) to enable AI assistants to interact with Kubernetes clusters.

## Table of Contents

- [PyPI Installation](#pypi-installation)
- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
  - [Global Installation](#global-installation)
  - [Local Development Installation](#local-development-installation)
  - [Docker Installation](#docker-installation)
- [Verifying Installation](#verifying-installation)
- [Troubleshooting](#troubleshooting)
- [Upgrading](#upgrading)
- [Uninstallation](#uninstallation)

## PyPI Installation

The simplest way to install kubectl-mcp-tool is directly from the Python Package Index (PyPI):

```bash
pip install kubectl-mcp-tool
```

For a specific version:

```bash
pip install kubectl-mcp-tool==1.0.0
```

The package is available on PyPI: [https://pypi.org/project/kubectl-mcp-tool/1.0.0/](https://pypi.org/project/kubectl-mcp-tool/1.0.0/)

## Prerequisites

Before installing kubectl-mcp-tool, ensure you have the following:

- Python 3.9 or higher
- pip (Python package manager)
- kubectl CLI installed and configured
- Access to a Kubernetes cluster
- (Optional) Helm v3 for Helm operations

To check your Python version:

```bash
python --version
```

To check if pip is installed:

```bash
pip --version
```

To check if kubectl is installed:

```bash
kubectl version --client
```

## Installation Methods

### Global Installation

#### From PyPI (Recommended)

Install the latest stable version from PyPI:

```bash
pip install kubectl-mcp-tool
```

#### From GitHub

Install the development version directly from GitHub:

```bash
pip install git+https://github.com/rohitg00/kubectl-mcp-server.git
```

#### Using pipx (Isolated Environment)

For a more isolated installation that doesn't affect your system Python:

```bash
# Install pipx if you don't have it
pip install pipx
pipx ensurepath

# Install kubectl-mcp-tool
pipx install kubectl-mcp-tool
```

### Local Development Installation

If you want to modify the code or contribute to the project:

```bash
# Clone the repository
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Docker Installation

For containerized usage:

```bash
# Pull the Docker image
docker pull rohitg00/kubectl-mcp-tool:latest

# Run the container
docker run -it --rm \
  -v ~/.kube:/root/.kube \
  rohitg00/kubectl-mcp-tool:latest
```

## Verifying Installation

After installation, verify that the tool is working correctly:

```bash
# Check version
kubectl-mcp --version

# Check CLI mode
kubectl-mcp --help

# Test connection to Kubernetes
kubectl-mcp get pods
```

## Troubleshooting

### Common Issues

1. **Command not found**:
   - Ensure the installation directory is in your PATH
   - For pipx installations, run `pipx ensurepath` and restart your terminal

2. **Permission errors during installation**:
   - Use `pip install --user kubectl-mcp-tool` to install for the current user only
   - On Linux/macOS, you might need to use `sudo pip install kubectl-mcp-tool`

3. **Dependency conflicts**:
   - Create a virtual environment: `python -m venv venv && source venv/bin/activate`
   - Then install within the virtual environment

4. **Kubernetes connection issues**:
   - Ensure your kubeconfig is correctly set up: `kubectl config view`
   - Check that your cluster is accessible: `kubectl cluster-info`

5. **ImportError: cannot import name 'Parameter' from 'mcp.types'**:
   - This is due to an MCP SDK version mismatch. Run the following commands to fix:
   ```bash
   # Uninstall conflicting packages
   pip uninstall -y kubectl-mcp-tool fastmcp mcp mcp-python
   
   # Install the correct version
   pip install mcp>=1.5.0
   
   # Reinstall kubectl-mcp-tool
   pip install kubectl-mcp-tool
   ```

6. **AttributeError: module 'kubectl_mcp_tool.cli' has no attribute 'main'**:
   - This is due to a CLI module path issue. Update your installation:
   ```bash
   pip uninstall -y kubectl-mcp-tool
   git clone https://github.com/rohitg00/kubectl-mcp-server.git
   cd kubectl-mcp-server
   pip install -e .
   ```
   - Or use our automatic install script:
   ```bash
   bash install.sh
   ```

7. **MCP Server compatibility issues**:
   - Make sure you're using the correct MCP configuration for your AI assistant
   - For Cursor AI, use this configuration in `~/.cursor/mcp.json`:
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
   - Replace `/path/to/your/.kube/config` with your actual kubeconfig path (usually `~/.kube/config`)
   - The `minimal_wrapper` module provides the most stable implementation for AI assistants

8. **Server implementation issues**:
   - This tool uses FastMCP from MCP SDK 1.5.0+ with a minimal wrapper approach
   - Key points about the implementation:
     - We use the simple `@server.tool(name)` decorator format without complex parameters
     - The minimal wrapper has better compatibility across MCP SDK versions
     - For debugging issues, run: `python -m kubectl_mcp_tool.minimal_wrapper`
     
9. **Client closed or connection errors**:
   - If you see "client closed" errors in your AI assistant, check:
     - Your kubeconfig path is correct in the configuration
     - kubectl is installed and in your PATH
     - You have proper permissions to access your Kubernetes cluster
     - Run the installation script: `bash install.sh` which handles these issues automatically

### Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/rohitg00/kubectl-mcp-server/issues) for similar problems
2. Join our [Discord community](https://discord.gg/kubectl-mcp) for real-time support
3. Open a new issue on GitHub with details about your problem

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade kubectl-mcp-tool
```

To upgrade to a specific version:

```bash
pip install --upgrade kubectl-mcp-tool==1.0.0
```

## Uninstallation

To uninstall kubectl-mcp-tool:

```bash
pip uninstall kubectl-mcp-tool
```

If installed with pipx:

```bash
pipx uninstall kubectl-mcp-tool
``` 