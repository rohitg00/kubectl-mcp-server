#!/usr/bin/env node

import { startServer } from "./server.js";
import type { KubectlMcpServerConfig } from "./types.js";

function parseArgs(args: string[]): KubectlMcpServerConfig {
  const config: KubectlMcpServerConfig = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--backend" || arg === "-b") {
      const value = args[++i];
      if (!value || value.startsWith("-")) {
        console.error(`Error: --backend requires a URL argument`);
        process.exit(1);
      }
      config.backend = value;
    } else if (arg === "--context" || arg === "-c") {
      const value = args[++i];
      if (!value || value.startsWith("-")) {
        console.error(`Error: --context requires a NAME argument`);
        process.exit(1);
      }
      config.context = value;
    } else if (arg === "--namespace" || arg === "-n") {
      const value = args[++i];
      if (!value || value.startsWith("-")) {
        console.error(`Error: --namespace requires a NAME argument`);
        process.exit(1);
      }
      config.namespace = value;
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else if (arg === "--version" || arg === "-v") {
      console.log("kubectl-mcp-app v1.0.0");
      process.exit(0);
    }
  }

  return config;
}

function printHelp(): void {
  console.log(`
kubectl-mcp-app - Interactive UI add-on for kubectl-mcp-server

USAGE:
  kubectl-mcp-app [OPTIONS]

OPTIONS:
  -b, --backend <URL>     Connect to remote kubectl-mcp-server backend
  -c, --context <NAME>    Kubernetes context to use
  -n, --namespace <NAME>  Default namespace
  -h, --help              Show this help message
  -v, --version           Show version

EXAMPLES:
  # Start with default settings (spawns kubectl-mcp-server subprocess)
  kubectl-mcp-app

  # Connect to a remote backend
  kubectl-mcp-app --backend http://localhost:8000/mcp

  # Use a specific Kubernetes context
  kubectl-mcp-app --context production-cluster

CLAUDE DESKTOP CONFIGURATION:
  {
    "mcpServers": {
      "kubectl-app": {
        "command": "npx",
        "args": ["kubectl-mcp-app"]
      }
    }
  }

AVAILABLE UI TOOLS:
  k8s-pods        Interactive pod viewer
  k8s-logs        Real-time log viewer
  k8s-deploy      Deployment dashboard
  k8s-helm        Helm release manager
  k8s-cluster     Cluster overview
  k8s-cost        Cost analyzer
  k8s-events      Events timeline
  k8s-network     Network topology

For more information, visit:
  https://github.com/rohitg00/kubectl-mcp-server
`);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const config = parseArgs(args);

  process.on("SIGINT", () => {
    console.error("\n[main] Received SIGINT, shutting down...");
    process.exit(0);
  });

  process.on("SIGTERM", () => {
    console.error("[main] Received SIGTERM, shutting down...");
    process.exit(0);
  });

  try {
    await startServer(config);
  } catch (error) {
    console.error(
      "[main] Failed to start server:",
      error instanceof Error ? error.message : error
    );
    process.exit(1);
  }
}

main();
