"""
MCP prompts registration for kubectl-mcp-server.

This module handles registration of both built-in and custom prompts.
Custom prompts can be loaded from a TOML configuration file.
"""

import logging
import os
from typing import Optional, Dict, Any

from .custom import (
    CustomPrompt,
    PromptMessage,
    render_prompt,
    load_prompts_from_toml_file,
    validate_prompt_args,
    apply_defaults,
)
from .builtin import get_builtin_prompts

logger = logging.getLogger("mcp-server")


# Default paths for custom prompts configuration
DEFAULT_CONFIG_PATHS = [
    os.path.expanduser("~/.kubectl-mcp/prompts.toml"),
    os.path.expanduser("~/.config/kubectl-mcp/prompts.toml"),
    "./kubectl-mcp-prompts.toml",
]


def _get_custom_prompts_path() -> Optional[str]:
    """
    Get the path to custom prompts configuration file.

    Checks (in order):
    1. MCP_PROMPTS_FILE environment variable
    2. Default config paths

    Returns:
        Path to config file if found, None otherwise
    """
    # Check environment variable first
    env_path = os.environ.get("MCP_PROMPTS_FILE")
    if env_path and os.path.isfile(env_path):
        return env_path

    # Check default paths
    for path in DEFAULT_CONFIG_PATHS:
        if os.path.isfile(path):
            return path

    return None


def _merge_prompts(builtin: list, custom: list) -> Dict[str, CustomPrompt]:
    """
    Merge built-in and custom prompts.

    Custom prompts override built-in prompts with the same name.

    Args:
        builtin: List of built-in CustomPrompt objects
        custom: List of custom CustomPrompt objects

    Returns:
        Dictionary of prompt name -> CustomPrompt
    """
    prompts = {}

    # Add built-in prompts first
    for prompt in builtin:
        prompts[prompt.name] = prompt

    # Custom prompts override built-in
    for prompt in custom:
        if prompt.name in prompts:
            logger.info(f"Custom prompt '{prompt.name}' overrides built-in prompt")
        prompts[prompt.name] = prompt

    return prompts


def register_prompts(server, config_path: Optional[str] = None):
    """
    Register all MCP prompts for Kubernetes workflows.

    Registers:
    1. Built-in prompts from builtin.py
    2. Custom prompts from configuration file (if found)
    3. Original inline prompts for backward compatibility

    Custom prompts can override built-in prompts by using the same name.

    Args:
        server: FastMCP server instance
        config_path: Optional path to custom prompts TOML file
    """
    # Load built-in prompts
    builtin_prompts = get_builtin_prompts()
    logger.debug(f"Loaded {len(builtin_prompts)} built-in prompts")

    # Load custom prompts
    prompts_file = config_path or _get_custom_prompts_path()
    custom_prompts = []
    if prompts_file:
        custom_prompts = load_prompts_from_toml_file(prompts_file)
        logger.info(f"Loaded {len(custom_prompts)} custom prompts from {prompts_file}")

    # Merge prompts (custom overrides built-in)
    all_prompts = _merge_prompts(builtin_prompts, custom_prompts)

    # Register each configurable prompt
    for prompt in all_prompts.values():
        _register_custom_prompt(server, prompt)

    logger.debug(f"Registered {len(all_prompts)} configurable prompts")

    # Register original inline prompts for backward compatibility
    _register_inline_prompts(server)


def _register_custom_prompt(server, prompt: CustomPrompt):
    """
    Register a single CustomPrompt with the server.

    Args:
        server: FastMCP server instance
        prompt: CustomPrompt to register
    """
    # Build the argument schema for FastMCP
    def create_prompt_handler(p: CustomPrompt):
        """Create a closure that captures the prompt."""
        def handler(**kwargs) -> str:
            # Apply defaults for missing optional arguments
            args = apply_defaults(p, kwargs)

            # Validate required arguments
            errors = validate_prompt_args(p, args)
            if errors:
                return f"Error: {'; '.join(errors)}"

            # Render the prompt messages
            rendered = render_prompt(p, args)

            # Return the content (for now, just the first message)
            # MCP prompts typically return a single string
            if rendered:
                return rendered[0].content
            return f"Prompt '{p.name}' has no messages defined."

        return handler

    # Create the handler
    handler = create_prompt_handler(prompt)

    # Set function metadata for FastMCP registration
    handler.__name__ = prompt.name.replace("-", "_")
    handler.__doc__ = prompt.description or prompt.title

    # Build parameter annotations from arguments
    params = {}
    for arg in prompt.arguments:
        # All prompt arguments are strings with Optional if not required
        if arg.required:
            params[arg.name] = str
        else:
            params[arg.name] = Optional[str]

    handler.__annotations__ = params
    handler.__annotations__["return"] = str

    # Register with server
    try:
        server.prompt()(handler)
        logger.debug(f"Registered configurable prompt: {prompt.name}")
    except Exception as e:
        logger.warning(f"Failed to register prompt '{prompt.name}': {e}")


def _register_inline_prompts(server):
    """
    Register original inline prompts for backward compatibility.

    These prompts are kept for users who may be using them directly.
    They can be overridden by custom prompts with the same name.
    """

    @server.prompt()
    def troubleshoot_workload(workload: str, namespace: Optional[str] = None, resource_type: str = "pod") -> str:
        """Comprehensive troubleshooting guide for Kubernetes workloads."""
        ns_text = f"in namespace '{namespace}'" if namespace else "across all namespaces"
        return f"""# Kubernetes Troubleshooting: {workload}

Target: {resource_type}s matching '{workload}' {ns_text}

## Step 1: Discovery
First, identify all relevant resources:
- Use `get_pods` with namespace={namespace or 'None'} to list pods
- Filter results for pods containing '{workload}' in the name
- Note the status of each pod (Running, Pending, CrashLoopBackOff, etc.)

## Step 2: Status Analysis
For each pod found, check:
- **Phase**: Is it Running, Pending, Failed, or Unknown?
- **Ready**: Are all containers ready? (e.g., 1/1, 2/2)
- **Restarts**: High restart count indicates crashes
- **Age**: Recently created pods may still be starting

### Common Status Issues:
| Status | Likely Cause | First Check |
|--------|--------------|-------------|
| Pending | Scheduling issues | get_pod_events |
| CrashLoopBackOff | App crash on start | get_logs |
| ImagePullBackOff | Image not found | kubectl_describe |
| OOMKilled | Memory limit exceeded | kubectl_describe |
| CreateContainerError | Config issue | get_pod_events |

## Step 3: Deep Inspection
Use these tools in order:

1. **Events** - `get_pod_events(pod_name, namespace)`
   - Look for: FailedScheduling, FailedMount, Unhealthy
   - Check timestamps for recent issues

2. **Logs** - `get_logs(pod_name, namespace, tail=100)`
   - Look for: exceptions, errors, stack traces
   - If container crashed: use previous=true

3. **Describe** - `kubectl_describe("pod", pod_name, namespace)`
   - Check: resource requests/limits, node assignment
   - Look at: conditions, volumes, container states

## Step 4: Related Resources
Check parent resources:
- For Deployments: `kubectl_describe("deployment", name, namespace)`
- For StatefulSets: `kubectl_describe("statefulset", name, namespace)`
- For DaemonSets: `kubectl_describe("daemonset", name, namespace)`

Check dependencies:
- Services: `get_services(namespace)`
- ConfigMaps/Secrets: referenced in pod spec
- PVCs: `kubectl_describe("pvc", name, namespace)` if storage issues

## Step 5: Resolution Checklist
For each issue, provide:

1. **Root Cause**: What is actually wrong
2. **Evidence**: Specific log line or event message
3. **Fix Command**: Exact kubectl command or manifest change
4. **Verification**: How to confirm the fix worked
5. **Prevention**: Configuration to prevent recurrence

## Common Fixes Reference:
- **OOMKilled**: Increase memory limits in deployment spec
- **CrashLoopBackOff**: Fix application error, check logs
- **Pending (no nodes)**: Check node capacity, add nodes
- **ImagePullBackOff**: Verify image name, check imagePullSecrets
- **Mount failures**: Check PVC status, storage class

Start the investigation now."""

    @server.prompt()
    def deploy_application(app_name: str, namespace: str = "default", replicas: int = 1) -> str:
        """Step-by-step guide for deploying applications to Kubernetes."""
        return f"""# Kubernetes Deployment Guide: {app_name}

Target Namespace: {namespace}
Desired Replicas: {replicas}

## Pre-Deployment Checklist

### Step 1: Verify Cluster Access
- Use `get_namespaces` to confirm cluster connectivity
- Check if namespace '{namespace}' exists
- If not, create it: `kubectl_create_namespace("{namespace}")`

### Step 2: Review Existing Resources
Check for conflicts or existing deployments:
- `get_deployments(namespace="{namespace}")` - List current deployments
- `get_services(namespace="{namespace}")` - List current services
- `get_configmaps(namespace="{namespace}")` - List ConfigMaps

### Step 3: Prepare Deployment Manifest
Required components for '{app_name}':

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  namespace: {namespace}
  labels:
    app: {app_name}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: <IMAGE_NAME>:<TAG>
        ports:
        - containerPort: <PORT>
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: <PORT>
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: <PORT>
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Step 4: Apply Configuration
Use `kubectl_apply` with the manifest YAML

### Step 5: Verify Deployment
1. `kubectl_rollout_status("deployment", "{app_name}", "{namespace}")` - Watch rollout
2. `get_pods(namespace="{namespace}")` - Check pod status
3. `get_logs(pod_name, "{namespace}")` - Check application logs

### Step 6: Expose Service (if needed)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {app_name}
  namespace: {namespace}
spec:
  selector:
    app: {app_name}
  ports:
  - port: 80
    targetPort: <PORT>
  type: ClusterIP  # or LoadBalancer, NodePort
```

### Step 7: Post-Deployment Verification
- `kubectl_describe("deployment", "{app_name}", "{namespace}")` - Full details
- `kubectl_get_endpoints("{app_name}", "{namespace}")` - Service endpoints
- Test connectivity to the application

## Rollback Plan
If issues occur:
- `kubectl_rollout("undo", "deployment", "{app_name}", "{namespace}")` - Rollback
- `kubectl_rollout_history("deployment", "{app_name}", "{namespace}")` - View history

Start the deployment process now."""

    @server.prompt()
    def security_audit(namespace: Optional[str] = None, scope: str = "full") -> str:
        """Security audit workflow for Kubernetes clusters."""
        ns_text = f"namespace '{namespace}'" if namespace else "all namespaces"
        return f"""# Kubernetes Security Audit

Scope: {scope}
Target: {ns_text}

## Phase 1: RBAC Analysis

### Step 1: Review ClusterRoles
- `kubectl_get("clusterroles")` - List all cluster roles
- Look for overly permissive roles (e.g., `*` on verbs or resources)
- Check for `cluster-admin` bindings

### Step 2: Review RoleBindings
- `kubectl_get("clusterrolebindings")` - Cluster-wide bindings
- `kubectl_get("rolebindings", namespace="{namespace or 'all'}")` - Namespace bindings
- Identify which users/serviceaccounts have elevated privileges

### Step 3: ServiceAccount Analysis
- `kubectl_get("serviceaccounts", namespace="{namespace or 'all'}")` - List SAs
- Check for default SA usage in pods
- Verify SA token automounting is disabled where not needed

## Phase 2: Pod Security

### Step 4: Security Context Review
Use `kubectl_get_security_contexts(namespace="{namespace}")` to check:
- [ ] Pods running as non-root
- [ ] Read-only root filesystem
- [ ] Dropped capabilities
- [ ] No privilege escalation

### Step 5: Image Security
- `kubectl_list_images(namespace="{namespace}")` - List all images
- Check for:
  - [ ] Specific image tags (not `latest`)
  - [ ] Trusted registries
  - [ ] Image pull policies

### Step 6: Network Policies
- `kubectl_get("networkpolicies", namespace="{namespace}")` - List policies
- Verify default deny policies exist
- Check ingress/egress rules

## Phase 3: Secrets Management

### Step 7: Secrets Audit
- `kubectl_get("secrets", namespace="{namespace}")` - List secrets
- Check for:
  - [ ] Unused secrets
  - [ ] Secrets mounted as environment variables (less secure)
  - [ ] External secrets management integration

### Step 8: ConfigMap Review
- `kubectl_get("configmaps", namespace="{namespace}")` - List ConfigMaps
- Ensure no sensitive data in ConfigMaps

## Phase 4: Resource Security

### Step 9: Resource Quotas
- `kubectl_get("resourcequotas", namespace="{namespace}")` - Check quotas
- Verify limits are set appropriately

### Step 10: Pod Disruption Budgets
- `kubectl_get("poddisruptionbudgets", namespace="{namespace}")` - Check PDBs
- Ensure critical workloads have PDBs

## Security Report Template

For each finding, document:
1. **Severity**: Critical/High/Medium/Low
2. **Resource**: Specific resource affected
3. **Issue**: Description of the security concern
4. **Risk**: Potential impact if exploited
5. **Remediation**: Steps to fix
6. **Verification**: How to confirm the fix

## Common Fixes:
- Add `securityContext.runAsNonRoot: true`
- Set `automountServiceAccountToken: false`
- Add NetworkPolicy with default deny
- Use specific image tags
- Enable Pod Security Standards

Begin the security audit now."""

    @server.prompt()
    def cost_optimization(namespace: Optional[str] = None) -> str:
        """Cost optimization analysis workflow."""
        ns_text = f"namespace '{namespace}'" if namespace else "cluster-wide"
        return f"""# Kubernetes Cost Optimization Analysis

Scope: {ns_text}

## Phase 1: Resource Usage Analysis

### Step 1: Current Resource Consumption
Use `kubectl_get_resource_usage(namespace="{namespace}")` to analyze:
- CPU requests vs actual usage
- Memory requests vs actual usage
- Identify over-provisioned resources

### Step 2: Idle Resource Detection
Use `kubectl_get_idle_resources(namespace="{namespace}")` to find:
- Pods with < 10% CPU utilization
- Pods with < 20% memory utilization
- Unused PersistentVolumes
- Idle LoadBalancer services

### Step 3: Resource Recommendations
Use `kubectl_get_resource_recommendations(namespace="{namespace}")`:
- Right-sizing suggestions based on usage
- HPA recommendations
- VPA recommendations

## Phase 2: Workload Optimization

### Step 4: Deployment Analysis
For each deployment:
- Check replica count vs actual load
- Review resource requests/limits
- Identify candidates for autoscaling

### Step 5: Node Utilization
- `kubectl_top("nodes")` - Node resource usage
- Identify underutilized nodes
- Consider node consolidation

### Step 6: Storage Optimization
- Review PVC sizes vs actual usage
- Identify unused PVCs
- Consider storage class optimization

## Phase 3: Scheduling Optimization

### Step 7: Pod Scheduling
- Review pod affinity/anti-affinity rules
- Check for bin-packing opportunities
- Evaluate spot/preemptible node usage

### Step 8: Priority Classes
- Review PriorityClasses
- Ensure critical workloads have appropriate priority

## Phase 4: Cost Estimation

### Step 9: Current Cost Analysis
Use `kubectl_get_cost_analysis(namespace="{namespace}")`:
- Estimated monthly costs
- Cost breakdown by resource type
- Cost per namespace/workload

### Step 10: Optimization Savings
Estimate savings from:
- Right-sizing resources
- Implementing autoscaling
- Using spot instances
- Consolidating workloads

## Optimization Actions

### Quick Wins (Immediate Impact):
1. Remove idle resources
2. Right-size over-provisioned pods
3. Delete unused PVCs

### Medium-Term:
1. Implement HPA for variable workloads
2. Use VPA for stable workloads
3. Consolidate underutilized nodes

### Long-Term:
1. Implement cluster autoscaler
2. Use spot/preemptible nodes
3. Multi-tenancy optimization

Begin the cost optimization analysis now."""

    @server.prompt()
    def disaster_recovery(namespace: Optional[str] = None, dr_type: str = "full") -> str:
        """Disaster recovery planning and execution workflow."""
        ns_text = f"namespace '{namespace}'" if namespace else "entire cluster"
        return f"""# Kubernetes Disaster Recovery Plan

Scope: {ns_text}
DR Type: {dr_type}

## Phase 1: Pre-Disaster Preparation

### Step 1: Inventory Current State
Document all resources:
- `get_deployments(namespace="{namespace}")` - All deployments
- `get_services(namespace="{namespace}")` - All services
- `kubectl_get("configmaps", namespace="{namespace}")` - ConfigMaps
- `kubectl_get("secrets", namespace="{namespace}")` - Secrets
- `kubectl_get("pvc", namespace="{namespace}")` - Persistent volumes

### Step 2: Backup Strategy
For each resource type:

**Deployments/StatefulSets:**
- Export YAML manifests using `kubectl_export`
- Store in version control
- Document image versions

**ConfigMaps/Secrets:**
- Export with `kubectl_export`
- Encrypt secrets before storage
- Use external secret management

**Persistent Data:**
- Volume snapshots (if supported)
- Application-level backups
- Document backup frequency

### Step 3: Document Dependencies
Create dependency map:
- External services (databases, APIs)
- DNS configurations
- Load balancer settings
- SSL certificates

## Phase 2: Backup Execution

### Step 4: Export Resources
For namespace '{namespace or "all"}':
```
kubectl_export("deployment", namespace="{namespace}")
kubectl_export("service", namespace="{namespace}")
kubectl_export("configmap", namespace="{namespace}")
kubectl_export("secret", namespace="{namespace}")
kubectl_export("ingress", namespace="{namespace}")
```

### Step 5: Verify Backups
- Validate YAML syntax
- Check completeness
- Test restore in staging

## Phase 3: Recovery Procedures

### Step 6: Cluster Recovery
If cluster is lost:
1. Provision new cluster
2. Configure networking
3. Set up storage classes
4. Apply RBAC configurations

### Step 7: Namespace Recovery
For namespace '{namespace or "default"}':
1. `kubectl_create_namespace("{namespace}")` - Create namespace
2. Apply secrets first (dependencies)
3. Apply ConfigMaps
4. Apply PVCs
5. Apply deployments
6. Apply services
7. Apply ingresses

### Step 8: Data Recovery
- Restore from volume snapshots
- Execute application-level restores
- Verify data integrity

### Step 9: Verification
Post-recovery checks:
- `get_pods(namespace="{namespace}")` - All pods running
- `kubectl_get_endpoints` - Services have endpoints
- Application health checks
- Data verification

## Quick Reference Commands
```
# Full namespace backup
kubectl get all -n {namespace or 'default'} -o yaml > backup.yaml

# Restore from backup
kubectl apply -f backup.yaml

# Check restore status
kubectl get pods -n {namespace or 'default'} -w
```

Begin disaster recovery planning now."""

    @server.prompt()
    def debug_networking(service_name: str, namespace: str = "default") -> str:
        """Network debugging workflow for Kubernetes services."""
        return f"""# Kubernetes Network Debugging: {service_name}

Target: Service '{service_name}' in namespace '{namespace}'

## Phase 1: Service Discovery

### Step 1: Verify Service Exists
- `kubectl_describe("service", "{service_name}", "{namespace}")` - Service details
- Check service type (ClusterIP, NodePort, LoadBalancer)
- Note selector labels and ports

### Step 2: Check Endpoints
- `kubectl_get_endpoints("{service_name}", "{namespace}")` - Endpoint addresses
- If empty: No pods match the service selector
- Verify endpoint IPs match pod IPs

### Step 3: Verify Backend Pods
- `get_pods(namespace="{namespace}")` - List pods
- Check pods have matching labels
- Verify pods are in Running state

## Phase 2: DNS Resolution

### Step 4: Test DNS Resolution
From within a pod:
```
nslookup {service_name}.{namespace}.svc.cluster.local
```

Expected format: `<service>.<namespace>.svc.cluster.local`

### Step 5: CoreDNS Health
- `get_pods(namespace="kube-system")` - Check CoreDNS pods
- `get_logs(coredns_pod, "kube-system")` - Check DNS logs

## Phase 3: Connectivity Testing

### Step 6: Pod-to-Pod Connectivity
Test from a debug pod:
```
kubectl run debug --rm -it --image=busybox -- wget -qO- http://{service_name}.{namespace}:PORT
```

### Step 7: Service Port Verification
- Verify `port` (service port) and `targetPort` (container port) match
- Check if container is listening on targetPort
- Use `kubectl_port_forward` to test directly

### Step 8: Network Policies
- `kubectl_get("networkpolicies", namespace="{namespace}")` - List policies
- Check if policies block ingress/egress
- Verify policy selectors

## Phase 4: Common Issues

### Issue: No Endpoints
Causes:
- Pod selector mismatch
- Pods not running
- Readiness probe failing

Fix:
1. Check service selector labels
2. Verify pod labels match
3. Fix readiness probe

### Issue: Connection Refused
Causes:
- Wrong targetPort
- App not listening
- App crashed

Fix:
1. Verify container port
2. Check pod logs
3. Test with port-forward

### Issue: Connection Timeout
Causes:
- Network policy blocking
- Wrong service IP/port
- CNI issues

Fix:
1. Review network policies
2. Verify kube-proxy running
3. Check CNI plugin status

## Debugging Commands Reference
```
# Test from debug pod
kubectl run debug --rm -it --image=nicolaka/netshoot -- /bin/bash

# Inside debug pod:
curl -v http://{service_name}.{namespace}:PORT
dig {service_name}.{namespace}.svc.cluster.local
traceroute {{service_ip}}
netstat -tlnp
```

## Network Flow Verification
1. Client -> Service IP (kube-proxy/iptables)
2. Service -> Endpoint (pod IP)
3. Pod IP -> Container port

Check each hop for failures.

Begin network debugging now."""

    @server.prompt()
    def scale_application(app_name: str, namespace: str = "default", target_replicas: int = 3) -> str:
        """Application scaling guide with best practices."""
        return f"""# Kubernetes Scaling Guide: {app_name}

Target: Deployment '{app_name}' in namespace '{namespace}'
Target Replicas: {target_replicas}

## Pre-Scaling Checklist

### Step 1: Current State Assessment
- `kubectl_describe("deployment", "{app_name}", "{namespace}")` - Current config
- `kubectl_top("pods", namespace="{namespace}")` - Resource usage
- Note current replica count and resource limits

### Step 2: Capacity Planning
Calculate required resources:
- Current pod resources x {target_replicas} = Total needed
- Check node capacity: `kubectl_top("nodes")`
- Verify cluster can accommodate new pods

### Step 3: Check Dependencies
- Database connection pools
- External API rate limits
- Shared resources (ConfigMaps, Secrets)
- Service mesh sidecar limits

## Scaling Methods

### Method 1: Manual Scaling
Immediate scale operation:
```
kubectl_scale("deployment", "{app_name}", {target_replicas}, "{namespace}")
```

Monitor rollout:
```
kubectl_rollout_status("deployment", "{app_name}", "{namespace}")
```

### Method 2: Horizontal Pod Autoscaler (HPA)
For automatic scaling based on metrics:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {app_name}-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {app_name}
  minReplicas: 2
  maxReplicas: {target_replicas * 2}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Post-Scaling Verification

### Step 4: Verify Scaling Success
1. `get_pods(namespace="{namespace}")` - Check pod count
2. Verify all pods are Running and Ready
3. Check pod distribution across nodes

### Step 5: Monitor Application
- Check application metrics
- Verify response times
- Monitor error rates
- Check resource utilization

## Rollback Plan
If issues occur after scaling:
```
kubectl_scale("deployment", "{app_name}", original_count, "{namespace}")
```

Begin scaling operation now."""

    @server.prompt()
    def upgrade_cluster(current_version: str = "1.28", target_version: str = "1.29") -> str:
        """Kubernetes cluster upgrade planning guide."""
        return f"""# Kubernetes Cluster Upgrade Plan

Current Version: {current_version}
Target Version: {target_version}

## Pre-Upgrade Phase

### Step 1: Compatibility Check
Review upgrade path:
- Kubernetes supports N-2 version skew
- Upgrade one minor version at a time
- Check: {current_version} -> {target_version} is valid

### Step 2: Deprecation Review
Check for deprecated APIs:
- `kubectl_get_deprecated_resources` - Find deprecated resources
- Review release notes for {target_version}
- Update manifests before upgrade

### Step 3: Addon Compatibility
Verify addon versions support {target_version}:
- CNI plugin (Calico, Cilium, etc.)
- Ingress controller
- Metrics server
- Storage drivers

### Step 4: Backup Everything
Create full backups:
- etcd snapshot
- All resource manifests
- PersistentVolume data
- External configurations

## Control Plane Upgrade

### Step 5: Upgrade Control Plane Components
Order of operations:
1. kube-apiserver
2. kube-controller-manager
3. kube-scheduler
4. cloud-controller-manager (if applicable)

For managed clusters (EKS, GKE, AKS):
- Use provider's upgrade mechanism
- Monitor upgrade progress

### Step 6: Verify Control Plane
After control plane upgrade:
- `kubectl_cluster_info` - Verify API server version
- Check component health
- Test API connectivity

## Node Upgrade

### Step 7: Upgrade Strategy Selection
Choose one:

**Rolling Upgrade (Recommended):**
- Upgrade nodes one at a time
- Minimal disruption
- Slower but safer

**Blue-Green:**
- Create new node pool
- Migrate workloads
- Delete old nodes

### Step 8: Node Upgrade Process
For each node:

1. **Cordon the node:**
   `kubectl_cordon(node_name)`

2. **Drain workloads:**
   `kubectl_drain(node_name, ignore_daemonsets=True)`

3. **Upgrade kubelet & kubectl:**
   - Update packages
   - Restart kubelet

4. **Uncordon the node:**
   `kubectl_uncordon(node_name)`

5. **Verify node health:**
   `kubectl_describe("node", node_name)`

### Step 9: Verify Node Versions
- `kubectl_get("nodes")` - Check all node versions
- Ensure all nodes show {target_version}

## Post-Upgrade Verification

### Step 10: Cluster Health Check
Run comprehensive checks:
- `kubectl_cluster_info` - Cluster status
- `get_pods(namespace="kube-system")` - System pods
- All nodes Ready
- All system pods Running

### Step 11: Application Verification
For each namespace:
- Check pod health
- Verify service endpoints
- Test application functionality
- Monitor for errors

### Step 12: Update Tooling
After successful upgrade:
- Update kubectl client
- Update CI/CD pipelines
- Update documentation
- Update monitoring dashboards

## Upgrade Checklist

Pre-Upgrade:
- [ ] Backup etcd
- [ ] Backup all manifests
- [ ] Check API deprecations
- [ ] Verify addon compatibility
- [ ] Test upgrade in staging
- [ ] Schedule maintenance window
- [ ] Notify stakeholders

During Upgrade:
- [ ] Upgrade control plane
- [ ] Verify control plane health
- [ ] Upgrade nodes (rolling)
- [ ] Monitor for issues

Post-Upgrade:
- [ ] Verify all nodes upgraded
- [ ] Check application health
- [ ] Update client tools
- [ ] Document any issues
- [ ] Update runbooks

Begin upgrade planning now."""
