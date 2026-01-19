# Contributing Rules

## Git Workflow

1. Create feature branch from main
2. Make changes following code style
3. Test with `python -m py_compile kubectl_mcp_tool/*.py`
4. Commit with conventional commit messages
5. Push and create PR

## Commit Message Format

```
type: brief description

- Detail 1
- Detail 2

Fixes #issue_number
```

Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code change that neither fixes nor adds
- `security:` Security improvements
- `chore:` Maintenance tasks

## PR Checklist

- [ ] Code compiles without errors
- [ ] No stdout pollution in stdio mode
- [ ] Docker build succeeds
- [ ] README updated if new features
- [ ] CHANGES.md updated

## Adding New Tools

1. Add tool method in `mcp_server.py`:

```python
@self.server.tool()
def new_tool(param: str) -> Dict[str, Any]:
    """Description for AI assistants."""
    # Implementation
```

2. Follow existing patterns in the file
3. Return structured Dict responses
4. Handle errors gracefully
5. Add to README tool list

## File Locations

- Main server: `kubectl_mcp_tool/mcp_server.py`
- Entry point: `kubectl_mcp_tool/__main__.py`
- Security: `kubectl_mcp_tool/natural_language.py`
- Docs: `README.md`, `docs/`
- Docker: `Dockerfile`, `server.yaml`

## Testing MCP Server

```bash
# Test stdio (pipe JSON-RPC)
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m kubectl_mcp_tool.mcp_server

# Test SSE
python -m kubectl_mcp_tool.mcp_server --transport sse --port 8000
curl http://localhost:8000/health

# Test Docker
docker build -t test-mcp .
docker run -i -v $HOME/.kube:/root/.kube:ro test-mcp
```

## Issues Reference

When fixing issues, reference the GitHub issue number in commits and PRs:

- Issue #35: Docker MCP Toolkit compatibility
- Issue #36: Security - command injection
- Issue #39: HTTP transport mode
- Issue #26: Docker binding address
- Issue #20: Port configuration
- Issue #33: Claude Code support
- Issue #19: Multi-cluster support
- Issue #17: Monitoring features
