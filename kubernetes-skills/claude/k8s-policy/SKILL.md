---
name: k8s-policy
description: Kubernetes policy management with Kyverno and Gatekeeper. Use when enforcing security policies, validating resources, or auditing policy compliance.
---

# Kubernetes Policy Management

Manage policies using kubectl-mcp-server's Kyverno and Gatekeeper tools.

## Kyverno

### Detect Installation

```python
kyverno_detect_tool()
```

### List Policies

```python
# Cluster-wide policies
kyverno_clusterpolicies_list_tool()

# Namespace policies
kyverno_policies_list_tool(namespace="default")
```

### Get Policy Details

```python
kyverno_clusterpolicy_get_tool(name="require-labels")
kyverno_policy_get_tool(name="require-resources", namespace="default")
```

### Policy Reports

```python
# Cluster policy reports
kyverno_clusterpolicyreports_list_tool()

# Namespace policy reports
kyverno_policyreports_list_tool(namespace="default")

# Reports show:
# - Pass: Resources compliant
# - Fail: Resources violating policy
# - Warn: Advisory violations
# - Error: Policy evaluation errors
```

### Common Kyverno Policies

```python
# Require labels
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

# Require resource limits
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
# List all constraints
gatekeeper_constraints_list_tool()

# List constraint templates
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
# Constraint template for required labels
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

# Constraint using template
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
1. kyverno_detect_tool() or gatekeeper_detect_tool()
2. kyverno_clusterpolicies_list_tool()  # List policies
3. kyverno_clusterpolicyreports_list_tool()  # Check violations
4. # Fix violations or update policies
```

## Related Skills

- [k8s-security](../k8s-security/SKILL.md) - RBAC and security
- [k8s-operations](../k8s-operations/SKILL.md) - Apply policies
