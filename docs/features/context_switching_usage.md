# Context Switching Features

The kubectl-mcp-tool includes advanced context and namespace switching capabilities using the kubectx and kubens tools. These features allow users to easily switch between Kubernetes contexts and namespaces using natural language commands.

## Features

- **Context Listing**: View all available Kubernetes contexts
- **Context Switching**: Switch between different Kubernetes contexts
- **Context Details**: View details of Kubernetes contexts
- **Namespace Listing**: View all available Kubernetes namespaces
- **Namespace Switching**: Switch between different Kubernetes namespaces
- **Namespace Creation**: Create new Kubernetes namespaces
- **Namespace Deletion**: Delete Kubernetes namespaces

## Usage

### Using Natural Language

You can use natural language to switch contexts and namespaces:

```
"switch to context minikube"
"change to namespace kube-system"
"show all contexts"
"list available namespaces"
"create namespace test-ns"
"delete namespace test-ns"
```

### Using the MCP Tool

The context switching features are integrated with the Model Context Protocol (MCP) tool, allowing you to use them through AI assistants like Claude, Cursor, or Windsurf.

Example queries:
- "Switch to the minikube context and show all pods"
- "Change to the kube-system namespace and list all services"
- "Create a new namespace called test-ns and deploy nginx to it"

## Context Manager Module

The context manager module (`kubectl_mcp_tool.context_switcher.context_manager`) provides the following key functions:

### `get_contexts()`

Gets all available Kubernetes contexts.

Returns a list of context names.

### `get_current_context()`

Gets the current Kubernetes context.

Returns the name of the current context.

### `switch_context(context_name)`

Switches to the specified Kubernetes context.

Parameters:
- `context_name`: Name of the context to switch to

Returns a dictionary containing the result of the operation.

### `get_context_details(context_name)`

Gets details of a Kubernetes context.

Parameters:
- `context_name`: Name of the context (optional, defaults to current context)

Returns a dictionary containing context details.

## Namespace Manager Module

The namespace manager module (`kubectl_mcp_tool.context_switcher.namespace_manager`) provides the following key functions:

### `get_namespaces()`

Gets all available Kubernetes namespaces.

Returns a dictionary containing namespaces.

### `get_current_namespace(context)`

Gets the current Kubernetes namespace.

Parameters:
- `context`: Context name (optional, defaults to current context)

Returns a dictionary containing the current namespace.

### `switch_namespace(namespace)`

Switches to the specified Kubernetes namespace.

Parameters:
- `namespace`: Name of the namespace to switch to

Returns a dictionary containing the result of the operation.

### `create_namespace(namespace)`

Creates a new Kubernetes namespace.

Parameters:
- `namespace`: Name of the namespace to create

Returns a dictionary containing the result of the operation.

### `delete_namespace(namespace)`

Deletes a Kubernetes namespace.

Parameters:
- `namespace`: Name of the namespace to delete

Returns a dictionary containing the result of the operation.

## Example

```python
from kubectl_mcp_tool.context_switcher.context_manager import ContextManager
from kubectl_mcp_tool.context_switcher.namespace_manager import NamespaceManager

# Create context and namespace managers
context_manager = ContextManager()
namespace_manager = NamespaceManager()

# Get available contexts
contexts = context_manager.get_contexts()
print(f"Available contexts: {contexts}")

# Get current context
current_context = context_manager.get_current_context()
print(f"Current context: {current_context}")

# Switch context
result = context_manager.switch_context("minikube")
if result["success"]:
    print(f"Successfully switched to context: {result['result']}")
else:
    print(f"Error switching context: {result['error']}")

# Get available namespaces
namespaces_data = namespace_manager.get_namespaces()
if namespaces_data["success"]:
    print(f"Available namespaces: {namespaces_data['result']}")
else:
    print(f"Error getting namespaces: {namespaces_data['error']}")

# Switch namespace
result = namespace_manager.switch_namespace("kube-system")
if result["success"]:
    print(f"Successfully switched to namespace: {result['result']}")
else:
    print(f"Error switching namespace: {result['error']}")
```

## Integration with MCP

The context switching features are fully integrated with the Model Context Protocol (MCP), allowing AI assistants to use these capabilities through the MCP interface. This enables natural language interaction with Kubernetes contexts and namespaces, making it easier to manage multiple clusters and namespaces.
