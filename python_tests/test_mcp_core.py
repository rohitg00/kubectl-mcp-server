#!/usr/bin/env python3
"""
Core MCP tests for kubectl-mcp-tool.
Tests basic functionality like connecting to a cluster, 
managing resources, and namespace operations.
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
    namespace_context, generate_test_pod, generate_test_deployment,
    validate_mcp_response, validate_kubernetes_state, wait_for_pod_ready
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

class TestMCPCore:
    """
    Test MCP Kubectl Tool core functionality through MCP protocol.
    Tests basic operations like connecting to a cluster, 
    resource management, and namespace operations.
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
    
    def test_list_tools(self, mcp_client):
        """Test listing available tools."""
        response = mcp_client.list_tools()
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tools", "Response type should be 'tools'"
        assert "result" in response, "Response should contain 'result' field"
        assert "tools" in response["result"], "Result should contain 'tools' field"
        
        # Verify there are some tools in the list
        tools = response["result"]["tools"]
        assert isinstance(tools, list), "Tools should be a list"
        assert len(tools) > 0, "Tools list should not be empty"
        
        # Check each tool has the required fields
        for tool in tools:
            assert "name" in tool, "Tool should have a name"
            assert "description" in tool, "Tool should have a description"
            
        logger.info(f"Found {len(tools)} tools")
    
    def test_get_namespaces(self, mcp_client):
        """Test getting namespaces."""
        response = mcp_client.call_tool("get_namespaces", {})
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # Verify default namespaces are present
        result = response["result"]
        assert "items" in result, "Result should contain 'items' field with namespaces"
        
        namespace_names = [ns["metadata"]["name"] for ns in result["items"]]
        expected_namespaces = ["default", "kube-system"]
        
        for ns in expected_namespaces:
            assert ns in namespace_names, f"Expected namespace '{ns}' not found"
            
        logger.info(f"Found {len(namespace_names)} namespaces")
    
    def test_set_and_get_namespace(self, mcp_client):
        """Test setting and getting namespace."""
        # First check the current namespace
        initial_response = mcp_client.call_tool("get_current_namespace", {})
        initial_namespace = initial_response["result"]["namespace"]
        
        # Set namespace to kube-system
        set_response = mcp_client.call_tool("set_namespace", {"namespace": "kube-system"})
        
        # Validate response format
        is_valid, error = validate_mcp_response(set_response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert set_response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in set_response, "Response should contain 'result' field"
        assert set_response["result"]["success"] is True, "Setting namespace should succeed"
        
        # Verify namespace was set by getting current namespace
        get_response = mcp_client.call_tool("get_current_namespace", {})
        
        # Validate response format
        is_valid, error = validate_mcp_response(get_response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert get_response["result"]["namespace"] == "kube-system", \
            f"Expected namespace to be 'kube-system', got '{get_response['result']['namespace']}'"
            
        # Reset namespace to previous value
        mcp_client.call_tool("set_namespace", {"namespace": initial_namespace})
        
        logger.info(f"Successfully set and verified namespace")
    
    def test_create_and_get_pod(self, mcp_client):
        """Test creating and getting a pod."""
        # Create test namespace
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Create pod
            pod_name = "test-pod"
            pod_spec = generate_test_pod(pod_name)
            
            # Create temporary file with pod definition
            with self.temp_resource_file(pod_spec) as pod_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": pod_file
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(create_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert create_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in create_response, "Response should contain 'result' field"
                assert create_response["result"]["success"] is True, \
                    f"Creating pod should succeed: {create_response['result'].get('error', '')}"
                
                # Wait for pod to be ready
                assert wait_for_pod_ready(pod_name, namespace), f"Pod {pod_name} failed to become ready"
                
                # Get pod
                get_response = mcp_client.call_tool("get_pods", {
                    "namespace": namespace,
                    "name": pod_name
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(get_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert get_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in get_response, "Response should contain 'result' field"
                
                # Verify pod exists in response
                result = get_response["result"]
                assert "items" in result, "Result should contain 'items' field with pods"
                assert len(result["items"]) == 1, f"Expected 1 pod, got {len(result['items'])}"
                assert result["items"][0]["metadata"]["name"] == pod_name, \
                    f"Expected pod name '{pod_name}', got '{result['items'][0]['metadata']['name']}'"
                
                # Verify pod state in Kubernetes
                is_valid, state = validate_kubernetes_state("pod", pod_name, namespace)
                assert is_valid, f"Failed to get pod state: {state}"
                assert state["kind"] == "Pod", "Expected resource kind to be 'Pod'"
                assert state["metadata"]["name"] == pod_name, f"Expected pod name to be '{pod_name}'"
                
                logger.info(f"Successfully created and verified pod {pod_name}")
    
    def test_create_and_scale_deployment(self, mcp_client):
        """Test creating and scaling a deployment."""
        # Create test namespace
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Create deployment
            deployment_name = "test-deployment"
            deployment_spec = generate_test_deployment(deployment_name, replicas=1)
            
            # Create temporary file with deployment definition
            with self.temp_resource_file(deployment_spec) as deployment_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": deployment_file
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(create_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert create_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in create_response, "Response should contain 'result' field"
                assert create_response["result"]["success"] is True, \
                    f"Creating deployment should succeed: {create_response['result'].get('error', '')}"
                
                # Wait for deployment to be available (simple delay)
                time.sleep(5)
                
                # Scale deployment
                scale_response = mcp_client.call_tool("scale_deployment", {
                    "deployment": deployment_name,
                    "replicas": 2,
                    "namespace": namespace
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(scale_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert scale_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in scale_response, "Response should contain 'result' field"
                assert scale_response["result"]["success"] is True, \
                    f"Scaling deployment should succeed: {scale_response['result'].get('error', '')}"
                
                # Wait for scaling to complete (simple delay)
                time.sleep(5)
                
                # Get deployment
                get_response = mcp_client.call_tool("get_deployments", {
                    "namespace": namespace,
                    "name": deployment_name
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(get_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert get_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in get_response, "Response should contain 'result' field"
                
                # Verify deployment replicas
                result = get_response["result"]
                assert "items" in result, "Result should contain 'items' field with deployments"
                assert len(result["items"]) == 1, f"Expected 1 deployment, got {len(result['items'])}"
                
                replicas = result["items"][0]["spec"]["replicas"]
                assert replicas == 2, f"Expected 2 replicas, got {replicas}"
                
                logger.info(f"Successfully created and scaled deployment {deployment_name}")
    
    def test_explain_resource(self, mcp_client):
        """Test explaining a Kubernetes resource."""
        response = mcp_client.call_tool("explain_resource", {
            "resource": "pod"
        })
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # Verify explanation content
        result = response["result"]
        assert "explanation" in result, "Result should contain 'explanation' field"
        assert "pod" in result["explanation"].lower(), "Explanation should describe pods"
        
        logger.info("Successfully retrieved resource explanation")
    
    def test_get_api_resources(self, mcp_client):
        """Test getting API resources."""
        response = mcp_client.call_tool("get_api_resources", {})
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # Verify API resources
        result = response["result"]
        assert "resources" in result, "Result should contain 'resources' field"
        
        # Check for common resources
        resource_names = [res["name"] for res in result["resources"]]
        expected_resources = ["pods", "services", "deployments"]
        
        for res in expected_resources:
            assert res in resource_names, f"Expected resource '{res}' not found"
        
        logger.info(f"Successfully retrieved {len(resource_names)} API resources")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 