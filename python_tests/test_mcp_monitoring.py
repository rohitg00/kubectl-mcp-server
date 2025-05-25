#!/usr/bin/env python3
"""
Monitoring MCP tests for kubectl-mcp-tool.
Tests monitoring-related functionality like resource utilization tracking,
health checks, and event monitoring.
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

class TestMCPMonitoring:
    """
    Test MCP Kubectl Tool monitoring functionality through MCP protocol.
    Tests resource utilization tracking, health checks, and event monitoring.
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
    
    def test_get_events(self, mcp_client):
        """Test getting events from a namespace."""
        # Create test namespace
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Create a pod to generate events
            pod_name = "event-test-pod"
            pod_spec = generate_test_pod(pod_name)
            
            # Create temporary file with pod definition
            with self.temp_resource_file(pod_spec) as pod_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": pod_file
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(create_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Wait for pod to generate events
                time.sleep(5)
                
                # Get events
                events_response = mcp_client.call_tool("get_events", {
                    "namespace": namespace
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(events_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert events_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in events_response, "Response should contain 'result' field"
                
                # The result should contain events
                result = events_response["result"]
                assert "items" in result, "Result should contain 'items' field with events"
                
                # We should have at least one event (pod creation)
                assert len(result["items"]) > 0, "Expected at least one event"
                
                # Log events
                logger.info(f"Found {len(result['items'])} events")
                for event in result["items"][:3]:  # Log first 3 events only
                    logger.info(f"Event: {event.get('reason', 'Unknown')} - {event.get('message', 'No message')}")
    
    def test_resource_utilization(self, mcp_client):
        """Test getting resource utilization data."""
        # Create test namespace with resources to monitor
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Create a deployment with multiple replicas to generate usage
            deployment_name = "usage-test-deployment"
            deployment_spec = generate_test_deployment(deployment_name, replicas=2)
            
            # Create temporary file with deployment definition
            with self.temp_resource_file(deployment_spec) as deployment_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": deployment_file
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(create_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Wait for deployment to be ready
                time.sleep(10)
                
                # Get pod usage
                usage_response = mcp_client.call_tool("get_resource_usage", {
                    "namespace": namespace,
                    "resource_type": "pods"
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(usage_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert usage_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in usage_response, "Response should contain 'result' field"
                
                # The result should contain usage data
                result = usage_response["result"]
                assert "items" in result, "Result should contain 'items' field with usage data"
                
                # Log usage data
                logger.info(f"Resource usage data: {len(result['items'])} items")
                for item in result.get("items", []):
                    logger.info(f"Pod: {item.get('name', 'Unknown')}, "
                                f"CPU: {item.get('cpu', 'N/A')}, "
                                f"Memory: {item.get('memory', 'N/A')}")
    
    def test_node_health(self, mcp_client):
        """Test checking node health."""
        response = mcp_client.call_tool("get_node_health", {})
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # The result should contain node health data
        result = response["result"]
        assert "nodes" in result, "Result should contain 'nodes' field"
        
        # Log node health data
        logger.info(f"Node health data: {len(result['nodes'])} nodes")
        for node in result.get("nodes", []):
            logger.info(f"Node: {node.get('name', 'Unknown')}, "
                        f"Status: {node.get('status', 'Unknown')}, "
                        f"CPU: {node.get('cpu', 'N/A')}, "
                        f"Memory: {node.get('memory', 'N/A')}")
    
    def test_pod_health_check(self, mcp_client):
        """Test checking pod health."""
        # Create test namespace with a pod to check
        with namespace_context() as namespace:
            logger.info(f"Using test namespace: {namespace}")
            
            # Set current namespace
            mcp_client.call_tool("set_namespace", {"namespace": namespace})
            
            # Create a pod with readiness probe
            pod_spec = {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "name": "health-test-pod",
                    "labels": {
                        "app": "health-test",
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
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            },
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/",
                                    "port": 80
                                },
                                "initialDelaySeconds": 15,
                                "periodSeconds": 20
                            }
                        }
                    ]
                }
            }
            
            # Create pod with health probes
            with self.temp_resource_file(pod_spec) as pod_file:
                create_response = mcp_client.call_tool("create_resource", {
                    "filepath": pod_file
                })
                assert create_response["result"]["success"] is True, \
                    f"Creating pod should succeed: {create_response['result'].get('error', '')}"
                
                # Wait for pod to be ready
                wait_for_pod_ready("health-test-pod", namespace, timeout=60)
                
                # Check pod health
                health_response = mcp_client.call_tool("check_pod_health", {
                    "namespace": namespace,
                    "name": "health-test-pod"
                })
                
                # Validate response format
                is_valid, error = validate_mcp_response(health_response)
                assert is_valid, f"Invalid MCP response: {error}"
                
                # Check response contents
                assert health_response["type"] == "tool_call", "Response type should be 'tool_call'"
                assert "result" in health_response, "Response should contain 'result' field"
                
                # The health check result should contain status and probes
                result = health_response["result"]
                assert "status" in result, "Result should contain 'status' field"
                assert "probes" in result, "Result should contain 'probes' field"
                
                # Log health check data
                logger.info(f"Pod health status: {result.get('status', 'Unknown')}")
                logger.info(f"Readiness probe: {result.get('probes', {}).get('readiness', 'N/A')}")
                logger.info(f"Liveness probe: {result.get('probes', {}).get('liveness', 'N/A')}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 