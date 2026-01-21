#!/usr/bin/env node

const { spawn } = require('child_process');
const { existsSync } = require('fs');
const path = require('path');
const os = require('os');

// ANSI color codes
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(message, color = 'reset') {
  console.error(`${colors[color]}${message}${colors.reset}`);
}

function getPythonCommand() {
  // Try different Python commands
  const commands = process.platform === 'win32'
    ? ['python', 'python3', 'py']
    : ['python3', 'python'];

  for (const cmd of commands) {
    try {
      const result = require('child_process').spawnSync(cmd, ['--version'], {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe']
      });
      if (result.status === 0) {
        return cmd;
      }
    } catch (e) {
      // Continue to next command
    }
  }
  return null;
}

function checkPythonPackage(pythonCmd) {
  try {
    const result = require('child_process').spawnSync(
      pythonCmd,
      ['-c', 'import kubectl_mcp_tool; print(kubectl_mcp_tool.__file__)'],
      { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
    );
    return result.status === 0;
  } catch (e) {
    return false;
  }
}

function main() {
  const args = process.argv.slice(2);

  // Handle help flag
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
kubectl-mcp-server - MCP Server for Kubernetes

Usage: kubectl-mcp-server [options]

Options:
  --transport <mode>     Transport mode: stdio, sse, http, streamable-http (default: stdio)
  --host <host>          Host to bind for network transports (default: 0.0.0.0)
  --port <port>          Port for network transports (default: 8000)
  --non-destructive      Block destructive operations (delete, apply, create, etc.)
  --help, -h             Show this help message
  --version, -v          Show version

Examples:
  kubectl-mcp-server                           # Start with stdio transport
  kubectl-mcp-server --transport sse           # Start with SSE transport
  kubectl-mcp-server --transport http --port 3000

Environment Variables:
  KUBECONFIG             Path to kubeconfig file (default: ~/.kube/config)
  MCP_DEBUG              Set to "1" for verbose logging
  MCP_LOG_FILE           Path to log file

For more information, visit: https://github.com/rohitg00/kubectl-mcp-server
`);
    process.exit(0);
  }

  // Handle version flag
  if (args.includes('--version') || args.includes('-v')) {
    const pkg = require('../package.json');
    console.log(`kubectl-mcp-server v${pkg.version}`);
    process.exit(0);
  }

  // Check for Python
  const pythonCmd = getPythonCommand();
  if (!pythonCmd) {
    log('Error: Python 3.9+ is required but not found.', 'red');
    log('Please install Python from https://www.python.org/downloads/', 'yellow');
    process.exit(1);
  }

  // Check if kubectl-mcp-tool is installed
  if (!checkPythonPackage(pythonCmd)) {
    log('kubectl-mcp-tool Python package not found. Installing...', 'yellow');

    const installResult = require('child_process').spawnSync(
      pythonCmd,
      ['-m', 'pip', 'install', 'kubectl-mcp-tool'],
      { stdio: 'inherit' }
    );

    if (installResult.status !== 0) {
      log('Error: Failed to install kubectl-mcp-tool package.', 'red');
      log('Try installing manually: pip install kubectl-mcp-tool', 'yellow');
      process.exit(1);
    }

    log('kubectl-mcp-tool installed successfully!', 'green');
  }

  // Run the Python MCP server
  const serverArgs = ['-m', 'kubectl_mcp_tool.mcp_server', ...args];

  const server = spawn(pythonCmd, serverArgs, {
    stdio: 'inherit',
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1'
    }
  });

  server.on('error', (err) => {
    log(`Error starting MCP server: ${err.message}`, 'red');
    process.exit(1);
  });

  server.on('close', (code) => {
    process.exit(code || 0);
  });

  // Handle signals
  process.on('SIGINT', () => {
    server.kill('SIGINT');
  });

  process.on('SIGTERM', () => {
    server.kill('SIGTERM');
  });
}

main();
