#!/usr/bin/env python3
"""
Security MCP tests for kubectl-mcp-tool.
Tests security-related functionality like RBAC validation, 
ServiceAccount operations, and security context auditing.
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

class TestMCPSecurity:
    """
    Test MCP Kubectl Tool security functionality through MCP protocol.
    Tests RBAC operations, ServiceAccount management, and security auditing.
    """
    
    @pytest.fixture(scope="class")
    def mcp_client(self):
        """Fixture to create and manage MCP client."""
        # Initialize MCP client with stdio transport
        with MCPClientSimulator(stdio_cmd=MCP_SERVER_CMD) as client:
            yield client
    
    @contextmanager
    def temp_resource_file(self, resource_dict):
        """Create a temporary file with resource definition."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp:
            json.dump(resource_dict, temp)
            temp_path = temp.name
        
        try:
            yield temp_path
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def generate_service_account(self, name):
        """Generate a ServiceAccount resource definition."""
        return {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": name,
                "labels": {
                    "created-by": "mcp-test"
                }
            }
        }
    
    def generate_role(self, name, rules):
        """Generate a Role resource definition."""
        return {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {
                "name": name,
                "labels": {
                    "created-by": "mcp-test"
                }
            },
            "rules": rules
        }
    
    def generate_role_binding(self, name, role_name, sa_name):
        """Generate a RoleBinding resource definition."""
        return {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {
                "name": name,
                "labels": {
                    "created-by": "mcp-test"
                }
            },
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "name": sa_name
                }
            ],
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "Role",
                "name": role_name
            }
        }
    
    def test_create_service_account(self, mcp_client):
        """Test creating a ServiceAccount."""
        # Create test namespace
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Create ServiceAccount
            sa_name = "test-sa"
            sa_spec = self.generate_service_account(sa_name)
            
            # Create temporary file with ServiceAccount definition
            with self.temp_resource_file(sa_spec) as sa_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": sa_file
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(create_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert create_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in create_response, "Response should contain 'result' field"
                assert create_response["result"]["success"] is True, \
                    f"Creating ServiceAccount should succeed: {create_response['result'].get('error', '')}"
                
                # Verify ServiceAccount exists
                is_valid, state = validate_kubernetes_state(
                    "serviceaccount", sa_name, namespace
                )
                assert is_valid, f"Invalid ServiceAccount state: {state}"
                
                logger.info(f"Successfully created ServiceAccount {sa_name}")
    
    def test_rbac_operations(self, mcp_client):
        """Test RBAC operations (Role and RoleBinding)."""
        # Create test namespace
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Create ServiceAccount
            sa_name = "rbac-test-sa"
            sa_spec = self.generate_service_account(sa_name)
            
            # Create Role with pod read permissions
            role_name = "pod-reader"
            role_spec = self.generate_role(role_name, [
                {
                    "apiGroups": [""],
                    "resources": ["pods"],
                    "verbs": ["get", "watch", "list"]
                }
            ])
            
            # Create RoleBinding to bind Role to ServiceAccount
            binding_name = "pod-reader-binding"
            binding_spec = self.generate_role_binding(binding_name, role_name, sa_name)
            
            # Create each resource
            with self.temp_resource_file(sa_spec) as sa_file:
                mcp_client.call_tool("create_resource", {"filepath": sa_file})
            
            with self.temp_resource_file(role_spec) as role_file:
                role_response = mcp_client.call_tool("create_resource", {"filepath": role_file})
                
                # Validate response format
                is_valid, error = validate_mcp_response(role_response)
                assert is_valid, f"Invalid MCP response: {error}"
                assert role_response["result"]["success"] is True, \
                    f"Creating Role should succeed: {role_response['result'].get('error', '')}"
            
            with self.temp_resource_file(binding_spec) as binding_file:
                binding_response = mcp_client.call_tool("create_resource", {"filepath": binding_file})
                
                # Validate response format
                is_valid, error = validate_mcp_response(binding_response)
                assert is_valid, f"Invalid MCP response: {error}"
                assert binding_response["result"]["success"] is True, \
                    f"Creating RoleBinding should succeed: {binding_response['result'].get('error', '')}"
            
            # Verify Role and RoleBinding exist
            is_valid, state = validate_kubernetes_state("role", role_name, namespace)
            assert is_valid, f"Invalid Role state: {state}"
            
            is_valid, state = validate_kubernetes_state("rolebinding", binding_name, namespace)
            assert is_valid, f"Invalid RoleBinding state: {state}"
            
            logger.info(f"Successfully created RBAC resources")
    
    def test_can_i_rbac_check(self, mcp_client):
        """Test RBAC authorization check with can-i."""
        # This test checks if the current user can perform certain actions
        response = mcp_client.call_tool("can_i", {
            "verb": "get",
            "resource": "pods"
        })
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # The result should contain an 'allowed' field (true or false)
        assert "allowed" in response["result"], "Result should contain 'allowed' field"
        
        # Just log the result, as we don't know the exact permissions
        logger.info(f"RBAC check result: {response['result']['allowed']}")
    
    def test_security_audit(self, mcp_client):
        """Test security context audit."""
        # Create test namespace with a pod to audit
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Create a pod with security context
            pod_spec = {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "name": "security-test-pod",
                    "labels": {
                        "app": "security-test",
                        "created-by": "mcp-test"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "nginx",
                            "image": "nginx:latest",
                            "securityContext": {
                                "privileged": False,
                                "runAsNonRoot": True,
                                "runAsUser": 1000,
                                "capabilities": {
                                    "drop": ["ALL"]
                                }
                            }
                        }
                    ]
                }
            }
            
            # Create pod for security audit
            with self.temp_resource_file(pod_spec) as pod_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": pod_file
                })
                assert create_response["result"]["success"] is True, \
                    f"Creating pod should succeed: {create_response['result'].get('error', '')}"
                
                # Wait for pod to be created
                time.sleep(3)
                
                # Run security audit
                audit_response = mcp_client.call_tool("audit_pod_security", {
                    "namespace": namespace,
                    "name": "security-test-pod"
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(audit_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert audit_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in audit_response, "Response should contain 'result' field"
                
                # The audit result should contain security information
                result = audit_response["result"]
                assert "findings" in result, "Result should contain 'findings' field"
                
                # Log findings
                logger.info(f"Security audit findings: {len(result['findings'])}")
                for finding in result.get("findings", []):
                    logger.info(f"Finding: {finding.get('message', 'No message')}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 