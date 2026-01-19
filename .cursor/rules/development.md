# kubectl-mcp-server Development Rules

## Project Overview

This is a Model Context Protocol (MCP) server that enables AI assistants to interact with Kubernetes clusters. It follows the [MCP specification](https://modelcontextprotocol.io/docs/getting-started/intro).

## Commands

```bash
# Install dependencies
pip install -e .

# Run the MCP server (stdio - default for MCP clients)
python -m kubectl_mcp_tool.mcp_server

# Run with SSE transport (for web clients)
python -m kubectl_mcp_tool.mcp_server --transport sse --port 8000

# Run with HTTP transport
python -m kubectl_mcp_tool.mcp_server --transport http --port 8000

# Verify Python files compile
python -m py_compile kubectl_mcp_tool/*.py

# Build Docker image
docker build -t kubectl-mcp-server .

# Test Docker image with stdio
docker run -i -v $HOME/.kube:/root/.kube:ro kubectl-mcp-server
```

## Code Style

- Use Python 3.9+ features
- Type hints are required for all function parameters and return values
- Use `Optional[T]` for parameters that can be None
- Use `Dict[str, Any]` for Kubernetes API responses
- Docstrings required for all public functions and classes
- See `kubectl_mcp_tool/mcp_server.py` for canonical MCP tool implementation

## MCP Protocol Rules

**CRITICAL: stdout is reserved for MCP JSON-RPC protocol**

- All logging MUST go to stderr or a log file, NEVER stdout
- Use `logging.StreamHandler(sys.stderr)` for console logging
- Check `MCP_LOG_FILE` environment variable for file logging
- Check `MCP_DEBUG` environment variable for debug level

Example logging setup:
```python
import sys
import logging

handlers = [logging.StreamHandler(sys.stderr)]
logging.basicConfig(level=logging.INFO, handlers=handlers)
```

## Tool Registration Pattern

Register MCP tools using the FastMCP decorator pattern:

```python
@self.server.tool()
def tool_name(param1: str, param2: Optional[str] = None) -> Dict[str, Any]:
    """Tool description for AI assistants."""
    try:
        # Implementation
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error in tool_name: {e}")
        return {"success": False, "error": str(e)}
```

## Security Requirements

- NEVER use `shell=True` with subprocess when handling user input
- Use `shlex.split()` to parse command strings safely
- Validate and sanitize all kubectl command arguments
- Whitelist allowed kubectl subcommands
- See `kubectl_mcp_tool/natural_language.py` for security patterns

## File Structure

```
kubectl_mcp_tool/
├── __init__.py           # Package exports
├── __main__.py           # Entry point
├── mcp_server.py         # Main MCP server (FastMCP-based)
├── natural_language.py   # NL processing with security
├── diagnostics.py        # Diagnostics tools
├── minimal_wrapper.py    # Lightweight fallback server
├── cli/                  # CLI package
├── core/                 # Core Kubernetes operations
└── security/             # RBAC and security operations
```

## Docker Compatibility

The Dockerfile must support both:
1. **Docker MCP Toolkit** (stdio transport, default)
2. **Standalone** (SSE/HTTP transport)

Use ENTRYPOINT + CMD pattern:
```dockerfile
ENTRYPOINT ["python", "-m", "kubectl_mcp_tool.mcp_server"]
CMD ["--transport", "stdio"]
```

## Testing Checklist

Before committing:
1. `python -m py_compile kubectl_mcp_tool/*.py` - All files compile
2. Test stdio transport works with no stdout pollution
3. Test with real kubectl if cluster available
4. Verify Docker build succeeds
