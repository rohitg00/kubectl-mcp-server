#!/usr/bin/env node

/**
 * Post-install script for kubectl-mcp-server npm package
 * Checks for Python and optionally installs the Python package
 */

const { spawnSync } = require('child_process');

// ANSI color codes
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function getPythonCommand() {
  const commands = process.platform === 'win32'
    ? ['python', 'python3', 'py']
    : ['python3', 'python'];

  for (const cmd of commands) {
    try {
      const result = spawnSync(cmd, ['--version'], {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe']
      });
      if (result.status === 0) {
        const version = result.stdout.trim() || result.stderr.trim();
        return { cmd, version };
      }
    } catch (e) {
      // Continue
    }
  }
  return null;
}

function checkPythonPackage(pythonCmd) {
  try {
    const result = spawnSync(
      pythonCmd,
      ['-c', 'import kubectl_mcp_tool; print(kubectl_mcp_tool.__version__ if hasattr(kubectl_mcp_tool, "__version__") else "installed")'],
      { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
    );
    if (result.status === 0) {
      return result.stdout.trim();
    }
    return null;
  } catch (e) {
    return null;
  }
}

function checkKubectl() {
  try {
    const result = spawnSync('kubectl', ['version', '--client', '--short'], {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return result.status === 0;
  } catch (e) {
    return false;
  }
}

function main() {
  console.log('');
  log('='.repeat(60), 'cyan');
  log('  kubectl-mcp-server - Post-Installation Check', 'bold');
  log('='.repeat(60), 'cyan');
  console.log('');

  // Check Python
  const python = getPythonCommand();
  if (!python) {
    log('WARNING: Python 3.9+ is required but not found.', 'yellow');
    log('Please install Python from https://www.python.org/downloads/', 'yellow');
    log('The MCP server will attempt to install dependencies on first run.', 'yellow');
    console.log('');
  } else {
    log(`Found ${python.version}`, 'green');

    // Check if kubectl-mcp-tool is installed
    const pkgVersion = checkPythonPackage(python.cmd);
    if (pkgVersion) {
      log(`kubectl-mcp-tool Python package: v${pkgVersion}`, 'green');
    } else {
      log('kubectl-mcp-tool Python package: Not installed', 'yellow');
      log('It will be installed automatically on first run.', 'yellow');

      // Optionally install now
      if (process.env.KUBECTL_MCP_INSTALL_NOW === '1') {
        log('Installing kubectl-mcp-tool...', 'cyan');
        const result = spawnSync(python.cmd, ['-m', 'pip', 'install', 'kubectl-mcp-tool'], {
          stdio: 'inherit'
        });
        if (result.status === 0) {
          log('kubectl-mcp-tool installed successfully!', 'green');
        } else {
          log('Failed to install kubectl-mcp-tool. It will retry on first run.', 'yellow');
        }
      }
    }
  }

  // Check kubectl
  if (checkKubectl()) {
    log('kubectl CLI: Found', 'green');
  } else {
    log('kubectl CLI: Not found', 'yellow');
    log('Please install kubectl: https://kubernetes.io/docs/tasks/tools/', 'yellow');
  }

  console.log('');
  log('-'.repeat(60), 'cyan');
  log('  Quick Start', 'bold');
  log('-'.repeat(60), 'cyan');
  console.log('');
  log('  Run the MCP server:', 'reset');
  log('    npx kubectl-mcp-server', 'cyan');
  console.log('');
  log('  Or with options:', 'reset');
  log('    npx kubectl-mcp-server --transport sse --port 8000', 'cyan');
  console.log('');
  log('  Add to Claude Desktop config (claude_desktop_config.json):', 'reset');
  log(`    {
      "mcpServers": {
        "kubernetes": {
          "command": "npx",
          "args": ["-y", "kubectl-mcp-server"]
        }
      }
    }`, 'cyan');
  console.log('');
  log('='.repeat(60), 'cyan');
  console.log('');
}

main();
