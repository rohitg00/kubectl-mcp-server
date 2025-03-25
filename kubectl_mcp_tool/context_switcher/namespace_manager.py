#!/usr/bin/env python3
"""
Namespace manager module for kubectl-mcp-tool.
"""

import json
import logging
import subprocess
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="namespace_manager.log"
)
logger = logging.getLogger("namespace-manager")

class NamespaceManager:
    """Class for managing Kubernetes namespaces."""
    
    def __init__(self):
        """Initialize the NamespaceManager class."""
        logger.info("NamespaceManager initialized")
    
    def get_namespaces(self) -> Dict[str, Any]:
        """
        Get available Kubernetes namespaces.
        
        Returns:
            Dictionary containing namespaces
        """
        try:
            # Try using kubens
            result = subprocess.run(
                ["kubens"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Parse kubens output
                namespaces = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                return {
                    "success": True,
                    "command": "kubens",
                    "result": namespaces
                }
            
            # Fallback to kubectl if kubens fails
            result = subprocess.run(
                ["kubectl", "get", "namespaces", "-o", "name"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Parse kubectl output and remove "namespace/" prefix
                namespaces = [line.strip().replace("namespace/", "") for line in result.stdout.strip().split('\n') if line.strip()]
                return {
                    "success": True,
                    "command": "kubectl get namespaces -o name",
                    "result": namespaces
                }
            
            return {
                "success": False,
                "command": "kubectl get namespaces -o name",
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error getting namespaces: {e}")
            return {
                "success": False,
                "command": "kubectl get namespaces -o name",
                "error": str(e)
            }
    
    def get_current_namespace(self, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current Kubernetes namespace.
        
        Args:
            context: Context name (optional, defaults to current context)
        
        Returns:
            Dictionary containing the current namespace
        """
        try:
            cmd = ["kubectl", "config", "view", "--minify", "-o", "jsonpath={..namespace}"]
            
            if context:
                cmd.extend(["--context", context])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                namespace = result.stdout.strip()
                
                if not namespace:
                    namespace = "default"
                
                return {
                    "success": True,
                    "command": " ".join(cmd),
                    "result": namespace
                }
            
            return {
                "success": False,
                "command": " ".join(cmd),
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error getting current namespace: {e}")
            return {
                "success": False,
                "command": " ".join(["kubectl", "config", "view", "--minify", "-o", "jsonpath={..namespace}"]),
                "error": str(e)
            }
    
    def switch_namespace(self, namespace: str) -> Dict[str, Any]:
        """
        Switch to the specified Kubernetes namespace.
        
        Args:
            namespace: Name of the namespace to switch to
        
        Returns:
            Dictionary containing the result of the operation
        """
        try:
            # Try using kubens
            result = subprocess.run(
                ["kubens", namespace],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": f"kubens {namespace}",
                    "result": result.stdout.strip()
                }
            
            # Fallback to kubectl if kubens fails
            result = subprocess.run(
                ["kubectl", "config", "set-context", "--current", f"--namespace={namespace}"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": f"kubectl config set-context --current --namespace={namespace}",
                    "result": result.stdout.strip()
                }
            
            return {
                "success": False,
                "command": f"kubens {namespace}",
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error switching namespace: {e}")
            return {
                "success": False,
                "command": f"kubens {namespace}",
                "error": str(e)
            }
    
    def create_namespace(self, namespace: str) -> Dict[str, Any]:
        """
        Create a new Kubernetes namespace.
        
        Args:
            namespace: Name of the namespace to create
        
        Returns:
            Dictionary containing the result of the operation
        """
        try:
            result = subprocess.run(
                ["kubectl", "create", "namespace", namespace],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": f"kubectl create namespace {namespace}",
                    "result": result.stdout.strip()
                }
            
            return {
                "success": False,
                "command": f"kubectl create namespace {namespace}",
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error creating namespace: {e}")
            return {
                "success": False,
                "command": f"kubectl create namespace {namespace}",
                "error": str(e)
            }
    
    def delete_namespace(self, namespace: str) -> Dict[str, Any]:
        """
        Delete a Kubernetes namespace.
        
        Args:
            namespace: Name of the namespace to delete
        
        Returns:
            Dictionary containing the result of the operation
        """
        try:
            result = subprocess.run(
                ["kubectl", "delete", "namespace", namespace],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": f"kubectl delete namespace {namespace}",
                    "result": result.stdout.strip()
                }
            
            return {
                "success": False,
                "command": f"kubectl delete namespace {namespace}",
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error deleting namespace: {e}")
            return {
                "success": False,
                "command": f"kubectl delete namespace {namespace}",
                "error": str(e)
            }
    
    def get_namespace_details(self, namespace: str) -> Dict[str, Any]:
        """
        Get details of a Kubernetes namespace.
        
        Args:
            namespace: Name of the namespace
        
        Returns:
            Dictionary containing namespace details
        """
        try:
            result = subprocess.run(
                ["kubectl", "describe", "namespace", namespace],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": f"kubectl describe namespace {namespace}",
                    "result": result.stdout.strip()
                }
            
            return {
                "success": False,
                "command": f"kubectl describe namespace {namespace}",
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error getting namespace details: {e}")
            return {
                "success": False,
                "command": f"kubectl describe namespace {namespace}",
                "error": str(e)
            }
