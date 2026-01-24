#!/bin/bash
# Cleanup script for kubectl-mcp-server evals
# Removes all test resources created during evaluation

set -e

# Configuration
NAMESPACE="${EVAL_NAMESPACE:-eval-test}"
FORCE="${EVAL_FORCE_CLEANUP:-false}"

echo "=== Cleaning up eval environment ==="
echo "Namespace: $NAMESPACE"

# Function to safely delete resources
safe_delete() {
    local resource=$1
    local namespace=$2
    local timeout=${3:-30}

    echo "Deleting $resource in namespace $namespace..."
    kubectl delete "$resource" -n "$namespace" --all --timeout="${timeout}s" --ignore-not-found 2>/dev/null || true
}

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "Namespace $NAMESPACE does not exist, nothing to clean up"
    exit 0
fi

# Delete resources in order (to handle dependencies)
echo "Removing resources from namespace $NAMESPACE..."

# Delete workloads first
safe_delete deployments "$NAMESPACE"
safe_delete statefulsets "$NAMESPACE"
safe_delete daemonsets "$NAMESPACE"
safe_delete replicasets "$NAMESPACE"
safe_delete pods "$NAMESPACE"
safe_delete jobs "$NAMESPACE"
safe_delete cronjobs "$NAMESPACE"

# Delete services and networking
safe_delete services "$NAMESPACE"
safe_delete ingresses "$NAMESPACE"
safe_delete networkpolicies "$NAMESPACE"

# Delete config resources
safe_delete configmaps "$NAMESPACE"
safe_delete secrets "$NAMESPACE"

# Delete storage resources
safe_delete persistentvolumeclaims "$NAMESPACE"

# Delete RBAC resources
safe_delete serviceaccounts "$NAMESPACE"
safe_delete roles "$NAMESPACE"
safe_delete rolebindings "$NAMESPACE"

# Delete resource quotas and limits
safe_delete resourcequotas "$NAMESPACE"
safe_delete limitranges "$NAMESPACE"

# Uninstall Helm releases in namespace
echo "Removing Helm releases..."
if command -v helm &>/dev/null; then
    for release in $(helm list -n "$NAMESPACE" -q 2>/dev/null); do
        echo "Uninstalling Helm release: $release"
        helm uninstall "$release" -n "$NAMESPACE" --wait --timeout 60s 2>/dev/null || true
    done
fi

# Wait for pods to terminate
echo "Waiting for pods to terminate..."
kubectl wait --for=delete pod --all -n "$NAMESPACE" --timeout=60s 2>/dev/null || true

# Delete the namespace itself
echo "Deleting namespace $NAMESPACE..."
kubectl delete namespace "$NAMESPACE" --ignore-not-found --timeout=120s

# Verify namespace is gone
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "WARNING: Namespace $NAMESPACE still exists (may have finalizers)"

    if [[ "$FORCE" == "true" ]]; then
        echo "Force cleanup enabled, removing finalizers..."
        kubectl patch namespace "$NAMESPACE" -p '{"metadata":{"finalizers":[]}}' --type=merge 2>/dev/null || true
        kubectl delete namespace "$NAMESPACE" --force --grace-period=0 2>/dev/null || true
    fi
else
    echo "Namespace $NAMESPACE deleted successfully"
fi

echo ""
echo "=== Cleanup complete ==="

# Show any remaining resources (for debugging)
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo ""
    echo "WARNING: Some resources may still exist:"
    kubectl get all -n "$NAMESPACE" 2>/dev/null || true
fi
