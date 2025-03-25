# Migration Guide: Custom MCP Implementation to Official SDK
    
This guide explains the migration from our custom MCP implementation to the official MCP Python SDK.
    
## Why Migrate?
    
The official MCP Python SDK provides several advantages:
    
- Better compliance with the MCP specification
- Reduced maintenance burden
- Access to more advanced features
- Improved integration with AI assistants
- Better developer experience
    
## Key Changes
    
1. **Server Implementation**
   - Old: Custom `MCPServer` class with manual JSON-RPC handling
   - New: `FastMCP` from the official SDK
    
2. **Tool Registration**
   - Old: Manual registration with `register_tool` method
   - New: Decorator-based registration with `@mcp.tool()`
    
3. **Transport Handling**
   - Old: Custom implementations for stdio and SSE
   - New: Built-in support from the SDK
    
4. **Error Handling**
   - Old: Custom error responses
   - New: Standardized error handling from the SDK
    
## Migration Steps
    
1. Install the official MCP Python SDK:
   ```bash
   pip install mcp-python
   ```
    
2. Replace custom server implementation with FastMCP:
   ```python
   from mcp.server.fastmcp import FastMCP
       
   mcp = FastMCP("kubectl-mcp-tool")
   ```
    
3. Convert tool registrations to decorators:
   ```python
   # Old
   server.register_tool(
       "process_natural_language",
       "Process natural language query for kubectl",
       {"query": {"type": "string", "required": True}},
       process_natural_language
   )
       
   # New
   @mcp.tool()
   def process_natural_language(query: str) -> Dict[str, Any]:
       """Process natural language query for kubectl"""
       return process_query(query)
   ```
    
4. Use built-in transport methods:
   ```python
   # Old
   server.serve_stdio()
       
   # New
   mcp.serve_stdio()
   ```
    
## Testing the Migration
    
1. Test with Cursor:
   ```bash
   python3 fast_cursor_server.py
   ```
    
2. Test with Windsurf:
   ```bash
   python3 fast_windsurf_server.py
   ```

## Troubleshooting

### Common Issues

1. **Type Annotations**
   - The official SDK relies on type annotations for parameter validation
   - Make sure all tool functions have proper type annotations
   - Use `Optional[Type]` for optional parameters

2. **Context Parameter**
   - The official SDK passes a `Context` object to tool functions
   - Add an optional context parameter to all tool functions:
     ```python
     def my_tool(param: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
         # Implementation
     ```

3. **Import Errors**
   - If you encounter import errors, make sure you've installed the SDK:
     ```bash
     pip install mcp-python>=0.1.0
     ```

4. **Transport Errors**
   - If you encounter transport errors, check that you're using the correct transport method
   - For Cursor: `mcp.serve_stdio()`
   - For Windsurf: `await mcp.serve_sse(port=8080)`

## Resources

- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://spec.modelcontextprotocol.io/specification/2024-11-05/)
- [FastMCP Examples](https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/fastmcp)
