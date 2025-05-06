"""
Enhanced Claude-specific JSON sanitization for fixing position 4 errors.

This module provides specialized JSON sanitization functions specifically
designed to address the "Unexpected non-whitespace character after JSON at position 4"
error that occurs in Claude Desktop.
"""

import json
import logging
import re
import os
from typing import Dict, Any, Union, List, Tuple

log_level = os.environ.get("KUBECTL_MCP_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("claude-json-fix-v3")

def find_json_boundaries(text: str) -> Tuple[int, int]:
    """
    Find the start and end indices of the first valid JSON object in a string.
    
    This function is crucial for handling cases where there might be content
    before or after the actual JSON, which can cause "after JSON" errors.
    
    Args:
        text: String that may contain a JSON object
        
    Returns:
        Tuple of (start_index, end_index) of the JSON object
    """
    if not text:
        return (-1, -1)
    
    start_idx = text.find('{')
    if start_idx == -1:
        return (-1, -1)
    
    brace_count = 1
    in_string = False
    escape_next = False
    
    for i in range(start_idx + 1, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\':
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                
            if brace_count == 0:
                return (start_idx, i + 1)
    
    return (start_idx, -1)  # No matching closing brace found

def extract_clean_json(text: str) -> str:
    """
    Extract and clean a JSON object from a string that might contain other content.
    
    This function specifically addresses the "Unexpected non-whitespace character after JSON"
    error by extracting only the valid JSON portion of the string.
    
    Args:
        text: String that may contain a JSON object with other content
        
    Returns:
        A clean JSON string
    """
    logger.debug(f"Extracting clean JSON from text: {repr(text[:50])}...")
    
    start_idx, end_idx = find_json_boundaries(text)
    
    if start_idx == -1 or end_idx == -1:
        logger.warning("Could not find valid JSON boundaries in the text")
        return text
    
    if start_idx > 0:
        logger.warning(f"Found content before JSON: {repr(text[:start_idx])}")
    
    if end_idx < len(text):
        logger.warning(f"Found content after JSON: {repr(text[end_idx:])}")
    
    json_text = text[start_idx:end_idx]
    
    try:
        parsed = json.loads(json_text)
        clean_json = json.dumps(parsed, ensure_ascii=True, separators=(',', ':'))
        logger.debug(f"Successfully extracted and cleaned JSON: {repr(clean_json[:50])}...")
        return clean_json
    except json.JSONDecodeError as e:
        logger.error(f"Extracted JSON is invalid: {e}")
        return json_text

def sanitize_json_for_claude(data: Dict[str, Any]) -> str:
    """
    Sanitize JSON specifically for Claude Desktop to prevent position 4 errors.
    
    This function applies multiple sanitization techniques specifically
    targeting Claude's JSON parser requirements, with special handling for
    "after JSON" errors.
    
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
            
            if "after JSON" in str(e):
                logger.warning("Detected 'after JSON' error, attempting to extract clean JSON")
                extracted_json = extract_clean_json(json_str)
                try:
                    json.loads(extracted_json)
                    logger.debug("Successfully extracted clean JSON")
                    json_str = extracted_json
                except json.JSONDecodeError as e3:
                    logger.error(f"Extracted JSON is still invalid: {e3}")
            
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
            clean_json = extract_clean_json(json_str)
            return clean_json
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
        
        try:
            json.loads(result)
            clean_result = extract_clean_json(result)
            return clean_result
        except json.JSONDecodeError as e:
            logger.error(f"JSON validation failed in format_claude_json_response: {e}")
            if "after JSON" in str(e):
                clean_result = extract_clean_json(result)
                return clean_result
            return result
    except Exception as e:
        logger.error(f"Error in format_claude_json_response: {e}")
        return json.dumps({
            "error": str(e), 
            "success": False,
            "command": "kubectl get pods",  # Default command to prevent UI errors
            "result": "Error processing JSON response"
        }, ensure_ascii=True, separators=(',', ':'))

def sanitize_claude_response(response: str) -> str:
    """
    Sanitize a complete response string for Claude Desktop.
    
    This function is specifically designed to handle the case where there might be
    content before or after the JSON in the response, which can cause the
    "Unexpected non-whitespace character after JSON at position 4" error.
    
    Args:
        response: The complete response string that may contain a JSON object
        
    Returns:
        A sanitized response string with only the valid JSON part
    """
    if not response:
        return response
    
    logger.debug(f"Sanitizing Claude response: {repr(response[:50])}...")
    
    clean_json = extract_clean_json(response)
    
    if clean_json != response:
        logger.info("Successfully extracted clean JSON from response")
    
    return clean_json

def ensure_claude_json_safety(json_str: str) -> str:
    """
    Final safety check for Claude JSON responses.
    
    This function applies all sanitization techniques and ensures the response
    is free from any characters that could cause parsing errors in Claude Desktop.
    
    Args:
        json_str: The JSON string to sanitize
        
    Returns:
        A sanitized JSON string
    """
    if not json_str:
        return json_str
    
    clean_json = extract_clean_json(json_str)
    
    try:
        parsed = json.loads(clean_json)
        final_json = json.dumps(parsed, ensure_ascii=True, separators=(',', ':'))
        
        if len(final_json) > 4:
            if not final_json[3].isalnum() and final_json[3] not in ['"', "'", "_", ":", "}", ",", "]", "["]:
                logger.warning(f"Final check: Detected position 4 error character: '{final_json[3]}' (Unicode: U+{ord(final_json[3]):04X})")
                final_json = final_json[:3] + final_json[4:]
        
        json.loads(final_json)
        
        return final_json
    except json.JSONDecodeError as e:
        logger.error(f"Error in ensure_claude_json_safety: {e}")
        
        if "after JSON" in str(e):
            return extract_clean_json(clean_json)
        
        return clean_json
