# MCP Protocol Rules

## Transport Modes

| Transport | Use Case | Default Port |
|-----------|----------|--------------|
| stdio | Docker MCP Toolkit, Claude Desktop, Cursor | N/A |
| sse | Web clients, long-running connections | 8000 |
| http | REST-like stateless requests | 8000 |
| streamable-http | HTTP with streaming responses | 8000 |

## stdio Transport (Default)

**CRITICAL:** When using stdio transport, the stdout stream is the MCP JSON-RPC channel.

- ALL logging must go to stderr
- NO print() statements to stdout
- NO debug output to stdout
- Use `sys.stderr.write()` or `logging.StreamHandler(sys.stderr)`

```python
# Before serving stdio, clean stdout handlers
for handler in logging.root.handlers[:]:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        logging.root.removeHandler(handler)
```

## Server Initialization

Use FastMCP for server creation:

```python
from mcp.server.fastmcp import FastMCP

server = FastMCP(
    name="kubectl-mcp-server",
    version="1.2.0"
)
```

## Tool Response Format

All tools must return serializable data:

```python
@server.tool()
def my_tool(param: str) -> Dict[str, Any]:
    """Description shown to AI assistants."""
    return {
        "success": True,
        "data": {...},
        "message": "Human-readable summary"
    }
```

## Error Responses

```python
return {
    "success": False,
    "error": "Brief error type",
    "details": "Full error message for debugging",
    "suggestion": "What the user can try"
}
```

## Resource Registration (Optional)

```python
@server.resource("resource://kubectl/namespaces")
def list_namespaces() -> str:
    """Expose Kubernetes namespaces as MCP resource."""
    result = run_kubectl(["get", "namespaces", "-o", "json"])
    return result
```

## Prompt Templates (Optional)

```python
@server.prompt()
def debug_pod(pod_name: str, namespace: str = "default") -> str:
    """Generate debugging workflow for a pod."""
    return f"""
    Debug workflow for pod {pod_name}:
    1. Check pod status: get_pods({namespace})
    2. Get pod events: get_pod_events({pod_name}, {namespace})
    3. Check logs: get_logs({pod_name}, {namespace})
    """
```

## Client Compatibility

The server must work with:
- **Claude Desktop** (stdio)
- **Cursor** (stdio)
- **Docker MCP Toolkit** (stdio)
- **Web clients** (SSE/HTTP)
- **Claude Code** (stdio)

## Health Checks

For network transports, implement health endpoint:

```python
@app.get("/health")
async def health():
    return {"status": "healthy", "transport": transport_type}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| MCP_DEBUG | Enable debug logging | false |
| MCP_LOG_FILE | Log to file instead of stderr | None |
| KUBECONFIG | Kubernetes config path | ~/.kube/config |
| MCP_PORT | Server port for network transports | 8000 |
| MCP_HOST | Bind address for network transports | 0.0.0.0 |
