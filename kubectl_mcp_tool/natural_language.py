#!/usr/bin/env python3
"""
Natural language processing for kubectl.
This module parses natural language queries and converts them to kubectl commands.
"""

import re
import subprocess
import logging
import os
import json
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("natural-language")

def process_query(query: str) -> Dict[str, Any]:
    """
    Process a natural language query and convert it to a kubectl command.
    
    Args:
        query: The natural language query to process
        
    Returns:
        A dictionary containing the kubectl command and its output
    """
    try:
        # Try to parse the query and generate a kubectl command
        command = parse_query(query)
        
        # Log the generated command
        logger.info(f"Generated kubectl command: {command}")
        
        # Execute the command
        try:
            result = execute_command(command)
            success = True
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            result = f"Error executing command: {str(e)}"
            success = False
        
        # Return the result
        return {
            "command": command,
            "result": result,
            "success": success
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return {
            "command": "",
            "result": f"Error processing query: {str(e)}",
            "success": False
        }

def parse_query(query: str) -> str:
    """
    Parse a natural language query and convert it to a kubectl command.
    
    Args:
        query: The natural language query to parse
        
    Returns:
        The kubectl command to execute
    """
    # Normalize the query
    query = query.lower().strip()
    
    # Check for keyword patterns
    if re.search(r"get\s+pod", query) or re.search(r"list\s+pod", query):
        namespace = extract_namespace(query)
        if namespace:
            return f"kubectl get pods -n {namespace}"
        else:
            return "kubectl get pods"
    
    if re.search(r"get\s+all", query) or re.search(r"list\s+all", query):
        namespace = extract_namespace(query)
        if namespace:
            return f"kubectl get all -n {namespace}"
        else:
            return "kubectl get all"
    
    if re.search(r"get\s+deployment", query) or re.search(r"list\s+deployment", query):
        namespace = extract_namespace(query)
        if namespace:
            return f"kubectl get deployments -n {namespace}"
        else:
            return "kubectl get deployments"
    
    if re.search(r"get\s+service", query) or re.search(r"list\s+service", query):
        namespace = extract_namespace(query)
        if namespace:
            return f"kubectl get services -n {namespace}"
        else:
            return "kubectl get services"
    
    if re.search(r"describe\s+pod", query):
        pod_name = extract_pod_name(query)
        namespace = extract_namespace(query)
        if pod_name and namespace:
            return f"kubectl describe pod {pod_name} -n {namespace}"
        elif pod_name:
            return f"kubectl describe pod {pod_name}"
        else:
            return "kubectl get pods"
    
    if re.search(r"get\s+log", query) or re.search(r"show\s+log", query):
        pod_name = extract_pod_name(query)
        namespace = extract_namespace(query)
        if pod_name and namespace:
            return f"kubectl logs {pod_name} -n {namespace}"
        elif pod_name:
            return f"kubectl logs {pod_name}"
        else:
            return "kubectl get pods"
    
    if re.search(r"delete\s+pod", query):
        pod_name = extract_pod_name(query)
        namespace = extract_namespace(query)
        if pod_name and namespace:
            return f"kubectl delete pod {pod_name} -n {namespace}"
        elif pod_name:
            return f"kubectl delete pod {pod_name}"
        else:
            return "kubectl get pods"
    
    # Default: just do a get all
    return "kubectl get all"

def extract_namespace(query: str) -> Optional[str]:
    """
    Extract namespace from a query.
    
    Args:
        query: The query to extract the namespace from
        
    Returns:
        The namespace or None if not found
    """
    namespace_match = re.search(r"(?:in|from|namespace|ns)\s+(\w+)", query)
    if namespace_match:
        return namespace_match.group(1)
    return None

def extract_pod_name(query: str) -> Optional[str]:
    """
    Extract pod name from a query.
    
    Args:
        query: The query to extract the pod name from
        
    Returns:
        The pod name or None if not found
    """
    pod_match = re.search(r"pod\s+(\w+[\w\-]*)", query)
    if pod_match:
        return pod_match.group(1)
    return None

def execute_command(command: str) -> str:
    """
    Execute a kubectl command and return the output.
    
    Args:
        command: The kubectl command to execute
        
    Returns:
        The command output
    """
    try:
        # For enhanced safety, handle the case where kubeconfig doesn't exist
        kubeconfig = os.environ.get('KUBECONFIG', os.path.expanduser('~/.kube/config'))
        if not os.path.exists(kubeconfig):
            logger.warning(f"Kubeconfig not found at {kubeconfig}")
            return f"Warning: Kubernetes config not found at {kubeconfig}. Please configure kubectl."
        
        # Try to run the command with a timeout for safety
        result = subprocess.run(
            command,
            shell=True,
            check=False,  # Don't raise exception on non-zero exit
            capture_output=True,
            text=True,
            timeout=10  # Timeout after 10 seconds
        )
        
        # Check for errors
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.warning(f"Command failed with exit code {result.returncode}: {error_msg}")
            return f"Command failed: {error_msg}\n\nCommand: {command}"
        
        return result.stdout if result.stdout else "Command completed successfully with no output"
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return "Command timed out after 10 seconds"
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return f"Error: {str(e)}"
