#!/usr/bin/env python3
"""
Natural language processing for kubectl MCP tool.
"""

import os
import logging
import subprocess
import json
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger("kubectl-nl-processor")

def process_query(query: str) -> Dict[str, Any]:
    """
    Process a natural language query related to kubectl operations.
    
    Args:
        query: The natural language query to process
        
    Returns:
        Dict containing the kubectl command and result
    """
    logger.info(f"Processing query: {query}")
    
    # Check if we're in mock mode (for testing)
    if os.environ.get("MCP_TEST_MOCK_MODE", "0") == "1":
        logger.info("Running in mock mode")
        return _mock_process_query(query)
    
    # Process the query into a kubectl command
    kubectl_cmd = _translate_query_to_kubectl(query)
    
    # Execute the kubectl command
    try:
        logger.info(f"Executing kubectl command: {kubectl_cmd}")
        result = subprocess.run(
            kubectl_cmd, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        # Check if the command was successful
        if result.returncode == 0:
            logger.info("kubectl command successful")
            return {
                "command": kubectl_cmd,
                "result": result.stdout,
                "success": True
            }
        else:
            logger.warning(f"kubectl command failed: {result.stderr}")
            return {
                "command": kubectl_cmd,
                "result": f"Error: {result.stderr}",
                "success": False
            }
    except Exception as e:
        logger.error(f"Error executing kubectl command: {e}")
        return {
            "command": kubectl_cmd,
            "result": f"Error: {str(e)}",
            "success": False
        }

def _translate_query_to_kubectl(query: str) -> str:
    """
    Translate a natural language query to a kubectl command.
    
    This is a simple mapping for testing purposes. A real implementation
    would use NLP techniques or an LLM to generate proper kubectl commands.
    
    Args:
        query: The natural language query
        
    Returns:
        The kubectl command as a string
    """
    query_lower = query.lower().strip()
    
    # Simple mapping of common patterns
    if "get pods" in query_lower or "list pods" in query_lower or "show pods" in query_lower:
        if "namespace" in query_lower and "all" not in query_lower:
            # Try to extract namespace
            parts = query_lower.split("namespace")
            if len(parts) > 1:
                namespace = parts[1].strip().split()[0]
                return f"kubectl get pods -n {namespace}"
        return "kubectl get pods"
    
    elif "get deployments" in query_lower or "list deployments" in query_lower:
        return "kubectl get deployments"
    
    elif "get services" in query_lower or "list services" in query_lower:
        return "kubectl get services"
    
    elif "get nodes" in query_lower or "list nodes" in query_lower:
        return "kubectl get nodes"
    
    elif "get namespaces" in query_lower or "list namespaces" in query_lower:
        return "kubectl get namespaces"
    
    elif "describe pod" in query_lower:
        # Try to extract pod name
        parts = query_lower.split("describe pod")
        if len(parts) > 1:
            pod_name = parts[1].strip().split()[0]
            return f"kubectl describe pod {pod_name}"
        return "kubectl get pods"
    
    elif "current namespace" in query_lower or "which namespace" in query_lower:
        return "kubectl config view --minify --output 'jsonpath={..namespace}'"
    
    # If no pattern matches, return a generic command or help
    return "kubectl get all"

def _mock_process_query(query: str) -> Dict[str, Any]:
    """
    Process a query in mock mode for testing.
    
    Args:
        query: The natural language query
        
    Returns:
        Dict containing mock response data
    """
    kubectl_cmd = _translate_query_to_kubectl(query)
    
    # Return mock data based on command
    if "get pods" in kubectl_cmd:
        return {
            "command": kubectl_cmd,
            "result": """NAME                                READY   STATUS    RESTARTS   AGE
nginx-deployment-66b6c48dd5-4nsjt   1/1     Running   0          24h
nginx-deployment-66b6c48dd5-87vpb   1/1     Running   0          24h
nginx-deployment-66b6c48dd5-f4m7b   1/1     Running   0          24h""",
            "success": True
        }
    
    elif "get deployments" in kubectl_cmd:
        return {
            "command": kubectl_cmd,
            "result": """NAME               READY   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment   3/3     3            3           24h""",
            "success": True
        }
    
    elif "get services" in kubectl_cmd:
        return {
            "command": kubectl_cmd,
            "result": """NAME         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
kubernetes   ClusterIP   10.96.0.1       <none>        443/TCP   48h""",
            "success": True
        }
    
    elif "get nodes" in kubectl_cmd:
        return {
            "command": kubectl_cmd,
            "result": """NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   48h   v1.29.1""",
            "success": True
        }
    
    elif "get namespaces" in kubectl_cmd:
        return {
            "command": kubectl_cmd,
            "result": """NAME              STATUS   AGE
default           Active   48h
kube-node-lease   Active   48h
kube-public       Active   48h
kube-system       Active   48h""",
            "success": True
        }
    
    else:
        return {
            "command": kubectl_cmd,
            "result": "Mock data not available for this command",
            "success": True
        }
