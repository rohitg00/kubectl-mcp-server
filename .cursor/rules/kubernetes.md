# Kubernetes Operations Rules

## kubectl Command Execution

Always execute kubectl commands safely:

```python
import subprocess
import shlex

def run_kubectl(args: List[str]) -> str:
    """Execute kubectl with args list (NOT shell string)."""
    cmd = ["kubectl"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout
```

## Allowed kubectl Subcommands

Only these subcommands should be allowed for AI-triggered operations:

**Read-only (safe):**
- get, describe, explain, logs, top, api-resources, api-versions
- version, cluster-info, config view, config get-contexts

**Write operations (require confirmation):**
- apply, create, delete, patch, scale, rollout
- label, annotate, taint

**Dangerous (block or require extra confirmation):**
- exec, port-forward (security implications)
- delete namespace, delete all

## Output Formatting

Return structured data for AI parsing:

```python
# Good: Structured response
return {
    "success": True,
    "pods": [
        {"name": "pod-1", "status": "Running", "restarts": 0},
        {"name": "pod-2", "status": "Pending", "restarts": 0}
    ],
    "namespace": "default",
    "count": 2
}

# Avoid: Raw kubectl output
return {"output": "NAME   STATUS   ...\npod-1  Running  ..."}
```

## Multi-cluster Support

Handle multiple Kubernetes contexts:

```python
# List contexts
kubectl config get-contexts -o name

# Use specific context
kubectl --context=production get pods

# Switch context
kubectl config use-context production
```

## Namespace Handling

- Default to "default" namespace if not specified
- Support --all-namespaces for cluster-wide queries
- Validate namespace exists before operations

```python
namespace = namespace or "default"
cmd = ["kubectl", "get", "pods", "-n", namespace, "-o", "json"]
```

## Error Handling

Parse kubectl errors and return actionable messages:

```python
if result.returncode != 0:
    error = result.stderr
    if "not found" in error.lower():
        return {"success": False, "error": "Resource not found", "details": error}
    if "forbidden" in error.lower():
        return {"success": False, "error": "Permission denied", "details": error}
    return {"success": False, "error": "kubectl failed", "details": error}
```

## Helm Operations

For Helm chart operations:

```python
# Install
helm install <name> <chart> -n <namespace> --create-namespace

# Upgrade
helm upgrade <name> <chart> -n <namespace>

# Uninstall
helm uninstall <name> -n <namespace>
```

Always check if Helm is available before offering Helm tools.
