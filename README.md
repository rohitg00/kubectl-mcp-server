# kubectl-mcp-server

A Kubernetes Model Context Protocol (MCP) server implementation that provides natural language processing capabilities for `kubectl` commands. This tool enables AI assistants to interact with Kubernetes clusters through natural language.

## Overview

kubectl-mcp-server bridges the gap between natural language and Kubernetes operations, allowing you to:

- Execute Kubernetes commands using natural language
- Integrate with AI assistants like Cursor and Windsurf via the Model Context Protocol
- Analyze Kubernetes logs with AI assistance
- Manage contexts and namespaces seamlessly
- Visualize Kubernetes resources with enhanced CLI formatting

## Repository Structure

```
kubectl-mcp-server/
├── kubectl_mcp_tool/        # Main package code
├── compatible_servers/      # MCP server implementations
├── python_tests/            # Test scripts
├── demos/                   # Demo scripts
├── docs/                    # Documentation
│   ├── integration/         # AI assistant integration guides
│   ├── features/            # Feature documentation
│   └── configuration/       # Configuration guides
├── cursor_server.py         # Cursor integration entry point
├── windsurf_server.py       # Windsurf integration entry point
├── deployment.yaml          # Kubernetes deployment configuration
├── service.yaml             # Kubernetes service configuration
├── Dockerfile               # For building the container image
└── requirements.txt         # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8+
- Kubernetes cluster (local or remote)
- kubectl configured with access to your cluster

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

Alternatively, use the provided installation script:

```bash
chmod +x install.sh
./install.sh
```

## Usage

### With Cursor AI

1. Start the Cursor-compatible MCP server:

```bash
# Using the convenience script
./cursor_server.py

# Or using the module
python -m compatible_servers.fast_cursor_server
```

2. Configure Cursor:
   - Open Cursor settings
   - Navigate to "Tools" > "Model Context Protocol"
   - Add a new MCP server with the following settings:
     - Name: `kubectl-mcp-server`
     - Command: `python3`
     - Args: [`cursor_server.py`]
     - Working directory: `/path/to/kubectl-mcp-server`

### With Windsurf

1. Start the Windsurf-compatible MCP server:

```bash
# Using the convenience script
./windsurf_server.py

# Or using the module
python -m compatible_servers.fast_windsurf_server
```

2. Configure according to the Windsurf integration guide in the documentation.

## Example Commands

Once configured, you can interact with your Kubernetes cluster using natural language:

- "Get all pods across all namespaces"
- "Show nodes in the cluster"
- "Scale deployment nginx to 3 replicas"
- "Describe pod metrics-server in kube-system namespace"
- "Analyze logs for pod nginx for errors"

## Documentation

- [Integration Guides](docs/integration/) - AI assistant integration
- [Feature Documentation](docs/features/) - Available features
- [Configuration Guides](docs/configuration/) - Configuration instructions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
