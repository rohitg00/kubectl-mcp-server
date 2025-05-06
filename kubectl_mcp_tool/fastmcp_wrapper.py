"""
Custom FastMCP wrapper to handle BOM and invisible characters at the transport level.
"""

import json
import logging
import sys
import os
import re
from typing import Any, Dict, Optional

try:
    from mcp.server.fastmcp import FastMCP as OriginalFastMCP
except ImportError:
    logging.error("MCP SDK not found. Please install it with pip install mcp>=1.5.0")
    sys.exit(1)

try:
    from .enhanced_json_fix import sanitize_json, parse_json_safely, format_json_response as enhanced_format_json_response
except ImportError:
    try:
        from kubectl_mcp_tool.enhanced_json_fix import sanitize_json, parse_json_safely, format_json_response as enhanced_format_json_response
    except ImportError:
        sanitize_json = None
        parse_json_safely = None
        enhanced_format_json_response = None

logger = logging.getLogger("fastmcp-wrapper")

def sanitize_json_string(json_string: str) -> str:
    """
    Enhanced sanitization of JSON strings to fix position 4 errors.
    
    This function applies multiple sanitization techniques to ensure
    the JSON string is free from any characters that could cause
    parsing errors in Claude Desktop, including:
    - BOM and invisible characters
    - Timestamp prefixes and infixes
    - Whitespace issues
    - Control characters
    """
    if not json_string:
        return json_string
    
    if json_string.startswith('\ufeff'):
        logger.debug("Removing BOM from beginning of JSON string")
        json_string = json_string[1:]
    
    timestamp_patterns = [
        r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
        r'.*?(20\d{2}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
    ]
    
    for pattern in timestamp_patterns:
        match = re.search(pattern, json_string)
        if match:
            logger.debug(f"Found timestamp with pattern {pattern} in JSON string")
            timestamp_start = match.start(1)
            timestamp_end = match.end(1)
            
            if timestamp_start == 0 and '{' in json_string[timestamp_end:]:
                start = json_string.find('{', timestamp_end)
                end = json_string.rfind('}') + 1
                if start < end:
                    json_string = json_string[start:end]
                    logger.debug(f"Extracted JSON content after timestamp: {json_string[:30]}...")
            elif timestamp_start > 0:
                before = json_string[:timestamp_start]
                after = json_string[timestamp_end:]
                
                if before.count('{') > before.count('}') and after.count('}') > after.count('{'):
                    json_string = before + after
                    logger.debug(f"Removed timestamp from middle of JSON: {json_string[:30]}...")
    
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
    
    try:
        parsed = json.loads(json_string)
        clean_json = json.dumps(parsed, ensure_ascii=True, separators=(',', ':'))
        return clean_json
    except json.JSONDecodeError:
        if '{' in json_string and '}' in json_string:
            start = json_string.find('{')
            end = json_string.rfind('}') + 1
            if start < end:
                potential_json = json_string[start:end]
                try:
                    json.loads(potential_json)
                    logger.debug("Extracted valid JSON from mixed content")
                    return potential_json
                except json.JSONDecodeError:
                    pass
        
        return json_string.strip()

class FastMCP(OriginalFastMCP):
    """
    Extended FastMCP implementation that handles BOM and invisible characters at the transport level.
    """
    
    async def _read_message(self, stream: Any) -> Optional[Dict[str, Any]]:
        """
        Read a message from the given stream with comprehensive error handling.
        
        This overrides the original _read_message method to add enhanced JSON parsing
        that can handle problematic characters and log output mixed with JSON.
        """
        try:
            line = await stream.readline()
            if not line:
                return None
            
            line_str = line.decode("utf-8").strip()
            
            if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true"):
                logger.debug(f"Received raw message: {repr(line_str[:50])}...")
                if len(line_str) > 10:
                    for i in range(min(10, len(line_str))):
                        logger.debug(f"Char at position {i}: '{line_str[i]}' (Unicode: U+{ord(line_str[i]):04X})")
            
            timestamp_patterns = [
                r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
                r'.*?(20\d{2}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
            ]
            
            for pattern in timestamp_patterns:
                match = re.search(pattern, line_str)
                if match:
                    logger.debug(f"Detected log line with timestamp using pattern {pattern}, attempting to extract JSON")
                    timestamp_start = match.start(1)
                    timestamp_end = match.end(1)
                    
                    if timestamp_start == 0:
                        if '{' in line_str[timestamp_end:]:
                            start = line_str.find('{', timestamp_end)
                            end = line_str.rfind('}') + 1
                            if start < end:
                                line_str = line_str[start:end]
                                logger.debug(f"Extracted JSON after timestamp: {line_str[:30]}...")
                    else:
                        before = line_str[:timestamp_start]
                        after = line_str[timestamp_end:]
                        
                        if before.count('{') > before.count('}') and after.count('}') > after.count('{'):
                            line_str = before + after
                            logger.debug(f"Removed timestamp from middle of JSON: {line_str[:30]}...")
            
            if parse_json_safely:
                parsed = parse_json_safely(line_str)
                if parsed:
                    logger.debug("Successfully parsed message using enhanced JSON parser")
                    return parsed
            
            sanitized = sanitize_json_string(line_str)
            try:
                return json.loads(sanitized)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse message: {e}")
                
                if '{' in sanitized and '}' in sanitized:
                    start = sanitized.find('{')
                    end = sanitized.rfind('}') + 1
                    if start < end:
                        potential_json = sanitized[start:end]
                        try:
                            parsed = json.loads(potential_json)
                            logger.debug("Successfully extracted JSON from mixed content")
                            return parsed
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to extract JSON from message: {e}")
                            if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true"):
                                logger.debug(f"Failed JSON content: {potential_json[:100]}...")
                
                return None
        except Exception as e:
            logger.error(f"Error reading message: {e}")
            return None
    
    async def _write_message(self, message: Dict[str, Any], stream: Any) -> None:
        """
        Write a message to the given stream with comprehensive BOM and invisible character handling.
        """
        try:
            if enhanced_format_json_response:
                json_str = enhanced_format_json_response(message)
                logger.debug("Using enhanced JSON formatter")
            else:
                json_str = json.dumps(message, ensure_ascii=True, separators=(',', ':'))
                logger.debug("Using standard JSON formatter")
            
            timestamp_patterns = [
                r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
                r'.*?(20\d{2}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
            ]
            
            for pattern in timestamp_patterns:
                match = re.search(pattern, json_str)
                if match:
                    logger.warning(f"Found timestamp with pattern {pattern} in JSON string")
                    timestamp_start = match.start(1)
                    timestamp_end = match.end(1)
                    
                    if timestamp_start == 0 and '{' in json_str[timestamp_end:]:
                        start = json_str.find('{', timestamp_end)
                        end = json_str.rfind('}') + 1
                        if start < end:
                            json_str = json_str[start:end]
                            logger.debug(f"Extracted JSON content after timestamp: {json_str[:30]}...")
                    elif timestamp_start > 0:
                        before = json_str[:timestamp_start]
                        after = json_str[timestamp_end:]
                        
                        if before.count('{') > before.count('}') and after.count('}') > after.count('{'):
                            json_str = before + after
                            logger.debug(f"Removed timestamp from middle of JSON: {json_str[:30]}...")
            
            if sanitize_json:
                clean_json = sanitize_json(json_str)
                if clean_json:
                    logger.debug("Applied enhanced JSON sanitization")
                    json_str = clean_json
            
            encoded = json_str.encode('utf-8')
            if encoded.startswith(b'\xef\xbb\xbf'):
                encoded = encoded[3:]
                logger.debug("Removed BOM from JSON output bytes")
            
            clean_json = encoded.decode('utf-8').strip()
            
            clean_json = sanitize_json_string(clean_json)
            
            try:
                json.loads(clean_json)
                logger.debug("Verified JSON is valid after sanitization")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON after sanitization: {e}")
                
                timestamp_patterns = [
                    r'^(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
                    r'.*?(20\d{2}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
                ]
                
                for pattern in timestamp_patterns:
                    match = re.search(pattern, clean_json)
                    if match:
                        logger.warning(f"Found timestamp pattern: {pattern} in JSON, attempting to extract clean JSON")
                        timestamp_start = match.start(1)
                        timestamp_end = match.end(1)
                        
                        if timestamp_start == 0:
                            if '{' in clean_json[timestamp_end:]:
                                start = clean_json.find('{', timestamp_end)
                                end = clean_json.rfind('}') + 1
                                if start < end:
                                    clean_json = clean_json[start:end]
                                    logger.debug(f"Extracted JSON after timestamp: {clean_json[:30]}...")
                                    break
                        else:
                            before = clean_json[:timestamp_start]
                            after = clean_json[timestamp_end:]
                            
                            if before.count('{') > before.count('}') and after.count('}') > after.count('{'):
                                clean_json = before + after
                                logger.debug(f"Removed timestamp from middle of JSON: {clean_json[:30]}...")
                                break
                
                if '{' in clean_json and '}' in clean_json:
                    start = clean_json.find('{')
                    end = clean_json.rfind('}') + 1
                    if start < end:
                        potential_json = clean_json[start:end]
                        try:
                            json.loads(potential_json)
                            logger.debug("Extracted valid JSON from mixed content")
                            clean_json = potential_json
                        except json.JSONDecodeError:
                            clean_json = json_str
                else:
                    clean_json = json_str
                
            if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true"):
                if len(clean_json) > 10:
                    logger.debug(f"JSON output first 10 chars: {repr(clean_json[:10])}")
                    for i in range(min(10, len(clean_json))):
                        logger.debug(f"Char at position {i}: '{clean_json[i]}' (Unicode: U+{ord(clean_json[i]):04X})")
            
            await stream.write(clean_json + "\n")
        except Exception as e:
            logger.error(f"Error writing message: {e}")
            await super()._write_message(message, stream)
            
            if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true"):
                if len(clean_json) > 10:
                    logger.debug(f"JSON output first 10 chars: {repr(clean_json[:10])}")
                    for i in range(min(10, len(clean_json))):
                        logger.debug(f"Char at position {i}: '{clean_json[i]}' (Unicode: U+{ord(clean_json[i]):04X})")
            
            await stream.write(clean_json + "\n")
        except Exception as e:
            logger.error(f"Error writing message: {e}")
            await super()._write_message(message, stream)
