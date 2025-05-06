"""
Claude-specific message framing module for MCP server.

This module provides functions to properly frame JSON-RPC messages for Claude Desktop,
addressing the "Unexpected non-whitespace character after JSON at position 4" error
by ensuring proper message boundaries between JSON responses.
"""

import json
import logging
import re
import os
from typing import Dict, Any, Optional, Union, List, Tuple

logging.basicConfig(
    level=logging.DEBUG if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true") else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("claude-message-framing")

def ensure_message_boundary(message: str) -> str:
    """
    Ensure the message has proper boundaries for Claude Desktop.
    
    Args:
        message: The JSON-RPC message to frame
        
    Returns:
        A properly framed message with boundaries
    """
    if not message:
        return message
    
    if not message.endswith('\n'):
        message = message + '\n'
    
    return message

def frame_jsonrpc_message(data: Dict[str, Any], message_id: Optional[str] = None) -> str:
    """
    Frame a JSON-RPC message for Claude Desktop.
    
    Args:
        data: The data to include in the message
        message_id: Optional message ID to include
        
    Returns:
        A properly framed JSON-RPC message
    """
    if not isinstance(data, dict):
        logger.warning(f"Expected dict for JSON-RPC message, got {type(data)}")
        data = {"result": str(data)}
    
    jsonrpc_message = {
        "jsonrpc": "2.0",
        "id": message_id if message_id is not None else data.get("id", "1"),
        "result": data
    }
    
    try:
        json_str = json.dumps(jsonrpc_message, ensure_ascii=True, separators=(',', ':'))
        
        framed_message = ensure_message_boundary(json_str)
        
        return framed_message
    except Exception as e:
        logger.error(f"Error framing JSON-RPC message: {e}")
        error_message = {
            "jsonrpc": "2.0",
            "id": message_id if message_id is not None else "error",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }
        return json.dumps(error_message, ensure_ascii=True, separators=(',', ':')) + '\n'

def extract_message_id(request: str) -> Optional[str]:
    """
    Extract the message ID from a JSON-RPC request.
    
    Args:
        request: The JSON-RPC request string
        
    Returns:
        The message ID if found, None otherwise
    """
    try:
        data = json.loads(request)
        id_value = data.get("id")
        if id_value is not None:
            return str(id_value)
        return None
    except json.JSONDecodeError:
        id_match = re.search(r'"id"\s*:\s*"?([^",\s]+)"?', request)
        if id_match:
            return id_match.group(1)
        
        id_match = re.search(r'"id"\s*:\s*(\d+)', request)
        if id_match:
            return id_match.group(1)
        
        return None
    except Exception as e:
        logger.error(f"Error extracting message ID: {e}")
        return None

def create_response_buffer() -> List[str]:
    """
    Create a buffer for storing responses before sending them.
    
    Returns:
        An empty list to use as a response buffer
    """
    return []

def add_to_response_buffer(buffer: List[str], response: str) -> List[str]:
    """
    Add a response to the buffer.
    
    Args:
        buffer: The response buffer
        response: The response to add
        
    Returns:
        The updated buffer
    """
    buffer.append(response)
    return buffer

def flush_response_buffer(buffer: List[str]) -> str:
    """
    Flush the response buffer and return a properly framed message.
    
    Args:
        buffer: The response buffer
        
    Returns:
        A properly framed message containing all responses in the buffer
    """
    if not buffer:
        return ""
    
    joined_response = "\n".join(buffer)
    
    buffer.clear()
    
    return joined_response

def sanitize_for_claude(json_str: str) -> str:
    """
    Sanitize a JSON string for Claude Desktop.
    
    Args:
        json_str: The JSON string to sanitize
        
    Returns:
        A sanitized JSON string
    """
    if not json_str:
        return json_str
    
    problematic_chars = [
        '\ufeff',  # BOM
        '\u200b',  # Zero-width space
        '\u200c',  # Zero-width non-joiner
        '\u200d',  # Zero-width joiner
        '\u2060',  # Word joiner
        '\ufffe',  # Reversed BOM
        '\u00a0',  # Non-breaking space
        '\u2028',  # Line separator
        '\u2029',  # Paragraph separator
    ]
    
    for char in problematic_chars:
        if char in json_str:
            json_str = json_str.replace(char, '')
    
    if not json_str.endswith('\n'):
        json_str = json_str + '\n'
    
    return json_str

def extract_clean_json(text: str) -> str:
    """
    Extract clean JSON from text that might have content before or after the JSON.
    
    Args:
        text: The text containing JSON
        
    Returns:
        Clean JSON string
    """
    if not text:
        return text
    
    logger.debug(f"Extracting clean JSON from text: '{text[:50]}'...")
    
    start_idx = text.find('{')
    if start_idx == -1:
        logger.warning("Could not find valid JSON boundaries in the text")
        return text
    
    brace_count = 0
    end_idx = -1
    
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if end_idx == -1:
        logger.warning("Could not find valid JSON boundaries in the text")
        return text
    
    if start_idx > 0:
        logger.warning(f"Found content before JSON: '{text[:start_idx]}'")
    
    if end_idx < len(text):
        logger.warning(f"Found content after JSON: '{text[end_idx:]}'")
    
    json_str = text[start_idx:end_idx]
    
    clean_json = sanitize_for_claude(json_str)
    
    logger.debug(f"Successfully extracted and cleaned JSON: '{clean_json[:50]}'...")
    
    return clean_json

class ClaudeMessageFramer:
    """
    Class to handle message framing for Claude Desktop.
    """
    
    def __init__(self):
        """Initialize the message framer."""
        self.response_buffer = create_response_buffer()
        self.message_counter = 0
    
    def frame_response(self, data: Dict[str, Any], request_id: Optional[str] = None) -> str:
        """
        Frame a response for Claude Desktop.
        
        Args:
            data: The data to include in the response
            request_id: Optional request ID to include
            
        Returns:
            A properly framed response
        """
        self.message_counter += 1
        
        response = frame_jsonrpc_message(data, request_id)
        add_to_response_buffer(self.response_buffer, response)
        
        return flush_response_buffer(self.response_buffer)
    
    def extract_request_id(self, request: str) -> Optional[str]:
        """
        Extract the request ID from a request.
        
        Args:
            request: The request string
            
        Returns:
            The request ID if found, None otherwise
        """
        return extract_message_id(request)
