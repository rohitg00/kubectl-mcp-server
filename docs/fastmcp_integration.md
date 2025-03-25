# FastMCP Integration Guide
    
This guide explains how the kubectl-mcp-tool uses the official MCP Python SDK (FastMCP) for implementing the Model Context Protocol.
    
## Overview
    
The kubectl-mcp-tool now uses the official MCP Python SDK for protocol handling, which provides several advantages:
    
- Better compliance with the MCP specification
- Reduced maintenance burden
- Access to more advanced features
- Improved integration with AI assistants
- Better developer experience
    
## Implementation Details
    
The `KubectlMCPServer` class wraps the FastMCP implementation and provides the following:
    
- Tool registration using decorators
- Support for both stdio and SSE transports
- Integration with our natural language processing for kubectl
    
## Adding New Tools
    
To add a new tool to the server, simply add a new method to the `register_tools` method in `fastmcp_server.py`:
    
```python
@self.mcp.tool()
def my_new_tool(param1: str, param2: int = 0, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """
    Description of my new tool.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        ctx: Optional MCP context
    
    Returns:
        Dictionary containing the result
    """
    # Implementation
    return result
```
    
## Transport Options
    
The FastMCP implementation supports both stdio and SSE transports:
    
- **stdio**: Used for Cursor integration
- **SSE**: Used for Windsurf integration
    
## Error Handling
    
The FastMCP implementation provides better error handling and reporting:
    
- Structured error responses
- Detailed error messages
- Proper status codes
    
## Resources
    
In addition to tools, FastMCP also supports resources:
    
```python
@self.mcp.resource("kubectl://namespace/{namespace}")
def get_namespace_info(namespace: str, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """Get information about a namespace."""
    result = process_query(f"describe namespace {namespace}")
    return result
```
