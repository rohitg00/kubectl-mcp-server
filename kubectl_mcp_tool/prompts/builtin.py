"""
Built-in prompts for kubectl-mcp-server.

These prompts provide comprehensive workflows for common Kubernetes tasks.
Users can override any of these by defining a prompt with the same name
in their custom configuration.
"""

from .custom import CustomPrompt, PromptArgument, PromptMessage


# Cluster Health Check Prompt
CLUSTER_HEALTH_CHECK = CustomPrompt(
    name="cluster-health-check",
    title="Cluster Health Check",
    description="Comprehensive health assessment of your Kubernetes cluster",
    arguments=[
        PromptArgument(
            name="namespace",
            description="Limit to specific namespace (optional)",
            required=False
        ),
        PromptArgument(
            name="check_events",
            description="Include recent events in the check (true/false)",
            required=False,
            default="true"
        ),
        PromptArgument(
            name="check_metrics",
            description="Include resource metrics (true/false)",
            required=False,
            default="true"
        ),
    ],
    messages=[
        PromptMessage(
            role="user",
            content="""Perform a comprehensive health check of the Kubernetes cluster{{#namespace}} in namespace {{namespace}}{{/namespace}}.

## Check Categories

### 1. Node Health
- Check node status and conditions (Ready, MemoryPressure, DiskPressure, PIDPressure)
- Verify all nodes are reporting Ready
- Check node resource capacity and allocatable resources
{{#check_metrics}}- Review node CPU and memory utilization{{/check_metrics}}

### 2. Pod Health{{#namespace}} in {{namespace}}{{/namespace}}
- Identify pods in problematic states:
  - CrashLoopBackOff: Application crash on start
  - ImagePullBackOff: Image not found or registry auth issues
  - Pending: Scheduling issues or resource constraints
  - OOMKilled: Memory limit exceeded
  - Error: Container exited with error
- Check restart counts for running pods
{{#check_metrics}}- Review pod resource usage vs limits{{/check_metrics}}

### 3. Workload Status{{#namespace}} in {{namespace}}{{/namespace}}
- Deployment replica status (desired vs ready)
- StatefulSet replica status
- DaemonSet desired vs scheduled vs ready
- Job completion status
- CronJob schedule health

### 4. Storage Health
- PVC binding status (Bound, Pending, Lost)
- PV availability and reclaim status
- StorageClass availability

### 5. Networking Health
- Service endpoint health (services with no endpoints)
- Ingress configuration validity
- NetworkPolicy presence and coverage

{{#check_events}}### 6. Recent Events{{#namespace}} in {{namespace}}{{/namespace}}
- Warning events in the last hour
- Error events indicating failures
- Event patterns suggesting issues{{/check_events}}

## Output Required

Provide:
1. **Overall Health Status**: Healthy, Warning, or Critical
2. **Summary Statistics**:
   - Total nodes and healthy count
   - Total pods and healthy count
   - Workloads with issues
3. **Critical Issues** (require immediate attention)
4. **Warnings** (should be addressed soon)
5. **Recommendations** for improvements

Start the health check now using the appropriate kubectl tools."""
        ),
    ]
)


# Debug Workload Prompt
DEBUG_WORKLOAD = CustomPrompt(
    name="debug-workload",
    title="Debug Workload Issues",
    description="Diagnose and troubleshoot Kubernetes workload problems",
    arguments=[
        PromptArgument(
            name="workload_name",
            description="Name of the workload to debug",
            required=True
        ),
        PromptArgument(
            name="namespace",
            description="Namespace of the workload",
            required=False,
            default="default"
        ),
        PromptArgument(
            name="workload_type",
            description="Type of workload (deployment, statefulset, daemonset, pod)",
            required=False,
            default="deployment"
        ),
        PromptArgument(
            name="include_related",
            description="Check related resources (services, configmaps, secrets)",
            required=False,
            default="true"
        ),
    ],
    messages=[
        PromptMessage(
            role="user",
            content="""Debug the {{workload_type}} '{{workload_name}}' in namespace '{{namespace}}'.

## Debugging Steps

### Step 1: Identify the Workload
- Get the {{workload_type}} details
- List all pods belonging to this workload
- Note the current status and any error conditions

### Step 2: Pod Status Analysis
For each pod:
1. Check phase (Running, Pending, Failed, Unknown)
2. Check container readiness
3. Count restarts
4. Identify the problematic state if any

### Step 3: Event Investigation
- Get events for the {{workload_type}}
- Get events for each pod
- Look for:
  - FailedScheduling
  - FailedCreate
  - FailedMount
  - Unhealthy (probe failures)
  - BackOff (crash loops)

### Step 4: Log Analysis
For pods not in Running/Ready state:
- Get current logs (last 100 lines)
- If crashed, get previous container logs
- Look for:
  - Stack traces / exceptions
  - Connection errors
  - Configuration errors
  - Permission issues

### Step 5: Resource Analysis
- Check resource requests vs limits
- Verify if pods are OOMKilled
- Check if resources are available on nodes

{{#include_related}}### Step 6: Related Resources
Check dependencies:
- Services pointing to this workload
- ConfigMaps mounted by pods
- Secrets referenced by pods
- PVCs used by pods
- ServiceAccount permissions{{/include_related}}

## Output Required

For each issue found, provide:
1. **Issue Description**: What is wrong
2. **Evidence**: Specific log lines, events, or status
3. **Root Cause**: Likely reason for the issue
4. **Resolution**: Steps to fix the problem
5. **Verification**: How to confirm the fix worked

Start debugging now."""
        ),
    ]
)


# Resource Usage Analysis Prompt
RESOURCE_USAGE = CustomPrompt(
    name="resource-usage",
    title="Resource Usage Analysis",
    description="Analyze resource consumption and identify optimization opportunities",
    arguments=[
        PromptArgument(
            name="namespace",
            description="Namespace to analyze (optional, defaults to all)",
            required=False
        ),
        PromptArgument(
            name="threshold_cpu",
            description="CPU utilization threshold percentage for alerts",
            required=False,
            default="80"
        ),
        PromptArgument(
            name="threshold_memory",
            description="Memory utilization threshold percentage for alerts",
            required=False,
            default="80"
        ),
        PromptArgument(
            name="include_recommendations",
            description="Include right-sizing recommendations",
            required=False,
            default="true"
        ),
    ],
    messages=[
        PromptMessage(
            role="user",
            content="""Analyze resource usage{{#namespace}} in namespace {{namespace}}{{/namespace}} and identify optimization opportunities.

## Analysis Areas

### 1. Node Resource Utilization
- Current CPU and memory usage per node
- Identify nodes exceeding {{threshold_cpu}}% CPU
- Identify nodes exceeding {{threshold_memory}}% memory
- Node capacity vs allocatable resources

### 2. Pod Resource Consumption{{#namespace}} in {{namespace}}{{/namespace}}
- Top CPU consumers
- Top memory consumers
- Pods near resource limits
- Pods with no resource limits (risk)

### 3. Request vs Usage Analysis
Compare for each workload:
- CPU requested vs actual usage
- Memory requested vs actual usage
- Identify over-provisioned resources (waste)
- Identify under-provisioned resources (risk)

### 4. Resource Efficiency
Calculate:
- Overall cluster utilization
- Namespace-level utilization{{#namespace}} for {{namespace}}{{/namespace}}
- Cost of unused/reserved resources

{{#include_recommendations}}### 5. Right-sizing Recommendations
For each over/under-provisioned workload:
- Current requests/limits
- Recommended requests/limits
- Estimated savings/risk reduction
- Priority (high/medium/low){{/include_recommendations}}

### 6. Autoscaling Candidates
Identify workloads that would benefit from:
- Horizontal Pod Autoscaler (HPA)
- Vertical Pod Autoscaler (VPA)
- Cluster Autoscaler configuration

## Output Required

Provide:
1. **Summary Dashboard**:
   - Cluster utilization overview
   - Resource efficiency score
   - Potential savings estimate

2. **Alerts** (immediate attention):
   - Workloads exceeding thresholds
   - Workloads without limits
   - Nodes at capacity

3. **Optimization Actions** (prioritized list):
   - Quick wins (immediate impact)
   - Medium-term improvements
   - Long-term architecture changes

Start the resource analysis now."""
        ),
    ]
)


# Security Posture Review Prompt
SECURITY_POSTURE = CustomPrompt(
    name="security-posture",
    title="Security Posture Review",
    description="Comprehensive security assessment of your Kubernetes cluster",
    arguments=[
        PromptArgument(
            name="namespace",
            description="Namespace to analyze (optional, defaults to all)",
            required=False
        ),
        PromptArgument(
            name="check_rbac",
            description="Include RBAC analysis",
            required=False,
            default="true"
        ),
        PromptArgument(
            name="check_network",
            description="Include network policy analysis",
            required=False,
            default="true"
        ),
        PromptArgument(
            name="check_secrets",
            description="Include secrets management analysis",
            required=False,
            default="true"
        ),
    ],
    messages=[
        PromptMessage(
            role="user",
            content="""Perform a security posture review{{#namespace}} for namespace {{namespace}}{{/namespace}}.

## Security Assessment Areas

{{#check_rbac}}### 1. RBAC Analysis
- Review ClusterRoles with elevated privileges
- Identify ClusterRoleBindings to cluster-admin
- Check for overly permissive roles (wildcards)
- ServiceAccount analysis:
  - Default SA usage
  - Token automounting
  - Unnecessary privileges{{/check_rbac}}

### 2. Pod Security Standards{{#namespace}} in {{namespace}}{{/namespace}}
Check for security anti-patterns:
- [ ] Privileged containers
- [ ] Running as root
- [ ] Host namespace usage (hostNetwork, hostPID, hostIPC)
- [ ] Host path mounts
- [ ] Privilege escalation allowed
- [ ] Missing security contexts
- [ ] Writable root filesystem

### 3. Image Security
- Images using 'latest' tag
- Images from untrusted registries
- Missing imagePullPolicy
- Missing imagePullSecrets

{{#check_network}}### 4. Network Security
- Namespaces without NetworkPolicies
- Missing default deny policies
- Overly permissive ingress rules
- Unprotected egress traffic{{/check_network}}

{{#check_secrets}}### 5. Secrets Management
- Secrets mounted as environment variables (less secure)
- Secrets in pod specs (should use references)
- Unused secrets
- Secrets without encryption at rest{{/check_secrets}}

### 6. Supply Chain Security
- Image vulnerability scanning status
- Admission controller configuration
- Pod Security Standards enforcement

## Risk Categories

For each finding, classify as:
- **Critical**: Immediate exploitation risk
- **High**: Significant security gap
- **Medium**: Best practice violation
- **Low**: Hardening opportunity

## Output Required

Provide:
1. **Security Score**: Overall assessment (A-F grade)

2. **Critical Findings** (fix immediately):
   - Issue description
   - Affected resources
   - Remediation steps

3. **High Priority Issues**:
   - Issue description
   - Risk explanation
   - Fix recommendation

4. **Compliance Checklist**:
   - Pod Security Standards
   - CIS Kubernetes Benchmark highlights
   - Network segmentation

5. **Remediation Plan** (prioritized):
   - Quick wins
   - Medium-term hardening
   - Long-term architecture

Start the security review now."""
        ),
    ]
)


# Deployment Checklist Prompt
DEPLOYMENT_CHECKLIST = CustomPrompt(
    name="deployment-checklist",
    title="Production Deployment Checklist",
    description="Pre-deployment verification checklist for production workloads",
    arguments=[
        PromptArgument(
            name="app_name",
            description="Application name being deployed",
            required=True
        ),
        PromptArgument(
            name="namespace",
            description="Target namespace for deployment",
            required=True
        ),
        PromptArgument(
            name="image",
            description="Container image being deployed",
            required=True
        ),
        PromptArgument(
            name="replicas",
            description="Number of replicas",
            required=False,
            default="2"
        ),
    ],
    messages=[
        PromptMessage(
            role="user",
            content="""Verify deployment readiness for '{{app_name}}' ({{image}}) in namespace '{{namespace}}' with {{replicas}} replicas.

## Pre-Deployment Checklist

### 1. Namespace Preparation
- [ ] Namespace '{{namespace}}' exists
- [ ] Resource quotas are set
- [ ] LimitRanges are configured
- [ ] Network policies exist

### 2. Image Verification
- [ ] Image '{{image}}' uses specific tag (not :latest)
- [ ] Image exists and is pullable
- [ ] Image has been scanned for vulnerabilities
- [ ] imagePullSecrets are configured if needed

### 3. Resource Configuration
- [ ] CPU requests and limits are set
- [ ] Memory requests and limits are set
- [ ] Resources are appropriate for workload
- [ ] Pod Disruption Budget is configured for {{replicas}} replicas

### 4. Health Checks
- [ ] Liveness probe is configured
- [ ] Readiness probe is configured
- [ ] Startup probe (if slow starting)
- [ ] Probe endpoints are implemented

### 5. Security Configuration
- [ ] runAsNonRoot: true
- [ ] readOnlyRootFilesystem: true
- [ ] allowPrivilegeEscalation: false
- [ ] Capabilities dropped
- [ ] SecurityContext is set

### 6. Configuration Management
- [ ] ConfigMaps are created
- [ ] Secrets are created
- [ ] Environment variables are set
- [ ] Volume mounts are configured

### 7. Service Configuration
- [ ] Service is created
- [ ] Ports are correctly mapped
- [ ] Service selectors match pod labels
- [ ] Service type is appropriate

### 8. Scaling Configuration
- [ ] HPA is configured (if needed)
- [ ] Scaling metrics are appropriate
- [ ] Min/max replicas are set correctly

### 9. Observability
- [ ] Logging is configured
- [ ] Metrics endpoints exposed
- [ ] Tracing enabled (if applicable)
- [ ] Alerts are configured

### 10. Rollout Strategy
- [ ] RollingUpdate strategy configured
- [ ] maxSurge and maxUnavailable set
- [ ] Rollback plan documented

## Verification Commands

Run these checks before deployment:
1. Verify namespace: `get_namespaces()`
2. Check existing resources: `get_deployments(namespace="{{namespace}}")`
3. Verify configmaps: `get_configmaps(namespace="{{namespace}}")`
4. Check services: `get_services(namespace="{{namespace}}")`

## Post-Deployment Verification

After deploying:
1. Watch rollout: `kubectl_rollout_status("deployment", "{{app_name}}", "{{namespace}}")`
2. Check pods: `get_pods(namespace="{{namespace}}")`
3. Get logs: `get_logs(pod_name, "{{namespace}}")`
4. Verify endpoints: Check service has endpoints

Start the deployment checklist verification now."""
        ),
    ]
)


# Incident Response Prompt
INCIDENT_RESPONSE = CustomPrompt(
    name="incident-response",
    title="Incident Response Guide",
    description="Structured incident response workflow for Kubernetes issues",
    arguments=[
        PromptArgument(
            name="incident_type",
            description="Type of incident (pod-crash, high-latency, oom, network, storage)",
            required=True
        ),
        PromptArgument(
            name="affected_service",
            description="Name of affected service/workload",
            required=True
        ),
        PromptArgument(
            name="namespace",
            description="Namespace of affected resources",
            required=True
        ),
        PromptArgument(
            name="severity",
            description="Incident severity (critical, high, medium, low)",
            required=False,
            default="high"
        ),
    ],
    messages=[
        PromptMessage(
            role="user",
            content="""## INCIDENT RESPONSE: {{incident_type}}

**Affected**: {{affected_service}} in namespace {{namespace}}
**Severity**: {{severity}}

## Phase 1: Triage (First 5 minutes)

### Immediate Assessment
1. Verify the issue:
   - `get_pods(namespace="{{namespace}}")` - Check pod status
   - `kubectl_describe("deployment", "{{affected_service}}", "{{namespace}}")` - Get details

2. Determine blast radius:
   - Is this isolated to {{affected_service}}?
   - Are other services in {{namespace}} affected?
   - Are other namespaces affected?

3. User impact assessment:
   - Is the service completely down?
   - Is it degraded?
   - Are errors being returned?

## Phase 2: Investigation (Next 15 minutes)

### For {{incident_type}} incident:

{{#incident_type}}
**Pod Crash Investigation:**
- `get_pod_events("{{affected_service}}", "{{namespace}}")` - Recent events
- `get_logs(pod_name, "{{namespace}}", tail=200)` - Current logs
- `get_logs(pod_name, "{{namespace}}", previous=true)` - Previous container logs
- Check for OOMKilled, CrashLoopBackOff patterns

**High Latency Investigation:**
- Check pod resource usage
- Review HPA scaling events
- Check dependent services
- Review ingress/load balancer metrics

**OOM Investigation:**
- `kubectl_describe("pod", pod_name, "{{namespace}}")` - Check memory limits
- Review container memory usage patterns
- Check for memory leaks in logs
- Compare to historical usage

**Network Investigation:**
- Check service endpoints exist
- Verify NetworkPolicies aren't blocking
- Test DNS resolution
- Check for connection errors in logs

**Storage Investigation:**
- `kubectl_get("pvc", namespace="{{namespace}}")` - PVC status
- Check if PV is bound
- Verify storage class availability
- Check node storage capacity
{{/incident_type}}

## Phase 3: Mitigation

### Quick Mitigation Options:
1. **Scale up**: Increase replicas if resource-related
2. **Rollback**: Revert to previous working version
3. **Restart**: Delete problematic pods
4. **Cordon**: Remove problematic node from scheduling

### Execute mitigation:
```
# Option 1: Scale up
kubectl_scale("deployment", "{{affected_service}}", replicas+2, "{{namespace}}")

# Option 2: Rollback
kubectl_rollout("undo", "deployment", "{{affected_service}}", "{{namespace}}")

# Option 3: Restart
kubectl_delete_pod(pod_name, "{{namespace}}", force=false)
```

## Phase 4: Verification

1. Confirm mitigation worked:
   - `get_pods(namespace="{{namespace}}")` - All pods healthy
   - Service is responding normally
   - Error rates decreased

2. Monitor for recurrence:
   - Watch pod events
   - Monitor resource usage
   - Track error rates

## Phase 5: Post-Incident

After incident is resolved:
1. Document timeline
2. Capture root cause
3. Identify preventive measures
4. Update runbooks

## Incident Log Template

| Time | Action | Result |
|------|--------|--------|
| | Issue reported | |
| | Investigation started | |
| | Root cause identified | |
| | Mitigation applied | |
| | Service restored | |

Start incident response now."""
        ),
    ]
)


# All built-in prompts
BUILTIN_PROMPTS = [
    CLUSTER_HEALTH_CHECK,
    DEBUG_WORKLOAD,
    RESOURCE_USAGE,
    SECURITY_POSTURE,
    DEPLOYMENT_CHECKLIST,
    INCIDENT_RESPONSE,
]


def get_builtin_prompts() -> list:
    """Return all built-in prompts."""
    return BUILTIN_PROMPTS.copy()


def get_builtin_prompt_by_name(name: str) -> CustomPrompt | None:
    """Get a built-in prompt by name."""
    for prompt in BUILTIN_PROMPTS:
        if prompt.name == name:
            return prompt
    return None
