#!/bin/bash
# Setup script for kubectl-mcp-server evals
# Creates the test namespace and any required resources

set -e

# Configuration
NAMESPACE="${EVAL_NAMESPACE:-eval-test}"
TIMEOUT="${EVAL_TIMEOUT:-60}"

echo "=== Setting up eval environment ==="
echo "Namespace: $NAMESPACE"
echo "Timeout: ${TIMEOUT}s"

# Check kubectl connectivity
if ! kubectl cluster-info &>/dev/null; then
    echo "ERROR: Cannot connect to Kubernetes cluster"
    echo "Please ensure kubectl is configured correctly"
    exit 1
fi

echo "Connected to cluster: $(kubectl config current-context)"

# Create namespace (idempotent)
echo "Creating namespace $NAMESPACE..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Wait for namespace to be active
echo "Waiting for namespace to be active..."
kubectl wait --for=jsonpath='{.status.phase}'=Active "namespace/$NAMESPACE" --timeout="${TIMEOUT}s"

# Create a service account for tests (optional)
echo "Creating test service account..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: eval-test-sa
  namespace: $NAMESPACE
EOF

# Create resource quota to prevent runaway resources
echo "Creating resource quota..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: eval-quota
  namespace: $NAMESPACE
spec:
  hard:
    pods: "20"
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "8"
    limits.memory: "16Gi"
    persistentvolumeclaims: "5"
EOF

# Create a ConfigMap for test data
echo "Creating test ConfigMap..."
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: eval-config
  namespace: $NAMESPACE
data:
  test-key: "test-value"
  environment: "eval"
EOF

echo ""
echo "=== Setup complete ==="
echo "Namespace $NAMESPACE is ready for eval tasks"
echo ""
echo "Resources created:"
kubectl get all,configmap,sa -n "$NAMESPACE" 2>/dev/null || true
