#!/usr/bin/env python3
"""
Main entry point for the kubectl-mcp-tool CLI.
Allows running as: python -m kubectl_mcp_tool.cli
"""

from .cli import main

if __name__ == "__main__":
    exit(main())
