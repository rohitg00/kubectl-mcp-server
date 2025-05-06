
import json
import logging
import re
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

def is_json_start(text: str) -> bool:
    """Check if the text starts with a JSON object or array."""
    if not text:
        return False
    
    text = text.strip()
    
    return text.startswith('{') or text.startswith('[')

def extract_json_from_log(text: str) -> Optional[str]:
    """Extract JSON from log output if present."""
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    
    if text.startswith('202') and ' - INFO - Starting MCP server' in text:
        logger.debug("Detected MCP server startup message, creating standard response")
        standard_response = {
            "jsonrpc": "2.0",
            "id": 0,
            "result": {
                "serverInfo": {
                    "name": "kubectl-mcp-tool",
                    "version": "1.1.0"
                },
                "capabilities": {
                    "tools": True
                }
            }
        }
        return json.dumps(standard_response)
    
    timestamp_pattern = r'^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[,\.]\d{3}\s+-\s+\w+\s+-\s+(.*)'
    timestamp_match = re.match(timestamp_pattern, text)
    if timestamp_match:
        content_after_timestamp = timestamp_match.group(1)
        if content_after_timestamp.strip().startswith('{'):
            try:
                json.loads(content_after_timestamp)
                logger.debug("Found valid JSON after timestamp")
                return content_after_timestamp
            except json.JSONDecodeError:
                sanitized = sanitize_json_content(content_after_timestamp)
                try:
                    json.loads(sanitized)
                    logger.debug("Found and sanitized JSON after timestamp")
                    return sanitized
                except json.JSONDecodeError:
                    pass
    
    jsonrpc_pattern = r'.*?(\{"jsonrpc":"2\.0".*?\})'
    match = re.search(jsonrpc_pattern, text, re.DOTALL)
    if match:
        potential_json = match.group(1)
        try:
            json.loads(potential_json)
            logger.debug("Found valid JSON-RPC object")
            return potential_json
        except json.JSONDecodeError:
            sanitized = sanitize_json_content(potential_json)
            try:
                json.loads(sanitized)
                logger.debug("Found and sanitized JSON-RPC object")
                return sanitized
            except json.JSONDecodeError:
                pass
    
    json_pattern = r'\{.*?\}'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        potential_json = match.group(0)
        try:
            json.loads(potential_json)
            logger.debug("Found valid JSON object")
            return potential_json
        except json.JSONDecodeError:
            sanitized = sanitize_json_content(potential_json)
            try:
                json.loads(sanitized)
                logger.debug("Found and sanitized JSON object")
                return sanitized
            except json.JSONDecodeError:
                pass
    
    json_array_pattern = r'\[.*?\]'
    match = re.search(json_array_pattern, text, re.DOTALL)
    if match:
        potential_json = match.group(0)
        try:
            json.loads(potential_json)
            logger.debug("Found valid JSON array")
            return potential_json
        except json.JSONDecodeError:
            sanitized = sanitize_json_content(potential_json)
            try:
                json.loads(sanitized)
                logger.debug("Found and sanitized JSON array")
                return sanitized
            except json.JSONDecodeError:
                pass
    
    if '{' in text and '}' in text:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start < end:
            potential_json = text[start:end]
            try:
                json.loads(potential_json)
                logger.debug("Found JSON-like structure using braces")
                return potential_json
            except json.JSONDecodeError:
                sanitized = sanitize_json_content(potential_json)
                try:
                    json.loads(sanitized)
                    logger.debug("Found and sanitized JSON-like structure using braces")
                    return sanitized
                except json.JSONDecodeError:
                    for i in range(start + 1, min(start + 20, len(text))):
                        if i < len(text) and text[i] == '{':
                            subset = text[i:end]
                            try:
                                sanitized_subset = sanitize_json_content(subset)
                                json.loads(sanitized_subset)
                                logger.debug(f"Found valid JSON starting at position {i}")
                                return sanitized_subset
                            except json.JSONDecodeError:
                                pass
    
    if len(text) > 5 and text[4] == '-' and text.startswith('202'):
        logger.debug("Detected timestamp at start, attempting to extract JSON after timestamp")
        
        if ' - INFO - Starting MCP server' in text:
            logger.debug("Detected MCP server startup message, creating standard response")
            standard_response = {
                "jsonrpc": "2.0",
                "id": 0,
                "result": {
                    "serverInfo": {
                        "name": "kubectl-mcp-tool",
                        "version": "1.1.0"
                    },
                    "capabilities": {
                        "tools": True
                    }
                }
            }
            return json.dumps(standard_response)
        
        for i in range(30, len(text)):
            if i < len(text) and text[i] == '{':
                end_pos = text.rfind('}') + 1
                if i < end_pos:
                    json_content = text[i:end_pos]
                    sanitized_json = sanitize_json_content(json_content)
                    try:
                        json.loads(sanitized_json)
                        logger.debug(f"Extracted JSON after timestamp starting at position {i}")
                        return sanitized_json
                    except json.JSONDecodeError:
                        pass
    
    return None

def sanitize_json_content(text: str) -> str:
    """Remove problematic characters from JSON content."""
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
        text = text.replace(char, '')
    
    return text

def sanitize_json(text: str) -> Optional[str]:
    """
    Sanitize JSON string by removing problematic characters and
    extracting JSON from log output if necessary.
    
    Returns None if the input is not valid JSON and cannot be fixed.
    """
    if not text:
        return None
    
    try:
        json.loads(text)
        return text  # Already valid JSON
    except json.JSONDecodeError:
        pass
    
    sanitized = sanitize_json_content(text)
    try:
        json.loads(sanitized)
        return sanitized
    except json.JSONDecodeError:
        pass
    
    if len(text) > 4:
        if text[4] in ['-', '\ufeff', '\u200b', '\u200c', '\u200d', '\u2060']:
            logger.debug(f"Detected problematic character at position 4: {repr(text[4])}")
            
            if text.startswith('202') and text[4] == '-':
                logger.debug("Detected timestamp at start, attempting to extract JSON")
                
                for i in range(20, len(text)):
                    if i < len(text) and text[i] == '{':
                        end_pos = text.rfind('}') + 1
                        if i < end_pos:
                            json_content = text[i:end_pos]
                            sanitized_json = sanitize_json_content(json_content)
                            try:
                                json.loads(sanitized_json)
                                logger.debug(f"Extracted JSON after timestamp starting at position {i}")
                                return sanitized_json
                            except json.JSONDecodeError:
                                pass
            
            else:
                fixed_text = text[:4] + text[5:]
                try:
                    json.loads(fixed_text)
                    logger.debug(f"Successfully fixed JSON by removing character at position 4")
                    return fixed_text
                except json.JSONDecodeError:
                    sanitized_fixed = sanitize_json_content(fixed_text)
                    try:
                        json.loads(sanitized_fixed)
                        logger.debug(f"Successfully fixed and sanitized JSON by removing character at position 4")
                        return sanitized_fixed
                    except json.JSONDecodeError:
                        pass
    
    timestamp_pattern = r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[,\.]\d{3})'
    if re.match(timestamp_pattern, text):
        logger.debug("Detected log line with ISO timestamp, attempting to extract JSON")
        
        jsonrpc_pattern = r'.*?(\{"jsonrpc":"2\.0".*?\})'
        match = re.search(jsonrpc_pattern, text, re.DOTALL)
        if match:
            potential_json = match.group(1)
            try:
                json.loads(potential_json)
                logger.debug("Successfully extracted JSON-RPC from log line")
                return potential_json
            except json.JSONDecodeError:
                sanitized_potential = sanitize_json_content(potential_json)
                try:
                    json.loads(sanitized_potential)
                    logger.debug("Successfully sanitized extracted JSON-RPC")
                    return sanitized_potential
                except json.JSONDecodeError:
                    pass
        
        if '{' in text and '}' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start < end:
                potential_json = text[start:end]
                try:
                    sanitized_potential = sanitize_json_content(potential_json)
                    json.loads(sanitized_potential)
                    logger.debug("Found JSON object after timestamp")
                    return sanitized_potential
                except json.JSONDecodeError:
                    for i in range(start + 1, min(start + 50, len(text))):
                        if i < len(text) and text[i] == '{':
                            subset = text[i:end]
                            try:
                                sanitized_subset = sanitize_json_content(subset)
                                json.loads(sanitized_subset)
                                logger.debug(f"Found valid JSON starting at position {i}")
                                return sanitized_subset
                            except json.JSONDecodeError:
                                pass
    
    extracted = extract_json_from_log(text)
    if extracted:
        try:
            sanitized_extracted = sanitize_json_content(extracted)
            json.loads(sanitized_extracted)
            logger.debug("Successfully extracted and sanitized JSON from mixed content")
            return sanitized_extracted
        except json.JSONDecodeError:
            pass
    
    if '{' in text and '}' in text:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start < end:
            potential_json = text[start:end]
            try:
                sanitized_potential = sanitize_json_content(potential_json)
                json.loads(sanitized_potential)
                logger.debug("Found JSON-like structure using braces")
                return sanitized_potential
            except json.JSONDecodeError:
                for i in range(start + 1, min(start + 50, len(text))):
                    if i < len(text) and text[i] == '{':
                        subset = text[i:end]
                        try:
                            sanitized_subset = sanitize_json_content(subset)
                            json.loads(sanitized_subset)
                            logger.debug(f"Found valid JSON starting at position {i}")
                            return sanitized_subset
                        except json.JSONDecodeError:
                            pass
    
    error_pattern = r'Error.*?(\{.*\})'
    match = re.search(error_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        potential_json = match.group(1)
        try:
            sanitized_potential = sanitize_json_content(potential_json)
            json.loads(sanitized_potential)
            logger.debug("Found JSON in error message")
            return sanitized_potential
        except json.JSONDecodeError:
            pass
    
    return None

def extract_error_response(text: str) -> Optional[Dict[str, Any]]:
    """Extract error response from server error message."""
    connection_error_patterns = [
        "Connection lost", 
        "pipe closed by peer", 
        "ConnectionResetError", 
        "BrokenPipeError",
        "Connection reset by peer",
        "Connection refused",
        "Connection timed out",
        "Connection aborted",
        "Cannot write to closed transport",
        "Error sending request"
    ]
    
    for pattern in connection_error_patterns:
        if pattern in text:
            logger.debug(f"Detected connection error: {pattern}")
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32000,
                    "message": "Connection lost",
                    "data": {
                        "original_error": text,
                        "error_type": "connection_error"
                    }
                }
            }
    
    if "Error running server:" in text:
        logger.debug("Detected server error message")
        
        error_pattern = r'Error running server:.*?(\{"jsonrpc":"2\.0".*?"error".*?\})'
        match = re.search(error_pattern, text, re.DOTALL)
        if match:
            potential_json = match.group(1)
            try:
                sanitized = sanitize_json_content(potential_json)
                parsed = json.loads(sanitized)
                logger.debug("Successfully extracted JSON-RPC error object")
                
                if "error" in parsed:
                    return {
                        "jsonrpc": "2.0",
                        "id": parsed.get("id", None),
                        "error": {
                            "code": parsed["error"].get("code", -32603),
                            "message": parsed["error"].get("message", "Internal error"),
                            "data": {
                                "original_error": text.split("Error running server:", 1)[1].strip(),
                                "error_type": "server_error"
                            }
                        }
                    }
                return parsed
            except json.JSONDecodeError:
                pass
        
        if "unhandled errors in a TaskGroup" in text:
            logger.debug("Detected TaskGroup error")
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": "Internal error in TaskGroup",
                    "data": {
                        "original_error": text.split("Error running server:", 1)[1].strip(),
                        "error_type": "taskgroup_error"
                    }
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": {
                    "original_error": text.split("Error running server:", 1)[1].strip(),
                    "error_type": "server_error"
                }
            }
        }
    
    if text.startswith('202') and ' - INFO - Starting MCP server' in text:
        logger.debug("Detected MCP server startup message")
        return {
            "jsonrpc": "2.0",
            "id": 0,
            "result": {
                "serverInfo": {
                    "name": "kubectl-mcp-tool",
                    "version": "1.1.0"
                },
                "capabilities": {
                    "tools": True
                }
            }
        }
    
    if not text or text.strip() == "":
        logger.debug("Detected empty response")
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Empty response",
                "data": {
                    "original_error": "Server returned empty response",
                    "error_type": "empty_response"
                }
            }
        }
    
    return None

def parse_json_safely(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON safely, handling problematic characters and log output.
    
    Returns None if the input is not valid JSON and cannot be fixed.
    """
    error_response = extract_error_response(text)
    if error_response:
        return error_response
    
    sanitized = sanitize_json(text)
    if sanitized:
        try:
            return json.loads(sanitized)
        except json.JSONDecodeError:
            pass
    
    if text and len(text) > 0:
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error",
                "data": {
                    "original_text": text[:100] + ("..." if len(text) > 100 else "")
                }
            }
        }
    
    return None

def is_valid_json(text: str) -> bool:
    """Check if the text is valid JSON."""
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False

def format_json_response(data: Union[Dict[str, Any], list]) -> str:
    """Format JSON response with consistent serialization."""
    return json.dumps(data, separators=(',', ':'))

def sanitize_json_response(data: Union[Dict[str, Any], list]) -> str:
    """
    Sanitize and format JSON response specifically for Claude Desktop compatibility.
    
    This function provides extra sanitization for responses to Claude Desktop,
    particularly focusing on avoiding timestamp prefixes and position 4 errors.
    
    Args:
        data: The data to format as JSON
        
    Returns:
        A sanitized JSON string that is compatible with Claude Desktop
    """
    try:
        def sanitize_dict(d):
            if isinstance(d, dict):
                return {k: sanitize_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [sanitize_dict(item) for item in d]
            elif isinstance(d, str):
                for char in [
                    '\ufeff',  # BOM
                    '\u200b',  # Zero-width space
                    '\u200c',  # Zero-width non-joiner
                    '\u200d',  # Zero-width joiner
                    '\u2060',  # Word joiner
                    '\ufffe',  # Reversed BOM
                    '\u00a0',  # Non-breaking space
                    '\u2028',  # Line separator
                    '\u2029',  # Paragraph separator
                    '\u0000',  # Null character
                    '\u001f',  # Unit separator
                    '\u001e',  # Record separator
                ]:
                    d = d.replace(char, '')
                d = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', d)
                return d
            else:
                return d
        
        sanitized_data = sanitize_dict(data)
        
        json_str = json.dumps(sanitized_data, ensure_ascii=True, separators=(',', ':'))
        
        encoded = json_str.encode('utf-8')
        if encoded.startswith(b'\xef\xbb\xbf'):
            encoded = encoded[3:]
            logger.debug("Removed BOM from JSON output bytes")
        
        json_str = encoded.decode('utf-8').strip()
        
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', json_str)
        
        if json_str and json_str[0] == '{' and len(json_str) > 4:
            if not json_str[3].isalnum() and json_str[3] not in ['"', "'", "_", ":", "}", ",", "]", "["]:
                logger.warning(f"Detected potential position 4 error character: '{json_str[3]}' (Unicode: U+{ord(json_str[3]):04X})")
                json_str = json_str[:3] + json_str[4:]
                logger.debug("Removed problematic character at position 4")
        
        try:
            json.loads(json_str)
            logger.debug("Verified JSON response is valid after sanitization")
        except json.JSONDecodeError as e:
            logger.error(f"JSON response is invalid after sanitization: {e}")
            
            if "position 4" in str(e) and len(json_str) > 4:
                logger.warning(f"Position 4 error detected: character at position 4 is '{json_str[3]}' (Unicode: U+{ord(json_str[3]):04X})")
                fixed_json = json_str[:3] + json_str[4:]
                try:
                    json.loads(fixed_json)
                    logger.debug("Successfully fixed JSON by removing character at position 4")
                    json_str = fixed_json
                except json.JSONDecodeError as e2:
                    logger.error(f"Still invalid after removing character at position 4: {e2}")
                    
                    for i in range(5, 10):
                        if len(json_str) > i:
                            very_fixed_json = json_str[:3] + json_str[i:]
                            try:
                                json.loads(very_fixed_json)
                                logger.debug(f"Successfully fixed JSON by removing characters 4 through {i}")
                                json_str = very_fixed_json
                                break
                            except json.JSONDecodeError:
                                pass
            
            try:
                parsed = json.loads(json_str.strip())
                json_str = json.dumps(parsed, ensure_ascii=True, separators=(',', ':'))
                logger.debug("Fixed JSON response by re-serializing")
            except json.JSONDecodeError:
                logger.error("Failed to fix JSON response by re-serializing")
                
                logger.warning("Creating new clean JSON as last resort")
                error_obj = {
                    "error": "JSON formatting error",
                    "original_data_type": str(type(data)),
                    "success": False,
                    "command": "kubectl get pods",  # Default command to prevent UI errors
                    "result": "Error processing JSON response"
                }
                json_str = json.dumps(error_obj, ensure_ascii=True, separators=(',', ':'))
        
        if json_str.startswith('202') and len(json_str) > 4 and json_str[4] == '-':
            logger.warning("Detected timestamp prefix in JSON response, removing")
            for i in range(20, len(json_str)):
                if i < len(json_str) and json_str[i] == '{':
                    json_str = json_str[i:]
                    logger.debug(f"Removed timestamp prefix, JSON now starts with: {json_str[:20]}...")
                    break
        
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError as e:
            logger.error(f"Final JSON validation failed: {e}")
            return json.dumps({
                "error": "JSON formatting error", 
                "success": False,
                "command": "kubectl get pods",  # Default command to prevent UI errors
                "result": "Error processing JSON response"
            }, ensure_ascii=True, separators=(',', ':'))
    
    except Exception as e:
        logger.error(f"Unexpected error in sanitize_json_response: {e}")
        return json.dumps({
            "error": str(e), 
            "success": False,
            "command": "kubectl get pods",  # Default command to prevent UI errors
            "result": "Error processing JSON response"
        }, ensure_ascii=True, separators=(',', ':'))
