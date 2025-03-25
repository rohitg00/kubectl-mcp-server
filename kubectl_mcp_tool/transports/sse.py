"""
Server-Sent Events (SSE) transport implementation for MCP.
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional
from aiohttp import web

logger = logging.getLogger(__name__)

class SSETransport:
    """Transport implementation for SSE communication."""
    
    def __init__(self, port: int = 8080):
        """Initialize the SSE transport."""
        self.port = port
        self.app = web.Application()
        self.app.router.add_post("/mcp", self.handle_mcp)
        self.response_queue = asyncio.Queue()
    
    async def handle_mcp(self, request: web.Request) -> web.Response:
        """Handle MCP requests over HTTP."""
        try:
            message = await request.json()
            logger.debug(f"Received message: {message}")
            
            # Process the message
            response = await self.process_message(message)
            
            return web.json_response(response)
            
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }, status=500)
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process an MCP message."""
        try:
            # Put the message in the queue for processing
            await self.response_queue.put(message)
            
            # Wait for the response
            response = await self.response_queue.get()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def start(self):
        """Start the SSE transport server."""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.port)
        await site.start()
        logger.info(f"SSE transport listening on port {self.port}")
