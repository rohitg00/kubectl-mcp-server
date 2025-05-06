"""
Claude-specific JSON sanitization for fixing position 4 errors.

This module provides specialized JSON sanitization functions specifically
designed to address the "Unexpected non-whitespace character after JSON at position 4"
error that occurs in Claude Desktop.
"""

import json
import logging
import re
from typing import Dict, Any, Union, List

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("claude-json-fix")

def sanitize_json_for_claude(data: Dict[str, Any]) -> str:
    """
    Sanitize JSON specifically for Claude Desktop to prevent position 4 errors.
    
    This function applies multiple sanitization techniques specifically
    targeting Claude's JSON parser requirements.
    
    Args:
        data: Dictionary to convert to JSON
        
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
        
        if json_str and len(json_str) > 4:
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
        logger.error(f"Unexpected error in sanitize_json_for_claude: {e}")
        return json.dumps({
            "error": str(e), 
            "success": False,
            "command": "kubectl get pods",  # Default command to prevent UI errors
            "result": "Error processing JSON response"
        }, ensure_ascii=True, separators=(',', ':'))

def format_claude_json_response(data: Dict[str, Any]) -> str:
    """
    Format a dictionary as a JSON string specifically for Claude Desktop.
    
    This function is a wrapper around sanitize_json_for_claude that provides
    additional logging and error handling.
    
    Args:
        data: Dictionary to convert to JSON
        
    Returns:
        A sanitized JSON string that is compatible with Claude Desktop
    """
    try:
        result = sanitize_json_for_claude(data)
        
        if len(result) > 10:
            logger.debug(f"JSON output first 10 chars: {repr(result[:10])}")
            for i in range(min(10, len(result))):
                logger.debug(f"Char at position {i}: '{result[i]}' (Unicode: U+{ord(result[i]):04X})")
        
        return result
    except Exception as e:
        logger.error(f"Error in format_claude_json_response: {e}")
        return json.dumps({
            "error": str(e), 
            "success": False,
            "command": "kubectl get pods",  # Default command to prevent UI errors
            "result": "Error processing JSON response"
        }, ensure_ascii=True, separators=(',', ':'))

def claude_json_encode(obj: Any) -> str:
    """
    Encode any Python object to a Claude-safe JSON string.
    
    This function handles non-serializable objects by converting them to strings.
    
    Args:
        obj: Any Python object to encode
        
    Returns:
        A Claude-safe JSON string
    """
    try:
        class ClaudeJSONEncoder(json.JSONEncoder):
            def default(self, obj):
                try:
                    return super().default(obj)
                except TypeError:
                    return str(obj)
        
        json_str = json.dumps(obj, cls=ClaudeJSONEncoder, ensure_ascii=True, separators=(',', ':'))
        
        if isinstance(obj, dict):
            return sanitize_json_for_claude(obj)
        else:
            try:
                json.loads(json_str)  # Verify it's valid JSON
                return sanitize_json_string(json_str)
            except json.JSONDecodeError:
                wrapper = {"value": obj}
                return sanitize_json_for_claude(wrapper)
    except Exception as e:
        logger.error(f"Error in claude_json_encode: {e}")
        return json.dumps({
            "error": str(e), 
            "success": False,
            "value": str(obj)
        }, ensure_ascii=True, separators=(',', ':'))

def sanitize_json_string(json_string: str) -> str:
    """
    Sanitize a JSON string for Claude Desktop.
    
    This function applies multiple sanitization techniques to ensure
    the JSON string is free from any characters that could cause
    parsing errors in Claude Desktop.
    
    Args:
        json_string: The JSON string to sanitize
        
    Returns:
        A sanitized JSON string
    """
    if not json_string:
        return json_string
    
    if json_string.startswith('\ufeff'):
        logger.debug("Removing BOM from beginning of JSON string")
        json_string = json_string[1:]
    
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
        '\u0000',  # Null character
        '\u001f',  # Unit separator
        '\u001e',  # Record separator
    ]
    
    for char in problematic_chars:
        if char in json_string:
            logger.debug(f"Removing problematic character {repr(char)} from JSON string")
            json_string = json_string.replace(char, '')
    
    json_string = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', json_string)
    
    if json_string and len(json_string) > 4:
        if not json_string[3].isalnum() and json_string[3] not in ['"', "'", "_", ":", "}", ",", "]", "["]:
            logger.warning(f"Detected potential position 4 error character: '{json_string[3]}' (Unicode: U+{ord(json_string[3]):04X})")
            json_string = json_string[:3] + json_string[4:]
            logger.debug("Removed problematic character at position 4")
    
    try:
        parsed = json.loads(json_string)
        clean_json = json.dumps(parsed, ensure_ascii=True, separators=(',', ':'))
        return clean_json
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON string: {e}")
        
        if "position 4" in str(e) and len(json_string) > 4:
            logger.warning(f"Position 4 error detected: character at position 4 is '{json_string[3]}' (Unicode: U+{ord(json_string[3]):04X})")
            fixed_json = json_string[:3] + json_string[4:]
            try:
                json.loads(fixed_json)
                logger.debug("Successfully fixed JSON by removing character at position 4")
                return fixed_json
            except json.JSONDecodeError:
                logger.error("Still invalid after removing character at position 4")
        
        return json_string.strip()
