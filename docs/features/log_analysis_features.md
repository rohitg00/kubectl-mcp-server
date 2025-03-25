# Log Analysis Features

The kubectl-mcp-tool includes advanced log analysis capabilities that help users identify issues in their Kubernetes applications by analyzing pod logs. These features provide plain English explanations of technical errors and code smells detected in application logs.

## Features

- **Code Smell Detection**: Automatically identifies potential code issues like memory leaks, connection timeouts, and resource exhaustion.
- **Error Analysis**: Detects errors in logs and provides plain English explanations.
- **Recommendations**: Generates actionable recommendations based on detected issues.
- **Summary Generation**: Creates concise summaries of log analysis results.

## Usage

### Using Natural Language

You can use natural language to analyze logs:

```
"analyze logs from pod nginx-pod"
"check logs for errors in pod my-app-pod in namespace production"
"find code smells in container api in pod backend-service"
"summarize logs from all pods with label app=frontend"
```

### Using the MCP Tool

The log analysis features are integrated with the Model Context Protocol (MCP) tool, allowing you to use them through AI assistants like Claude, Cursor, or Windsurf.

Example queries:
- "Check the logs of the nginx pod for errors and explain them in plain English"
- "Analyze all pods in the default namespace for memory leaks"
- "Find connection issues in the database pod and suggest solutions"

## Log Analyzer Module

The log analyzer module (`kubectl_mcp_tool.log_analysis.log_analyzer`) provides the following key functions:

### `analyze_logs(pod_name, namespace, container, tail)`

Analyzes logs from a specific pod and container.

Parameters:
- `pod_name`: Name of the pod
- `namespace`: Namespace of the pod (default: "default")
- `container`: Container name (optional)
- `tail`: Number of lines to analyze (default: 100)

Returns a dictionary containing:
- Code smells detected
- Errors found with explanations
- Summary of log analysis
- Recommendations for addressing issues

### `analyze_cluster_logs(namespace, label_selector, tail)`

Analyzes logs from multiple pods in the cluster.

Parameters:
- `namespace`: Namespace to filter pods (optional)
- `label_selector`: Label selector to filter pods (optional)
- `tail`: Number of lines to analyze per pod (default: 100)

Returns aggregated analysis results across all matching pods.

## Error Patterns

The log analyzer detects various error patterns, including:

- Memory-related issues (memory leaks, memory pressure)
- Connection issues (timeouts, refused connections)
- Permission issues (access denied, unauthorized)
- Resource issues (resource exhaustion, disk space, CPU throttling)
- API issues (API server errors, timeouts)
- Network issues (unreachable networks, DNS resolution)
- Configuration issues (config errors, missing configs)
- Authentication issues (auth failures, expired tokens)
- Kubernetes-specific issues (pod evictions, image pull errors, probe failures)
- Application-specific issues (null pointers, index out of bounds, deadlocks)
- Database issues (connection problems, query timeouts)

## Example

```python
from kubectl_mcp_tool.log_analysis.log_analyzer import LogAnalyzer

# Create log analyzer
log_analyzer = LogAnalyzer()

# Analyze logs from a pod
analysis = log_analyzer.analyze_logs("nginx-pod", "default")

# Print analysis results
print(f"Summary: {analysis['result']['summary']}")

# Print code smells
for code_smell in analysis['result']['code_smells']:
    print(f"Code Smell: {code_smell['type']}")
    print(f"Description: {code_smell['description']}")
    print(f"Recommendation: {code_smell['recommendation']}")

# Print errors
for error in analysis['result']['errors']:
    print(f"Error: {error['line']}")
    print(f"Explanation: {error['explanation']}")

# Print recommendations
for recommendation in analysis['result']['recommendations']:
    print(f"Recommendation: {recommendation}")
```

## Integration with MCP

The log analysis features are fully integrated with the Model Context Protocol (MCP), allowing AI assistants to use these capabilities through the MCP interface. This enables natural language interaction with Kubernetes logs, making it easier to identify and understand issues in your applications.
