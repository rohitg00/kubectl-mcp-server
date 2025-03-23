#!/bin/bash
# install.sh

# Create necessary directories
mkdir -p kubectl_mcp_tool

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .

echo "kubectl-mcp-tool installed successfully!"
