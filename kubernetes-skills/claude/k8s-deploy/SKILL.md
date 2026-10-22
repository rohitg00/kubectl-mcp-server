---
name: k8s-deploy
description: Deploy and manage Kubernetes workloads with progressive delivery. Use for deployments, rollouts, blue-green, canary releases, scaling, and release management.
license: Apache-2.0
metadata:
  author: rohitg00
  version: "1.0.0"
  tools: 20
  category: workloads
---

# Kubernetes Deployment Workflows

Comprehensive deployment strategies using kubectl-mcp-server tools, including Argo Rollouts and Flagger for progressive delivery.

## When to Apply

Use this skill when:
- User mentions: "deploy", "release", "rollout", "scale", "update", "upgrade"
- Operations: creating deployments, updating images, scaling replicas
- Strategies: canary, blue-green, rolling update, recreate
- Keywords: "new version", "push to production", "traffic shifting"

## Priority Rules

| Priority | Rule | Impact | Tools |
|----------|------|--------|-------|
| 1 | Preview with template before apply | CRITICAL | `helm_template` |
| 2 | Check existing state first | CRITICAL | `kubectl_get`, `helm_list` |
| 3 | Use progressive delivery for prod | HIGH | `rollout_*` tools |
| 4 | Verify health after deployment | HIGH | `kubectl_top`, `kubectl_get` |
| 5 | Keep rollback revision noted | MEDIUM | `helm_history` |
| 6 | Scale incrementally | LOW | `kubectl_scale` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Deploy from manifest | `kubectl_apply` | `kubectl_apply(yaml, namespace)` |
| Deploy with Helm | `install_helm_chart` | `install_helm_chart(name, chart, namespace)` |
| Update image | `kubectl_patch` | `kubectl_patch(name, ns, container, image)` |
| Scale replicas | `kubectl_scale` | `kubectl_scale(resource_type="deployment", name, ns, replicas=5)` |
| Rollback | `kubectl_rollout` | `kubectl_rollout(name, ns, revision=0)` |
| Canary promote | `promote_rollout` | `promote_rollout(name, ns)` |

## Standard Deployments

### Deploy from Manifest

```python
kubectl_apply(manifest_yaml, namespace)
```

### Deploy with Helm

```python
install_helm_chart(
    name="my-app",
    chart="bitnami/nginx",
    namespace="production",
    values={"replicaCount": 3}
)
```

### Scale Deployment

```python
kubectl_scale(resource_type="deployment", name, namespace, replicas=5)
```

### Rolling Update

```python
kubectl_patch(name, namespace, container="app", image="myapp:v2")

kubectl_rollout(name, namespace, resource_type="deployment")
```

## Progressive Delivery

### Argo Rollouts (Recommended)

For canary and blue-green deployments with analysis.

**List Rollouts**
```python
get_rollouts_list(namespace)
```

**Canary Promotion**
```python
get_rollout_status(name, namespace)

promote_rollout(name, namespace)
```

**Abort Bad Release**
```python
abort_rollout(name, namespace)
```

**Retry Failed Rollout**
```python
retry_rollout(name, namespace)
```

See [ROLLOUTS.md](ROLLOUTS.md) for detailed Argo Rollouts workflows.

### Flagger Canary

For service mesh-integrated canary releases:

```python
get_flagger_canaries(namespace)
get_flagger_canary(name, namespace)
```

## Deployment Strategies

| Strategy | Use Case | Tools |
|----------|----------|-------|
| Rolling | Standard updates | `kubectl_patch`, `kubectl_rollout` |
| Recreate | Stateful apps | Set strategy in manifest |
| Canary | Risk mitigation | `rollout_*` tools |
| Blue-Green | Zero downtime | `rollout_*` with blue-green |

See [references/STRATEGIES.md](references/STRATEGIES.md) for detailed strategy comparisons.

## Rollback Operations

### Native Kubernetes

```python
kubectl_rollout(name, namespace, revision=0)

kubectl_rollout(name, namespace, revision=2)
```

### Helm Rollback

```python
helm_rollback(name, namespace, revision=1)
```

### Argo Rollouts Rollback

```python
abort_rollout(name, namespace)
```

## Health Verification

After deployment, verify health:

```python
kubectl_get(resource_type="pods", namespace, label_selector="app=myapp")

kubectl_top(name, namespace)

kubectl_get(resource_type="endpoints", namespace)
```

## Multi-Cluster Deployments

Deploy to specific clusters using context:

```python
install_helm_chart(
    name="app",
    chart="./charts/app",
    namespace="prod",
    context="production-us-east"
)

install_helm_chart(
    name="app",
    chart="./charts/app",
    namespace="prod",
    context="production-eu-west"
)
```

## Example Manifests

See [examples/](examples/) for ready-to-use deployment manifests:
- [examples/canary-rollout.yaml](examples/canary-rollout.yaml) - Argo Rollouts canary
- [examples/blue-green.yaml](examples/blue-green.yaml) - Blue-green deployment
- [examples/hpa-deployment.yaml](examples/hpa-deployment.yaml) - Deployment with HPA

## Prerequisites

- **Argo Rollouts**: Required for `rollout_*` tools
  ```bash
  kubectl create namespace argo-rollouts
  kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
  ```
- **Flagger**: Required for `flagger_*` tools
  ```bash
  kubectl apply -k github.com/fluxcd/flagger/kustomize/kubernetes
  ```

## Related Skills

- [k8s-gitops](../k8s-gitops/SKILL.md) - GitOps deployments with Flux/ArgoCD
- [k8s-autoscaling](../k8s-autoscaling/SKILL.md) - Auto-scale deployments
- [k8s-rollouts](../k8s-rollouts/SKILL.md) - Advanced progressive delivery
- [k8s-helm](../k8s-helm/SKILL.md) - Helm chart operations
