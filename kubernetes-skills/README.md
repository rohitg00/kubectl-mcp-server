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

### Option 1: Claude (Direct)

```bash
# Copy skills to Claude
cp -r kubernetes-skills/claude/* ~/.claude/skills/
```

### Option 2: Other Agents (via SkillKit)

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

### Option 3: Manual Conversion

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

## Skill Coverage (26 Skills)

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

### Tool Categories (280+ tools)

| Category | Tools | Examples |
|----------|-------|----------|
| **Core** | 17 | `kubectl_get`, `kubectl_get`, `kubectl_get`, `kubectl_get` |
| **Deployments** | 10 | `kubectl_scale`, `kubectl_rollout`, `kubectl_patch` |
| **Networking** | 8 | `kubectl_get`, `kubectl_get`, `analyze_network_policies` |
| **Storage** | 3 | `kubectl_get`, `kubectl_get`, `kubectl_get` |
| **Security** | 10 | `kubectl_get`, `kubectl_get`, `kubectl_get` |
| **Helm** | 16 | `install_helm_chart`, `upgrade_helm_chart`, `helm_rollback` |
| **Operations** | 14 | `kubectl_apply`, `delete_resource`, `kubectl_patch`, `exec_in_pod` |
| **Diagnostics** | 3 | `compare_namespaces`, `kubectl_top`, `cluster_health_check` |
| **Cost** | 8 | `kubectl_get`, `get_overprovisioned_resources`, `get_idle_resources` |
| **GitOps** | 7 | `gitops_apps_list`, `gitops_app_sync`, `gitops_app_status` |
| **Cert-Manager** | 9 | `list_certs`, `list_cert_issuers` |
| **Policy** | 6 | `get_policy_list`, `get_policy_violations` |
| **Backup** | 11 | `list_backups`, `create_backup`, `create_restore` |
| **KEDA** | 7 | `keda_scaledobjects_list`, `keda_scaledjobs_list` |
| **Cilium** | 8 | `cilium_list_policies`, `get_hubble_flows` |
| **Rollouts** | 11 | `promote_rollout`, `abort_rollout`, `get_flagger_canaries` |
| **Cluster API** | 11 | `capi_list_clusters`, `capi_list_machines` |
| **KubeVirt** | 13 | `kubevirt_vms_list`, `kubevirt_vm_start`, `kubevirt_vm_migrate` |
| **Istio** | 10 | `istio_virtualservices_list`, `istio_analyze`, `istio_proxy_status` |
| **vCluster (vind)** | 14 | `vind_create_cluster`, `vind_connect`, `vind_pause` |
| **kind** | 32 | `kind_create_cluster`, `kind_load_image`, `kind_get_kubeconfig` |

### MCP Resources (8)

| Resource | Description |
|----------|-------------|
| `cluster://status` | Cluster health and version info |
| `namespaces://list` | All namespaces with status |
| `pods://{namespace}` | Pods in a namespace |
| `deployments://{namespace}` | Deployments in a namespace |
| `services://{namespace}` | Services in a namespace |
| `events://{namespace}` | Recent events |
| `nodes://list` | Node status and capacity |
| `contexts://list` | Available kubeconfig contexts |

### MCP Prompts (8)

| Prompt | Description |
|--------|-------------|
| `troubleshoot-pod` | Debug a failing pod |
| `deploy-application` | Deploy with best practices |
| `security-audit` | RBAC and policy review |
| `cost-optimization` | Find savings opportunities |
| `incident-response` | Emergency debugging |
| `helm-workflow` | Helm chart operations |
| `gitops-sync` | Flux/ArgoCD reconciliation |
| `multi-cluster-compare` | Cross-cluster analysis |

### CLI Commands

```bash
# List all tools
kubectl-mcp-server tools -d

# Show tool schema
kubectl-mcp-server tools kubectl_get

# Search tools
kubectl-mcp-server grep "*helm*"

# Call tool directly
kubectl-mcp-server call kubectl_get '{"namespace": "default"}'

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
