# kubectl-mcp-server Evals Framework

This directory contains the evaluation framework for testing kubectl-mcp-server with different AI agents.

## Purpose

The evals framework provides:
- **Standardized test tasks** for validating MCP tool functionality
- **Agent configurations** for different AI coding assistants (Claude Code, OpenAI, etc.)
- **Assertion patterns** for verifying correct tool invocations
- **Setup/verify/cleanup scripts** for reproducible test environments

## Directory Structure

```
evals/
├── README.md              # This file
├── mcp-config.yaml        # MCP server configuration for evals
├── tasks/                 # Task definitions
│   ├── create-pod.yaml    # Create a basic pod
│   ├── deploy-app.yaml    # Deploy an application with service
│   ├── helm-install.yaml  # Install a Helm chart
│   ├── multi-cluster.yaml # Multi-cluster operations
│   ├── diagnostics.yaml   # Run diagnostic tools
│   ├── setup.sh           # Namespace setup script
│   ├── verify.sh          # Verification script
│   └── cleanup.sh         # Cleanup script
├── claude-code/           # Claude Code agent configuration
│   ├── agent.yaml         # Agent definition
│   └── eval.yaml          # Eval definition
└── openai-agent/          # OpenAI agent configuration
    ├── agent.yaml         # Agent definition
    └── eval.yaml          # Eval definition
```

## Running Evals

### Prerequisites

1. A running Kubernetes cluster (minikube, kind, or real cluster)
2. kubectl configured with cluster access
3. The target AI agent installed (Claude Code, OpenAI Codex, etc.)
4. kubectl-mcp-server installed: `pip install kubectl-mcp-server`

### Quick Start

```bash
# 1. Set up the test namespace
./evals/tasks/setup.sh

# 2. Run eval with Claude Code
cd evals/claude-code
claude --mcp-config ../mcp-config.yaml --print "$(cat ../tasks/create-pod.yaml | yq '.prompt')"

# 3. Verify the result
./evals/tasks/verify.sh

# 4. Clean up
./evals/tasks/cleanup.sh
```

### Using an Eval Runner

For automated evaluation, use an eval runner like [mcp-eval](https://github.com/mcp-eval):

```bash
# Install mcp-eval
npm install -g mcp-eval

# Run all evals for Claude Code
mcp-eval run --config evals/claude-code/eval.yaml

# Run specific task
mcp-eval run --config evals/claude-code/eval.yaml --task create-nginx-pod
```

## Adding New Tasks

### Task YAML Format

Create a new YAML file in `tasks/` with this structure:

```yaml
# Task metadata
name: my-custom-task
description: Description of what this task tests
category: core|networking|storage|helm|advanced

# Setup phase (optional)
setup:
  script: ./setup.sh
  # Or inline commands:
  commands:
    - kubectl create namespace my-test-ns

# The prompt to send to the AI agent
prompt: |
  Create a deployment named my-app with 3 replicas
  using the nginx:latest image in the eval-test namespace

# Expected tool invocations and outputs
assertions:
  # Tool name patterns (regex supported)
  - toolPattern: "(create_deployment|apply_manifest)"
  # Expected strings in output
  - outputContains: "created"
  - outputContains: "my-app"
  # Tool parameters (optional)
  - toolParams:
      name: "my-app"
      replicas: 3
  # Custom assertion script (optional)
  - script: |
      kubectl get deployment my-app -n eval-test -o json | jq -e '.spec.replicas == 3'

# Verification phase
verify:
  script: ./verify.sh
  # Or inline commands:
  commands:
    - kubectl get deployment my-app -n eval-test
  # Expected exit code (default: 0)
  exitCode: 0

# Cleanup phase
cleanup:
  script: ./cleanup.sh
  # Or inline commands:
  commands:
    - kubectl delete namespace my-test-ns --ignore-not-found

# Timeout in seconds (default: 60)
timeout: 120

# Tags for filtering
tags:
  - deployment
  - core
```

### Assertions Format

Assertions validate that the AI agent used the correct MCP tools:

| Field | Description | Example |
|-------|-------------|---------|
| `toolPattern` | Regex pattern for tool names | `"(get_pods\|list_pods)"` |
| `toolCalled` | Exact tool name | `"run_pod"` |
| `outputContains` | String that must appear in output | `"created"` |
| `outputMatches` | Regex pattern for output | `"pod/.*created"` |
| `outputNotContains` | String that must NOT appear | `"error"` |
| `toolParams` | Expected tool parameters | `{name: "web", image: "nginx"}` |
| `script` | Custom bash script assertion | `kubectl get pod ...` |

### Task Categories

- **core**: Basic pod, deployment, service operations
- **networking**: Ingress, network policies, services
- **storage**: PVCs, ConfigMaps, Secrets
- **helm**: Helm chart operations
- **advanced**: Multi-cluster, RBAC, diagnostics

## Agent Configuration

### Agent YAML Format

```yaml
name: agent-name
type: claude-code|openai|custom

# How to invoke the agent
commands:
  # Template for passing MCP config file
  argTemplateMcpServer: "--mcp-config {{ .File }}"
  # Full command template
  runPrompt: 'agent-cli {{ .McpServerFileArgs }} --print "{{ .Prompt }}"'

# Environment variables
env:
  AGENT_API_KEY: "${AGENT_API_KEY}"

# Agent-specific settings
settings:
  model: claude-3-opus
  maxTokens: 4096
```

### Eval YAML Format

```yaml
name: eval-suite-name
description: Description of this eval suite

# Agent to use
agent:
  file: agent.yaml

# MCP server configuration
mcpServer:
  file: ../mcp-config.yaml

# Tasks to run
tasks:
  - file: ../tasks/create-pod.yaml
  - file: ../tasks/deploy-app.yaml
  - file: ../tasks/helm-install.yaml

# Global settings
settings:
  parallel: false
  stopOnFailure: true
  timeout: 300
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EVAL_NAMESPACE` | Namespace for test resources | `eval-test` |
| `EVAL_TIMEOUT` | Default task timeout (seconds) | `60` |
| `EVAL_CLEANUP` | Auto-cleanup on completion | `true` |
| `MCP_DEBUG` | Enable MCP debug logging | `false` |
| `K8S_CONTEXT` | Kubernetes context to use | Current context |

## Results

Eval results are stored in `results/` directory:

```
results/
├── 2024-01-20T10-30-00/
│   ├── summary.json       # Overall results
│   ├── create-pod.json    # Individual task results
│   └── logs/
│       └── create-pod.log # Agent interaction logs
```

### Result Format

```json
{
  "eval": "kubectl-mcp-server-claude-code",
  "timestamp": "2024-01-20T10:30:00Z",
  "duration": 45.2,
  "tasks": {
    "total": 5,
    "passed": 4,
    "failed": 1
  },
  "results": [
    {
      "task": "create-nginx-pod",
      "status": "passed",
      "duration": 8.5,
      "toolsCalled": ["run_pod"],
      "assertions": {
        "total": 3,
        "passed": 3
      }
    }
  ]
}
```

## Contributing

1. Add new tasks to `tasks/` directory
2. Follow the YAML format specification above
3. Include setup, verify, and cleanup steps
4. Test with at least one agent before submitting
5. Update this README if adding new features

## Troubleshooting

### Common Issues

**Agent doesn't find MCP server**
- Verify `mcp-config.yaml` path is correct
- Check MCP server is installed: `which kubectl-mcp-server`

**Task times out**
- Increase timeout in task YAML
- Check cluster connectivity: `kubectl cluster-info`

**Assertions fail unexpectedly**
- Enable debug mode: `MCP_DEBUG=true`
- Check tool output in results logs

**Cleanup fails**
- Manually clean up: `kubectl delete namespace eval-test`
- Check for finalizers blocking deletion
