---
name: k8s-policy
description: Kubernetes policy management with Kyverno and Gatekeeper. Use when enforcing security policies, validating resources, or auditing policy compliance.
license: MIT-0
metadata:
  author: rohitg00
  version: "2.0.0"
  tools: 5
  category: security
---

# Kubernetes Policy Management

Manage policies using kubectl-mcp-server's Kyverno and Gatekeeper tools.

> Requires the `policy` toolset: start kubectl-mcp-server with `--toolsets default,policy` (or `MCP_TOOLSETS=default,policy`). For deep work, the project-maintained MCP servers may fit better: Kyverno: https://github.com/nirmata/kyverno-mcp.

## When to Apply

Use this skill when:
- User mentions: "Kyverno", "Gatekeeper", "OPA", "policy", "compliance"
- Operations: enforcing policies, checking violations, policy audit
- Keywords: "require labels", "block privileged", "validate", "enforce"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect policy engine first | CRITICAL | `detect_ecosystem`, `detect_ecosystem` |
| 2 | Use Audit mode before Enforce | HIGH | validationFailureAction |
| 3 | Check policy reports for violations | HIGH | `get_policy_violations` |
| 4 | Review constraint templates | MEDIUM | `get_policy_list` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List Kyverno cluster policies | `get_policy_list` | `get_policy_list()` |
| Get Kyverno policy | `get_policy` | `get_policy(name)` |
| List Gatekeeper constraints | `get_policy_list` | `get_policy_list()` |
| Get constraint | `get_policy` | `get_policy(kind, name)` |

## Kyverno

### Detect Installation

```python
detect_ecosystem()
```

### List Policies

```python
get_policy_list()

get_policy_list(namespace="default")
```

### Get Policy Details

```python
get_policy(name="require-labels")
get_policy(name="require-resources", namespace="default")
```

### Policy Reports

```python
get_policy_violations()

get_policy_violations(namespace="default")
```

### Common Kyverno Policies

```python
kubectl_apply(manifest="""
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
spec:
  validationFailureAction: Enforce
  rules:
  - name: require-app-label
    match:
      resources:
        kinds:
        - Pod
    validate:
      message: "Label 'app' is required"
      pattern:
        metadata:
          labels:
            app: "?*"
""")

kubectl_apply(manifest="""
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-limits
spec:
  validationFailureAction: Enforce
  rules:
  - name: require-cpu-memory
    match:
      resources:
        kinds:
        - Pod
    validate:
      message: "CPU and memory limits required"
      pattern:
        spec:
          containers:
          - resources:
              limits:
                cpu: "?*"
                memory: "?*"
""")
```

## Gatekeeper (OPA)

### Detect Installation

```python
detect_ecosystem()
```

### List Constraints

```python
get_policy_list()

get_policy_list()
```

### Get Constraint Details

```python
get_policy(
    kind="K8sRequiredLabels",
    name="require-app-label"
)

get_policy(name="k8srequiredlabels")
```

### Common Gatekeeper Policies

```python
kubectl_apply(manifest="""
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequiredlabels
      violation[{"msg": msg}] {
        provided := {label | input.review.object.metadata.labels[label]}
        required := {label | label := input.parameters.labels[_]}
        missing := required - provided
        count(missing) > 0
        msg := sprintf("Missing labels: %v", [missing])
      }
""")

kubectl_apply(manifest="""
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-app-label
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    labels: ["app", "env"]
""")
```

## Policy Audit Workflow

```python
detect_ecosystem()
get_policy_list()
get_policy_violations()
```

## Prerequisites

- **Kyverno**: Required for Kyverno tools
  ```bash
  kubectl create -f https://github.com/kyverno/kyverno/releases/latest/download/install.yaml
  ```
- **Gatekeeper**: Required for Gatekeeper tools
  ```bash
  kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/master/deploy/gatekeeper.yaml
  ```

## Related Skills

- [k8s-security](../k8s-security/SKILL.md) - RBAC and security
- [k8s-operations](../k8s-operations/SKILL.md) - Apply policies
