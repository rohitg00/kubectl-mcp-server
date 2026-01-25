---
name: k8s-deploy
description: Deploy and manage Kubernetes workloads with progressive delivery. Use for deployments, rollouts, blue-green, canary releases, scaling, and release management.
---

# Kubernetes Deployment Workflows

Comprehensive deployment strategies using kubectl-mcp-server tools, including Argo Rollouts and Flagger for progressive delivery.

## Standard Deployments

### Deploy from Manifest
```
apply_manifest(manifest_yaml, namespace)
```

### Deploy with Helm
```
install_helm_chart(
    name="my-app",
    chart="bitnami/nginx",
    namespace="production",
    values={"replicaCount": 3}
)
```

### Scale Deployment
```
scale_deployment(name, namespace, replicas=5)
```

### Rolling Update
```
# Update image
set_deployment_image(name, namespace, container="app", image="myapp:v2")

# Watch rollout
rollout_status(name, namespace, resource_type="deployment")
```

## Progressive Delivery

### Argo Rollouts (Recommended)

For canary and blue-green deployments with analysis:

**List Rollouts**
```
rollouts_list_tool(namespace)
```

**Canary Promotion**
```
# Check status first
rollout_status_tool(name, namespace)

# Promote if analysis passes
rollout_promote_tool(name, namespace)
```

**Abort Bad Release**
```
rollout_abort_tool(name, namespace)
```

**Retry Failed Rollout**
```
rollout_retry_tool(name, namespace)
```

See [ROLLOUTS.md](ROLLOUTS.md) for detailed Argo Rollouts workflows.

### Flagger Canary

For service mesh-integrated canary releases:

```
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

## Rollback Operations

### Native Kubernetes
```
rollback_deployment(name, namespace, revision=0)  # Previous
rollback_deployment(name, namespace, revision=2)  # Specific
```

### Helm Rollback
```
rollback_helm_release(name, namespace, revision=1)
```

### Argo Rollouts Rollback
```
rollout_abort_tool(name, namespace)  # Aborts and rolls back
```

## Health Verification

After deployment, verify health:
```
1. get_pods(namespace, label_selector="app=myapp")
2. get_pod_metrics(name, namespace)
3. get_endpoints(namespace)  # Check service backends
```

## Multi-Cluster Deployments

Deploy to specific clusters using context:
```
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

## Related Skills
- [k8s-gitops](../k8s-gitops/SKILL.md) - GitOps deployments with Flux/ArgoCD
- [k8s-autoscaling](../k8s-autoscaling/SKILL.md) - Auto-scale deployments
