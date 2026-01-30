---
name: k8s-policy
description: Kubernetes policy management with Kyverno and Gatekeeper. Use when enforcing security policies, validating resources, or auditing policy compliance.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 6
  category: security
---

# Kubernetes Policy Management

Manage policies using kubectl-mcp-server's Kyverno and Gatekeeper tools.

## When to Apply

Use this skill when:
- User mentions: "Kyverno", "Gatekeeper", "OPA", "policy", "compliance"
- Operations: enforcing policies, checking violations, policy audit
- Keywords: "require labels", "block privileged", "validate", "enforce"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Detect policy engine first | CRITICAL | `kyverno_detect_tool`, `gatekeeper_detect_tool` |
| 2 | Use Audit mode before Enforce | HIGH | validationFailureAction |
| 3 | Check policy reports for violations | HIGH | `kyverno_clusterpolicyreports_list_tool` |
| 4 | Review constraint templates | MEDIUM | `gatekeeper_constrainttemplates_list_tool` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| List Kyverno cluster policies | `kyverno_clusterpolicies_list_tool` | `kyverno_clusterpolicies_list_tool()` |
| Get Kyverno policy | `kyverno_clusterpolicy_get_tool` | `kyverno_clusterpolicy_get_tool(name)` |
| List Gatekeeper constraints | `gatekeeper_constraints_list_tool` | `gatekeeper_constraints_list_tool()` |
| Get constraint | `gatekeeper_constraint_get_tool` | `gatekeeper_constraint_get_tool(kind, name)` |

## Kyverno

### Detect Installation

```python
kyverno_detect_tool()
```

### List Policies

```python
kyverno_clusterpolicies_list_tool()

kyverno_policies_list_tool(namespace="default")
```

### Get Policy Details

```python
kyverno_clusterpolicy_get_tool(name="require-labels")
kyverno_policy_get_tool(name="require-resources", namespace="default")
```

### Policy Reports

```python
kyverno_clusterpolicyreports_list_tool()

kyverno_policyreports_list_tool(namespace="default")
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
gatekeeper_detect_tool()
```

### List Constraints

```python
gatekeeper_constraints_list_tool()

gatekeeper_constrainttemplates_list_tool()
```

### Get Constraint Details

```python
gatekeeper_constraint_get_tool(
    kind="K8sRequiredLabels",
    name="require-app-label"
)

gatekeeper_constrainttemplate_get_tool(name="k8srequiredlabels")
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
kyverno_detect_tool()
kyverno_clusterpolicies_list_tool()
kyverno_clusterpolicyreports_list_tool()
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
