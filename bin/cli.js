#!/usr/bin/env node

const {
    spawn,
    spawnSync
} = require('child_process');

const VERSION = require('../package.json').version;
const PACKAGE = `kubectl-mcp-server==${VERSION}`;

const colors = {
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    reset: '\x1b[0m'
};
const log = (msg, color = 'reset') => console.error(`${colors[color]}${msg}${colors.reset}`);

function run(cmd, args) {
    try {
        return spawnSync(cmd, args, {
            encoding: 'utf8',
            stdio: ['ignore', 'pipe', 'pipe']
        });
    } catch (e) {
        return {
            status: 1,
            stdout: ''
        };
    }
}

function getPythonCommand() {
    const commands = process.platform === 'win32' ? ['python', 'python3', 'py'] : ['python3', 'python'];
    return commands.find((cmd) => run(cmd, ['--version']).status === 0) || null;
}

function isAtLeast(installed, required) {
    const a = installed.split('.').map((n) => parseInt(n, 10) || 0);
    const b = required.split('.').map((n) => parseInt(n, 10) || 0);
    for (let i = 0; i < 3; i++) {
        if ((a[i] || 0) !== (b[i] || 0)) return (a[i] || 0) > (b[i] || 0);
    }
    return true;
}

function installedVersion(pythonCmd) {
    const result = run(pythonCmd, ['-c', 'import kubectl_mcp_tool; print(kubectl_mcp_tool.__version__)']);
    return result.status === 0 ? result.stdout.trim() : null;
}

function launch(cmd, args) {
    const server = spawn(cmd, args, {
        stdio: 'inherit',
        env: {
            ...process.env,
            PYTHONUNBUFFERED: '1'
        }
    });
    server.on('error', (err) => {
        log(`Error: ${err.message}`, 'red');
        process.exit(1);
    });
    server.on('close', (code) => process.exit(code || 0));
    process.on('SIGINT', () => server.kill('SIGINT'));
    process.on('SIGTERM', () => server.kill('SIGTERM'));
}

function main() {
    const args = process.argv.slice(2);

    if (args.includes('--help') || args.includes('-h')) {
        console.log(`
kubectl-mcp-server - stateless MCP server for Kubernetes

Usage: kubectl-mcp-server [options]

Options:
  --transport <mode>       stdio (default), http | streamable-http (stateless), sse (deprecated)
  --host <host>            Bind address for network transports (default: 127.0.0.1)
  --port <port>            Port for network transports (default: 8000)
  --allow-unauthenticated  Allow a non-loopback bind without OAuth (MCP_ALLOW_UNAUTHENTICATED)
  --read-only              Hide and block every tool that modifies state
  --disable-destructive    Block delete operations (alias: --non-destructive)
  --confirm-destructive    Ask the user before destructive operations
  --config <path>          Path to TOML configuration file
  --stateless              Do not cache Kubernetes API clients
  --watch-kubeconfig       Reload kubeconfig when the file changes
  --watch-interval <sec>   Interval for kubeconfig watch checks (default: 5.0)
  --help, -h               Show this help message
  --version, -v            Show version

Runs ${PACKAGE} via uvx when available, otherwise from the local Python.
More info: https://github.com/rohitg00/kubectl-mcp-server
`);
        process.exit(0);
    }

    if (args.includes('--version') || args.includes('-v')) {
        console.log(`kubectl-mcp-server v${VERSION}`);
        process.exit(0);
    }

    if (run('uvx', ['--version']).status === 0) {
        launch('uvx', ['--from', PACKAGE, 'kubectl-mcp', ...args]);
        return;
    }

    const pythonCmd = getPythonCommand();
    if (!pythonCmd) {
        log('Error: Python 3.10+ (or uv) is required. Install uv: https://docs.astral.sh/uv/', 'red');
        process.exit(1);
    }

    const current = installedVersion(pythonCmd);
    if (!current || !isAtLeast(current, VERSION)) {
        log(current ? `Upgrading kubectl-mcp-server ${current} -> ${VERSION}...` : `Installing ${PACKAGE}...`, 'yellow');
        const pip = spawnSync(pythonCmd, ['-m', 'pip', 'install', '--upgrade', PACKAGE], {
            stdio: ['ignore', 2, 2]
        });
        if (pip.status !== 0) {
            log(`Failed to install. Use uv (recommended): uvx --from ${PACKAGE} kubectl-mcp`, 'red');
            log(`or pipx: pipx install ${PACKAGE}`, 'red');
            process.exit(1);
        }
        log('Installed.', 'green');
    }

    launch(pythonCmd, ['-m', 'kubectl_mcp_tool.mcp_server', ...args]);
}

main();