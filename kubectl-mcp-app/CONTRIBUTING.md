# Contributing to kubectl-mcp-app

Thank you for your interest in contributing to kubectl-mcp-app!

## Development Setup

### Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0
- kubectl-mcp-server (for testing with real Kubernetes clusters)

### Getting Started

1. Clone the repository:
```bash
git clone https://github.com/rohitg00/kubectl-mcp-server.git
cd kubectl-mcp-server/kubectl-mcp-app
```

2. Install dependencies:
```bash
npm install
```

3. Build the project:
```bash
npm run build
```

## Project Structure

```text
kubectl-mcp-app/
├── src/
│   ├── server.ts          # MCP server with tool registration
│   ├── main.ts            # CLI entry point
│   ├── proxy.ts           # Proxy to kubectl-mcp-server
│   ├── types.ts           # Shared TypeScript types
│   └── ui/                # UI components
│       ├── shared/        # Shared components and utilities
│       │   ├── components/
│       │   ├── theme.ts
│       │   └── k8s-client.ts
│       ├── pods/          # Pod viewer
│       ├── logs/          # Log viewer
│       ├── deployments/   # Deployment dashboard
│       ├── helm/          # Helm manager
│       ├── cluster/       # Cluster overview
│       ├── cost/          # Cost analyzer
│       ├── events/        # Events timeline
│       └── network/       # Network topology
├── test/                  # Test files
├── dist/                  # Build output
└── scripts/               # Build scripts
```

## Development Workflow

### Building

```bash
# Build everything
npm run build

# Build only UI components
npm run build:ui

# Build only server
npm run build:server

# Type checking
npm run typecheck
```

### Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch
```

### Development Mode

```bash
# Start development with hot reload
npm run dev
```

## Adding a New UI

1. Create a new directory under `src/ui/`:
```bash
mkdir -p src/ui/my-feature
```

2. Create the required files:
   - `App.tsx` - Main React component
   - `mcp-app.html` - Entry HTML file

3. Update `src/server.ts` to register the new tool and resource

4. Update `vite.config.ts` to include the new UI in the build

5. Add tests in `test/`

## Code Style

- Use TypeScript for all new code
- Follow existing patterns in the codebase
- Keep components modular and reusable
- Use the shared theme and components when possible

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `npm test`
4. Run type check: `npm run typecheck`
5. Update documentation if needed
6. Submit a pull request

## UI Component Guidelines

### Using Shared Components

```tsx
import { Table, StatusBadge, ProgressBar } from "@shared/components";
import { baseStyles, getTheme } from "@shared/theme";
```

### Theme Support

All UIs should support dark/light theme:
```tsx
const [theme, setTheme] = useState<Theme>(getTheme());

const toggleTheme = () => {
  const newTheme = theme === "dark" ? "light" : "dark";
  setTheme(newTheme);
};
```

### Calling Server Tools

```tsx
const callTool = async (name: string, args: Record<string, unknown>) => {
  if (!window.callServerTool) return null;
  const result = await window.callServerTool({ name, arguments: args });
  return JSON.parse(result.content[0].text);
};
```

## Questions?

Feel free to open an issue for questions or discussions.
