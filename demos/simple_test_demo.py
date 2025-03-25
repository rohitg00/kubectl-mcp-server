#!/usr/bin/env python3
"""
Simple test demo for kubectl-mcp-tool functionality.
"""

import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional

from kubectl_mcp_tool.cli_output import CLIOutput
from kubectl_mcp_tool.natural_language import process_query
from kubectl_mcp_tool.context_switcher.context_manager import ContextManager
from kubectl_mcp_tool.context_switcher.namespace_manager import NamespaceManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="simple_test_demo.log"
)
logger = logging.getLogger("simple-test-demo")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_natural_language():
    """Test natural language processing."""
    print("\n=== Testing Natural Language Processing ===")
    
    # Test queries
    queries = [
        "get all pods",
        "show namespaces",
        "describe pod nginx in default namespace",
        "scale deployment nginx to 3 replicas",
        "get logs from pod nginx"
    ]
    
    cli = CLIOutput()
    
    for query in queries:
        print(f"\nProcessing query: '{query}'")
        result = process_query(query)
        
        if result.get("success", False):
            print(f"Command: {result.get('command', '')}")
            print(cli.display_command_result(result))
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")

def test_context_switching():
    """Test context switching."""
    print("\n=== Testing Context Switching ===")
    
    context_manager = ContextManager()
    namespace_manager = NamespaceManager()
    cli = CLIOutput()
    
    # Get contexts
    print("\nGetting available contexts:")
    contexts = context_manager.get_contexts()
    
    if contexts:
        print(f"Found {len(contexts)} contexts:")
        for context in contexts:
            print(f"- {context}")
    else:
        print("No contexts found")
    
    # Get current context
    print("\nGetting current context:")
    current_context = context_manager.get_current_context()
    
    if current_context.get("success", False):
        print(f"Current context: {current_context.get('result', '')}")
    else:
        print(f"Error: {current_context.get('error', 'Unknown error')}")
    
    # Get namespaces
    print("\nGetting available namespaces:")
    namespaces = namespace_manager.get_namespaces()
    
    if namespaces.get("success", False):
        print(f"Found {len(namespaces.get('result', []))} namespaces:")
        for namespace in namespaces.get("result", []):
            print(f"- {namespace}")
    else:
        print(f"Error: {namespaces.get('error', 'Unknown error')}")
    
    # Get current namespace
    print("\nGetting current namespace:")
    current_namespace = namespace_manager.get_current_namespace()
    
    if current_namespace.get("success", False):
        print(f"Current namespace: {current_namespace.get('result', '')}")
    else:
        print(f"Error: {current_namespace.get('error', 'Unknown error')}")

def test_log_analysis():
    """Test log analysis."""
    print("\n=== Testing Log Analysis ===")
    
    from kubectl_mcp_tool.log_analysis.log_analyzer import LogAnalyzer
    
    log_analyzer = LogAnalyzer()
    cli = CLIOutput()
    
    # Test pod log analysis
    pod_name = "nginx"
    namespace = "default"
    
    print(f"\nAnalyzing logs for pod {pod_name} in namespace {namespace}:")
    result = log_analyzer.analyze_logs(pod_name, namespace)
    
    if result.get("success", False):
        print(cli.format_log_analysis(result))
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Test error pattern detection
    print("\nDetecting error patterns in sample log:")
    sample_log = """
    2023-05-15T10:44:41.547Z [WARNING] plugin/kubernetes: starting server with unsynced Kubernetes API
    2023-05-15T10:44:41.547Z [INFO] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/rest/request.go:598: failed to list *v1.Service: Get "https://10.96.0.1:443/api/v1/services?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    2023-05-15T10:44:41.547Z [ERROR] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/tools/cache/reflector.go:167: Failed to watch *v1.Service: failed to list *v1.Service: Get "https://10.96.0.1:443/api/v1/services?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    2023-05-15T10:44:41.547Z [ERROR] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/tools/cache/reflector.go:167: Failed to watch *v1.Namespace: failed to list *v1.Namespace: Get "https://10.96.0.1:443/api/v1/namespaces?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    """
    
    patterns = log_analyzer.detect_error_patterns(sample_log)
    
    if patterns:
        print(f"Found {len(patterns)} error patterns:")
        for pattern in patterns:
            print(f"- Type: {pattern['type']}")
            print(f"  Line: {pattern['line']}")
            print(f"  Explanation: {pattern['explanation']}")
    else:
        print("No error patterns found")

def main():
    """Run the simple test demo."""
    try:
        print("Starting simple test demo for kubectl-mcp-tool...")
        
        # Run all tests
        test_natural_language()
        test_context_switching()
        test_log_analysis()
        
        print("\nTest demo completed successfully")
    except Exception as e:
        print(f"Error in test demo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
