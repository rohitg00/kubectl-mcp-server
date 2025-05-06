"""
Enhanced TaskGroup error handling for MCP server.
"""

import asyncio
import logging
import traceback
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)

async def run_with_taskgroup_protection(coro: Coroutine) -> Any:
    """
    Run a coroutine with TaskGroup error protection.
    
    This function wraps a coroutine in a try-except block that specifically
    handles TaskGroup errors, which are common when using asyncio.TaskGroup
    and one of the tasks fails.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine, or None if an error occurred
    """
    try:
        return await coro
    except asyncio.CancelledError:
        logger.info("Task was cancelled")
        raise
    except Exception as e:
        if "unhandled errors in a TaskGroup" in str(e):
            logger.error(f"TaskGroup error: {e}")
            
            if hasattr(e, "__context__") and e.__context__:
                logger.error(f"Original exception: {e.__context__}")
                
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error in TaskGroup",
                        "data": {
                            "original_error": str(e.__context__),
                            "error_type": "taskgroup_error"
                        }
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": "Internal error in TaskGroup",
                    "data": {
                        "original_error": str(e),
                        "error_type": "taskgroup_error"
                    }
                }
            }
        else:
            logger.error(f"Error in coroutine: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                    "data": {
                        "original_error": str(e),
                        "error_type": "coroutine_error"
                    }
                }
            }

def wrap_async_handler(handler: Callable) -> Callable:
    """
    Wrap an async handler function to catch and handle errors.
    
    This function wraps an async handler function in a try-except block
    that catches and handles errors, including TaskGroup errors.
    
    Args:
        handler: The async handler function to wrap
        
    Returns:
        The wrapped handler function
    """
    async def wrapped_handler(*args, **kwargs):
        try:
            result = await handler(*args, **kwargs)
            return result
        except asyncio.CancelledError:
            logger.info(f"Handler {handler.__name__} was cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in async handler {handler.__name__}: {e}")
            logger.error(traceback.format_exc())
            
            if "unhandled errors in a TaskGroup" in str(e):
                logger.error(f"TaskGroup error in handler {handler.__name__}: {e}")
                
                if hasattr(e, "__context__") and e.__context__:
                    logger.error(f"Original exception: {e.__context__}")
                
                error_result = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "Internal error in TaskGroup",
                        "data": {
                            "original_error": str(e),
                            "error_type": "taskgroup_error"
                        }
                    }
                }
            else:
                error_result = {
                    "command": "Error",
                    "result": f"Error in handler: {str(e)}",
                    "success": False,
                    "intent": "error",
                    "resource_type": "unknown"
                }
            
            try:
                from .enhanced_json_fix import format_json_response
                return format_json_response(error_result)
            except ImportError:
                import json
                return json.dumps(error_result, ensure_ascii=True, separators=(',', ':'))
    
    return wrapped_handler
