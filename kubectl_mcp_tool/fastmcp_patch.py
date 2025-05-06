"""
FastMCP patch module for handling TaskGroup errors in Claude Desktop.

This module adds a shutdown method to the FastMCP class and patches the
run_stdio_async method to properly handle TaskGroup errors, resolving the
'FastMCP' object has no attribute 'shutdown' error.
"""
import asyncio
import sys
import logging
import traceback

logger = logging.getLogger(__name__)

async def shutdown(self):
    """Gracefully shutdown the FastMCP server."""
    logger.info("Shutting down FastMCP server")
    if hasattr(self, 'task_group') and self.task_group is not None:
        self.task_group.cancel()
    
    if hasattr(self, 'reader') and self.reader is not None:
        if not self.reader.at_eof():
            self.reader.feed_eof()
    
    if hasattr(self, 'writer') and self.writer is not None:
        if not self.writer.is_closing():
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception as e:
                logger.debug(f"Error waiting for writer to close: {e}")

try:
    from mcp.server.fastmcp import FastMCP
    
    if not hasattr(FastMCP, 'shutdown'):
        FastMCP.shutdown = shutdown
        logger.info("Added shutdown method to FastMCP class")
    
    original_run_stdio_async = FastMCP.run_stdio_async
    
    async def patched_run_stdio_async(self):
        """Patched version of run_stdio_async that handles TaskGroup errors."""
        try:
            await original_run_stdio_async(self)
        except asyncio.exceptions.CancelledError:
            logger.info("FastMCP server cancelled")
        except Exception as e:
            logger.error(f"Error in FastMCP server: {e}")
            logger.error(traceback.format_exc())
            try:
                await self.shutdown()
            except Exception as shutdown_error:
                logger.error(f"Error during shutdown: {shutdown_error}")
    
    FastMCP.run_stdio_async = patched_run_stdio_async
    logger.info("Patched run_stdio_async method in FastMCP class")
    
except ImportError:
    logger.error("Could not import FastMCP class")
except Exception as e:
    logger.error(f"Error patching FastMCP class: {e}")
    logger.error(traceback.format_exc())
