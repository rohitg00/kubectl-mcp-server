#!/usr/bin/env python3
"""
Kubernetes operations module for kubectl-mcp-tool.

This module provides direct kubectl command execution for Kubernetes operations.
"""

import json
import logging
import subprocess
from typing import Dict, Any, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("kubernetes-ops")

class KubernetesOperations:
    """Class for executing kubectl operations."""
    
    def __init__(self):
        """Initialize the KubernetesOperations class."""
        self._check_kubectl()
        logger.info("KubernetesOperations initialized")
    
    def _check_kubectl(self) -> None:
        """Check if kubectl is installed and accessible."""
        try:
            result = subprocess.run(
                ["kubectl", "version", "--client", "-o", "json"],
                capture_output=True,
                text=True,
                check=True
            )
            version_info = json.loads(result.stdout)
            logger.info(f"kubectl client version: {version_info.get('clientVersion', {}).get('gitVersion', 'unknown')}")
        except subprocess.CalledProcessError as e:
            logger.error(f"kubectl command failed: {e}")
            raise RuntimeError("kubectl is not installed or not accessible")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse kubectl version output: {e}")
            raise RuntimeError("Failed to parse kubectl version output")
    
    def execute_command(self, command: List[str]) -> Tuple[bool, str]:
        """
        Execute a kubectl command.
        
        Args:
            command: List of command arguments to pass to kubectl
        
        Returns:
            Tuple of (success, output)
        """
        full_command = ["kubectl"] + command
        logger.debug(f"Executing kubectl command: {' '.join(full_command)}")
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                check=False  # Don't raise an exception on non-zero exit code
            )
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                logger.error(f"kubectl command failed: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            logger.error(f"Error executing kubectl command: {e}")
            return False, str(e)
    
    def get_pods(self, namespace: str = "default") -> Dict[str, Any]:
        """
        Get pods in the specified namespace.
        
        Args:
            namespace: Namespace to get pods from
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["get", "pods", "-n", namespace, "-o", "json"])
        
        if success:
            try:
                pods = json.loads(output)
                return {
                    "command": f"kubectl get pods -n {namespace}",
                    "result": pods,
                    "success": True
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse kubectl output: {e}")
                return {
                    "command": f"kubectl get pods -n {namespace}",
                    "result": output,
                    "success": False,
                    "error": f"Failed to parse kubectl output: {e}"
                }
        else:
            return {
                "command": f"kubectl get pods -n {namespace}",
                "result": output,
                "success": False,
                "error": "Command failed"
            }
    
    def get_namespaces(self) -> Dict[str, Any]:
        """
        Get all namespaces.
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["get", "namespaces", "-o", "json"])
        
        if success:
            try:
                namespaces = json.loads(output)
                return {
                    "command": "kubectl get namespaces",
                    "result": namespaces,
                    "success": True
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse kubectl output: {e}")
                return {
                    "command": "kubectl get namespaces",
                    "result": output,
                    "success": False,
                    "error": f"Failed to parse kubectl output: {e}"
                }
        else:
            return {
                "command": "kubectl get namespaces",
                "result": output,
                "success": False,
                "error": "Command failed"
            }
    
    def switch_namespace(self, namespace: str) -> Dict[str, Any]:
        """
        Switch to the specified namespace.
        
        Args:
            namespace: Namespace to switch to
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["config", "set-context", "--current", "--namespace", namespace])
        
        return {
            "command": f"kubectl config set-context --current --namespace {namespace}",
            "result": output,
            "success": success,
            "error": None if success else "Command failed"
        }
    
    def get_current_namespace(self) -> Dict[str, Any]:
        """
        Get the current namespace.
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["config", "view", "--minify", "-o", "jsonpath={..namespace}"])
        
        return {
            "command": "kubectl config view --minify -o jsonpath={..namespace}",
            "result": output.strip() or "default",
            "success": success,
            "error": None if success else "Command failed"
        }
    
    def get_deployments(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get deployments in the specified namespace.
        
        Args:
            namespace: Namespace to get deployments from
        
        Returns:
            Dictionary containing the command and result
        """
        command = ["get", "deployments"]
        
        if namespace:
            command.extend(["-n", namespace])
        
        command.extend(["-o", "json"])
        
        success, output = self.execute_command(command)
        
        if success:
            try:
                deployments = json.loads(output)
                return {
                    "command": f"kubectl get deployments{f' -n {namespace}' if namespace else ''}",
                    "result": deployments,
                    "success": True
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse kubectl output: {e}")
                return {
                    "command": f"kubectl get deployments{f' -n {namespace}' if namespace else ''}",
                    "result": output,
                    "success": False,
                    "error": f"Failed to parse kubectl output: {e}"
                }
        else:
            return {
                "command": f"kubectl get deployments{f' -n {namespace}' if namespace else ''}",
                "result": output,
                "success": False,
                "error": "Command failed"
            }
    
    def scale_deployment(self, deployment: str, replicas: int, namespace: str = "default") -> Dict[str, Any]:
        """
        Scale a deployment to the specified number of replicas.
        
        Args:
            deployment: Name of the deployment to scale
            replicas: Number of replicas to scale to
            namespace: Namespace of the deployment
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["scale", "deployment", deployment, f"--replicas={replicas}", "-n", namespace])
        
        return {
            "command": f"kubectl scale deployment {deployment} --replicas={replicas} -n {namespace}",
            "result": output,
            "success": success,
            "error": None if success else "Command failed"
        }
    
    def describe_pod(self, pod: str, namespace: str = "default") -> Dict[str, Any]:
        """
        Describe a pod in the specified namespace.
        
        Args:
            pod: Name of the pod to describe
            namespace: Namespace of the pod
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["describe", "pod", pod, "-n", namespace])
        
        return {
            "command": f"kubectl describe pod {pod} -n {namespace}",
            "result": output,
            "success": success,
            "error": None if success else "Command failed"
        }
    
    def get_logs(self, pod: str, namespace: str = "default", container: Optional[str] = None) -> Dict[str, Any]:
        """
        Get logs from a pod in the specified namespace.
        
        Args:
            pod: Name of the pod to get logs from
            namespace: Namespace of the pod
            container: Container to get logs from (optional)
        
        Returns:
            Dictionary containing the command and result
        """
        command = ["logs", pod, "-n", namespace]
        
        if container:
            command.extend(["-c", container])
        
        success, output = self.execute_command(command)
        
        return {
            "command": f"kubectl logs {pod} -n {namespace}{f' -c {container}' if container else ''}",
            "result": output,
            "success": success,
            "error": None if success else "Command failed"
        }
    
    def create_from_yaml(self, yaml_file: str) -> Dict[str, Any]:
        """
        Create resources from a YAML file.
        
        Args:
            yaml_file: Path to the YAML file
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["apply", "-f", yaml_file])
        
        return {
            "command": f"kubectl apply -f {yaml_file}",
            "result": output,
            "success": success,
            "error": None if success else "Command failed"
        }
    
    def delete_resource(self, resource_type: str, resource_name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a resource.
        
        Args:
            resource_type: Type of resource to delete
            resource_name: Name of the resource to delete
            namespace: Namespace of the resource
        
        Returns:
            Dictionary containing the command and result
        """
        command = ["delete", resource_type, resource_name]
        
        if namespace:
            command.extend(["-n", namespace])
        
        success, output = self.execute_command(command)
        
        return {
            "command": f"kubectl delete {resource_type} {resource_name}{f' -n {namespace}' if namespace else ''}",
            "result": output,
            "success": success,
            "error": None if success else "Command failed"
        }
    
    def get_contexts(self) -> Dict[str, Any]:
        """
        Get all contexts.
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["config", "get-contexts", "-o", "name"])
        
        if success:
            contexts = [context.strip() for context in output.splitlines() if context.strip()]
            return {
                "command": "kubectl config get-contexts -o name",
                "result": contexts,
                "success": True
            }
        else:
            return {
                "command": "kubectl config get-contexts -o name",
                "result": output,
                "success": False,
                "error": "Command failed"
            }
    
    def switch_context(self, context: str) -> Dict[str, Any]:
        """
        Switch to the specified context.
        
        Args:
            context: Context to switch to
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["config", "use-context", context])
        
        return {
            "command": f"kubectl config use-context {context}",
            "result": output,
            "success": success,
            "error": None if success else "Command failed"
        }
    
    def get_current_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            Dictionary containing the command and result
        """
        success, output = self.execute_command(["config", "current-context"])
        
        return {
            "command": "kubectl config current-context",
            "result": output.strip(),
            "success": success,
            "error": None if success else "Command failed"
        }
