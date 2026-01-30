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
| 1 | Preview with template before apply | CRITICAL | `template_helm_chart` |
| 2 | Check existing state first | CRITICAL | `get_pods`, `list_helm_releases` |
| 3 | Use progressive delivery for prod | HIGH | `rollout_*` tools |
| 4 | Verify health after deployment | HIGH | `get_pod_metrics`, `get_endpoints` |
| 5 | Keep rollback revision noted | MEDIUM | `get_helm_history` |
| 6 | Scale incrementally | LOW | `scale_deployment` |

## Quick Reference

| Task | Tool | Example |
|------|------|---------|
| Deploy from manifest | `kubectl_apply` | `apply_manifest(yaml, namespace)` |
| Deploy with Helm | `install_helm_chart` | `install_helm_chart(name, chart, namespace)` |
| Update image | `set_deployment_image` | `set_deployment_image(name, ns, container, image)` |
| Scale replicas | `scale_deployment` | `scale_deployment(name, ns, replicas=5)` |
| Rollback | `rollback_deployment` | `rollback_deployment(name, ns, revision=0)` |
| Canary promote | `rollout_promote_tool` | `rollout_promote_tool(name, ns)` |

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
scale_deployment(name, namespace, replicas=5)
```

### Rolling Update

```python
set_deployment_image(name, namespace, container="app", image="myapp:v2")

rollout_status(name, namespace, resource_type="deployment")
```

## Progressive Delivery

### Argo Rollouts (Recommended)

For canary and blue-green deployments with analysis.

**List Rollouts**
```python
rollouts_list_tool(namespace)
```

**Canary Promotion**
```python
rollout_status_tool(name, namespace)

rollout_promote_tool(name, namespace)
```

**Abort Bad Release**
```python
rollout_abort_tool(name, namespace)
```

**Retry Failed Rollout**
```python
rollout_retry_tool(name, namespace)
```

See [ROLLOUTS.md](ROLLOUTS.md) for detailed Argo Rollouts workflows.

### Flagger Canary

For service mesh-integrated canary releases:

```python
flagger_canaries_list_tool(namespace)
flagger_canary_get_tool(name, namespace)
```

## Deployment Strategies

| Strategy | Use Case | Tools |
|----------|----------|-------|
| Rolling | Standard updates | `set_deployment_image`, `rollout_status` |
| Recreate | Stateful apps | Set strategy in manifest |
| Canary | Risk mitigation | `rollout_*` tools |
| Blue-Green | Zero downtime | `rollout_*` with blue-green |

See [references/STRATEGIES.md](references/STRATEGIES.md) for detailed strategy comparisons.

## Rollback Operations

### Native Kubernetes

```python
rollback_deployment(name, namespace, revision=0)

rollback_deployment(name, namespace, revision=2)
```

### Helm Rollback

```python
rollback_helm_release(name, namespace, revision=1)
```

### Argo Rollouts Rollback

```python
rollout_abort_tool(name, namespace)
```

## Health Verification

After deployment, verify health:

```python
get_pods(namespace, label_selector="app=myapp")

get_pod_metrics(name, namespace)

get_endpoints(namespace)
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
