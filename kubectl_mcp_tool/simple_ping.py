#!/usr/bin/env python3
"""
Simple ping helper for the Kubernetes MCP server.
"""

import asyncio
import json
import os
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

logger = logging.getLogger("kubectl-mcp-ping")

async def read_message(stream: asyncio.StreamReader) -> Optional[Dict[str, Any]]:
    """Read and parse a JSON-RPC message from the stream."""
    try:
        line = await stream.readline()
        if not line:
            return None
        
        line_str = line.decode("utf-8").strip()
        logger.debug(f"Received raw message: {repr(line_str[:50])}...")
        
        if line_str.startswith('{"jsonrpc"'):
            try:
                return json.loads(line_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return None
        elif '{' in line_str and '}' in line_str:
            # Try to extract JSON
            start = line_str.find('{')
            end = line_str.rfind('}') + 1
            if start < end:
                try:
                    return json.loads(line_str[start:end])
                except json.JSONDecodeError:
                    logger.error(f"Failed to extract JSON from: {line_str[:100]}...")
                    return None
        else:
            logger.error(f"Received non-JSON data: {line_str[:100]}...")
            return None
    except Exception as e:
        logger.error(f"Error reading message: {e}")
        return None

async def write_message(message: Dict[str, Any], stream: asyncio.StreamWriter) -> None:
    """Write a JSON-RPC message to the stream."""
    try:
        json_str = json.dumps(message, ensure_ascii=True, separators=(',', ':'))
        await stream.write((json_str + "\n").encode("utf-8"))
    except Exception as e:
        logger.error(f"Error writing message: {e}")

async def ping_server():
    """Send a ping request to the MCP server and print the response."""
    stdin_reader = asyncio.StreamReader()
    stdin_protocol = asyncio.StreamReaderProtocol(stdin_reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: stdin_protocol, sys.stdin)
    
    stdout_transport, stdout_protocol = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    stdout_writer = asyncio.StreamWriter(stdout_transport, stdout_protocol, None, None)
    
    # Send initialization request
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "clientInfo": {
                "name": "kubectl-ping",
                "version": "1.0.0"
            }
        }
    }
    
    await write_message(init_request, stdout_writer)
    init_response = await read_message(stdin_reader)
    
    if not init_response:
        logger.error("Failed to receive initialization response")
        return 1
    
    # Send ping request
    ping_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "mcp/tools/call",
        "params": {
            "name": "kubernetes_ping",
            "arguments": {"query": "ping test"}
        }
    }
    
    await write_message(ping_request, stdout_writer)
    ping_response = await read_message(stdin_reader)
    
    if not ping_response:
        logger.error("Failed to receive ping response")
        return 1
    
    # Print results
    print("Ping response (to stderr):", file=sys.stderr)
    print(json.dumps(ping_response, indent=2), file=sys.stderr)
    
    # Send shutdown request
    shutdown_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "shutdown",
        "params": {}
    }
    
    await write_message(shutdown_request, stdout_writer)
    shutdown_response = await read_message(stdin_reader)
    
    if not shutdown_response:
        logger.warning("Failed to receive shutdown response")
    
    await write_message({"jsonrpc": "2.0", "method": "exit"}, stdout_writer)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(ping_server())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Ping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error running ping: {e}")
        sys.exit(1) 