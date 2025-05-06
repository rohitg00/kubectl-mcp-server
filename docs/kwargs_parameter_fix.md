# Kwargs Parameter Fix

## Issue Description

Claude Desktop was experiencing errors with the Kubernetes MCP server:

```
Error in handler: main.<locals>.process_natural_language() got an unexpected keyword argument 'kwargs'
Error in handler: main.<locals>.advanced_kubernetes_query() got an unexpected keyword argument 'kwargs'
Error in handler: main.<locals>.kubernetes_ping() got an unexpected keyword argument 'kwargs'
```

## Root Cause

The function signatures in `minimal_wrapper.py` and `cursor_compatible_mcp_server.py` did not properly handle variable keyword arguments. While previous fixes addressed the `args` parameter, Claude Desktop was also sending additional parameters as keyword arguments.

The issue was that the functions were defined with:
```python
async def process_natural_language(query: str, args: List[str] = None, kwargs: Dict[str, Any] = None):
```

This treats `kwargs` as a regular parameter that expects a dictionary, not as a variable keyword arguments collector. When Claude Desktop sent actual keyword arguments, Python tried to assign them to a parameter named `kwargs` rather than collecting them as variable keyword arguments.

## Fix

We've updated the function signatures to use Python's `**kwargs` syntax for variable keyword arguments:

```python
# Before
async def process_natural_language(query: str, args: List[str] = None, kwargs: Dict[str, Any] = None):
    # function body

# After
async def process_natural_language(query: str, args: List[str] = None, **kwargs):
    # function body
```

Similar changes were made to:
- `advanced_kubernetes_query()` in minimal_wrapper.py
- `kubernetes_ping()` in minimal_wrapper.py
- `process_query()` in cursor_compatible_mcp_server.py

We also updated all tool calls in cursor_compatible_mcp_server.py to extract and pass kwargs consistently:

```python
# Before
result = await self.tools.process_query(query, args)

# After
kwargs = {k: v for k, v in tool_input.items() if k not in ["query", "args"]}
result = await self.tools.process_query(query, args, **kwargs)
```

## Testing

To verify this fix:

1. Created a test script `test_kwargs_parameter_fix.py` that simulates Claude Desktop's interaction with the MCP server
2. Tested with additional keyword arguments to ensure all functions handle them correctly
3. Verified that the functions no longer raise the "unexpected keyword argument" error
4. Checked that all tool calls in cursor_compatible_mcp_server.py consistently pass kwargs

The test script generates test requests in JSON-RPC format and writes them to a file named "test_kwargs_requests.json" that can be used to test the MCP server directly.

## Related PRs

- PR #19: Args parameter fix
- PR #22: Function signature standardization
- PR #23: Schema definition fix
- PR #24: Function call fix for args parameter

This fix completes the series of changes needed to ensure full compatibility with Claude Desktop and Cursor.

# Fixing "Unexpected non-whitespace character after JSON" Errors (v1.1.1+)

## Problem

When using kubectl-mcp-tool with AI assistants like Claude Desktop or Cursor, you might encounter an error where the MCP server becomes unresponsive or shows as disconnected after a single query, with an error message like:

```
Unexpected non-whitespace character after JSON at position 4 (line 1 column 5)
```

This commonly happens because logs or debug information are being written to stdout, which corrupts the JSON-RPC communication channel.

## Solution

Version 1.1.1 fixes this issue by:

1. Properly directing all logs to either stderr or a log file
2. Adding comprehensive JSON validation and sanitization
3. Handling special characters and BOM in JSON responses
4. Implementing better error recovery

## How to Fix

1. **Update to the latest version**:
   ```bash
   pip install kubectl-mcp-tool==1.1.1
   ```

2. **Use the minimal wrapper in your configuration**:
   ```json
   {
     "mcpServers": {
       "kubernetes": {
         "command": "python",
         "args": ["-m", "kubectl_mcp_tool.minimal_wrapper"],
         "env": {
           "KUBECONFIG": "/path/to/your/.kube/config",
           "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
           "MCP_LOG_FILE": "/path/to/logs/debug.log"
         }
       }
     }
   }
   ```

3. **Specify a log file**: Set the `MCP_LOG_FILE` environment variable to direct logs to a file instead of stderr.

4. **Test connection**: Use the included ping utility to verify your server is working correctly:
   ```bash
   python -m kubectl_mcp_tool.simple_ping
   ```

## Detailed Technical Explanation

The error occurs because:

1. **Mixed Channel Communication**: JSON-RPC protocol requires clean stdout for communication, but logs were contaminating this channel
2. **BOM Characters**: Some Unicode Byte Order Mark (BOM) or invisible characters were being included in the JSON
3. **Position 4 Issue**: The character at position 4 (1-indexed) in the JSON response was often invalid

The fix involves:
1. Proper logger configuration to use stderr or log files
2. Sanitizing JSON strings before transmission
3. Validating JSON responses before sending
4. Adding special handling for known error patterns
