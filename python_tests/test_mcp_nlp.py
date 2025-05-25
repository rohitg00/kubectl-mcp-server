#!/usr/bin/env python3
"""
Natural Language Processing MCP tests for kubectl-mcp-tool.
Tests NLP-related functionality like command extraction,
context-awareness, and intent recognition.
"""

import os
import json
import time
import pytest
import logging
import tempfile
from pathlib import Path

from mcp_client_simulator import MCPClientSimulator
from test_utils import (
    namespace_context, validate_mcp_response
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

class TestMCPNLP:
    """
    Test MCP Kubectl Tool natural language processing functionality through MCP protocol.
    Tests command extraction, context-awareness, and intent recognition.
    """
    
    @pytest.fixture(scope="class")
    def mcp_client(self):
        """Fixture to create and manage MCP client."""
        # Initialize MCP client with stdio transport
        with MCPClientSimulator(stdio_cmd=MCP_SERVER_CMD) as client:
            yield client
    
    def test_simple_query(self, mcp_client):
        """Test simple natural language query for pods."""
        query = "list all pods in the default namespace"
        
        response = mcp_client.call_tool("process_natural_language", {
            "query": query
        })
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # The result should contain processed query info
        result = response["result"]
        assert "intent" in result, "Result should contain 'intent' field"
        assert "kubernetes_command" in result, "Result should contain 'kubernetes_command' field"
        assert "response" in result, "Result should contain 'response' field"
        
        # Verify the intent matches listing pods
        assert "list" in result["intent"].lower(), f"Expected list intent, got '{result['intent']}'"
        assert "pod" in result["intent"].lower(), f"Expected pod resource, got '{result['intent']}'"
        
        # Verify the command includes kubectl get pods
        assert "kubectl get pods" in result["kubernetes_command"], \
            f"Expected 'kubectl get pods' in command, got '{result['kubernetes_command']}'"
        
        logger.info(f"NLP Query: '{query}'")
        logger.info(f"Detected Intent: {result['intent']}")
        logger.info(f"Generated Command: {result['kubernetes_command']}")
    
    def test_complex_query(self, mcp_client):
        """Test more complex natural language query."""
        query = "show me deployments with more than 2 replicas"
        
        response = mcp_client.call_tool("process_natural_language", {
            "query": query
        })
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # The result should contain processed query info
        result = response["result"]
        assert "intent" in result, "Result should contain 'intent' field"
        assert "kubernetes_command" in result, "Result should contain 'kubernetes_command' field"
        
        # Verify the intent matches checking deployments with a condition
        assert "deployment" in result["intent"].lower(), \
            f"Expected deployment in intent, got '{result['intent']}'"
        
        logger.info(f"NLP Query: '{query}'")
        logger.info(f"Detected Intent: {result['intent']}")
        logger.info(f"Generated Command: {result['kubernetes_command']}")
    
    def test_context_aware_query(self, mcp_client):
        """Test context-aware natural language query."""
        # First set a specific namespace
        test_namespace = "kube-system"
        mcp_client.call_tool("set_namespace", {"namespace": test_namespace})
        
        # Then run a query that should use that namespace context
        query = "how many pods are running"
        
        response = mcp_client.call_tool("process_natural_language", {
            "query": query
        })
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check if the generated command or response includes the namespace
        result = response["result"]
        
        # Check either the command or the response for namespace context
        command_has_namespace = test_namespace in result["kubernetes_command"]
        response_has_namespace = test_namespace in result["response"]
        
        assert command_has_namespace or response_has_namespace, \
            f"Expected namespace '{test_namespace}' to be considered in command or response"
        
        logger.info(f"NLP Query: '{query}' (with namespace context: {test_namespace})")
        logger.info(f"Detected Intent: {result['intent']}")
        logger.info(f"Generated Command: {result['kubernetes_command']}")
        
        # Reset namespace to default
        mcp_client.call_tool("set_namespace", {"namespace": "default"})
    
    def test_error_query(self, mcp_client):
        """Test handling of invalid or erroneous queries."""
        query = "make kubernetes explode dramatically"
        
        response = mcp_client.call_tool("process_natural_language", {
            "query": query
        })
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents - shouldn't error even for nonsensical queries
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # The result should indicate an issue with the query
        result = response["result"]
        assert "error" in result or "message" in result, \
            "Result should contain 'error' or 'message' field for invalid queries"
        
        logger.info(f"NLP Query: '{query}'")
        logger.info(f"Response: {result.get('response') or result.get('error') or result.get('message')}")
    
    def test_mock_data_query(self, mcp_client):
        """Test queries with mock data mode enabled."""
        query = "list all services"
        
        response = mcp_client.call_tool("process_natural_language", {
            "query": query,
            "use_mock_data": True
        })
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # The result should indicate mock data being used
        result = response["result"]
        assert "mock_data" in result or "is_mock" in result, \
            "Result should indicate mock data usage"
        
        # If there's mock response data, it should contain services
        if "response" in result and isinstance(result["response"], str):
            assert "service" in result["response"].lower(), \
                "Mock response should contain service information"
        
        logger.info(f"NLP Query with mock data: '{query}'")
        logger.info(f"Response: {result.get('response', 'No response')}")
    
    def test_explanation_query(self, mcp_client):
        """Test queries asking for explanations."""
        query = "explain what a deployment is"
        
        response = mcp_client.call_tool("process_natural_language", {
            "query": query
        })
        
        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"
        
        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"
        
        # The result should contain an explanation
        result = response["result"]
        assert "response" in result, "Result should contain 'response' field"
        assert len(result["response"]) > 50, "Explanation should be reasonably detailed"
        
        # Check for relevant terms in the explanation
        explanation_terms = ["deployment", "replicas", "pod"]
        found_terms = [term for term in explanation_terms if term in result["response"].lower()]
        
        assert len(found_terms) > 0, \
            f"Explanation should contain relevant terms like {explanation_terms}"
        
        logger.info(f"NLP Explanation Query: '{query}'")
        logger.info(f"Explanation length: {len(result['response'])} chars")
        logger.info(f"Found terms in explanation: {found_terms}")

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 