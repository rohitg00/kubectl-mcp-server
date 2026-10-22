#!/usr/bin/env python3
"""Main entry point for the kubectl MCP server."""

import sys

from .mcp_server import main

if __name__ == "__main__":
    sys.exit(main())
