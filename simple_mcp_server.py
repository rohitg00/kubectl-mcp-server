#!/usr/bin/env python3
"""
Simple MCP server for testing kubectl integration.
"""

import sys
import logging
import asyncio
import os
import json
from typing import Dict, Any
import traceback

import uvicorn
from fastapi import FastAPI

from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_mcp_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simple-mcp')

# Directory for logs
os.makedirs("logs", exist_ok=True)

logger.info("Script started")

try:
    import mcp
    logger.info("Successfully imported MCP SDK")
except ImportError:
    logger.error("MCP SDK import error")
    logger.info("Installing MCP SDK from GitHub")
    try:
        os.system('pip install git+https://github.com/modelcontextprotocol/python-sdk.git')
        import mcp
        logger.info("Successfully installed and imported MCP SDK")
    except Exception as e:
        logger.error(f"Failed to install MCP SDK: {e}")
        print(f"Failed to install MCP SDK: {e}")
        sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error importing MCP SDK: {e}")
    print(f"Unexpected error importing MCP SDK: {e}")
    sys.exit(1)

async def run_kubectl_command(command: str) -> Dict[str, Any]:
    """
    Run a kubectl command and return the output
    """
    process = await asyncio.create_subprocess_shell(
        f"kubectl {command}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    return {
        "stdout": stdout.decode() if stdout else "",
        "stderr": stderr.decode() if stderr else "",
        "returncode": process.returncode
    }

# Create FastAPI app
app = FastAPI()

# Create FastMCP instance
mcp_server = FastMCP(
    name="simple-kubectl-mcp",
    version="1.0.0",
    description="A simple MCP server for kubectl commands"
)

# Add server-info endpoint to main app
@app.get("/server-info")
async def server_info():
    return {
        "name": mcp_server.name,
        "version": mcp_server.version,
        "description": mcp_server.description
    }

# Define the kubectl tool schema
kubectl_tool = Tool(
    name="run_kubectl",
    description="Run a kubectl command",
    parameters={
        "command": {
            "type": "string",
            "description": "The kubectl command to run (without 'kubectl' prefix)"
        }
    },
    returns={
        "type": "object",
        "properties": {
            "stdout": {"type": "string"},
            "stderr": {"type": "string"},
            "returncode": {"type": "integer"}
        }
    }
)

# Register the run_kubectl tool
@mcp_server.tool(kubectl_tool)
async def run_kubectl(command: str) -> Dict[str, Any]:
    """
    Run a kubectl command
    
    Args:
        command: The kubectl command to run (without 'kubectl' prefix)
        
    Returns:
        Dict containing stdout, stderr, and return code
    """
    try:
        result = await run_kubectl_command(command)
        return result
    except Exception as e:
        logger.error(f"Error running kubectl command: {e}")
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": 1
        }

# Mount MCP routes
app.mount("/mcp", mcp_server.router)

if __name__ == "__main__":
    logger.info("Starting simple MCP server")
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8095,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        raise 