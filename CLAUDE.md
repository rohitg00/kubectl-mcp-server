# kubectl-mcp-server Project Memory

## Project Overview
- **Name**: kubectl-mcp-server
- **Version**: 1.21.0
- **Description**: A Model Context Protocol (MCP) server for Kubernetes with 270+ tools, 8 resources, and 8 prompts
- **Framework**: FastMCP 3.0.0b1 (Python)
- **Repository**: https://github.com/rohitg00/kubectl-mcp-server

## Current State (as of 2026-01-29)

### Latest Release: v1.21.0
- **Changes**: Comprehensive kind support - expanded from 15 to 32 tools
- **Tool Count**: 270 core tools
- **Skills**: 26 Agent Skills covering all tools
- **Optional**: 26 browser tools (with MCP_BROWSER_ENABLED=true)

### Release v1.21.0 Changes

#### Comprehensive kind (Kubernetes IN Docker) Support
Expanded kind toolset from 15 to 32 tools covering all kind CLI capabilities:

**New kind Tools (17 additional tools):**

**Configuration Management:**
| Tool | Description |
|------|-------------|
| `kind_config_validate_tool` | Validate kind config YAML before cluster creation |
| `kind_config_generate_tool` | Generate sample config for multi-node/HA clusters |
| `kind_config_show_tool` | Show effective config for a running cluster |
| `kind_available_images_tool` | List available kindest/node images (K8s versions) |

**Registry Integration:**
| Tool | Description |
|------|-------------|
| `kind_registry_create_tool` | Create local Docker registry for kind |
| `kind_registry_connect_tool` | Connect cluster to local registry |
| `kind_registry_status_tool` | Check local registry status and config |

**Node Management:**
| Tool | Description |
|------|-------------|
| `kind_node_exec_tool` | Execute command on kind node (docker exec) |
| `kind_node_logs_tool` | Get logs from specific node |
| `kind_node_inspect_tool` | Inspect node container details |
| `kind_node_restart_tool` | Restart a kind node container |

**Networking & Ports:**
| Tool | Description |
|------|-------------|
| `kind_network_inspect_tool` | Inspect kind Docker network |
| `kind_port_mappings_tool` | List all port mappings for cluster |
| `kind_ingress_setup_tool` | Setup NGINX/Contour ingress controller |

**Advanced Diagnostics:**
| Tool | Description |
|------|-------------|
| `kind_cluster_status_tool` | Detailed cluster health/status |
| `kind_images_list_tool` | List images loaded on cluster nodes |
| `kind_provider_info_tool` | Get container runtime provider info |

**Usage Examples:**
```python
# Config generation & validation
kind_config_generate_tool(workers=2, ingress=True, registry=True)
kind_config_validate_tool(config_path="/tmp/kind.yaml")

# Registry setup
kind_registry_create_tool()
kind_create_cluster_tool(name="dev", config="/tmp/kind-with-registry.yaml")
kind_registry_connect_tool(cluster_name="dev")
kind_registry_status_tool()

# Node operations
kind_node_exec_tool(node="dev-control-plane", command="crictl images")
kind_node_inspect_tool(node="dev-control-plane")
kind_cluster_status_tool(name="dev")

# Networking
kind_network_inspect_tool()
kind_port_mappings_tool(cluster="dev")
kind_ingress_setup_tool(cluster="dev")
```

### Release v1.20.0 Changes

#### kind (Kubernetes IN Docker) Support
Added initial 15 tools for managing local Kubernetes clusters using kind CLI:

**kind Tools (15 tools):**
| Tool | Description |
|------|-------------|
| `kind_detect_tool` | Detect if kind CLI is installed |
| `kind_version_tool` | Get kind CLI version |
| `kind_list_clusters_tool` | List all kind clusters |
| `kind_get_nodes_tool` | List nodes in a cluster |
| `kind_get_kubeconfig_tool` | Get kubeconfig for a cluster |
| `kind_export_logs_tool` | Export cluster logs for debugging |
| `kind_cluster_info_tool` | Get cluster information |
| `kind_node_labels_tool` | Get node labels |
| `kind_create_cluster_tool` | Create a new kind cluster |
| `kind_delete_cluster_tool` | Delete a cluster |
| `kind_delete_all_clusters_tool` | Delete all kind clusters |
| `kind_load_image_tool` | Load Docker images into cluster |
| `kind_load_image_archive_tool` | Load images from tar archive |
| `kind_build_node_image_tool` | Build custom node image |
| `kind_set_kubeconfig_tool` | Export and set kubeconfig context |

**kind vs vind (vCluster):**
- **kind** = Full local K8s clusters using Docker containers as nodes (for local dev/testing)
- **vind** = Virtual clusters inside existing K8s clusters (for multi-tenancy)

### Release v1.19.0 Changes

#### vind (vCluster in Docker) Support
Added 14 tools for managing virtual Kubernetes clusters using vCluster CLI:

**vind Tools (14 tools):**
| Tool | Description |
|------|-------------|
| `vind_detect_tool` | Detect if vCluster CLI is installed |
| `vind_list_clusters_tool` | List all vCluster instances |
| `vind_status_tool` | Get detailed status of a cluster |
| `vind_get_kubeconfig_tool` | Get kubeconfig for a cluster |
| `vind_logs_tool` | Get cluster logs |
| `vind_create_cluster_tool` | Create a new vCluster instance |
| `vind_delete_cluster_tool` | Delete a cluster |
| `vind_pause_tool` | Pause/sleep a cluster (resource saving) |
| `vind_resume_tool` | Resume a sleeping cluster |
| `vind_connect_tool` | Connect kubectl to cluster |
| `vind_disconnect_tool` | Disconnect from cluster |
| `vind_upgrade_tool` | Upgrade cluster k8s version |
| `vind_describe_tool` | Describe cluster details |
| `vind_platform_start_tool` | Start vCluster Platform UI |

**New Files:**
- `kubectl_mcp_tool/tools/vind.py` - vind (vCluster) tools
- `kubernetes-skills/claude/k8s-vind/SKILL.md` - Agent skill for vCluster

**Usage Examples:**
```python
vind_detect_tool()

vind_create_cluster_tool(name="dev-cluster", kubernetes_version="v1.29.0")

vind_connect_tool(name="dev-cluster")

vind_pause_tool(name="dev-cluster")

vind_resume_tool(name="dev-cluster")

vind_delete_cluster_tool(name="dev-cluster")
```

### Release v1.18.0 Changes

#### Agent Skills Library (24 Skills)
Added comprehensive Kubernetes skills following [agenstskills.com](https://agenstskills.com) specification:

| Category | Skills |
|----------|--------|
| **Core Resources** | k8s-core, k8s-networking, k8s-storage |
| **Workloads** | k8s-deploy, k8s-operations, k8s-helm |
| **Observability** | k8s-diagnostics, k8s-troubleshoot, k8s-incident |
| **Security** | k8s-security, k8s-policy, k8s-certs |
| **GitOps** | k8s-gitops, k8s-rollouts |
| **Scaling** | k8s-autoscaling, k8s-cost, k8s-backup |
| **Multi-Cluster** | k8s-multicluster, k8s-capi, k8s-kubevirt, k8s-vind, k8s-kind |
| **Networking** | k8s-service-mesh, k8s-cilium |
| **Tools** | k8s-browser, k8s-cli |

**Installation:**
```bash
# Copy all skills to Claude
cp -r kubernetes-skills/claude/* ~/.claude/skills/

# Convert to other agents with SkillKit
npm install -g skillkit
skillkit translate kubernetes-skills/claude --to cursor --output .cursor/rules/
```

#### Enhanced Provider Module
New `providers.py` with better multi-cluster management:
- **Singleton Pattern**: `KubernetesProvider.get_instance()`
- **API Client Caching**: Cached clients per context
- **Context Validation**: `UnknownContextError` with available contexts
- **Environment Variables**:
  - `MCP_K8S_PROVIDER`: kubeconfig, in-cluster, or single
  - `MCP_K8S_CONTEXT`: Default context for single provider
  - `MCP_K8S_QPS`: API rate limit (default: 100)
  - `MCP_K8S_BURST`: API burst limit (default: 200)
  - `MCP_K8S_TIMEOUT`: Request timeout (default: 30)

**New Files:**
- `kubectl_mcp_tool/providers.py` - Enhanced provider module
- `kubernetes-skills/` - 24 Agent Skills directory

#### Advanced Kubernetes Ecosystem Tools
Added 60 new tools across 6 ecosystem toolsets for comprehensive Kubernetes platform management:

**KEDA Autoscaling (7 tools):**
| Tool | Description |
|------|-------------|
| `keda_scaledobjects_list_tool` | List ScaledObjects |
| `keda_scaledobject_get_tool` | Get ScaledObject details |
| `keda_scaledjobs_list_tool` | List ScaledJobs |
| `keda_triggerauths_list_tool` | List TriggerAuthentications |
| `keda_triggerauth_get_tool` | Get TriggerAuthentication details |
| `keda_hpa_list_tool` | List KEDA-managed HPAs |
| `keda_detect_tool` | Detect KEDA installation |

**Cilium/Hubble Network Observability (8 tools):**
| Tool | Description |
|------|-------------|
| `cilium_policies_list_tool` | List CiliumNetworkPolicies |
| `cilium_policy_get_tool` | Get policy details |
| `cilium_endpoints_list_tool` | List Cilium endpoints |
| `cilium_identities_list_tool` | List Cilium identities |
| `cilium_nodes_list_tool` | List Cilium nodes |
| `cilium_status_tool` | Get Cilium agent status |
| `hubble_flows_query_tool` | Query Hubble network flows |
| `cilium_detect_tool` | Detect Cilium installation |

**Argo Rollouts/Flagger Progressive Delivery (11 tools):**
| Tool | Description |
|------|-------------|
| `rollouts_list_tool` | List Argo Rollouts |
| `rollout_get_tool` | Get rollout details |
| `rollout_status_tool` | Get rollout status |
| `rollout_promote_tool` | Promote rollout |
| `rollout_abort_tool` | Abort rollout |
| `rollout_retry_tool` | Retry rollout |
| `rollout_restart_tool` | Restart rollout |
| `analysis_runs_list_tool` | List AnalysisRuns |
| `flagger_canaries_list_tool` | List Flagger Canaries |
| `flagger_canary_get_tool` | Get Canary details |
| `rollouts_detect_tool` | Detect Rollouts installation |

**Cluster API Lifecycle Management (11 tools):**
| Tool | Description |
|------|-------------|
| `capi_clusters_list_tool` | List CAPI clusters |
| `capi_cluster_get_tool` | Get cluster details |
| `capi_machines_list_tool` | List machines |
| `capi_machine_get_tool` | Get machine details |
| `capi_machinedeployments_list_tool` | List MachineDeployments |
| `capi_machinedeployment_scale_tool` | Scale MachineDeployment |
| `capi_machinesets_list_tool` | List MachineSets |
| `capi_machinehealthchecks_list_tool` | List MachineHealthChecks |
| `capi_clusterclasses_list_tool` | List ClusterClasses |
| `capi_cluster_kubeconfig_tool` | Get cluster kubeconfig |
| `capi_detect_tool` | Detect CAPI installation |

**KubeVirt VM Management (13 tools):**
| Tool | Description |
|------|-------------|
| `kubevirt_vms_list_tool` | List VirtualMachines |
| `kubevirt_vm_get_tool` | Get VM details |
| `kubevirt_vmis_list_tool` | List VirtualMachineInstances |
| `kubevirt_vm_start_tool` | Start VM |
| `kubevirt_vm_stop_tool` | Stop VM |
| `kubevirt_vm_restart_tool` | Restart VM |
| `kubevirt_vm_pause_tool` | Pause VM |
| `kubevirt_vm_unpause_tool` | Unpause VM |
| `kubevirt_vm_migrate_tool` | Live migrate VM |
| `kubevirt_datasources_list_tool` | List DataSources |
| `kubevirt_instancetypes_list_tool` | List VirtualMachineInstancetypes |
| `kubevirt_datavolumes_list_tool` | List DataVolumes |
| `kubevirt_detect_tool` | Detect KubeVirt installation |

**Istio/Kiali Service Mesh (10 tools):**
| Tool | Description |
|------|-------------|
| `istio_virtualservices_list_tool` | List VirtualServices |
| `istio_virtualservice_get_tool` | Get VirtualService details |
| `istio_destinationrules_list_tool` | List DestinationRules |
| `istio_gateways_list_tool` | List Gateways |
| `istio_peerauthentications_list_tool` | List PeerAuthentications |
| `istio_authorizationpolicies_list_tool` | List AuthorizationPolicies |
| `istio_proxy_status_tool` | Get proxy sync status |
| `istio_analyze_tool` | Analyze Istio configuration |
| `istio_sidecar_status_tool` | Check sidecar injection status |
| `istio_detect_tool` | Detect Istio installation |

**New Files:**
- `kubectl_mcp_tool/tools/keda.py` - KEDA autoscaling tools
- `kubectl_mcp_tool/tools/cilium.py` - Cilium/Hubble network tools
- `kubectl_mcp_tool/tools/rollouts.py` - Argo Rollouts/Flagger tools
- `kubectl_mcp_tool/tools/capi.py` - Cluster API tools
- `kubectl_mcp_tool/tools/kubevirt.py` - KubeVirt VM tools
- `kubectl_mcp_tool/tools/kiali.py` - Istio/Kiali tools

### Release v1.17.0 Changes
- GitOps tools (Flux/ArgoCD) - 7 tools
- Cert-Manager tools - 9 tools
- Policy tools (Kyverno/Gatekeeper) - 6 tools
- Backup tools (Velero) - 11 tools

### Release v1.15.0 Changes
- Multi-cluster support with context targeting
- Tool Count: 131 core tools + 6 UI tools (was 127)
- Optional: 26 browser tools (with MCP_BROWSER_ENABLED=true)

### Release v1.15.0 Changes

#### Multi-Cluster Support
All Kubernetes tools now support targeting different clusters via the `context` parameter:
- Added `context: str = ""` parameter to all cluster-interacting tools
- Default behavior unchanged (uses current kubeconfig context)
- Specify any valid kubeconfig context name to target different clusters

**New Tools:**
| Tool | Description |
|------|-------------|
| `kubeconfig_view` | View kubeconfig (sanitized) |
| `list_contexts_tool` | List all available kubeconfig contexts |
| `get_api_versions` | Get available API versions |
| `check_crd_exists` | Check if a CRD exists |
| `list_crds` | List all CRDs in cluster |
| `get_nodes_summary` | Get summarized node information |

**Files Updated:**
- `k8s_config.py` - Context-aware client factory functions
- `pods.py` - All 11 pod tools support context
- `core.py` - All 6 core tools support context
- `deployments.py` - All 10 deployment tools support context
- `cluster.py` - All cluster tools support context + new tools
- `networking.py` - All 8 networking tools support context
- `storage.py` - All 3 storage tools support context
- `security.py` - All 10 security tools support context
- `helm.py` - All 16 cluster-interacting Helm tools support context
- `operations.py` - All 14 kubectl operation tools support context
- `diagnostics.py` - All 3 diagnostic tools support context
- `cost.py` - All 8 cost tools support context

**Usage Examples:**
```python
# Get pods from a specific cluster context
get_pods(namespace="default", context="production-cluster")

# Install helm chart on staging cluster
install_helm_chart(name="nginx", chart="bitnami/nginx",
                   namespace="web", context="staging-cluster")

# Compare namespaces across clusters
compare_namespaces(namespace1="prod", namespace2="staging",
                   resource_type="deployment", context="prod-cluster")
```

### Release v1.14.0 Changes

#### 1. Enhanced CLI (inspired by mcp-cli)
New subcommands for shell-friendly operation:

| Command | Description |
|---------|-------------|
| `tools [-d] [--json]` | List all tools with optional descriptions |
| `tools <name>` | Show tool schema and parameters |
| `resources` | List all 8 MCP resources |
| `prompts` | List all 8 MCP prompts |
| `call <tool> [json]` | Call a tool directly (stdin supported) |
| `grep <pattern>` | Search tools by glob pattern |
| `info` | Show server info (version, counts) |
| `context [name]` | Show/switch Kubernetes context |
| `doctor` | Check dependencies and configuration |

#### 2. agent-browser v0.7 Support
- Cloud providers (Browserbase, Browser Use)
- Persistent profiles (`--profile`)
- Remote CDP connections (`wss://...`)
- Retry with exponential backoff for transient errors
- 7 new browser tools

#### 3. Structured Error Handling
- Actionable error messages with suggestions
- Colorized output (respects NO_COLOR)
- JSON output mode for scripting

### New Browser Tools (v0.7)
| Tool | Description |
|------|-------------|
| `browser_connect_cdp` | Connect via CDP port or WebSocket URL |
| `browser_install` | Install Chromium browser |
| `browser_set_provider` | Configure cloud provider |
| `browser_session_list` | List active sessions |
| `browser_session_switch` | Switch session |
| `browser_open_with_headers` | Open URL with auth headers |
| `browser_set_viewport` | Set viewport or emulate device |

## CLI Usage Examples

```bash
# List all tools with descriptions
kubectl-mcp-server tools -d

# Show specific tool schema
kubectl-mcp-server tools get_pods

# Search for pod-related tools
kubectl-mcp-server grep "*pod*"

# Call a tool directly
kubectl-mcp-server call get_pods '{"namespace": "kube-system"}'

# Pipe JSON from stdin
echo '{"namespace": "default"}' | kubectl-mcp-server call get_pods

# Check dependencies
kubectl-mcp-server doctor

# Show current k8s context
kubectl-mcp-server context
```

## Environment Variables

### Core Settings
| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_DEBUG` | Enable debug logging | `false` |
| `MCP_LOG_FILE` | Log to file | (none) |
| `NO_COLOR` | Disable colored output | (unset) |

### Browser Settings (v0.7)
| Variable | Description | Example |
|----------|-------------|---------|
| `MCP_BROWSER_ENABLED` | Enable browser tools | `true` |
| `MCP_BROWSER_PROVIDER` | Cloud provider | `browserbase` / `browseruse` |
| `BROWSERBASE_API_KEY` | Browserbase API key | `bb_...` |
| `BROWSERBASE_PROJECT_ID` | Browserbase project ID | `proj_...` |
| `BROWSER_USE_API_KEY` | Browser Use API key | `bu_...` |
| `MCP_BROWSER_PROFILE` | Persistent profile path | `~/.k8s-browser` |
| `MCP_BROWSER_CDP_URL` | Remote CDP WebSocket | `wss://...` |
| `MCP_BROWSER_PROXY` | Proxy server URL | `http://proxy:8080` |
| `MCP_BROWSER_PROXY_BYPASS` | Bypass proxy hosts | `localhost,*.internal` |
| `MCP_BROWSER_USER_AGENT` | Custom user agent | `Mozilla/5.0...` |
| `MCP_BROWSER_ARGS` | Extra browser args | `--disable-gpu` |
| `MCP_BROWSER_SESSION` | Session name | `k8s-session` |
| `MCP_BROWSER_HEADED` | Show browser window | `true` |
| `MCP_BROWSER_DEBUG` | Browser debug logging | `true` |
| `MCP_BROWSER_MAX_RETRIES` | Retry attempts | `3` |
| `MCP_BROWSER_RETRY_DELAY` | Base retry delay (ms) | `1000` |
| `MCP_BROWSER_TIMEOUT` | Command timeout (sec) | `60` |

## Version Files (update for releases)
- setup.py:8
- package.json:3
- kubectl_mcp_tool/__init__.py:10

## Key Files Modified in v1.14.0

### kubectl_mcp_tool/cli/errors.py (New)
- ErrorCode enum (SUCCESS, CLIENT_ERROR, SERVER_ERROR, K8S_ERROR, BROWSER_ERROR, NETWORK_ERROR)
- CliError dataclass with actionable fields
- Factory functions for common errors

### kubectl_mcp_tool/cli/output.py (New)
- Colorized formatters (respects NO_COLOR)
- format_tools_list, format_tool_schema, format_resources_list
- format_prompts_list, format_call_result, format_server_info
- format_doctor_results with status icons

### kubectl_mcp_tool/cli/cli.py (Enhanced)
- New subcommands: tools, resources, prompts, call, grep, info, context, doctor
- Stdin support for JSON arguments
- Debug mode support

### kubectl_mcp_tool/tools/browser.py (Enhanced)
- v0.7 environment variables
- _get_global_options() helper for CLI flags
- _run_browser_with_retry() for transient errors
- 7 new browser tools (26 total)
- Enhanced browser_open with headers/session/headed params

### tests/test_cli.py (New)
- Tests for CLI errors module
- Tests for output formatters
- Tests for command handlers

### tests/test_browser.py (Updated)
- Tests for v0.7 features
- Tests for _get_global_options()
- Tests for retry logic
- Updated tool count to 26

## Project Structure
```
kubectl-mcp-server-3/
├── kubectl_mcp_tool/
│   ├── __init__.py          # Version 1.19.0
│   ├── mcp_server.py        # Main MCP server
│   ├── k8s_config.py        # In-cluster config support
│   ├── diagnostics.py       # Diagnostic tools
│   ├── cli/                  # Enhanced CLI
│   │   ├── __init__.py
│   │   ├── cli.py           # Main CLI with subcommands
│   │   ├── errors.py        # Structured error handling
│   │   └── output.py        # Colorized formatters
│   └── tools/               # 235+ Kubernetes tools
│       ├── pods.py          # Pod management
│       ├── deployments.py   # Deployments, StatefulSets
│       ├── core.py          # Namespaces, ConfigMaps
│       ├── cluster.py       # Context/cluster management
│       ├── networking.py    # Services, Ingress
│       ├── storage.py       # PVCs, StorageClasses
│       ├── security.py      # RBAC, ServiceAccounts
│       ├── helm.py          # Helm v3 operations
│       ├── operations.py    # kubectl apply/patch/etc
│       ├── diagnostics.py   # Metrics, comparisons
│       ├── cost.py          # Cost optimization
│       ├── browser.py       # Browser v0.7 (26 tools)
│       ├── ui.py            # MCP-UI dashboards
│       ├── gitops.py        # GitOps (Flux/ArgoCD)
│       ├── certs.py         # Cert-Manager
│       ├── policy.py        # Policy (Kyverno/Gatekeeper)
│       ├── backup.py        # Backup (Velero)
│       ├── keda.py          # KEDA autoscaling
│       ├── cilium.py        # Cilium/Hubble network
│       ├── rollouts.py      # Argo Rollouts/Flagger
│       ├── capi.py          # Cluster API
│       ├── kubevirt.py      # KubeVirt VMs
│       ├── kiali.py         # Istio/Kiali service mesh
│       ├── vind.py          # vCluster (vind) management
│       └── kind.py          # kind (Kubernetes IN Docker) management
├── deploy/
│   ├── kubernetes/          # K8s deployment manifests
│   └── kagent/              # kagent integration manifests
├── tests/                   # Test suite
│   ├── test_cli.py          # CLI tests
│   ├── test_browser.py      # Browser tests
│   ├── test_ecosystem.py    # Ecosystem tools tests
│   └── ...
├── setup.py                 # Python package config
├── package.json             # npm package config
├── mcp.yaml                 # MCP manifest
└── Dockerfile               # Multi-arch Docker build
```

## Tool Counts
- **Core K8s tools**: 270 (was 253 in v1.20)
- **Browser tools**: 26 (optional, MCP_BROWSER_ENABLED=true)
- **UI tools**: 6 (included in core count)
- **Ecosystem tools**: 139 (GitOps, Certs, Policy, Backup, KEDA, Cilium, Rollouts, CAPI, KubeVirt, Istio, vind, kind)
- **kind tools**: 32 (expanded from 15)
- **Total with all optional**: 296

## Installation Methods
1. **pip**: `pip install kubectl-mcp-server`
2. **pip (with UI)**: `pip install kubectl-mcp-server[ui]`
3. **npm**: `npx kubectl-mcp-server@1.21.0`
4. **Docker**: `docker pull rohitghumare64/kubectl-mcp-server:1.21.0`

## Testing
```bash
# Run all tests
pytest tests/ -v

# Run CLI tests
pytest tests/test_cli.py -v

# Run browser tests
pytest tests/test_browser.py -v
```

## Previous Versions
- v1.21.0: Comprehensive kind support - expanded from 15 to 32 tools (config, registry, node management, networking, diagnostics)
- v1.20.0: kind (Kubernetes IN Docker) support - 15 tools for local development clusters
- v1.19.0: vind (vCluster in Docker) support - 14 tools for virtual clusters
- v1.18.0: Advanced ecosystem tools (KEDA, Cilium, Rollouts, CAPI, KubeVirt, Istio) - 60 new tools
- v1.17.0: Kubernetes ecosystem tools (GitOps, Certs, Policy, Backup) - 33 tools
- v1.15.0: Multi-cluster support with context targeting
- v1.14.0: Enhanced CLI + agent-browser v0.7 support
- v1.13.0: MCP-UI interactive dashboard tools
- v1.12.0: SSE transport fix, in-cluster config support, kagent integration
- v1.11.0: Browser automation tools (19 tools), package rename
- v1.10.0: Initial FastMCP 3.0 migration

## agentgateway Integration

### Configuration
- Transport: `streamable-http` (required, not SSE)
- Endpoint: `/mcp`
- All tools discoverable through gateway

### Working Config
```yaml
binds:
- port: 3000
  listeners:
  - routes:
    - backends:
      - mcp:
          targets:
          - name: kubectl-mcp-server
            mcp:
              host: http://localhost:8000/mcp
```

### Commands
```bash
# Start server
kubectl-mcp-server serve --transport streamable-http --port 8000

# Run gateway
agentgateway --config gateway.yaml

# Connect clients to http://localhost:3000/mcp
```

## Next Steps (v1.16.0+)
1. Phase 2: Cross-cluster Operations (copy-secret, compare-deployments across clusters)
2. Phase 3: Cluster Lifecycle Management (provision, scale, upgrade clusters)
3. Phase 4: Multi-tenancy Support (namespace quotas, tenant isolation)
4. Phase 5: Enhanced Observability (distributed tracing, metrics aggregation)
5. Add shell completion scripts for CLI
