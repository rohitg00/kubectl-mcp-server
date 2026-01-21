#!/usr/bin/env node

const { spawn, spawnSync } = require('child_process');

const colors = { red: '\x1b[31m', green: '\x1b[32m', yellow: '\x1b[33m', reset: '\x1b[0m' };
const log = (msg, color = 'reset') => console.error(`${colors[color]}${msg}${colors.reset}`);

function getPythonCommand() {
  const commands = process.platform === 'win32' ? ['python', 'python3', 'py'] : ['python3', 'python'];
  for (const cmd of commands) {
    try {
      if (spawnSync(cmd, ['--version'], { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).status === 0) return cmd;
    } catch (e) {}
  }
  return null;
}

function checkPythonPackage(pythonCmd) {
  try {
    return spawnSync(pythonCmd, ['-c', 'import kubectl_mcp_tool'], { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).status === 0;
  } catch (e) {
    return false;
  }
}

function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
kubectl-mcp-server - MCP Server for Kubernetes

Usage: kubectl-mcp-server [options]

Options:
  --transport <mode>   Transport: stdio, sse, http, streamable-http (default: stdio)
  --host <host>        Host for network transports (default: 0.0.0.0)
  --port <port>        Port for network transports (default: 8000)
  --non-destructive    Block destructive operations
  --help, -h           Show this help message
  --version, -v        Show version

For more info: https://github.com/rohitg00/kubectl-mcp-server
`);
    process.exit(0);
  }

  if (args.includes('--version') || args.includes('-v')) {
    console.log(`kubectl-mcp-server v${require('../package.json').version}`);
    process.exit(0);
  }

  const pythonCmd = getPythonCommand();
  if (!pythonCmd) {
    log('Error: Python 3.9+ is required. Install from https://python.org', 'red');
    process.exit(1);
  }

  if (!checkPythonPackage(pythonCmd)) {
    log('Installing kubectl-mcp-tool...', 'yellow');
    if (spawnSync(pythonCmd, ['-m', 'pip', 'install', 'kubectl-mcp-tool'], { stdio: 'inherit' }).status !== 0) {
      log('Failed to install. Try: pip install kubectl-mcp-tool', 'red');
      process.exit(1);
    }
    log('Installed successfully!', 'green');
  }

  const server = spawn(pythonCmd, ['-m', 'kubectl_mcp_tool.mcp_server', ...args], {
    stdio: 'inherit',
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  server.on('error', (err) => { log(`Error: ${err.message}`, 'red'); process.exit(1); });
  server.on('close', (code) => process.exit(code || 0));
  process.on('SIGINT', () => server.kill('SIGINT'));
  process.on('SIGTERM', () => server.kill('SIGTERM'));
}

main();
