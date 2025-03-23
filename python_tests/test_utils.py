#!/usr/bin/env python3
"""
Test utilities for kubectl-mcp-tool MCP testing.
Provides functions for test setup, validation, and cleanup.
"""

import os
import time
import json
import uuid
import logging
import subprocess
from typing import Dict, List, Any, Tuple, Optional, Union, Callable
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Check if we're running in mock mode
MOCK_MODE = os.environ.get("MCP_TEST_MOCK_MODE", "0") == "1"

def setup_test_namespace(prefix="mcp-test-", max_retries=5, wait_time=3) -> str:
    """
    Create a test namespace with retry logic.
    
    Args:
        prefix: Prefix for the namespace name
        max_retries: Maximum number of retry attempts
        wait_time: Time to wait between retries (seconds)
        
    Returns:
        The name of the created namespace
        
    Raises:
        RuntimeError: If namespace creation fails after all retries
    """
    if MOCK_MODE:
        # In mock mode, just return a fake namespace name
        return f"{prefix}{uuid.uuid4().hex[:8]}"
    
    namespace_name = f"{prefix}{uuid.uuid4().hex[:8]}"
    for attempt in range(max_retries):
        try:
            logger.info(f"Creating namespace {namespace_name} (attempt {attempt+1}/{max_retries})")
            result = subprocess.run(
                ["kubectl", "create", "namespace", namespace_name],
                capture_output=True, check=True, text=True
            )
            logger.info(f"Namespace {namespace_name} created successfully")
            return namespace_name
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to create namespace: {e.stderr}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"Failed to create namespace after {max_retries} attempts")
    
    # This shouldn't be reachable, but just in case
    raise RuntimeError("Unexpected error in namespace creation")

def cleanup_test_namespace(namespace: str) -> bool:
    """
    Delete a test namespace.
    
    Args:
        namespace: The namespace to delete
        
    Returns:
        True if successful, False otherwise
    """
    if MOCK_MODE:
        # In mock mode, just pretend we deleted it
        logger.info(f"[MOCK] Deleted namespace {namespace}")
        return True
    
    try:
        logger.info(f"Deleting namespace {namespace}")
        subprocess.run(
            ["kubectl", "delete", "namespace", namespace, "--wait=false"],
            capture_output=True, check=True, text=True
        )
        logger.info(f"Namespace {namespace} deletion initiated")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to delete namespace: {e.stderr}")
        return False

@contextmanager
def namespace_context(prefix="mcp-test-"):
    """
    Context manager for creating and cleaning up a test namespace.
    
    Args:
        prefix: Prefix for the namespace name
        
    Yields:
        The name of the created namespace
    """
    namespace = setup_test_namespace(prefix)
    try:
        yield namespace
    finally:
        cleanup_test_namespace(namespace)

def deploy_test_resources(namespace: str, yaml_file: str) -> bool:
    """
    Deploy test resources from a YAML file to a namespace.
    
    Args:
        namespace: The namespace to deploy to
        yaml_file: Path to the YAML file containing resources
        
    Returns:
        True if successful, False otherwise
    """
    if MOCK_MODE:
        # In mock mode, just pretend we deployed it
        logger.info(f"[MOCK] Deployed resources from {yaml_file} to {namespace}")
        return True
    
    try:
        logger.info(f"Deploying resources from {yaml_file} to {namespace}")
        subprocess.run(
            ["kubectl", "apply", "-f", yaml_file, "-n", namespace],
            capture_output=True, check=True, text=True
        )
        logger.info(f"Resources deployed successfully to {namespace}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to deploy resources: {e.stderr}")
        return False

def wait_for_pod_ready(pod_name: str, namespace: str, timeout: int = 60) -> bool:
    """
    Wait for a pod to be ready.
    
    Args:
        pod_name: The name of the pod to wait for
        namespace: The namespace containing the pod
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if the pod is ready, False otherwise
    """
    if MOCK_MODE:
        # In mock mode, just pretend the pod is ready
        logger.info(f"[MOCK] Pod {pod_name} is ready in namespace {namespace}")
        return True
    
    logger.info(f"Waiting for pod {pod_name} in namespace {namespace} to be ready")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(
                ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", "jsonpath={.status.phase}"],
                capture_output=True, check=True, text=True
            )
            status = result.stdout.strip()
            if status == "Running":
                # Check if all containers are ready
                ready_result = subprocess.run(
                    ["kubectl", "get", "pod", pod_name, "-n", namespace, "-o", 
                     "jsonpath={.status.containerStatuses[*].ready}"],
                    capture_output=True, check=True, text=True
                )
                ready_statuses = ready_result.stdout.strip().split()
                if all(status == "true" for status in ready_statuses):
                    logger.info(f"Pod {pod_name} is ready")
                    return True
            
            logger.debug(f"Pod status: {status}, waiting...")
            time.sleep(3)
        except subprocess.CalledProcessError:
            logger.debug(f"Error checking pod status, retrying...")
            time.sleep(3)
    
    logger.warning(f"Timed out waiting for pod {pod_name} to be ready")
    return False

def generate_test_pod(name: str, image: str = "nginx:latest") -> Dict[str, Any]:
    """
    Generate a simple test pod definition.
    
    Args:
        name: The name for the pod
        image: The container image to use
        
    Returns:
        A pod resource definition as a dictionary
    """
    return {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": name,
            "labels": {
                "app": name,
                "created-by": "mcp-test"
            }
        },
        "spec": {
            "containers": [
                {
                    "name": "main",
                    "image": image,
                    "ports": [
                        {
                            "containerPort": 80
                        }
                    ]
                }
            ]
        }
    }

def generate_test_deployment(name: str, replicas: int = 1, image: str = "nginx:latest") -> Dict[str, Any]:
    """
    Generate a simple test deployment definition.
    
    Args:
        name: The name for the deployment
        replicas: The number of replicas
        image: The container image to use
        
    Returns:
        A deployment resource definition as a dictionary
    """
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "labels": {
                "app": name,
                "created-by": "mcp-test"
            }
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": {
                    "app": name
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": name,
                        "created-by": "mcp-test"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "main",
                            "image": image,
                            "ports": [
                                {
                                    "containerPort": 80
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }

def validate_mcp_response(response: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Validate that an MCP response meets the expected format.
    
    Args:
        response: The MCP response to validate
        schema: Optional schema to validate against
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Basic structure validation
    if not isinstance(response, dict):
        return False, "Response is not a dictionary"
    
    if "type" not in response:
        return False, "Response missing 'type' field"
    
    # Accept both tool_call and tools response types
    valid_types = ["tool_call", "tools"]
    if response["type"] not in valid_types:
        return False, f"Expected response type to be one of {valid_types}, got '{response['type']}'"
    
    # For tool_call responses, check for result field
    if response["type"] == "tool_call" and "result" not in response:
        return False, "Response of type 'tool_call' missing 'result' field"
    
    # For tools responses, check for tools list
    if response["type"] == "tools" and "result" not in response:
        return False, "Response of type 'tools' missing 'result' field"
    
    if response["type"] == "tools" and "tools" not in response["result"]:
        return False, "Response of type 'tools' missing 'tools' field in result"
    
    # Schema validation if provided (only for tool_call responses)
    if schema and response["type"] == "tool_call":
        # Simplified schema validation - in a real implementation, you might use jsonschema
        for key, expected_type in schema.items():
            if key not in response["result"]:
                return False, f"Result missing required field '{key}'"
            
            if not isinstance(response["result"][key], expected_type):
                return False, f"Field '{key}' has wrong type: expected {expected_type}, got {type(response['result'][key])}"
    
    return True, ""

def validate_kubernetes_state(resource_type: str, name: str, namespace: str) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    Validate that Kubernetes resources match an expected state.
    
    Args:
        resource_type: The type of resource to check (pod, deployment, etc.)
        name: The name of the resource
        namespace: The namespace containing the resource
        
    Returns:
        Tuple of (is_valid, actual_state_or_error)
    """
    if MOCK_MODE:
        # In mock mode, return a fake successful state
        logger.info(f"[MOCK] Validating {resource_type}/{name} in namespace {namespace}")
        return True, {
            "kind": resource_type.capitalize(),
            "metadata": {
                "name": name,
                "namespace": namespace
            },
            "status": {
                "phase": "Running" if resource_type == "pod" else None,
                "availableReplicas": 1 if resource_type == "deployment" else None
            }
        }
    
    try:
        result = subprocess.run(
            ["kubectl", "get", resource_type, name, "-n", namespace, "-o", "json"],
            capture_output=True, check=True, text=True
        )
        state = json.loads(result.stdout)
        return True, state
    except subprocess.CalledProcessError as e:
        return False, e.stderr
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

# Add more test utilities as needed 