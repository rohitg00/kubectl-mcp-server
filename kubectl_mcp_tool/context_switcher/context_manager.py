#!/usr/bin/env python3
"""
Context manager module for kubectl-mcp-tool.
"""

import json
import logging
import subprocess
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="context_manager.log"
)
logger = logging.getLogger("context-manager")

class ContextManager:
    """Class for managing Kubernetes contexts."""
    
    def __init__(self):
        """Initialize the ContextManager class."""
        logger.info("ContextManager initialized")
    
    def get_contexts(self) -> List[str]:
        """
        Get available Kubernetes contexts.
        
        Returns:
            List of available contexts
        """
        try:
            # Try using kubectx
            result = subprocess.run(
                ["kubectx"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Parse kubectx output
                contexts = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                return contexts
            
            # Fallback to kubectl if kubectx fails
            result = subprocess.run(
                ["kubectl", "config", "get-contexts", "-o", "name"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                # Parse kubectl output
                contexts = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                return contexts
            
            logger.error(f"Error getting contexts: {result.stderr}")
            return []
        except Exception as e:
            logger.error(f"Error getting contexts: {e}")
            return []
    
    def get_current_context(self) -> Dict[str, Any]:
        """
        Get the current Kubernetes context.
        
        Returns:
            Dictionary containing the current context information
        """
        try:
            result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": "kubectl config current-context",
                    "result": result.stdout.strip()
                }
            
            logger.error(f"Error getting current context: {result.stderr}")
            return {
                "success": False,
                "command": "kubectl config current-context",
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error getting current context: {e}")
            return {
                "success": False,
                "command": "kubectl config current-context",
                "error": str(e)
            }
    
    def switch_context(self, context_name: str) -> Dict[str, Any]:
        """
        Switch to the specified Kubernetes context.
        
        Args:
            context_name: Name of the context to switch to
        
        Returns:
            Dictionary containing the result of the operation
        """
        try:
            # Try using kubectx
            result = subprocess.run(
                ["kubectx", context_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": f"kubectx {context_name}",
                    "result": result.stdout.strip()
                }
            
            # Fallback to kubectl if kubectx fails
            result = subprocess.run(
                ["kubectl", "config", "use-context", context_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": f"kubectl config use-context {context_name}",
                    "result": result.stdout.strip()
                }
            
            return {
                "success": False,
                "command": f"kubectx {context_name}",
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error switching context: {e}")
            return {
                "success": False,
                "command": f"kubectx {context_name}",
                "error": str(e)
            }
    
    def get_context_details(self, context_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get details of a Kubernetes context.
        
        Args:
            context_name: Name of the context (optional, defaults to current context)
        
        Returns:
            Dictionary containing context details
        """
        try:
            cmd = ["kubectl", "config", "get-contexts"]
            
            if context_name:
                cmd.append(context_name)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": " ".join(cmd),
                    "result": result.stdout.strip()
                }
            
            return {
                "success": False,
                "command": " ".join(cmd),
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error getting context details: {e}")
            return {
                "success": False,
                "command": " ".join(["kubectl", "config", "get-contexts", context_name or ""]),
                "error": str(e)
            }
    
    def create_context(self, context_name: str, cluster: str, user: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new Kubernetes context.
        
        Args:
            context_name: Name of the context to create
            cluster: Name of the cluster
            user: Name of the user
            namespace: Namespace (optional)
        
        Returns:
            Dictionary containing the result of the operation
        """
        try:
            cmd = ["kubectl", "config", "set-context", context_name, f"--cluster={cluster}", f"--user={user}"]
            
            if namespace:
                cmd.append(f"--namespace={namespace}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": " ".join(cmd),
                    "result": result.stdout.strip()
                }
            
            return {
                "success": False,
                "command": " ".join(cmd),
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error creating context: {e}")
            return {
                "success": False,
                "command": " ".join(["kubectl", "config", "set-context", context_name, f"--cluster={cluster}", f"--user={user}", namespace and f"--namespace={namespace}" or ""]),
                "error": str(e)
            }
    
    def delete_context(self, context_name: str) -> Dict[str, Any]:
        """
        Delete a Kubernetes context.
        
        Args:
            context_name: Name of the context to delete
        
        Returns:
            Dictionary containing the result of the operation
        """
        try:
            result = subprocess.run(
                ["kubectl", "config", "delete-context", context_name],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "command": f"kubectl config delete-context {context_name}",
                    "result": result.stdout.strip()
                }
            
            return {
                "success": False,
                "command": f"kubectl config delete-context {context_name}",
                "error": result.stderr.strip()
            }
        except Exception as e:
            logger.error(f"Error deleting context: {e}")
            return {
                "success": False,
                "command": f"kubectl config delete-context {context_name}",
                "error": str(e)
            }
