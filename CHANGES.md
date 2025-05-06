# Changes to kubectl-mcp-tool Configuration

## Version 1.1.1 (Latest)

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