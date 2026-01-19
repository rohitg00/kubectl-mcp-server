# Changes to kubectl-mcp-tool Configuration

## Version 1.2.0 (Latest)

### Security Fixes
1. **Fixed Command Injection Vulnerability (Issue #36)**
   - Removed `shell=True` from subprocess calls in natural language processing
   - Added input validation and sanitization for kubectl commands
   - Implemented whitelist of allowed kubectl subcommands
   - Added protection against dangerous characters and path traversal

### New Features
1. **HTTP/Streamable HTTP Transport Support (Issue #39)**
   - Added `--transport http` and `--transport streamable-http` options
   - Supports JSON-RPC over HTTP for clients that don't support SSE
   - Falls back to custom HTTP implementation if FastMCP doesn't support it

2. **Multi-Cluster Support (Issue #19)**
   - Added `list_contexts` tool to list all available kubeconfig contexts
   - Added `get_context_details` tool for detailed context information
   - Added `set_namespace_for_context` tool to set default namespace
   - Added `get_cluster_info` tool for cluster information
   - Enhanced `switch_context` for seamless cluster switching

3. **Claude Code Support (Issue #33)**
   - Added comprehensive Claude Code integration documentation
   - Created `docs/claude/claude_code_integration.md` guide
   - Added Claude Code configuration examples to README

### Bug Fixes
1. **Fixed "context deadline exceeded" Error (Issue #24)**
   - Made dependency checks lazy (no longer runs during `__init__`)
   - Added 2-second timeout to kubectl/helm availability checks
   - `tools/list` now works immediately without K8s configuration
   - Fixed `KubernetesOperations` and `KubernetesSecurityOps` to use lazy initialization
   - Server initialization no longer blocks on K8s connectivity

2. **Fixed Docker MCP Toolkit Compatibility (Issue #35)**
   - Fixed "failed to connect: context canceled" error with Docker MCP Toolkit
   - Changed default transport to `stdio` for Docker container
   - Fixed logging to use stderr instead of stdout (prevents MCP protocol pollution)
   - Added ENTRYPOINT/CMD split for flexible transport mode selection
   - Added proper health check for network transports
   - Updated `server.yaml` with full Docker MCP Toolkit configuration

3. **Fixed Docker Container Binding (Issue #26)**
   - Container now properly binds to `0.0.0.0` to accept external connections
   - Added `--host` parameter to control bind address
   - Updated Dockerfile with proper host configuration

4. **Fixed Port Configuration Inconsistency (Issue #20)**
   - Standardized default port to `8000` across all components
   - Dockerfile, run_server.py, and mcp_server.py now use consistent defaults

5. **Fixed Windows asyncio Error (Issue #18)**
   - Added `WindowsSelectorEventLoopPolicy` for Windows compatibility
   - Fixes "句柄无效" (Invalid handle) error with asyncio pipes on Windows
   - Applied fix in both `mcp_server.py` and `__main__.py`

### Documentation
1. **Monitoring Features Documentation (Issue #17)**
   - Created comprehensive `docs/monitoring.md` guide
   - Documented all monitoring tools and their use cases
   - Added common monitoring workflows

### Command-Line Changes
```bash
# New transport modes
python -m kubectl_mcp_tool.mcp_server --transport http --host 0.0.0.0 --port 8000
python -m kubectl_mcp_tool.mcp_server --transport streamable-http --port 8000

# Default port changed from 8080 to 8000
python -m kubectl_mcp_tool.mcp_server --transport sse --port 8000
```

---

## Version 1.1.1

### Key Fixes and Improvements
1. **Fixed JSON RPC Communication Issues**
   - Resolved "Unexpected non-whitespace character after JSON at position 4" error
   - Properly configured logging to use stderr or log files instead of stdout
   - Added comprehensive JSON validation and sanitization
   - Improved handling of special characters and BOM in JSON responses

2. **Enhanced Logging Configuration**
   - Added support for MCP_LOG_FILE environment variable
   - Implemented proper log file rotation
   - Prevented log output from corrupting JSON-RPC communication
   - Improved debug logging for troubleshooting

3. **Added ping utility for server validation**
   - Created simple_ping.py utility for validating server connections
   - Implemented better error detection and debugging
   - Added detailed diagnostic information for connection issues

4. **Improved shutdown handling**
   - Better signal handling for graceful shutdown
   - Fixed memory leaks during server restart
   - Enhanced server resilience during connection failures
   
## Key Improvements

1. **Simplified MCP Server Implementation**
   - Created a minimal wrapper (`kubectl_mcp_tool.minimal_wrapper.py`) for better compatibility
   - Removed complex parameter schemas that were causing compatibility issues
   - Used direct tool registration with simple names

2. **Improved Cursor Integration**
   - Updated Cursor configuration to use the minimal wrapper
   - Added explicit environment variables for PATH and KUBECONFIG
   - Provided better error handling and logging

3. **Enhanced Claude and WindSurf Support**
   - Updated configuration for Claude Desktop
   - Updated configuration for WindSurf
   - Standardized configuration format across all AI assistants

4. **Streamlined Installation Process**
   - Improved installation script to set up all configurations automatically
   - Added automatic testing of kubectl and kubeconfig
   - Created better error handling during installation

5. **Comprehensive Documentation Updates**
   - Updated README.md with working configuration examples
   - Updated integration guides for all supported AI assistants
   - Created a new QUICKSTART.md guide for new users
   - Enhanced troubleshooting section with more specific solutions

## Configuration Changes

### Previous Configuration (Not Working)
```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.cli.cli"]
    }
  }
}
```

### New Configuration (Working)
```json
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.minimal_wrapper"],
      "env": {
        "KUBECONFIG": "/path/to/your/.kube/config",
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"
      }
    }
  }
}
```

## Implementation Details

The key implementation changes include:

1. Using a simpler tool registration approach:
```python
@server.tool("process_natural_language")
async def process_natural_language(query: str):
    # Implementation...
```

2. Avoiding complex parameter schemas that aren't supported in some MCP SDK versions

3. Setting explicit environment variables to ensure kubectl can be found

4. Better error handling throughout the codebase

5. Comprehensive debugging and logging

## Testing Your Installation

After applying these changes, you can verify your installation with:

```bash
# Test command line
kubectl-mcp --help

# Test MCP server directly
python -m kubectl_mcp_tool.minimal_wrapper

# Run automated installation
bash install.sh
```

Then try using your AI assistant to interact with your Kubernetes cluster. 