# Kubernetes Skills for AI Coding Agents

Multi-agent Kubernetes skills powered by [kubectl-mcp-server](https://github.com/rohitg00/kubectl-mcp-server) (270+ tools).

## Overview

This directory contains Kubernetes operational skills in Claude format (`SKILL.md`). Use [SkillKit](https://github.com/rohitg00/skillkit) to convert to your preferred AI agent format.

Skills follow the [agenstskills.com](https://agenstskills.com) specification with enhanced frontmatter, activation triggers, and priority rules.

## Directory Structure

```
kubernetes-skills/
├── README.md
├── claude/                 # Source skills (26 skills)
│   ├── k8s-core/           # Pods, namespaces, configmaps, secrets
│   ├── k8s-networking/     # Services, ingress, network policies
│   ├── k8s-storage/        # PVCs, storage classes, volumes
│   ├── k8s-deploy/         # Deployments, StatefulSets, DaemonSets
│   │   ├── SKILL.md
│   │   ├── references/     # Strategy documentation
│   │   └── examples/       # Runnable YAML manifests
│   ├── k8s-operations/     # kubectl apply/patch/delete/exec
│   ├── k8s-helm/           # Helm charts and releases
│   │   ├── SKILL.md
│   │   ├── references/     # Chart structure docs
│   │   └── scripts/        # Executable scripts
│   ├── k8s-diagnostics/    # Metrics, health checks
│   ├── k8s-troubleshoot/   # Debug pods, nodes, workloads
│   │   ├── SKILL.md
│   │   └── references/     # Decision trees, error guides
│   ├── k8s-incident/       # Emergency runbooks
│   ├── k8s-security/       # RBAC, service accounts
│   ├── k8s-policy/         # Kyverno/Gatekeeper policies
│   ├── k8s-certs/          # Cert-manager certificates
│   ├── k8s-gitops/         # Flux and ArgoCD
│   ├── k8s-rollouts/       # Argo Rollouts/Flagger
│   ├── k8s-autoscaling/    # HPA, VPA, KEDA
│   │   ├── SKILL.md
│   │   └── examples/       # HPA and KEDA manifests
│   ├── k8s-cost/           # Cost optimization
│   ├── k8s-backup/         # Velero backup/restore
│   ├── k8s-multicluster/   # Multi-cluster operations
│   ├── k8s-capi/           # Cluster API lifecycle
│   ├── k8s-kubevirt/       # KubeVirt VMs
│   ├── k8s-service-mesh/   # Istio traffic management
│   ├── k8s-cilium/         # Cilium/Hubble observability
│   ├── k8s-vind/           # vCluster virtual clusters
│   │   ├── SKILL.md
│   │   └── references/     # Workflow documentation
│   ├── k8s-kind/           # kind local clusters
│   │   ├── SKILL.md
│   │   └── references/     # Configuration examples
│   └── k8s-cli/            # MCP server CLI
```

## Skill Format

Each skill follows the enhanced agenstskills.com specification:

```yaml
---
name: k8s-troubleshoot
description: Debug Kubernetes pods, nodes, and workloads...
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 15
  category: observability
---

# Kubernetes Troubleshooting

## When to Apply
Use this skill when:
- User mentions: "debug", "troubleshoot", "failing", "crash"
- Pod states: Pending, CrashLoopBackOff, ImagePullBackOff
- Keywords: "logs", "events", "describe"

## Priority Rules
| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Check pod status first | CRITICAL | `kubectl_get` |
| 2 | View recent events | CRITICAL | `kubectl_get` |
| 3 | Inspect logs | HIGH | `kubectl_logs` |

## Quick Reference
| Task | Tool | Example |
|------|------|---------|
| Get pods | `kubectl_get` | `kubectl_get(resource_type="pods", namespace)` |
```

## Installation

### Option 1: skills CLI (any agent)

[`npx skills`](https://skills.sh) installs into Claude Code, Codex, Cursor, OpenCode, Gemini CLI and 70+ other agents:

```bash
# Pick skills and agents interactively
npx skills add rohitg00/kubectl-mcp-server

# One skill for one agent
npx skills add rohitg00/kubectl-mcp-server --skill k8s-helm --agent claude-code

# Every skill, user-level, no prompts
npx skills add rohitg00/kubectl-mcp-server --skill '*' -g -y

# List the skills without installing
npx skills add rohitg00/kubectl-mcp-server --list
```

### Option 2: ClawHub (OpenClaw)

Every skill is published to [ClawHub](https://clawhub.ai/rohitg00) and re-synced from this directory on each merge to `main`:

```bash
openclaw skills install @rohitg00/k8s-helm
# or
npx clawhub install @rohitg00/k8s-helm
```

### Option 3: Copy into Claude Code

```bash
cp -r kubernetes-skills/claude/* ~/.claude/skills/
```

### Option 4: Other formats via SkillKit

Install [SkillKit](https://github.com/rohitg00/skillkit):

```bash
npm install -g skillkit
```

Convert to your agent:

```bash
# Convert all skills to Cursor format
skillkit translate kubernetes-skills/claude --to cursor --output .cursor/rules/

# Convert all skills to Codex format
skillkit translate kubernetes-skills/claude --to codex --output ./

# Convert all skills to any supported agent
skillkit translate kubernetes-skills/claude --to <agent> --output <dir>
```

**Supported agents:** cursor, codex, gemini-cli, github-copilot, goose, kilo, roo, windsurf, amp, universal

### Option 5: Manual Conversion

Each `SKILL.md` file contains:
- YAML frontmatter with `name` and `description`
- Markdown content with tool references and workflows

Convert manually by copying the content to your agent's format:

| Agent | Target File |
|-------|-------------|
| Cursor | `.cursor/rules/<skill>.mdc` |
| Codex | `AGENTS.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Windsurf | `.windsurf/rules/<skill>.md` |
| Goose | `.goose/instructions.md` |

## Skill Coverage (25 Skills)

| Category | Skills |
|----------|--------|
| **Core Resources** | k8s-core, k8s-networking, k8s-storage |
| **Workloads** | k8s-deploy, k8s-operations, k8s-helm |
| **Observability** | k8s-diagnostics, k8s-troubleshoot, k8s-incident |
| **Security** | k8s-security, k8s-policy, k8s-certs |
| **GitOps** | k8s-gitops, k8s-rollouts |
| **Scaling** | k8s-autoscaling, k8s-cost, k8s-backup |
| **Multi-Cluster** | k8s-multicluster, k8s-capi, k8s-kubevirt |
| **Networking** | k8s-service-mesh, k8s-cilium |
| **Development** | k8s-vind, k8s-kind |
| **Tools** | k8s-cli |

## MCP Server Features

### Toolsets

The server registers only the `core` and `helm` toolsets by default. Skills that need another toolset say so at the top; start the server with `--toolsets default,<name>` (or `MCP_TOOLSETS`) to load it.

| Toolset | Default | Tools | Covers |
|---------|---------|-------|--------|
| `core` | yes | 18 | Generic kubectl operations for every resource kind, including CRDs |
| `helm` | yes | 8 | Helm release lifecycle |
| `helm_dev` |  | 16 | Helm charts and repositories: search, show, template, lint, package, dependencies |
| `ops` |  | 10 | Maintenance: create, label, annotate, taint, cordon/drain, copy files, wait, cleanup |
| `diagnostics` |  | 9 | Network, DNS, node and pod health diagnostics |
| `security` |  | 5 | RBAC, pod security and secret hygiene audits |
| `cost` |  | 8 | Resource right-sizing and cost allocation |
| `multicluster` |  | 7 | Kubeconfig contexts and cross-cluster queries |
| `crds` |  | 5 | CRD discovery and custom resource inspection |
| `gitops` |  | 6 | Flux and Argo CD |
| `certs` |  | 8 | cert-manager certificates and issuers |
| `policy` |  | 5 | Kyverno and Gatekeeper policies |
| `backup` |  | 10 | Velero backups and restores |
| `keda` |  | 6 | KEDA event-driven autoscaling |
| `cilium` |  | 7 | Cilium network policies and Hubble flows |
| `rollouts` |  | 10 | Argo Rollouts and Flagger progressive delivery |
| `capi` |  | 10 | Cluster API lifecycle |
| `kubevirt` |  | 12 | KubeVirt virtual machines |
| `istio` |  | 9 | Istio service mesh |
| `kind` |  | 29 | kind local clusters (runs docker on the server host) |
| `vind` |  | 11 | vCluster virtual clusters (runs vcluster on the server host) |

Resources, prompts and the full tool list are documented in the [main README](../README.md#toolsets).

### CLI Commands

```bash
# List all tools
kubectl-mcp-server tools -d

# Show tool schema
kubectl-mcp-server tools kubectl_get

# Search tools
kubectl-mcp-server grep "*helm*"

# Call tool directly
kubectl-mcp-server call kubectl_get '{"resource_type": "pods", "namespace": "default"}'

# Check dependencies
kubectl-mcp-server doctor

# Show/switch context
kubectl-mcp-server context
kubectl-mcp-server context production
```

## MCP Server Setup

```bash
# Install
pip install kubectl-mcp-server

# Run (HTTP transport)
kubectl-mcp-server serve --transport streamable-http --port 8000

# Run (stdio for Claude Desktop)
kubectl-mcp-server serve

# Verify
kubectl-mcp-server doctor
```

### Claude Desktop Config

```json
{
  "mcpServers": {
    "kubectl": {
      "command": "kubectl-mcp-server",
      "args": ["serve"]
    }
  }
}
```

### Docker

```bash
docker run -v ~/.kube:/root/.kube rohitghumare64/kubectl-mcp-server:latest
```

## References

- [kubectl-mcp-server](https://github.com/rohitg00/kubectl-mcp-server) - 270+ Kubernetes MCP tools
- [SkillKit](https://github.com/rohitg00/skillkit) - Universal CLI for AI agent skills
- [agenstskills.com](https://agenstskills.com) - Agent skills specification
- [MCP Protocol](https://modelcontextprotocol.io/) - Model Context Protocol spec

## License

Apache-2.0
