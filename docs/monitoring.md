# Monitoring Features Guide

This document provides detailed information about the monitoring capabilities of kubectl-mcp-server.

## Overview

The kubectl-mcp-server provides comprehensive monitoring features that allow AI assistants to observe and analyze your Kubernetes cluster's health, resource usage, and events.

## Available Monitoring Tools

### 1. Cluster Health Check

**Tool**: `health_check`

Performs a basic health check by pinging the Kubernetes API server.

**Example Response**:
```json
{
  "success": true,
  "message": "Cluster API is reachable"
}
```

**Use Cases**:
- Verify cluster connectivity before performing operations
- Quick status check for incident response
- Validate kubeconfig is working correctly

### 2. Resource Usage Monitoring

**Tool**: `get_resource_usage`

Gets CPU and memory usage statistics for pods and nodes using `kubectl top`.

**Parameters**:
- `namespace` (optional): Limit to a specific namespace. If not specified, shows all namespaces.

**Requirements**:
- Metrics Server must be installed in your cluster
- Install with: `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`

**Example Response**:
```json
{
  "success": true,
  "pod_usage": {
    "items": [
      {
        "namespace": "default",
        "name": "nginx-deployment-abc123",
        "cpu": "10m",
        "memory": "50Mi"
      }
    ]
  },
  "node_usage": {
    "items": [
      {
        "name": "node-1",
        "cpu": "500m",
        "memory": "2Gi"
      }
    ]
  }
}
```

**Use Cases**:
- Identify resource-hungry pods
- Capacity planning
- Troubleshoot performance issues
- Monitor node resource utilization

### 3. Cluster Events

**Tool**: `get_events`

Retrieves Kubernetes events from the cluster.

**Parameters**:
- `namespace` (optional): Limit to a specific namespace.

**Example Response**:
```json
{
  "success": true,
  "events": [
    {
      "name": "nginx.123abc",
      "namespace": "default",
      "type": "Warning",
      "reason": "FailedScheduling",
      "message": "0/3 nodes are available: 3 Insufficient memory."
    },
    {
      "name": "web-deployment.456def",
      "namespace": "production",
      "type": "Normal",
      "reason": "Scheduled",
      "message": "Successfully assigned production/web-pod to node-2"
    }
  ]
}
```

**Use Cases**:
- Troubleshoot scheduling issues
- Monitor deployment progress
- Identify recurring problems
- Audit cluster activity

### 4. Pod-Specific Events

**Tool**: `get_pod_events`

Retrieves events for a specific pod.

**Parameters**:
- `pod_name` (required): Name of the pod
- `namespace` (default: "default"): Namespace of the pod

**Example Response**:
```json
{
  "success": true,
  "events": [
    {
      "name": "nginx.pulling",
      "type": "Normal",
      "reason": "Pulling",
      "message": "Pulling image nginx:latest",
      "timestamp": "2025-01-19T10:00:00Z"
    },
    {
      "name": "nginx.pulled",
      "type": "Normal",
      "reason": "Pulled",
      "message": "Successfully pulled image nginx:latest",
      "timestamp": "2025-01-19T10:00:05Z"
    }
  ]
}
```

**Use Cases**:
- Debug pod startup issues
- Track image pull problems
- Investigate pod restarts
- Understand pod lifecycle

### 5. Pod Health Check

**Tool**: `check_pod_health`

Checks the health status of a specific pod.

**Parameters**:
- `pod_name` (required): Name of the pod
- `namespace` (default: "default"): Namespace of the pod

**Example Response**:
```json
{
  "success": true,
  "phase": "Running",
  "conditions": ["Initialized", "Ready", "ContainersReady", "PodScheduled"]
}
```

**Pod Phases**:
- `Pending`: Pod accepted but not yet running
- `Running`: Pod bound to a node, all containers started
- `Succeeded`: All containers terminated successfully
- `Failed`: All containers terminated, at least one failed
- `Unknown`: Pod state could not be determined

**Use Cases**:
- Verify deployment success
- Check readiness before routing traffic
- Identify unhealthy pods
- Validate liveness/readiness probes

### 6. Pod Logs

**Tool**: `get_logs`

Retrieves logs from a pod's containers.

**Parameters**:
- `pod_name` (required): Name of the pod
- `namespace` (default: "default"): Namespace of the pod
- `container` (optional): Specific container name
- `tail` (optional): Number of lines to retrieve from the end

**Example Response**:
```json
{
  "success": true,
  "logs": "2025-01-19 10:00:00 INFO Starting application...\n2025-01-19 10:00:01 INFO Server listening on port 8080"
}
```

**Use Cases**:
- Debug application errors
- Trace request processing
- Monitor startup issues
- Analyze crash logs

### 7. Node Information

**Tool**: `get_nodes`

Lists all cluster nodes with their status.

**Example Response**:
```json
{
  "success": true,
  "nodes": [
    {
      "name": "node-1",
      "status": "Ready",
      "addresses": ["192.168.1.10", "node-1.cluster.local"]
    },
    {
      "name": "node-2",
      "status": "NotReady",
      "addresses": ["192.168.1.11", "node-2.cluster.local"]
    }
  ]
}
```

**Use Cases**:
- Monitor node health
- Identify failed nodes
- Plan maintenance windows
- Verify cluster capacity

## Common Monitoring Workflows

### 1. Incident Response Workflow

```
1. health_check                    # Verify cluster is accessible
2. get_events                      # Check for cluster-wide issues
3. get_nodes                       # Verify all nodes are healthy
4. get_pods (namespace=affected)   # Check pod status
5. get_pod_events (pod=problem)    # Get specific pod events
6. get_logs (pod=problem)          # Analyze application logs
```

### 2. Performance Analysis Workflow

```
1. get_resource_usage              # Get current resource utilization
2. get_nodes                       # Check node capacity
3. get_deployments                 # Review replica counts
4. get_pods                        # Identify high-usage pods
```

### 3. Deployment Verification Workflow

```
1. get_deployments (namespace=x)   # Check deployment status
2. get_pods (namespace=x)          # Verify pods are running
3. check_pod_health (pod=new)      # Confirm pod is healthy
4. get_pod_events (pod=new)        # Review startup events
5. get_logs (pod=new, tail=50)     # Check application startup
```

## Best Practices

1. **Regular Health Checks**: Run `health_check` before critical operations to ensure cluster connectivity.

2. **Event Monitoring**: Regularly check `get_events` to catch issues early.

3. **Resource Monitoring**: Use `get_resource_usage` to prevent resource exhaustion.

4. **Log Rotation Awareness**: Use `tail` parameter to limit log retrieval for large applications.

5. **Namespace Isolation**: Always specify namespace to focus on relevant resources.

## Integration with AI Assistants

When using kubectl-mcp-server with AI assistants like Claude, you can ask natural language questions:

- "Is my cluster healthy?"
- "What events have occurred in the last hour?"
- "Show me the logs from the failing pod"
- "Which pods are using the most memory?"
- "Why is my deployment not starting?"

The AI assistant will use the appropriate monitoring tools to gather information and provide insights.

## Limitations

1. **Metrics Server Requirement**: `get_resource_usage` requires Metrics Server to be installed.

2. **Historical Data**: These tools provide current state only. For historical data, integrate with Prometheus/Grafana.

3. **Log Size**: Large log files may be truncated. Use `tail` parameter for specific line counts.

4. **Rate Limiting**: Frequent API calls may hit Kubernetes API rate limits.

## See Also

- [Quick Start Guide](./QUICKSTART.md)
- [Installation Guide](./INSTALLATION.md)
- [Claude Integration](./claude/claude_integration.md)
