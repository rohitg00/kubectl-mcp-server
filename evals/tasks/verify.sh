#!/bin/bash
# Verification script for kubectl-mcp-server evals
# Validates that expected resources exist and are in correct state

set -e

# Configuration
NAMESPACE="${EVAL_NAMESPACE:-eval-test}"
RESOURCE_NAME="${1:-web-server}"
RESOURCE_TYPE="${2:-pod}"

echo "=== Verifying eval results ==="
echo "Namespace: $NAMESPACE"
echo "Resource: $RESOURCE_TYPE/$RESOURCE_NAME"

# Function to check resource exists
check_resource() {
    local type=$1
    local name=$2
    local namespace=$3

    if kubectl get "$type" "$name" -n "$namespace" &>/dev/null; then
        echo "PASS: $type/$name exists"
        return 0
    else
        echo "FAIL: $type/$name not found"
        return 1
    fi
}

# Function to check pod is running
check_pod_running() {
    local name=$1
    local namespace=$2

    local phase
    phase=$(kubectl get pod "$name" -n "$namespace" -o jsonpath='{.status.phase}' 2>/dev/null)

    if [[ "$phase" == "Running" ]]; then
        echo "PASS: Pod $name is Running"
        return 0
    elif [[ "$phase" == "Succeeded" ]]; then
        echo "PASS: Pod $name has Succeeded"
        return 0
    else
        echo "FAIL: Pod $name is in phase: $phase (expected Running or Succeeded)"
        return 1
    fi
}

# Function to check deployment is ready
check_deployment_ready() {
    local name=$1
    local namespace=$2

    local ready
    ready=$(kubectl get deployment "$name" -n "$namespace" -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
    local desired
    desired=$(kubectl get deployment "$name" -n "$namespace" -o jsonpath='{.spec.replicas}' 2>/dev/null)

    if [[ "$ready" == "$desired" ]] && [[ -n "$ready" ]]; then
        echo "PASS: Deployment $name has $ready/$desired replicas ready"
        return 0
    else
        echo "FAIL: Deployment $name has ${ready:-0}/$desired replicas ready"
        return 1
    fi
}

# Function to check service has endpoints
check_service_endpoints() {
    local name=$1
    local namespace=$2

    local endpoints
    endpoints=$(kubectl get endpoints "$name" -n "$namespace" -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null)

    if [[ -n "$endpoints" ]]; then
        echo "PASS: Service $name has endpoints: $endpoints"
        return 0
    else
        echo "FAIL: Service $name has no endpoints"
        return 1
    fi
}

# Function to check Helm release exists
check_helm_release() {
    local name=$1
    local namespace=$2

    if helm status "$name" -n "$namespace" &>/dev/null; then
        local status
        status=$(helm status "$name" -n "$namespace" -o json | jq -r '.info.status')
        echo "PASS: Helm release $name exists with status: $status"
        return 0
    else
        echo "FAIL: Helm release $name not found"
        return 1
    fi
}

# Main verification logic
FAILURES=0

case "$RESOURCE_TYPE" in
    pod)
        check_resource pod "$RESOURCE_NAME" "$NAMESPACE" || ((FAILURES++))
        check_pod_running "$RESOURCE_NAME" "$NAMESPACE" || ((FAILURES++))
        ;;
    deployment)
        check_resource deployment "$RESOURCE_NAME" "$NAMESPACE" || ((FAILURES++))
        check_deployment_ready "$RESOURCE_NAME" "$NAMESPACE" || ((FAILURES++))
        ;;
    service)
        check_resource service "$RESOURCE_NAME" "$NAMESPACE" || ((FAILURES++))
        check_service_endpoints "$RESOURCE_NAME" "$NAMESPACE" || ((FAILURES++))
        ;;
    helm)
        check_helm_release "$RESOURCE_NAME" "$NAMESPACE" || ((FAILURES++))
        ;;
    *)
        check_resource "$RESOURCE_TYPE" "$RESOURCE_NAME" "$NAMESPACE" || ((FAILURES++))
        ;;
esac

echo ""
echo "=== Verification complete ==="

if [[ $FAILURES -eq 0 ]]; then
    echo "Result: PASSED"
    exit 0
else
    echo "Result: FAILED ($FAILURES checks failed)"
    exit 1
fi
