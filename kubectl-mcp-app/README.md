# kubectl-mcp-app

[![npm version](https://badge.fury.io/js/kubectl-mcp-app.svg)](https://www.npmjs.com/package/kubectl-mcp-app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Interactive UI add-on for kubectl-mcp-server using the MCP ext-apps SDK.

## Overview

kubectl-mcp-app provides 8 interactive UI dashboards for Kubernetes management that integrate seamlessly with Claude Desktop through the Model Context Protocol (MCP).

## Features

| Tool | Description |
| ---- | ----------- |
| `k8s-pods` | Interactive pod viewer with filtering, sorting, status indicators, and actions |
| `k8s-logs` | Real-time log viewer with syntax highlighting, search, and level filtering |
| `k8s-deploy` | Deployment dashboard with rollout status, scaling, restart, and rollback |
| `k8s-helm` | Helm release manager with upgrade, rollback, and uninstall actions |
| `k8s-cluster` | Cluster overview with node status, resource allocation, and health metrics |
| `k8s-cost` | Cost analyzer with waste detection and right-sizing recommendations |
| `k8s-events` | Events timeline with type filtering and resource grouping |
| `k8s-network` | Network topology graph showing Services, Pods, and Ingress connections |

## Prerequisites

- **Node.js** >= 18.0.0
- **kubectl-mcp-server** >= 1.21.0 (automatically spawned or connect to existing)
- **kubectl** configured with access to your Kubernetes cluster
- **Claude Desktop** (for MCP integration)

## Installation

### Via npm

```bash
npm install -g kubectl-mcp-app
```

### Via npx (no installation required)

```bash
npx kubectl-mcp-app
```

### From source

```bash
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server/kubectl-mcp-app
npm install
npm run build
npm link
```

## Quick Start

### 1. Configure Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "kubectl-app": {
      "command": "npx",
      "args": ["kubectl-mcp-app"]
    }
  }
}
```

### 2. Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the new MCP server.

### 3. Use the Tools

Ask Claude to use any of the Kubernetes UI tools:

- "Show me my pods using the k8s-pods UI"
- "Open the deployment dashboard"
- "Analyze my cluster costs"
- "Show the network topology for the default namespace"

## Configuration Modes

### Mode 1: Standalone (Default)

Spawns kubectl-mcp-server as a subprocess automatically.

```json
{
  "mcpServers": {
    "kubectl-app": {
      "command": "npx",
      "args": ["kubectl-mcp-app"]
    }
  }
}
```

### Mode 2: With Specific Context

Use a specific Kubernetes context:

```json
{
  "mcpServers": {
    "kubectl-app": {
      "command": "npx",
      "args": ["kubectl-mcp-app", "--context", "production-cluster"]
    }
  }
}
```

### Mode 3: Connect to Existing Server

Connect to an already-running kubectl-mcp-server:

```json
{
  "mcpServers": {
    "kubectl": {
      "command": "kubectl-mcp-server",
      "args": ["serve", "--transport", "streamable-http", "--port", "8000"]
    },
    "kubectl-app": {
      "command": "npx",
      "args": ["kubectl-mcp-app", "--backend", "http://localhost:8000/mcp"]
    }
  }
}
```

## CLI Options

```text
kubectl-mcp-app [OPTIONS]

OPTIONS:
  -b, --backend <URL>     Connect to remote kubectl-mcp-server backend
  -c, --context <NAME>    Kubernetes context to use
  -n, --namespace <NAME>  Default namespace
  -h, --help              Show help message
  -v, --version           Show version

EXAMPLES:
  kubectl-mcp-app                              # Start with defaults
  kubectl-mcp-app --context prod               # Use specific context
  kubectl-mcp-app --backend http://host:8000   # Connect to remote server
```

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP Host (Claude Desktop)                    │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐     ┌─────────────────────────────────────┐   │
│  │ kubectl-mcp-app │────▶│  Interactive UI (iframe)            │   │
│  │  (TypeScript)   │     │  - Pod Viewer                       │   │
│  │                 │     │  - Log Viewer                       │   │
│  │  Tools:         │     │  - Deployment Dashboard             │   │
│  │  - k8s-pods     │     │  - Helm Manager                     │   │
│  │  - k8s-logs     │     │  - Cluster Overview                 │   │
│  │  - k8s-deploy   │     │  - Cost Analyzer                    │   │
│  │  - k8s-helm     │     │  - Events Timeline                  │   │
│  │  - k8s-cluster  │     │  - Network Topology                 │   │
│  │  - k8s-cost     │     └─────────────────────────────────────┘   │
│  │  - k8s-events   │                      │                        │
│  │  - k8s-network  │                      │ callServerTool()       │
│  └────────┬────────┘                      │                        │
│           │                               ▼                        │
│           │              ┌─────────────────────────────────────┐   │
│           └─────────────▶│      kubectl-mcp-server             │   │
│              MCP proxy   │      (Python, 270+ tools)           │   │
│                          │      stdio/SSE/HTTP                 │   │
│                          └─────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## UI Features

### Pod Viewer (`k8s-pods`)
- Interactive table with sorting and filtering
- Status indicators (Running, Pending, Failed, CrashLoopBackOff, etc.)
- CPU/Memory usage progress bars
- Quick actions: View logs, Delete pod
- Namespace selector
- Search across all columns

### Log Viewer (`k8s-logs`)
- Real-time log streaming with auto-scroll
- Syntax highlighting for JSON and timestamps
- Regex search support
- Filter by log level (INFO, WARN, ERROR, DEBUG)
- Multi-container selector
- Download logs as file

### Deployment Dashboard (`k8s-deploy`)
- Replica count visualization with progress bars
- Rolling update status tracking
- Quick actions: Scale, Restart, Rollback
- Revision history
- Strategy information (RollingUpdate/Recreate)

### Helm Manager (`k8s-helm`)
- Release table with status badges
- Version and revision tracking
- Chart and app version display
- Actions: Upgrade, Rollback, Uninstall
- Release details modal

### Cluster Overview (`k8s-cluster`)
- Node health donut chart
- Pod count and namespace count
- Kubernetes version display
- Resource allocation (CPU/Memory) charts
- Node cards with status and resource usage

### Cost Analyzer (`k8s-cost`)
- Resource waste detection by namespace
- Right-sizing recommendations with confidence levels
- Potential savings calculator
- CPU/Memory usage vs requests charts
- Apply recommendations button

### Events Timeline (`k8s-events`)
- Vertical timeline visualization
- Event type filtering (Normal/Warning)
- Resource grouping by date
- Click-to-expand event details
- Auto-refresh toggle

### Network Topology (`k8s-network`)
- Force-directed graph visualization
- Shows Services, Pods, and Ingress
- Connection lines with port information
- Click to inspect node details
- Pan and zoom controls
- Legend for resource types

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server/kubectl-mcp-app

# Install dependencies
npm install

# Build everything
npm run build
```

### Commands

```bash
# Build UI components (all 8 UIs)
npm run build:ui

# Build server (TypeScript → JavaScript)
npm run build:server

# Build everything
npm run build

# Development mode with hot reload
npm run dev

# Type checking
npm run typecheck

# Run tests
npm test

# Run tests in watch mode
npm run test:watch
```

### Project Structure

```text
kubectl-mcp-app/
├── src/
│   ├── server.ts          # MCP server with tool/resource registration
│   ├── main.ts            # CLI entry point
│   ├── proxy.ts           # Proxy to kubectl-mcp-server
│   ├── types.ts           # Shared TypeScript types
│   └── ui/                # UI components
│       ├── shared/        # Shared components and utilities
│       │   ├── components/  # Table, StatusBadge, Chart, etc.
│       │   ├── theme.ts     # Dark/light theme support
│       │   └── k8s-client.ts
│       ├── pods/
│       ├── logs/
│       ├── deployments/
│       ├── helm/
│       ├── cluster/
│       ├── cost/
│       ├── events/
│       └── network/
├── test/                  # Test files
├── dist/                  # Build output
│   ├── server.js
│   ├── main.js
│   └── ui/                # Bundled single-file HTML apps
├── scripts/               # Build scripts
├── package.json
├── tsconfig.json
├── tsconfig.server.json
└── vite.config.ts
```

## Troubleshooting

### "kubectl-mcp-server not found"

Install kubectl-mcp-server:
```bash
pip install kubectl-mcp-server
```

Or use the `--backend` option to connect to a remote server.

### "No pods found"

Ensure kubectl is configured correctly:
```bash
kubectl get pods
```

### UI not loading

Check that the dist/ui/ directory contains the HTML files:
```bash
ls dist/ui/
```

If empty, rebuild the UIs:
```bash
npm run build:ui
```

### Connection timeout

If connecting to a remote backend, ensure:
1. The server is running and accessible
2. The URL includes the `/mcp` path
3. No firewall is blocking the connection

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines.

## License

MIT - see [LICENSE](./LICENSE) for details.

## Related Projects

- [kubectl-mcp-server](https://github.com/rohitg00/kubectl-mcp-server) - MCP server for Kubernetes with 270+ tools
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP specification
- [Claude Desktop](https://claude.ai/download) - Desktop app for Claude with MCP support
