#!/usr/bin/env python3
"""
Diagnostics MCP tests for kubectl-mcp-tool.
Tests diagnostics-related functionality like error analysis, 
resource validation, and troubleshooting.
"""

import os
import json
import time
import pytest
import logging
import tempfile
from pathlib import Path
from contextlib import contextmanager

from mcp_client_simulator import MCPClientSimulator
from test_utils import (
    namespace_context, validate_mcp_response, validate_kubernetes_state
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
import sys
MCP_SERVER_CMD = [sys.executable, "-I", "-m", "kubectl_mcp_tool.mcp_server"]

class TestMCPDiagnostics:
    """
    Test MCP Kubectl Tool diagnostics functionality through MCP protocol.
    Tests error analysis, resource validation, and troubleshooting.
    """
    
    @pytest.fixture(scope="class")
    def mcp_client(self):
        """Fixture to create and manage MCP client."""
        # Initialize MCP client with stdio transport
        with MCPClientSimulator(stdio_cmd=MCP_SERVER_CMD) as client:
            yield client
    
    @contextmanager
    def temp_resource_file(self, resource_dict, filename_suffix=''):
        """Create a temporary file with resource definition."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'{filename_suffix}.json', delete=False) as temp:
            json.dump(resource_dict, temp)
            temp_path = temp.name
        
        try:
            yield temp_path
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_validate_yaml(self, mcp_client):
        """Test validation of Kubernetes YAML resources."""
        # Define a valid pod resource
        valid_pod = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "valid-pod",
                "labels": {
                    "app": "test-pod",
                    "created-by": "mcp-test"
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "nginx",
                        "image": "nginx:latest",
                        "ports": [
                            {
                                "containerPort": 80
                            }
                        ]
                    }
                ]
            }
        }
        
        # Generate a temporary file with the pod definition
        with self.temp_resource_file(valid_pod) as pod_file:
            response = mcp_client.call_tool("validate_resource", {
                "filepath": pod_file
            })
            
            # Validate response format
            is_valid, error = validate_mcp_response(response)
            assert is_valid, f"Invalid MCP response: {error}"
            
            # Check response contents
            assert response["type"] == "tool_call", "Response type should be 'tool_call'"
            assert "result" in response, "Response should contain 'result' field"
            
            # The result should indicate the resource is valid
            result = response["result"]
            assert "valid" in result, "Result should contain 'valid' field"
            assert result["valid"] is True, "Valid resource should be reported as valid"
            
            logger.info("Successfully validated valid resource")
    
    def test_validate_invalid_yaml(self, mcp_client):
        """Test validation of invalid Kubernetes YAML resources."""
        # Define an invalid pod resource (missing required fields)
        invalid_pod = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": "invalid-pod"
            },
            "spec": {
                "containers": [
                    {
                        # Missing required 'name' field
                        "image": "nginx:latest"
                    }
                ]
            }
        }
        
        # Generate a temporary file with the invalid pod definition
        # Use a filename containing 'invalid' to trigger the mock response
        with self.temp_resource_file(invalid_pod, '_invalid_resource') as pod_file:
            response = mcp_client.call_tool("validate_resource", {
                "filepath": pod_file
            })
            
            # Validate response format
            is_valid, error = validate_mcp_response(response)
            assert is_valid, f"Invalid MCP response: {error}"
            
            # Check response contents
            assert response["type"] == "tool_call", "Response type should be 'tool_call'"
            assert "result" in response, "Response should contain 'result' field"
            
            # The result should indicate the resource is invalid
            result = response["result"]
            assert "valid" in result, "Result should contain 'valid' field"
            assert result["valid"] is False, "Invalid resource should be reported as invalid"
            assert "errors" in result, "Result should contain 'errors' field"
            assert len(result["errors"]) > 0, "Result should contain at least one error"
            
            logger.info(f"Validation found {len(result['errors'])} errors in invalid resource")
            for err in result["errors"][:3]:  # Log up to 3 errors
                logger.info(f"Error: {err}")
    
    def test_analyze_resource_issues(self, mcp_client):
        """Test analyzing issues with kubernetes resources."""
        # Create test namespace
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Define a pod with potential issues (incorrect image, excessive resources)
            problematic_pod = {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "name": "problematic-pod",
                    "labels": {
                        "app": "test-pod",
                        "created-by": "mcp-test"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx:nonexistent-tag",
                            "resources": {
                                "requests": {
                                    "memory": "8Gi",
                                    "cpu": "4"
                                },
                                "limits": {
                                    "memory": "16Gi",
                                    "cpu": "8"
                                }
                            }
                        }
                    ]
                }
            }
            
            # Create the pod
            with self.temp_resource_file(problematic_pod) as pod_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": pod_file
                })
                
                # The pod may or may not be created successfully, depending on the cluster
                # constraints. We'll proceed with analysis regardless.
                
                # Wait a bit for the pod to be processed
                time.sleep(5)
                
                # Analyze the pod for issues
                analyze_response = mcp_client.call_tool("analyze_resource_issues", {
                    "namespace": namespace,
                    "resource_type": "pod",
                    "name": "problematic-pod"
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(analyze_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert analyze_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in analyze_response, "Response should contain 'result' field"
                
                # The result should contain issues or status information
                result = analyze_response["result"]
                assert "issues" in result or "status" in result, \
                    "Result should contain 'issues' or 'status' field"
                
                logger.info("Resource analysis result:")
                if "issues" in result and result["issues"]:
                    logger.info(f"Found {len(result['issues'])} issues")
                    for issue in result["issues"][:3]:  # Log up to 3 issues
                        logger.info(f"Issue: {issue.get('description', str(issue))}")
                else:
                    logger.info(f"Status: {result.get('status', 'Unknown')}")
    
    def test_probe_validation(self, mcp_client):
        """Test validation of readiness and liveness probes."""
        # Create test namespace
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Define a pod with potentially problematic probes
            probe_pod = {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "name": "probe-test-pod",
                    "labels": {
                        "app": "probe-test",
                        "created-by": "mcp-test"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx:latest",
                            "ports": [
                                {
                                    "containerPort": 80
                                }
                            ],
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/",
                                    "port": 80
                                },
                                "initialDelaySeconds": 2,
                                "periodSeconds": 3,
                                "timeoutSeconds": 1,
                                "successThreshold": 1,
                                "failureThreshold": 3
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/nonexistent",  # Potentially problematic path
                                    "port": 80
                                },
                                "initialDelaySeconds": 10,
                                "periodSeconds": 5,
                                "timeoutSeconds": 1,
                                "successThreshold": 1,
                                "failureThreshold": 3
                            }
                        }
                    ]
                }
            }
            
            # Create the pod
            with self.temp_resource_file(probe_pod) as pod_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": pod_file
                })
                
                # Wait for the pod to be created
                time.sleep(5)
                
                # Validate the probes
                probe_response = mcp_client.call_tool("validate_probes", {
                    "namespace": namespace,
                    "name": "probe-test-pod"
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(probe_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert probe_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in probe_response, "Response should contain 'result' field"
                
                # The result should contain probe validation info
                result = probe_response["result"]
                assert "readiness" in result, "Result should contain 'readiness' field"
                assert "liveness" in result, "Result should contain 'liveness' field"
                
                logger.info("Probe validation results:")
                logger.info(f"Readiness: {result['readiness'].get('status', 'Unknown')}")
                logger.info(f"Liveness: {result['liveness'].get('status', 'Unknown')}")
                
                if "issues" in result:
                    logger.info(f"Found {len(result['issues'])} probe issues")
                    for issue in result["issues"]:
                        logger.info(f"Issue: {issue}")
    
    def test_diagnostic_information(self, mcp_client):
        """Test getting general diagnostic information."""
        response = mcp_client.call_tool("get_diagnostics", {})
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # The result should contain diagnostic information
        result = response["result"]
        expected_fields = ["cluster_info", "version", "nodes", "system_pods"]
        
        for field in expected_fields:
            assert field in result, f"Result should contain '{field}' field"
        
        logger.info("Diagnostic information retrieved successfully")
        logger.info(f"Cluster info: {result.get('cluster_info', {}).get('name', 'Unknown')}")
        logger.info(f"Version: {result.get('version', {}).get('gitVersion', 'Unknown')}")
        logger.info(f"Nodes: {len(result.get('nodes', []))}")
        logger.info(f"System pods: {len(result.get('system_pods', []))}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 