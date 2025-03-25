#!/usr/bin/env python3
"""
Cursor-compatible MCP server entrypoint for kubectl-mcp-tool.
This script provides backward compatibility after restructuring.
"""

import os
import sys

# Make sure the server directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the actual server implementation
from compatible_servers.fast_cursor_server import main

if __name__ == "__main__":
    # Run the server
    main() 