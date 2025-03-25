#!/usr/bin/env python3
"""
Simple test script for FastMCP integration with kubectl-mcp-tool.
"""

import json
import logging
import os
import sys
import time
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_fastmcp_simple.log"
)
logger = logging.getLogger("test-fastmcp-simple")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def main():
    """Run the FastMCP test."""
    try:
        print("Testing FastMCP integration with kubectl-mcp-tool...")
        
        # Import FastMCP
        try:
            from fastmcp import FastMCP
            print("Successfully imported FastMCP")
        except ImportError as e:
            print(f"Error importing FastMCP: {e}")
            return
        
        # Create FastMCP instance
        try:
            mcp = FastMCP(name="kubectl-mcp-tool")
            print("Successfully created FastMCP instance")
        except Exception as e:
            print(f"Error creating FastMCP instance: {e}")
            return
        
        # Register a simple tool
        try:
            @mcp.tool("get_kubernetes_version")
            def get_kubernetes_version() -> Dict[str, Any]:
                """Get the Kubernetes version."""
                import subprocess
                
                try:
                    result = subprocess.run(
                        ["kubectl", "version", "--output=json"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        return {
                            "success": True,
                            "command": "kubectl version --output=json",
                            "result": result.stdout
                        }
                    else:
                        return {
                            "success": False,
                            "command": "kubectl version --output=json",
                            "error": result.stderr
                        }
                except Exception as e:
                    return {
                        "success": False,
                        "command": "kubectl version --output=json",
                        "error": str(e)
                    }
            
            print("Successfully registered tool: get_kubernetes_version")
        except Exception as e:
            print(f"Error registering tool: {e}")
            return
        
        # Test tool call
        try:
            print("\nTesting tool call...")
            
            result = mcp.tools.get_kubernetes_version()
            
            if result.get("success", False):
                print("Tool call successful")
                print(f"Command: {result.get('command', '')}")
                print(f"Result: {result.get('result', '')}")
            else:
                print("Tool call failed")
                print(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"Error calling tool: {e}")
            return
        
        print("\nTest completed successfully")
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    main()
