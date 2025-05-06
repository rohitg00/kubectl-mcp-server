#!/usr/bin/env python3
"""
Minimal MCP server for kubectl.
"""

import os
import sys
import json
import logging
import subprocess
import re
import asyncio
import traceback
import time
from typing import Dict, Any, List, Optional, Union, Tuple

# Set up a comprehensive logging configuration using the MCP_LOG_FILE environment variable
log_file = os.environ.get("MCP_LOG_FILE")
log_level = logging.DEBUG if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true") else logging.INFO

# Configure root logger to use a file handler if MCP_LOG_FILE is specified, otherwise use stderr
handlers = []
if log_file:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handlers.append(logging.FileHandler(log_file))
else:
    handlers.append(logging.StreamHandler(sys.stderr))

# Apply the configuration to the root logger
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=handlers
)

# Create module loggers
logger = logging.getLogger("kubectl-mcp-tool")

# Prevent propagation of logs to stdout
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        logging.root.removeHandler(handler)

try:
    from .claude_message_framing import ClaudeMessageFramer, extract_clean_json
    logger.debug("Successfully imported ClaudeMessageFramer from relative path")
except ImportError:
    try:
        from kubectl_mcp_tool.claude_message_framing import ClaudeMessageFramer, extract_clean_json
        logger.debug("Successfully imported ClaudeMessageFramer from absolute path")
    except ImportError:
        logger.warning("Could not import ClaudeMessageFramer, message framing will not be available")

CLAUDE_ENVIRONMENT = os.environ.get("MCP_CLIENT", "").lower() == "claude" or "claude" in os.environ.get("MCP_CLIENT_INFO", "").lower()

claude_message_framer = None
try:
    if CLAUDE_ENVIRONMENT:
        claude_message_framer = ClaudeMessageFramer()
        logger.debug("Initialized ClaudeMessageFramer for Claude environment")
except NameError:
    logger.warning("ClaudeMessageFramer not available, skipping initialization")

def default_wrap_async_handler(handler):
    async def wrapped_handler(*args, **kwargs):
        try:
            return await handler(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger("minimal-mcp")
            logger.error(f"Error in async handler: {e}")
            error_result = {
                "command": "Error",
                "result": f"Error in handler: {str(e)}",
                "success": False,
                "intent": "error",
                "resource_type": "unknown"
            }
            return json.dumps(error_result, ensure_ascii=True, separators=(',', ':'))
    return wrapped_handler

wrap_async_handler = default_wrap_async_handler

# Remove redundant logging.basicConfig() call
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("minimal-mcp")

try:
    from .enhanced_json_fix import sanitize_json, parse_json_safely, format_json_response as enhanced_format_json_response
    try:
        from .taskgroup_fix import wrap_async_handler as enhanced_wrap_async_handler, patch_fastmcp
        wrap_async_handler = enhanced_wrap_async_handler
        logger.info("Imported taskgroup_fix for TaskGroup error handling")
    except ImportError:
        try:
            from .enhanced_json_fix import wrap_async_handler as enhanced_wrap_async_handler
            wrap_async_handler = enhanced_wrap_async_handler
        except ImportError:
            pass
except ImportError:
    try:
        from kubectl_mcp_tool.enhanced_json_fix import sanitize_json, parse_json_safely, format_json_response as enhanced_format_json_response
        try:
            from kubectl_mcp_tool.taskgroup_fix import wrap_async_handler as enhanced_wrap_async_handler, patch_fastmcp
            wrap_async_handler = enhanced_wrap_async_handler
            logger.info("Imported taskgroup_fix for TaskGroup error handling")
        except ImportError:
            try:
                from kubectl_mcp_tool.enhanced_json_fix import wrap_async_handler as enhanced_wrap_async_handler
                wrap_async_handler = enhanced_wrap_async_handler
            except ImportError:
                pass
    except ImportError:
        sanitize_json = None
        parse_json_safely = None
        enhanced_format_json_response = None

# Remove another redundant logging.basicConfig() call
# Set up logging
# logging.basicConfig(
#    level=logging.DEBUG,
#    format="%(asctime)s - %(levelname)s - %(message)s",
#    handlers=[
#        logging.StreamHandler(sys.stderr)
#    ]
# )
logger = logging.getLogger("minimal-mcp")

def run_kubectl_command(command):
    """Run a kubectl command and return the result."""
    try:
        if not command.strip().startswith("kubectl "):
            command = f"kubectl {command}"
        
        env = os.environ.copy()
        if "GOOGLE_APPLICATION_CREDENTIALS" in env and "USE_GKE_GCLOUD_AUTH_PLUGIN" not in env:
            env["USE_GKE_GCLOUD_AUTH_PLUGIN"] = "True"
        
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,  # Increased timeout for longer-running commands
            env=env
        )
        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""
        
        response = {
            "command": command,
            "result": stdout if result.returncode == 0 else stderr,
            "success": result.returncode == 0
        }
        
        return response
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return {
            "command": command,
            "result": "Command timed out after 30 seconds",
            "success": False
        }
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return {
            "command": command,
            "result": f"Error: {str(e)}",
            "success": False
        }

def get_pod_resource_usage() -> Dict[str, Any]:
    """Get resource usage for all pods."""
    result = run_kubectl_command("kubectl top pods --all-namespaces")
    return result

def get_pods_with_restart_counts() -> Dict[str, Any]:
    """Get pods with their restart counts."""
    cmd = "kubectl get pods --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,STATUS:.status.phase"
    result = run_kubectl_command(cmd)
    return result

def get_node_resource_usage() -> Dict[str, Any]:
    """Get resource usage for all nodes."""
    result = run_kubectl_command("kubectl top nodes")
    return result

def get_deployments_with_replicas() -> Dict[str, Any]:
    """Get deployments with their replica counts."""
    cmd = "kubectl get deployments --all-namespaces -o custom-columns=NAMESPACE:.metadata.namespace,NAME:.metadata.name,DESIRED:.spec.replicas,CURRENT:.status.replicas,AVAILABLE:.status.availableReplicas,STRATEGY:.spec.strategy.type"
    result = run_kubectl_command(cmd)
    return result

def get_service_endpoints() -> Dict[str, Any]:
    """Get services with their endpoints."""
    result = run_kubectl_command("kubectl get endpoints --all-namespaces")
    return result

def get_persistent_volumes() -> Dict[str, Any]:
    """Get persistent volumes and their status."""
    result = run_kubectl_command("kubectl get pv")
    return result

def get_service_accounts() -> Dict[str, Any]:
    """Get service accounts in all namespaces."""
    result = run_kubectl_command("kubectl get serviceaccounts --all-namespaces")
    return result

def get_cluster_events() -> Dict[str, Any]:
    """Get recent cluster events."""
    result = run_kubectl_command("kubectl get events --sort-by=.metadata.creationTimestamp")
    return result

def get_api_resources() -> Dict[str, Any]:
    """Get available API resources."""
    result = run_kubectl_command("kubectl api-resources")
    return result

def format_json_response(data: Dict[str, Any]) -> str:
    """
    Format a dictionary as a JSON string with comprehensive handling to prevent position 4 errors.
    
    This function specifically addresses the "Unexpected non-whitespace character after JSON at position 4"
    error by ensuring the JSON output is properly formatted with no unexpected characters.
    It also handles the case where there might be content after the JSON.
    """
    if CLAUDE_ENVIRONMENT and claude_message_framer is not None:
        try:
            message_id = data.get("id", str(int(time.time())))
            
            framed_response = claude_message_framer.frame_response(data, message_id)
            logger.debug(f"Using ClaudeMessageFramer to frame response with ID {message_id}")
            
            return framed_response
        except Exception as e:
            logger.error(f"Error using ClaudeMessageFramer: {e}")
            logger.debug("Falling back to standard JSON formatting")
    
    sanitize_json_response_func = None
    
    try:
        if CLAUDE_ENVIRONMENT:
            try:
                try:
                    from .claude_json_fix_v3 import sanitize_json_for_claude as claude_sanitize_v3
                    from .claude_json_fix_v3 import ensure_claude_json_safety
                    sanitize_json_response_func = claude_sanitize_v3
                    logger.debug("Successfully imported sanitize_json_for_claude from claude_json_fix_v3")
                except ImportError:
                    try:
                        from kubectl_mcp_tool.claude_json_fix_v3 import sanitize_json_for_claude as claude_sanitize_v3
                        from kubectl_mcp_tool.claude_json_fix_v3 import ensure_claude_json_safety
                        sanitize_json_response_func = claude_sanitize_v3
                        logger.debug("Successfully imported sanitize_json_for_claude from absolute path claude_json_fix_v3")
                    except ImportError:
                        logger.warning("Could not import claude_json_fix_v3, falling back to claude_json_fix")
                        from .claude_json_fix import sanitize_json_for_claude as claude_sanitize
                        sanitize_json_response_func = claude_sanitize
                        logger.debug("Successfully imported sanitize_json_for_claude from relative path for Claude environment")
            except ImportError:
                try:
                    from kubectl_mcp_tool.claude_json_fix import sanitize_json_for_claude as claude_sanitize
                    sanitize_json_response_func = claude_sanitize
                    logger.debug("Successfully imported sanitize_json_for_claude from absolute path for Claude environment")
                except ImportError:
                    logger.warning("Could not import sanitize_json_for_claude from claude_json_fix, falling back to enhanced_json_fix")
                    from .enhanced_json_fix import sanitize_json_response as enhanced_sanitize
                    sanitize_json_response_func = enhanced_sanitize
        else:
            from .enhanced_json_fix import sanitize_json_response as enhanced_sanitize
            sanitize_json_response_func = enhanced_sanitize
            logger.debug("Successfully imported sanitize_json_response from relative path")
    except ImportError:
        try:
            if CLAUDE_ENVIRONMENT:
                try:
                    try:
                        from kubectl_mcp_tool.claude_json_fix_v3 import sanitize_json_for_claude as claude_sanitize_v3
                        from kubectl_mcp_tool.claude_json_fix_v3 import ensure_claude_json_safety
                        sanitize_json_response_func = claude_sanitize_v3
                        logger.debug("Successfully imported sanitize_json_for_claude from absolute path claude_json_fix_v3")
                    except ImportError:
                        logger.warning("Could not import claude_json_fix_v3, falling back to claude_json_fix")
                        from kubectl_mcp_tool.claude_json_fix import sanitize_json_for_claude as claude_sanitize
                        sanitize_json_response_func = claude_sanitize
                        logger.debug("Successfully imported sanitize_json_for_claude from absolute path for Claude environment")
                except ImportError:
                    logger.warning("Could not import sanitize_json_for_claude from claude_json_fix, falling back to enhanced_json_fix")
                    from kubectl_mcp_tool.enhanced_json_fix import sanitize_json_response as enhanced_sanitize
                    sanitize_json_response_func = enhanced_sanitize
            else:
                from kubectl_mcp_tool.enhanced_json_fix import sanitize_json_response as enhanced_sanitize
                sanitize_json_response_func = enhanced_sanitize
                logger.debug("Successfully imported sanitize_json_response from absolute path")
        except ImportError:
            logger.warning("Could not import sanitize_json_response from enhanced_json_fix")
    
    if sanitize_json_response_func:
        try:
            result = sanitize_json_response_func(data)
            try:
                json.loads(result)
                logger.debug("Enhanced sanitize_json_response produced valid JSON")
                
                if CLAUDE_ENVIRONMENT and 'ensure_claude_json_safety' in locals():
                    try:
                        final_result = ensure_claude_json_safety(result)
                        logger.debug("Applied ensure_claude_json_safety for final validation")
                        return final_result
                    except Exception as e:
                        logger.error(f"Error in ensure_claude_json_safety: {e}")
                
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Enhanced sanitize_json_response produced invalid JSON: {e}")
                
                if CLAUDE_ENVIRONMENT and "after JSON" in str(e) and 'ensure_claude_json_safety' in locals():
                    try:
                        fixed_result = ensure_claude_json_safety(result)
                        logger.debug("Fixed 'after JSON' error with ensure_claude_json_safety")
                        return fixed_result
                    except Exception as e2:
                        logger.error(f"Error fixing 'after JSON' error: {e2}")
        except Exception as e:
            logger.error(f"Error using enhanced sanitize_json_response: {e}")
    
    if enhanced_format_json_response:
        try:
            result = enhanced_format_json_response(data)
            try:
                json.loads(result)
                logger.debug("Enhanced format_json_response produced valid JSON")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Enhanced format_json_response produced invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error using enhanced format_json_response: {e}")
    
    try:
        def sanitize_dict(d):
            if isinstance(d, dict):
                return {k: sanitize_dict(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [sanitize_dict(item) for item in d]
            elif isinstance(d, str):
                for char in ['\ufeff', '\u200b', '\u200c', '\u200d', '\u2060', '\ufffe', '\u00a0', '\u2028', '\u2029']:
                    d = d.replace(char, '')
                return d
            else:
                return d
        
        sanitized_data = sanitize_dict(data)
        
        json_output = json.dumps(sanitized_data, ensure_ascii=True, separators=(',', ':'))
        
        encoded = json_output.encode('utf-8')
        if encoded.startswith(b'\xef\xbb\xbf'):
            encoded = encoded[3:]
            logger.debug("Removed BOM from JSON output bytes")
        
        clean_json = encoded.decode('utf-8').strip()
        
        clean_json = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', clean_json)
        
        if clean_json and clean_json[0] == '{' and len(clean_json) > 4:
            if not clean_json[3].isalnum() and clean_json[3] not in ['"', "'", "_", ":", "}", ",", "]"]:
                logger.warning(f"Detected potential position 4 error character: '{clean_json[3]}' (Unicode: U+{ord(clean_json[3]):04X})")
                clean_json = clean_json[:3] + clean_json[4:]
                logger.debug("Removed problematic character at position 4")
        
        clean_json = sanitize_json_string(clean_json)
        
        try:
            json.loads(clean_json)
            logger.debug("Verified JSON response is valid after sanitization")
        except json.JSONDecodeError as e:
            logger.error(f"JSON response is invalid after sanitization: {e}")
            
            if "position 4" in str(e) and len(clean_json) > 4:
                logger.warning(f"Position 4 error detected: character at position 4 is '{clean_json[3]}' (Unicode: U+{ord(clean_json[3]):04X})")
                fixed_json = clean_json[:3] + clean_json[4:]
                try:
                    json.loads(fixed_json)
                    logger.debug("Successfully fixed JSON by removing character at position 4")
                    clean_json = fixed_json
                except json.JSONDecodeError as e2:
                    logger.error(f"Still invalid after removing character at position 4: {e2}")
            
            try:
                parsed = json.loads(clean_json.strip())
                clean_json = json.dumps(parsed, ensure_ascii=True, separators=(',', ':'))
                logger.debug("Fixed JSON response by re-serializing")
            except json.JSONDecodeError:
                logger.error("Failed to fix JSON response by re-serializing")
                
                logger.warning("Creating new clean JSON as last resort")
                error_obj = {
                    "error": "JSON formatting error",
                    "original_data_type": str(type(data)),
                    "success": False
                }
                clean_json = json.dumps(error_obj, ensure_ascii=True, separators=(',', ':'))
        
        if os.environ.get("MCP_DEBUG", "").lower() in ("1", "true"):
            if len(clean_json) > 10:
                logger.debug(f"JSON output first 10 chars: {repr(clean_json[:10])}")
                for i in range(min(10, len(clean_json))):
                    logger.debug(f"Char at position {i}: '{clean_json[i]}' (Unicode: U+{ord(clean_json[i]):04X})")
        
        try:
            json.loads(clean_json)
            return clean_json
        except json.JSONDecodeError as e:
            logger.error(f"Final JSON validation failed: {e}")
            return json.dumps({"error": "JSON formatting error", "success": False}, ensure_ascii=True, separators=(',', ':'))
    
    except Exception as e:
        logger.error(f"Unexpected error in format_json_response: {e}")
        error_json = json.dumps({"error": str(e), "success": False}, ensure_ascii=True, separators=(',', ':'))
        return error_json.strip()

def sanitize_json_string(json_string: str) -> str:
    """
    Enhanced sanitization of JSON strings to fix position 4 errors.
    
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
    
    if sanitize_json:
        try:
            sanitized = sanitize_json(json_string)
            if sanitized:
                return sanitized
        except Exception as e:
            logger.error(f"Enhanced JSON sanitization failed: {e}, falling back to basic sanitization")
    
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
    ]
    
    for char in problematic_chars:
        if char in json_string:
            logger.debug(f"Removing problematic character {repr(char)} from JSON string")
            json_string = json_string.replace(char, '')
    
    try:
        parsed = json.loads(json_string)
        clean_json = json.dumps(parsed, ensure_ascii=True, separators=(',', ':'))
        return clean_json
    except json.JSONDecodeError:
        return json_string.strip()

def process_advanced_query(query: str) -> Dict[str, Any]:
    """Process advanced Kubernetes queries."""
    query = query.lower().strip()
    
    if "kubectl top" in query or "top pods" in query:
        if "pods" in query:
            return get_pod_resource_usage()
        elif "nodes" in query or "node" in query:
            return get_node_resource_usage()
        else:
            return get_pod_resource_usage()
    
    if re.search(r"run.*command.*kubectl top", query):
        if "pods" in query:
            return get_pod_resource_usage()
        elif "nodes" in query or "node" in query:
            return get_node_resource_usage()
        else:
            return get_pod_resource_usage()
    
    if re.search(r"(resource|cpu|memory).*usage", query) or re.search(r"(show|get|display).*resource", query):
        if "pod" in query or "pods" in query:
            return get_pod_resource_usage()
        elif "node" in query or "nodes" in query:
            return get_node_resource_usage()
        else:
            return get_pod_resource_usage()
    
    if re.search(r"(show|get|display|list).*pod", query) and re.search(r"(resource|cpu|memory|usage)", query):
        return get_pod_resource_usage()
    
    if re.search(r"(show|get|display|list).*node", query) and re.search(r"(resource|cpu|memory|usage)", query):
        return get_node_resource_usage()
    
    if re.search(r"(pod|pods).*(status|health|restart)", query):
        return get_pods_with_restart_counts()
    
    if re.search(r"(deployment|deployments).*(replica|scale|status)", query):
        return get_deployments_with_replicas()
    
    if re.search(r"(service|services).*(endpoint|connection)", query):
        return get_service_endpoints()
    
    if re.search(r"(volume|volumes|pv|storage)", query):
        return get_persistent_volumes()
    
    if re.search(r"(service account|serviceaccount)", query):
        return get_service_accounts()
    
    if re.search(r"(event|events|recent|latest)", query):
        return get_cluster_events()
    
    if re.search(r"(api|resource|resources|available)", query):
        return get_api_resources()
    
    if query.startswith("kubectl "):
        return run_kubectl_command(query)
    
    return None

async def main():
    """Run a simple MCP server."""
    try:
        try:
            from .fastmcp_patch import logger as patch_logger
            logger.info("Imported FastMCP patch for TaskGroup error handling")
        except ImportError:
            try:
                from kubectl_mcp_tool.fastmcp_patch import logger as patch_logger
                logger.info("Imported FastMCP patch for TaskGroup error handling")
            except ImportError:
                logger.warning("Could not import FastMCP patch, TaskGroup errors may occur")
        
        from .fastmcp_wrapper import FastMCP
    except ImportError:
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError:
            try:
                from kubectl_mcp_tool.fastmcp_wrapper import FastMCP
            except ImportError as e:
                logger.error(f"Failed to import FastMCP: {e}")
                logger.error("Make sure the PYTHONPATH includes the repository root")
                logger.error(f"Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
                logger.error(f"Current sys.path: {sys.path}")
                raise ImportError("Could not import FastMCP. Please check your PYTHONPATH.") from e
    
    # Create a FastMCP server
    server = FastMCP("kubectl-mcp")
    
    # Register a simple tool
    @server.tool("process_natural_language")
    @wrap_async_handler
    async def process_natural_language(query: str = None, args: List[str] = None, **kwargs):
        """Process natural language query for kubectl."""
        logger.info(f"Received query: {query}")
        logger.info(f"Received args: {args}")
        logger.info(f"Received kwargs: {kwargs}")
        
        if query is None:
            if args and len(args) > 0 and isinstance(args[0], str):
                query = args[0]
                args = args[1:] if len(args) > 1 else []
                logger.info(f"Extracted query from args: {query}")
            elif "query" in kwargs:
                query = kwargs.pop("query")
                logger.info(f"Extracted query from kwargs: {query}")
            else:
                logger.error("No query parameter found in args or kwargs")
                result = {
                    "command": "Error",
                    "result": "Error: No query parameter provided",
                    "success": False,
                    "intent": "error",
                    "resource_type": "unknown"
                }
                return format_and_validate_json_response(result)
        
        try:
            if query and query.strip().startswith("kubectl "):
                logger.info(f"Detected direct kubectl command: {query}")
                result = run_kubectl_command(query)
                if "intent" not in result:
                    result["intent"] = "direct_command"
                if "resource_type" not in result:
                    result["resource_type"] = "multiple"
                
                logger.info(f"Direct command result: {result}")
                json_result = format_and_validate_json_response(result)
                logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
                return json_result
            
            if re.search(r"run.*command.*kubectl", query, re.IGNORECASE):
                cmd_match = re.search(r"kubectl\s+.*$", query, re.IGNORECASE)
                if cmd_match:
                    cmd = cmd_match.group(0)
                    logger.info(f"Extracted kubectl command: {cmd}")
                    result = run_kubectl_command(cmd)
                    if "intent" not in result:
                        result["intent"] = "direct_command"
                    if "resource_type" not in result:
                        result["resource_type"] = "multiple"
                    
                    logger.info(f"Extracted command result: {result}")
                    json_result = format_and_validate_json_response(result)
                    logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
                    return json_result
            
            query_lower = query.lower().strip()
            logger.debug(f"Processing natural language query: '{query_lower}'")
            
            if re.search(r'\b(show|get|list|display)\s+(me\s+)?(all\s+)?(the\s+)?pod[s]?\b', query_lower):
                logger.info(f"Detected pod query pattern: {query_lower}")
                resource_type = "pods"
                namespace_arg = ""
                
                if re.search(r'\bin\s+all\s+namespaces\b|\bacross\s+all\s+namespaces\b|\ball\s+namespaces\b', query_lower):
                    namespace_arg = "--all-namespaces"
                elif re.search(r'\bin\s+namespace\b|\bin\s+the\s+namespace\b|\bin\s+[\w-]+\s+namespace\b', query_lower):
                    namespace_match = re.search(r'in\s+(?:the\s+)?(?:namespace\s+)?([\w-]+)(?:\s+namespace)?', query_lower)
                    if namespace_match:
                        namespace = namespace_match.group(1)
                        namespace_arg = f"-n {namespace}"
                
                cmd = f"kubectl get {resource_type} {namespace_arg}".strip()
                logger.info(f"Constructed kubectl command for pods: {cmd}")
                
                # Run the command
                result = run_kubectl_command(cmd)
                if "intent" not in result:
                    result["intent"] = "natural_language_query"
                if "resource_type" not in result:
                    result["resource_type"] = resource_type
                if "kubernetes_command" not in result:
                    result["kubernetes_command"] = cmd
                
                logger.info(f"Pod query result: {result}")
                json_result = format_and_validate_json_response(result)
                logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
                return json_result
            
            filler_words = ["show", "me", "get", "list", "display", "what", "are", "the", "all", "please", "can", "you", "tell", "about"]
            
            clean_query = query_lower
            for word in filler_words:
                clean_query = re.sub(r'\b' + word + r'\b', ' ', clean_query)
            
            clean_query = re.sub(r'\s+', ' ', clean_query).strip()
            logger.debug(f"Original query: '{query_lower}'")
            logger.debug(f"Cleaned query: '{clean_query}'")
            
            resource_type = None
            namespace_arg = ""
            
            if re.search(r'\bpod[s]?\b', clean_query):
                resource_type = "pods"
            elif re.search(r'\bdeployment[s]?\b', clean_query):
                resource_type = "deployments"
            elif re.search(r'\bservice[s]?\b', clean_query):
                resource_type = "services"
            elif re.search(r'\bnamespace[s]?\b', clean_query) and ("list" in clean_query or clean_query.strip() == "namespaces"):
                resource_type = "namespaces"
            elif re.search(r'\bnode[s]?\b', clean_query):
                resource_type = "nodes"
            elif re.search(r'\bconfigmap[s]?\b', clean_query):
                resource_type = "configmaps"
            elif re.search(r'\bsecret[s]?\b', clean_query):
                resource_type = "secrets"
            elif re.search(r'\bpersistentvolume[s]?\b|\bpv[s]?\b', clean_query):
                resource_type = "persistentvolumes"
            elif re.search(r'\bpersistentvolumeclaim[s]?\b|\bpvc[s]?\b', clean_query):
                resource_type = "persistentvolumeclaims"
            elif re.search(r'\bingress[es]?\b', clean_query):
                resource_type = "ingress"
            else:
                resource_type = "all"
            
            if re.search(r'\bin\s+all\s+namespaces\b|\bacross\s+all\s+namespaces\b|\ball\s+namespaces\b', query_lower.replace("  ", " ")):
                namespace_arg = "--all-namespaces"
            elif re.search(r'\bin\s+namespace\b|\bin\s+the\s+namespace\b|\bin\s+[\w-]+\s+namespace\b', query_lower):
                namespace_match = re.search(r'in\s+(?:the\s+)?(?:namespace\s+)?([\w-]+)(?:\s+namespace)?', query_lower)
                if namespace_match:
                    namespace = namespace_match.group(1)
                    namespace_arg = f"-n {namespace}"
            
            cmd = f"kubectl get {resource_type} {namespace_arg}".strip()
            
            # Run the command
            result = run_kubectl_command(cmd)
            if "intent" not in result:
                result["intent"] = "natural_language_query"
            if "resource_type" not in result:
                result["resource_type"] = resource_type
            if "kubernetes_command" not in result:
                result["kubernetes_command"] = cmd
            
            logger.info(f"Natural language command result: {result}")
            json_result = format_and_validate_json_response(result)
            logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
            return json_result
            
            advanced_result = process_advanced_query(query)
            
            if advanced_result:
                if "intent" not in advanced_result:
                    advanced_result["intent"] = "advanced_query"
                if "resource_type" not in advanced_result:
                    advanced_result["resource_type"] = "multiple"
                
                logger.info(f"Advanced query result: {advanced_result}")
                json_result = format_and_validate_json_response(advanced_result)
                logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
                return json_result
            
            try:
                from kubectl_mcp_tool.natural_language import process_query
                
                try:
                    try:
                        from kubectl_mcp_tool.taskgroup_fix import run_with_taskgroup_protection
                        result = await run_with_taskgroup_protection(asyncio.to_thread(process_query, query, args, **kwargs))
                    except ImportError:
                        result = await asyncio.to_thread(process_query, query, args, **kwargs)
                    
                    if isinstance(result, dict) and "jsonrpc" in result and "error" in result:
                        logger.info(f"Received error response from TaskGroup protection: {result}")
                        json_result = format_and_validate_json_response(result)
                        logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
                        return json_result
                    
                    if not isinstance(result, dict):
                        result = {"result": str(result), "success": False}
                    
                    if "command" not in result:
                        result["command"] = "Unknown command"
                        
                    if "success" not in result:
                        result["success"] = False
                        
                    if "result" not in result:
                        result["result"] = "No result provided"
                        
                    if "intent" not in result:
                        result["intent"] = "unknown"
                        
                    if "resource_type" not in result:
                        result["resource_type"] = "unknown"
                    
                    logger.info(f"Command result: {result}")
                    json_result = format_and_validate_json_response(result)
                    logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
                    return json_result
                except Exception as e:
                    if "unhandled errors in a TaskGroup" in str(e):
                        logger.error(f"TaskGroup error in natural language processing: {e}")
                        error_result = {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {
                                "code": -32603,
                                "message": "Internal error in TaskGroup",
                                "data": {
                                    "error_type": "taskgroup_error",
                                    "original_error": str(e)
                                }
                            }
                        }
                        return format_and_validate_json_response(error_result)
                    raise
            except Exception as e:
                logger.error(f"Error in natural language processing: {e}")
                logger.error(traceback.format_exc())
                raise
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            logger.error(traceback.format_exc())
            error_result = {
                "command": "Error",
                "result": f"Error processing query: {str(e)}",
                "success": False,
                "intent": "error",
                "resource_type": "unknown"
            }
            return format_and_validate_json_response(error_result)
    
    @server.tool("advanced_kubernetes_query")
    @wrap_async_handler
    async def advanced_kubernetes_query(query: str = None, args: List[str] = None, **kwargs):
        """Execute advanced Kubernetes queries."""
        logger.info(f"Received advanced query: {query}")
        logger.info(f"Received args: {args}")
        logger.info(f"Received kwargs: {kwargs}")
        
        if query is None:
            if args and len(args) > 0 and isinstance(args[0], str):
                query = args[0]
                args = args[1:] if len(args) > 1 else []
                logger.info(f"Extracted query from args: {query}")
            elif "query" in kwargs:
                query = kwargs.pop("query")
                logger.info(f"Extracted query from kwargs: {query}")
            else:
                logger.error("No query parameter found in args or kwargs")
                return format_and_validate_json_response({
                    "command": "Error",
                    "result": "Error: No query parameter provided",
                    "success": False,
                    "intent": "error",
                    "resource_type": "unknown"
                })
        
        try:
            result = await asyncio.to_thread(process_advanced_query, query)
            
            if not result:
                result = {
                    "command": "Unknown advanced query",
                    "result": "Could not process advanced query",
                    "success": False,
                    "intent": "unknown",
                    "resource_type": "unknown"
                }
            
            logger.info(f"Advanced query result: {result}")
            json_result = format_and_validate_json_response(result)
            logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
            return json_result
        except Exception as e:
            logger.error(f"Error processing advanced query: {e}")
            logger.error(traceback.format_exc())
            error_result = {
                "command": "Error",
                "result": f"Error processing advanced query: {str(e)}",
                "success": False,
                "intent": "error",
                "resource_type": "unknown"
            }
            return format_and_validate_json_response(error_result)
    
    # Register a ping tool
    @server.tool("kubernetes_ping")
    @wrap_async_handler
    async def kubernetes_ping(query: str = None, args: List[str] = None, **kwargs):
        """Simple ping tool."""
        logger.info(f"Received query: {query}")
        logger.info(f"Received args: {args}")
        logger.info(f"Received kwargs: {kwargs}")
        
        if query is None:
            if args and len(args) > 0 and isinstance(args[0], str):
                query = args[0]
                args = args[1:] if len(args) > 1 else []
                logger.info(f"Extracted query from args: {query}")
            elif "query" in kwargs:
                query = kwargs.pop("query")
                logger.info(f"Extracted query from kwargs: {query}")
        
        
        result = {"status": "connected", "message": "Kubernetes is connected!"}
        if query:
            result["query"] = query
            
        json_result = format_and_validate_json_response(result)
        logger.debug(f"Formatted JSON result: {repr(json_result[:20])}...")
        return json_result
    
    logger.info("Starting MCP server with stdio transport")
    try:
        import signal
        loop = asyncio.get_running_loop()
        
        # Improved signal handling that ensures proper cleanup
        def handle_signal():
            logger.info("Received shutdown signal, cleaning up...")
            # Create task to ensure shutdown is handled properly in event loop
            asyncio.create_task(server.shutdown())
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal)
        
        try:
            from .taskgroup_fix import run_with_taskgroup_protection
            await run_with_taskgroup_protection(server.run_stdio_async())
        except ImportError:
            try:
                from kubectl_mcp_tool.taskgroup_fix import run_with_taskgroup_protection
                await run_with_taskgroup_protection(server.run_stdio_async())
            except ImportError:
                await server.run_stdio_async()
    except asyncio.CancelledError:
        logger.info("Server task was cancelled")
    except BrokenPipeError:
        logger.error("Broken pipe error - client disconnected unexpectedly")
        error_result = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32000,
                "message": "Broken pipe - client disconnected",
                "data": {"error_type": "connection_error"}
            }
        }
        print(format_and_validate_json_response(error_result))
    except ConnectionResetError:
        logger.error("Connection reset by peer")
        error_result = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32000,
                "message": "Connection reset by peer",
                "data": {"error_type": "connection_error"}
            }
        }
        print(format_and_validate_json_response(error_result))
    except Exception as e:
        logger.error(f"Error running server: {e}")
        logger.error(traceback.format_exc())
        
        if "unhandled errors in a TaskGroup" in str(e):
            logger.error("Detected TaskGroup error, providing structured error response")
            error_result = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": "Internal error in TaskGroup",
                    "data": {
                        "error_type": "taskgroup_error",
                        "original_error": str(e)
                    }
                }
            }
            print(format_and_validate_json_response(error_result))
    finally:
        try:
            await server.shutdown()
        except Exception as shutdown_error:
            logger.error(f"Error during shutdown: {shutdown_error}")

def format_and_validate_json_response(result: Dict[str, Any]) -> str:
    """
    Format and validate JSON responses to ensure they are properly
    sanitized and valid for the MCP protocol.
    """
    try:
        # Use the existing format_json_response function
        json_result = format_json_response(result)
        
        # Explicitly validate the JSON
        try:
            json.loads(json_result)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON after formatting: {e}")
            
            # Check for position 4 issues
            if "position 4" in str(e) and len(json_result) > 4:
                logger.warning(f"Position 4 error detected: '{json_result[3]}' (Unicode: U+{ord(json_result[3]):04X})")
                fixed_json = json_result[:3] + json_result[4:]
                try:
                    json.loads(fixed_json)  
                    logger.info("Fixed position 4 error by removing character")
                    json_result = fixed_json
                except json.JSONDecodeError:
                    pass
            
            # If still not valid, create a simple, guaranteed-valid response
            try:
                json.loads(json_result)
            except json.JSONDecodeError:
                logger.error("Creating fallback JSON response")
                fallback = {
                    "command": result.get("command", "kubectl"),
                    "result": str(result.get("result", "Error processing result")),
                    "success": False
                }
                json_result = json.dumps(fallback, ensure_ascii=True, separators=(',', ':'))
        
        return json_result
    except Exception as e:
        logger.error(f"Error formatting JSON response: {e}")
        return json.dumps({
            "command": "Error",
            "result": f"Error formatting response: {str(e)}",
            "success": False
        }, ensure_ascii=True, separators=(',', ':'))

if __name__ == "__main__":
    import asyncio
    import traceback
    
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except BrokenPipeError:
        logger.error("Broken pipe error - client disconnected unexpectedly")
        sys.exit(1)
    except ConnectionResetError:
        logger.error("Connection reset by peer")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running server: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)                                