#!/usr/bin/env python3
"""
Test script to verify the kubectl-mcp-tool installation.
"""

import sys
import importlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-installer")

def check_import(module_name, class_name=None):
    """Check if a module can be imported and optionally if a class exists in it."""
    try:
        module = importlib.import_module(module_name)
        logger.info(f"✅ Successfully imported {module_name}")
        
        if class_name:
            try:
                getattr(module, class_name)
                logger.info(f"✅ Successfully imported {class_name} from {module_name}")
                return True
            except AttributeError:
                logger.error(f"❌ Could not find {class_name} in {module_name}")
                return False
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import {module_name}: {e}")
        return False

def main():
    """Run the tests."""
    # Test MCP SDK
    if not check_import("mcp.server", "Server"):
        logger.error("MCP SDK not installed correctly. Try: pip install mcp>=1.5.0")
        return False
    
    # Test kubernetes module
    if not check_import("kubernetes", "client"):
        logger.error("Kubernetes module not installed correctly. Try: pip install kubernetes")
        return False
    
    # Test kubectl_mcp_tool modules
    if not check_import("kubectl_mcp_tool", "MCPServer"):
        logger.error("kubectl_mcp_tool not installed correctly. Try: pip install -e .")
        return False
    
    if not check_import("kubectl_mcp_tool.simple_server", "KubectlServer"):
        logger.error("kubectl_mcp_tool.simple_server module not installed correctly.")
        return False
    
    logger.info("All imports successful! Your installation looks good.")
    logger.info("You can now run: kubectl-mcp serve")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 