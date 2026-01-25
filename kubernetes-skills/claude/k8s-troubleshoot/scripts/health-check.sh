#!/bin/bash
# Kubernetes Cluster Health Check Script
#
# This script provides a quick cluster health overview.
# Used by the k8s-troubleshoot skill for rapid triage.

set -euo pipefail

CONTEXT="${1:-}"
NAMESPACE="${2:-}"

# Color codes (disabled in non-interactive mode)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

KUBECTL_OPTS=""
if [ -n "$CONTEXT" ]; then
    KUBECTL_OPTS="--context=$CONTEXT"
fi

echo "=== Kubernetes Cluster Health Check ==="
echo "Context: ${CONTEXT:-current}"
echo "Namespace: ${NAMESPACE:-all}"
echo ""

# Check node status
echo "--- Node Status ---"
NOT_READY=$(kubectl $KUBECTL_OPTS get nodes --no-headers 2>/dev/null | grep -v " Ready" | wc -l | tr -d ' ')
TOTAL_NODES=$(kubectl $KUBECTL_OPTS get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')

if [ "$NOT_READY" -eq 0 ]; then
    log_ok "All $TOTAL_NODES nodes are Ready"
else
    log_error "$NOT_READY of $TOTAL_NODES nodes are NOT Ready"
    kubectl $KUBECTL_OPTS get nodes | grep -v " Ready"
fi
echo ""

# Check system pods
echo "--- System Pods (kube-system) ---"
FAILED_SYSTEM=$(kubectl $KUBECTL_OPTS get pods -n kube-system --no-headers 2>/dev/null | grep -v "Running\|Completed" | wc -l | tr -d ' ')

if [ "$FAILED_SYSTEM" -eq 0 ]; then
    log_ok "All system pods are healthy"
else
    log_error "$FAILED_SYSTEM system pods are unhealthy"
    kubectl $KUBECTL_OPTS get pods -n kube-system | grep -v "Running\|Completed"
fi
echo ""

# Check namespace pods if specified
if [ -n "$NAMESPACE" ]; then
    echo "--- Pods in $NAMESPACE ---"
    FAILED_NS=$(kubectl $KUBECTL_OPTS get pods -n "$NAMESPACE" --no-headers 2>/dev/null | grep -v "Running\|Completed" | wc -l | tr -d ' ')

    if [ "$FAILED_NS" -eq 0 ]; then
        log_ok "All pods in $NAMESPACE are healthy"
    else
        log_warn "$FAILED_NS pods in $NAMESPACE are unhealthy"
        kubectl $KUBECTL_OPTS get pods -n "$NAMESPACE" | grep -v "Running\|Completed"
    fi
    echo ""
fi

# Check for pending PVCs
echo "--- Storage (Pending PVCs) ---"
PENDING_PVCS=$(kubectl $KUBECTL_OPTS get pvc --all-namespaces --no-headers 2>/dev/null | grep -v "Bound" | wc -l | tr -d ' ')

if [ "$PENDING_PVCS" -eq 0 ]; then
    log_ok "No pending PVCs"
else
    log_warn "$PENDING_PVCS PVCs are pending"
    kubectl $KUBECTL_OPTS get pvc --all-namespaces | grep -v "Bound"
fi
echo ""

# Check recent events
echo "--- Recent Warning Events (last 10) ---"
kubectl $KUBECTL_OPTS get events --all-namespaces --field-selector type=Warning --sort-by='.lastTimestamp' 2>/dev/null | tail -10 || true
echo ""

echo "=== Health Check Complete ==="
