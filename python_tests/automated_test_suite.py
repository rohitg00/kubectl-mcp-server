#!/usr/bin/env python3
"""
Automated test suite for kubectl-mcp-tool features.
"""

import json
import logging
import os
import subprocess
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="automated_test_suite.log"
)
logger = logging.getLogger("automated-test-suite")

def test_log_analysis():
    """Test log analysis features."""
    from kubectl_mcp_tool.log_analysis.log_analyzer import LogAnalyzer
    from kubectl_mcp_tool.cli_output import CLIOutput
    
    print("\n=== Testing Log Analysis ===")
    
    analyzer = LogAnalyzer()
    cli = CLIOutput()
    
    # Test analyzing pod logs
    pod_name = "coredns-668d6bf9bc-hc87p"
    namespace = "kube-system"
    
    print(f"\nAnalyzing logs for pod {pod_name} in namespace {namespace}")
    analysis = analyzer.analyze_logs(pod_name, namespace)
    
    if analysis.get("success", False):
        print("\nLog Analysis Results:")
        print(cli.format_log_analysis(analysis))
    else:
        print(f"Error analyzing logs: {analysis.get('error', 'Unknown error')}")

def test_context_switching():
    """Test context switching features."""
    from kubectl_mcp_tool.context_switcher.context_manager import ContextManager
    from kubectl_mcp_tool.context_switcher.namespace_manager import NamespaceManager
    
    print("\n=== Testing Context Switching ===")
    
    context_manager = ContextManager()
    namespace_manager = NamespaceManager()
    
    # Test getting contexts
    print("\nFetching available contexts...")
    contexts = context_manager.get_contexts()
    
    if contexts:
        print(f"Found {len(contexts)} contexts:")
        for context in contexts:
            print(f"- {context}")
    else:
        print("No contexts found")
    
    # Test getting namespaces
    print("\nFetching available namespaces...")
    namespaces_data = namespace_manager.get_namespaces()
    
    if namespaces_data.get("success", False):
        namespaces = namespaces_data.get("result", [])
        print(f"Found {len(namespaces)} namespaces:")
        for namespace in namespaces:
            print(f"- {namespace}")
    else:
        print(f"Error getting namespaces: {namespaces_data.get('error', 'Unknown error')}")

def test_cli_output():
    """Test CLI output formatting."""
    from kubectl_mcp_tool.cli_output import CLIOutput
    
    print("\n=== Testing CLI Output ===")
    
    cli = CLIOutput()
    
    # Test pod status formatting
    pod_data = {
        "metadata": {
            "name": "test-pod",
            "namespace": "default"
        },
        "status": {
            "phase": "Running",
            "containerStatuses": [
                {
                    "name": "nginx",
                    "ready": True,
                    "restartCount": 0
                }
            ]
        }
    }
    
    print("\nFormatted Pod Status:")
    print(cli.format_pod_status(pod_data))
    
    # Test namespace status formatting
    namespace_data = {
        "metadata": {
            "name": "test-namespace"
        },
        "status": {
            "phase": "Active"
        }
    }
    
    print("\nFormatted Namespace Status:")
    print(cli.format_namespace_status(namespace_data))

def main():
    """Run the automated test suite."""
    try:
        print("Starting automated test suite for kubectl-mcp-tool...")
        
        # Run all tests
        test_log_analysis()
        test_context_switching()
        test_cli_output()
        
        print("\nTest suite completed successfully")
    except Exception as e:
        print(f"Error in test suite: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
