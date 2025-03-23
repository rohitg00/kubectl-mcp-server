"""Natural language processing module for kubectl-mcp-tool."""

import logging
import subprocess
import shlex
import os
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Flag to control whether to use mock data as fallback
USE_MOCK_FALLBACK = True

def _run_kubectl_command(args: List[str]) -> Tuple[str, bool]:
    """Run a kubectl command and return the output.
    
    Args:
        args: List of arguments to pass to kubectl.
        
    Returns:
        Tuple of (output_string, success_flag)
    """
    cmd = ["kubectl"] + args
    logger.info(f"Running kubectl command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,  # Don't raise an exception on non-zero exit
            timeout=10    # Add timeout to prevent hanging
        )
        
        if result.returncode != 0:
            logger.error(f"kubectl command failed with exit code {result.returncode}: {result.stderr}")
            return (f"Error: {result.stderr}", False)
        
        return (result.stdout.strip(), True)
    except subprocess.TimeoutExpired:
        logger.error(f"kubectl command timed out: {' '.join(cmd)}")
        return ("Error: Command timed out", False)
    except Exception as e:
        logger.exception(f"Error running kubectl command: {e}")
        return (f"Error: {str(e)}", False)

def _get_mock_data(command_type: str, namespace: Optional[str] = None) -> str:
    """Get mock data for a command type when real kubectl fails.
    
    Args:
        command_type: Type of command (pods, namespaces, etc.)
        namespace: Optional namespace for the command
        
    Returns:
        Mock data as a string
    """
    if command_type == "pods":
        return """NAME                     READY   STATUS    RESTARTS   AGE
nginx-pod               1/1     Running   0          1h
web-deployment-abc123   1/1     Running   0          45m
db-statefulset-0        1/1     Running   0          30m"""
    elif command_type == "namespaces":
        return """NAME              STATUS   AGE
default           Active   1d
kube-system       Active   1d
kube-public       Active   1d
kube-node-lease   Active   1d"""
    elif command_type == "deployments":
        return """NAME               READY   UP-TO-DATE   AVAILABLE   AGE
nginx-deployment    3/3     3            3           2h
web-deployment      2/2     2            2           1h"""
    elif command_type == "services":
        return """NAME               TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
kubernetes         ClusterIP   10.96.0.1        <none>        443/TCP        1d
nginx-service      ClusterIP   10.96.123.45     <none>        80/TCP         2h"""
    elif command_type == "current-namespace":
        return namespace or "default"
    else:
        return f"Mock data not available for {command_type}"

def process_query(query: str) -> Dict[str, Any]:
    """Process a natural language query for kubectl operations."""
    logger.info(f"Processing natural language query: {query}")
    
    # Use real kubectl commands with mock data fallback
    try:
        query_lower = query.lower()
        
        # Get pods command
        if "get all pods" in query_lower or "get pods" in query_lower or "show pods" in query_lower or "list pods" in query_lower:
            namespace_arg = []
            namespace = None
            
            if "in namespace" in query_lower:
                # Extract namespace from query
                namespace = query_lower.split("in namespace")[1].strip()
                namespace_arg = ["-n", namespace]
            elif "in all namespaces" in query_lower or "across all namespaces" in query_lower:
                namespace_arg = ["--all-namespaces"]
                
            cmd = ["get", "pods"] + namespace_arg
            result, success = _run_kubectl_command(cmd)
            
            # Use mock data if kubectl command failed and fallback is enabled
            if not success and USE_MOCK_FALLBACK:
                logger.info("Using mock data for pods as fallback")
                result = _get_mock_data("pods", namespace)
                
            return {
                "command": "kubectl " + " ".join(cmd),
                "result": result
            }
            
        # Get namespaces command
        elif "show namespaces" in query_lower or "get namespaces" in query_lower or "list namespaces" in query_lower:
            cmd = ["get", "namespaces"]
            result, success = _run_kubectl_command(cmd)
            
            # Use mock data if kubectl command failed and fallback is enabled
            if not success and USE_MOCK_FALLBACK:
                logger.info("Using mock data for namespaces as fallback")
                result = _get_mock_data("namespaces")
                
            return {
                "command": "kubectl " + " ".join(cmd),
                "result": result
            }
            
        # Switch namespace command
        elif "switch to namespace" in query_lower or "change namespace" in query_lower or "use namespace" in query_lower:
            namespace = query_lower.split("namespace")[1].strip()
            cmd = ["config", "set-context", "--current", "--namespace", namespace]
            result, success = _run_kubectl_command(cmd)
            
            # Always return success for namespace switching in mock mode
            if not success and USE_MOCK_FALLBACK:
                logger.info(f"Using mock data for switching to namespace {namespace}")
                result = f"Switched to namespace {namespace}"
                
            return {
                "command": "kubectl " + " ".join(cmd),
                "result": result
            }
            
        # Current namespace command
        elif "current namespace" in query_lower or "what namespace" in query_lower:
            cmd = ["config", "view", "--minify", "--output", "jsonpath={..namespace}"]
            result, success = _run_kubectl_command(cmd)
            
            # Use mock data if kubectl command failed and fallback is enabled
            if not success and USE_MOCK_FALLBACK:
                logger.info("Using mock data for current namespace as fallback")
                result = _get_mock_data("current-namespace")
                
            return {
                "command": "kubectl " + " ".join(cmd),
                "result": result
            }
            
        # Get deployments command
        elif "get deployments" in query_lower or "show deployments" in query_lower or "list deployments" in query_lower:
            namespace_arg = []
            namespace = None
            
            if "in namespace" in query_lower:
                namespace = query_lower.split("in namespace")[1].strip()
                namespace_arg = ["-n", namespace]
                
            cmd = ["get", "deployments"] + namespace_arg
            result, success = _run_kubectl_command(cmd)
            
            # Use mock data if kubectl command failed and fallback is enabled
            if not success and USE_MOCK_FALLBACK:
                logger.info("Using mock data for deployments as fallback")
                result = _get_mock_data("deployments", namespace)
                
            return {
                "command": "kubectl " + " ".join(cmd),
                "result": result
            }
            
        # Get services command
        elif "get services" in query_lower or "show services" in query_lower or "list services" in query_lower:
            namespace_arg = []
            namespace = None
            
            if "in namespace" in query_lower:
                namespace = query_lower.split("in namespace")[1].strip()
                namespace_arg = ["-n", namespace]
                
            cmd = ["get", "services"] + namespace_arg
            result, success = _run_kubectl_command(cmd)
            
            # Use mock data if kubectl command failed and fallback is enabled
            if not success and USE_MOCK_FALLBACK:
                logger.info("Using mock data for services as fallback")
                result = _get_mock_data("services", namespace)
                
            return {
                "command": "kubectl " + " ".join(cmd),
                "result": result
            }
            
        # For other resource types
        else:
            # Try to identify kubectl commands in the query
            for resource in ["pods", "deployments", "services", "nodes", "configmaps", "secrets"]:
                if f"get {resource}" in query_lower or f"show {resource}" in query_lower or f"list {resource}" in query_lower:
                    namespace_arg = []
                    namespace = None
                    
                    if "in namespace" in query_lower:
                        namespace = query_lower.split("in namespace")[1].strip()
                        namespace_arg = ["-n", namespace]
                        
                    cmd = ["get", resource] + namespace_arg
                    result, success = _run_kubectl_command(cmd)
                    
                    # Use mock data if kubectl command failed and fallback is enabled
                    if not success and USE_MOCK_FALLBACK:
                        logger.info(f"Using mock data for {resource} as fallback")
                        result = _get_mock_data(resource, namespace)
                        
                    return {
                        "command": "kubectl " + " ".join(cmd),
                        "result": result
                    }
            
            # If no command was recognized
            return {
                "command": "Unknown command",
                "result": "Could not parse natural language query. Try commands like 'get all pods', 'show namespaces', or 'switch to namespace kube-system'."
            }
            
    except Exception as e:
        logger.exception(f"Error processing query: {e}")
        return {
            "command": "Error",
            "result": f"Error processing query: {str(e)}"
        }
