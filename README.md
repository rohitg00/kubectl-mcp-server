# Kubectl MCP Tool

A Model Context Protocol (MCP) server for Kubernetes that enables AI assistants like Claude, Cursor, and others to interact with Kubernetes clusters through natural language.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://github.com/modelcontextprotocol/spec)
[![PyPI version](https://badge.fury.io/py/kubectl-mcp-tool.svg)](https://pypi.org/project/kubectl-mcp-tool/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kubectl-mcp-tool)](https://pypi.org/project/kubectl-mcp-tool/)

## Features

### Core Kubernetes Operations
- [x] Connect to a Kubernetes cluster
- [x] List and manage pods, services, deployments, and nodes
- [x] Create, delete, and describe pods and other resources
- [x] Get pod logs and Kubernetes events
- [x] Support for Helm v3 operations (installation, upgrades, uninstallation)
- [x] kubectl explain and api-resources support
- [x] Choose namespace for next commands (memory persistence)
- [x] Port forward to pods
- [x] Scale deployments and statefulsets
- [x] Execute commands in containers
- [x] Manage ConfigMaps and Secrets
- [x] Rollback deployments to previous versions
- [x] Ingress and NetworkPolicy management
- [x] Context switching between clusters

### Natural Language Processing
- [x] Process natural language queries for kubectl operations
- [x] Context-aware commands with memory of previous operations
- [x] Human-friendly explanations of Kubernetes concepts
- [x] Intelligent command construction from intent
- [x] Fallback to kubectl when specialized tools aren't available
- [x] Mock data support for offline/testing scenarios
- [x] Namespace-aware query handling

### Monitoring
- [x] Cluster health monitoring
- [x] Resource utilization tracking
- [x] Pod status and health checks
- [x] Event monitoring and alerting
- [x] Node capacity and allocation analysis
- [x] Historical performance tracking
- [x] Resource usage statistics via kubectl top
- [x] Container readiness and liveness tracking

### Security
- [x] RBAC validation and verification
- [x] Security context auditing
- [x] Secure connections to Kubernetes API
- [x] Credentials management
- [x] Network policy assessment
- [x] Container security scanning
- [x] Security best practices enforcement
- [x] Role and ClusterRole management
- [x] ServiceAccount creation and binding
- [x] PodSecurityPolicy analysis
- [x] RBAC permissions auditing
- [x] Security context validation

### Diagnostics
- [x] Cluster diagnostics and troubleshooting
- [x] Configuration validation
- [x] Error analysis and recovery suggestions
- [x] Connection status monitoring
- [x] Log analysis and pattern detection
- [x] Resource constraint identification
- [x] Pod health check diagnostics
- [x] Common error pattern identification
- [x] Resource validation for misconfigurations
- [x] Detailed liveness and readiness probe validation

### Advanced Features
- [x] Multiple transport protocols support (stdio, SSE)
- [x] Integration with multiple AI assistants
- [x] Extensible tool framework
- [x] Custom resource definition support
- [x] Cross-namespace operations
- [x] Batch operations on multiple resources
- [x] Intelligent resource relationship mapping
- [x] Error explanation with recovery suggestions
- [x] Volume management and identification

## Architecture

### Model Context Protocol (MCP) Integration

The Kubectl MCP Tool implements the [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/spec), enabling AI assistants to interact with Kubernetes clusters through a standardized interface. The architecture consists of:

1. **MCP Server**: A compliant server that handles requests from MCP clients (AI assistants)
2. **Tools Registry**: Registers Kubernetes operations as MCP tools with schemas
3. **Transport Layer**: Supports stdio, SSE, and HTTP transport methods
4. **Core Operations**: Translates tool calls to Kubernetes API operations
5. **Response Formatter**: Converts Kubernetes responses to MCP-compliant responses

### Request Flow

![Request Flow](./image.png)

### Dual Mode Operation

The tool operates in two modes:

1. **CLI Mode**: Direct command-line interface for executing Kubernetes operations
2. **Server Mode**: Running as an MCP server to handle requests from AI assistants

## Installation

For detailed installation instructions, please see the [Installation Guide](./docs/INSTALLATION.md).

You can install kubectl-mcp-tool directly from PyPI:

```bash
pip install kubectl-mcp-tool
```

For a specific version:

```bash
pip install kubectl-mcp-tool==1.0.0
```

The package is available on PyPI: [https://pypi.org/project/kubectl-mcp-tool/1.0.0/](https://pypi.org/project/kubectl-mcp-tool/1.0.0/)

### Prerequisites

- Python 3.9+
- kubectl CLI installed and configured
- Access to a Kubernetes cluster
- pip (Python package manager)

### Global Installation

```bash
# Install latest version from PyPI
pip install kubectl-mcp-tool

# Or install development version from GitHub
pip install git+https://github.com/rohitg00/kubectl-mcp-server.git
```

### Local Development Installation

```bash
# Clone the repository
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server

# Install in development mode
pip install -e .
```

### Verifying Installation

After installation, verify the tool is working correctly:

```bash
# Check CLI mode
kubectl-mcp --help

# Test connection to Kubernetes
kubectl-mcp get pods
```

## Usage with AI Assistants

### Claude Desktop

Add the following to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.cli"]
    }
  }
}
```

### Cursor AI

Add the following to your Cursor AI configuration:

```json
{
  "tools": [
    {
      "name": "kubectl-mcp",
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.cli"],
      "description": "A tool for interacting with Kubernetes clusters."
    }
  ]
}
```

### Windsurf

Add the following to your Windsurf configuration:

```json
{
  "extensions": [
    {
      "name": "kubectl-mcp",
      "description": "Kubernetes operations using MCP",
      "exec": {
        "command": "python",
        "args": ["-m", "kubectl_mcp_tool.cli"]
      }
    }
  ]
}
```

## Prerequisites

1. kubectl installed and in your PATH
2. A valid kubeconfig file
3. Access to a Kubernetes cluster
4. Helm v3 (optional, for Helm operations)

## Examples

### List Pods

```
List all pods in the default namespace
```

### Deploy an Application

```
Create a deployment named nginx-test with 3 replicas using the nginx:latest image
```

### Check Pod Logs

```
Get logs from the nginx-test pod
```

### Port Forwarding

```
Forward local port 8080 to port 80 on the nginx-test pod
```

## Development

```bash
# Clone the repository
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests
python -m python_tests.test_all_features
```

## Project Structure

```
├── kubectl_mcp_tool/         # Main package
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # CLI entry point
│   ├── mcp_server.py         # MCP server implementation
│   ├── mcp_kubectl_tool.py   # Main kubectl MCP tool implementation
│   ├── natural_language.py   # Natural language processing
│   ├── diagnostics.py        # Diagnostics functionality
│   ├── core/                 # Core functionality 
│   ├── security/             # Security operations
│   ├── monitoring/           # Monitoring functionality
│   ├── utils/                # Utility functions
│   └── cli/                  # CLI functionality components
├── python_tests/             # Test suite
│   ├── run_mcp_tests.py      # Test runner script
│   ├── mcp_client_simulator.py # MCP client simulator for mock testing
│   ├── test_utils.py         # Test utilities
│   ├── test_mcp_core.py      # Core MCP tests
│   ├── test_mcp_security.py  # Security tests
│   ├── test_mcp_monitoring.py # Monitoring tests
│   ├── test_mcp_nlp.py       # Natural language tests
│   ├── test_mcp_diagnostics.py # Diagnostics tests
│   └── mcp_test_strategy.md  # Test strategy documentation
├── docs/                     # Documentation
│   ├── README.md             # Documentation overview
│   ├── INSTALLATION.md       # Installation guide
│   ├── integration_guide.md  # Integration guide
│   ├── cursor/               # Cursor integration docs
│   ├── windsurf/             # Windsurf integration docs
│   └── claude/               # Claude integration docs
├── compatible_servers/       # Compatible MCP server implementations
│   ├── cursor/               # Cursor-compatible servers
│   ├── windsurf/             # Windsurf-compatible servers
│   ├── minimal/              # Minimal server implementations
│   └── generic/              # Generic MCP servers
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup script
├── pyproject.toml            # Project configuration
├── MANIFEST.in               # Package manifest
├── LICENSE                   # MIT License
├── CHANGELOG.md              # Version history
├── .gitignore                # Git ignore file
├── install.sh                # Installation script
├── publish.sh                # PyPI publishing script
└── start_mcp_server.sh       # Server startup script
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
