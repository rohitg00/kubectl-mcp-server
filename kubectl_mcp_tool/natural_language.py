#!/usr/bin/env python3
"""
Natural language processing module for kubectl-mcp-tool.

This module provides functions for processing natural language queries
and converting them to kubectl commands.
"""

import logging
import re
import subprocess
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("natural-language")

def process_query(query: str) -> Dict[str, Any]:
    """
    Process a natural language query and convert it to a kubectl command.
    
    Args:
        query: Natural language query for kubectl operations
    
    Returns:
        Dictionary containing the command and result
    """
    logger.info(f"Processing query: {query}")
    
    # Normalize query
    query = query.lower().strip()
    
    # Extract command type and parameters
    command, params = extract_command_and_params(query)
    
    # Build kubectl command
    kubectl_cmd = build_kubectl_command(command, params)
    
    # Execute kubectl command
    result = execute_kubectl_command(kubectl_cmd)
    
    return {
        "command": kubectl_cmd,
        "result": result
    }

def extract_command_and_params(query: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract command type and parameters from a natural language query.
    
    Args:
        query: Natural language query
    
    Returns:
        Tuple of (command, params)
    """
    params = {}
    
    # Extract namespace
    namespace_match = re.search(r'(in|from) namespace (\w+)', query)
    if namespace_match:
        params['namespace'] = namespace_match.group(2)
    
    # Extract resource type
    resource_types = {
        'pod': ['pod', 'pods'],
        'deployment': ['deployment', 'deployments'],
        'service': ['service', 'services', 'svc'],
        'namespace': ['namespace', 'namespaces', 'ns'],
        'node': ['node', 'nodes'],
        'configmap': ['configmap', 'configmaps', 'cm'],
        'secret': ['secret', 'secrets'],
        'ingress': ['ingress', 'ingresses'],
        'persistentvolume': ['persistentvolume', 'persistentvolumes', 'pv'],
        'persistentvolumeclaim': ['persistentvolumeclaim', 'persistentvolumeclaims', 'pvc'],
    }
    
    for resource_type, aliases in resource_types.items():
        for alias in aliases:
            if alias in query:
                params['resource_type'] = resource_type
                break
        if 'resource_type' in params:
            break
    
    # Extract resource name
    if 'resource_type' in params:
        name_match = re.search(fr'{params["resource_type"]} (\w+[-\w]*)', query)
        if name_match:
            params['name'] = name_match.group(1)
    
    # Extract number of replicas for scaling
    if 'scale' in query:
        replicas_match = re.search(r'to (\d+) replicas', query)
        if replicas_match:
            params['replicas'] = replicas_match.group(1)
    
    # Extract container name for logs
    if 'container' in query:
        container_match = re.search(r'container (\w+)', query)
        if container_match:
            params['container'] = container_match.group(1)
    
    # Determine command type
    command = 'get'  # Default command
    
    if any(word in query for word in ['get', 'show', 'list', 'display']):
        command = 'get'
    elif any(word in query for word in ['describe', 'details', 'information about']):
        command = 'describe'
    elif any(word in query for word in ['create', 'add', 'new']):
        command = 'create'
    elif any(word in query for word in ['delete', 'remove']):
        command = 'delete'
    elif any(word in query for word in ['apply', 'update']):
        command = 'apply'
    elif any(word in query for word in ['scale']):
        command = 'scale'
    elif any(word in query for word in ['logs', 'log']):
        command = 'logs'
    elif any(word in query for word in ['exec', 'execute', 'run']):
        command = 'exec'
    elif any(word in query for word in ['port-forward', 'forward']):
        command = 'port-forward'
    elif any(word in query for word in ['switch', 'use', 'change']):
        if 'namespace' in params:
            command = 'switch-namespace'
        elif 'context' in query:
            command = 'switch-context'
    
    return command, params

def build_kubectl_command(command: str, params: Dict[str, str]) -> str:
    """
    Build a kubectl command from command type and parameters.
    
    Args:
        command: Command type
        params: Command parameters
    
    Returns:
        kubectl command string
    """
    if command == 'switch-namespace':
        return f"kubectl config set-context --current --namespace={params.get('namespace', 'default')}"
    
    if command == 'switch-context':
        return f"kubectl config use-context {params.get('context', '')}"
    
    kubectl_cmd = ["kubectl", command]
    
    if command == 'scale':
        kubectl_cmd = ["kubectl", "scale", f"deployment/{params.get('name', '')}"]
        if 'replicas' in params:
            kubectl_cmd.append(f"--replicas={params['replicas']}")
    else:
        if 'resource_type' in params:
            kubectl_cmd.append(params['resource_type'])
        
        if 'name' in params and command not in ['create', 'apply']:
            kubectl_cmd.append(params['name'])
    
    if 'namespace' in params and command != 'switch-namespace':
        kubectl_cmd.append(f"--namespace={params['namespace']}")
    
    if command == 'logs' and 'container' in params:
        kubectl_cmd.append(f"--container={params['container']}")
    
    return " ".join(kubectl_cmd)

def execute_kubectl_command(command: str) -> str:
    """
    Execute a kubectl command and return the result.
    
    Args:
        command: kubectl command to execute
    
    Returns:
        Command output
    """
    logger.info(f"Executing command: {command}")
    
    try:
        # Check if kubectl is available
        try:
            subprocess.run(["kubectl", "version", "--client"], 
                          check=True, 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("kubectl not available, returning mock data")
            return f"Mock result for: {command}\n(kubectl not available)"
        
        # Execute the command
        result = subprocess.run(command.split(), 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        
        if result.returncode == 0:
            return result.stdout
        else:
            logger.error(f"Command failed: {result.stderr}")
            return f"Error: {result.stderr}"
    
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        return f"Error: {str(e)}"
