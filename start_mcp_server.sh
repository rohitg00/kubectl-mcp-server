#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables
export PYTHONUNBUFFERED=1
export MCP_DEBUG=true
export KUBECTL_MCP_LOG_LEVEL=DEBUG

# Start the server
echo "Starting kubectl MCP server..."
python -m kubectl_mcp_tool.cli serve --transport stdio 