#!/usr/bin/env python3
"""
Test script specifically for verifying the newly added methods in KubernetesOperations class
"""

import logging
from kubectl_mcp_tool.core.kubernetes_ops import KubernetesOperations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_new_methods():
    """Test the newly added methods in KubernetesOperations class."""
    
    try:
        # Initialize KubernetesOperations
        logger.info("Initializing KubernetesOperations...")
        k8s_ops = KubernetesOperations()
        
        # Test Resource Listing Methods
        
        logger.info("\n=== Testing Resource Listing Methods ===")
        
        # 1. Test list_pods
        logger.info("\nTesting list_pods method...")
        result = k8s_ops.list_pods(namespace="kube-system")
        logger.info(f"list_pods result status: {result.get('status')}")
        logger.info(f"Found {result.get('count', 0)} pods in kube-system namespace")
        
        # 2. Test list_services
        logger.info("\nTesting list_services method...")
        result = k8s_ops.list_services(namespace="kube-system")
        logger.info(f"list_services result status: {result.get('status')}")
        logger.info(f"Found {result.get('count', 0)} services in kube-system namespace")
        
        # 3. Test list_deployments
        logger.info("\nTesting list_deployments method...")
        result = k8s_ops.list_deployments(namespace="kube-system")
        logger.info(f"list_deployments result status: {result.get('status')}")
        logger.info(f"Found {result.get('count', 0)} deployments in kube-system namespace")
        
        # 4. Test list_nodes
        logger.info("\nTesting list_nodes method...")
        result = k8s_ops.list_nodes()
        logger.info(f"list_nodes result status: {result.get('status')}")
        logger.info(f"Found {result.get('count', 0)} nodes in the cluster")
        
        # 5. Test list_namespaces
        logger.info("\nTesting list_namespaces method...")
        result = k8s_ops.list_namespaces()
        logger.info(f"list_namespaces result status: {result.get('status')}")
        logger.info(f"Found {result.get('count', 0)} namespaces in the cluster")
        
        # Test Kubectl Utilities
        
        logger.info("\n=== Testing Kubectl Utilities ===")
        
        # 1. Test explain_resource
        logger.info("\nTesting explain_resource method...")
        result = k8s_ops.explain_resource(resource="pods")
        logger.info(f"explain_resource result status: {result.get('status')}")
        if result.get('status') == 'success':
            explanation = result.get('explanation', '')
            logger.info(f"Got explanation with length: {len(explanation)} characters")
            logger.info(f"First 100 characters: {explanation[:100]}...")
        
        # 2. Test list_api_resources
        logger.info("\nTesting list_api_resources method...")
        result = k8s_ops.list_api_resources()
        logger.info(f"list_api_resources result status: {result.get('status')}")
        logger.info(f"Found {result.get('count', 0)} API resources")
        
        # 3. Test describe_pod
        if result.get('count', 0) > 0 and k8s_ops.list_pods().get('count', 0) > 0:
            pod_name = k8s_ops.list_pods().get('items', [{}])[0].get('name', '')
            namespace = k8s_ops.list_pods().get('items', [{}])[0].get('namespace', 'default')
            
            if pod_name:
                logger.info(f"\nTesting describe_pod method with pod {pod_name}...")
                result = k8s_ops.describe_pod(pod_name=pod_name, namespace=namespace)
                logger.info(f"describe_pod result status: {result.get('status')}")
                if result.get('status') == 'success':
                    logger.info(f"Successfully described pod {pod_name}")
        
        # Test Helm Chart Support (skipping actual operations to avoid side effects)
        
        logger.info("\n=== Testing Helm Chart Support (Function Signatures Only) ===")
        logger.info("Note: Not performing actual Helm operations to avoid side effects")
        
        # Verify method signatures exist by inspecting the class
        logger.info("\nVerifying method signatures...")
        
        methods_to_check = [
            'install_helm_chart', 
            'upgrade_helm_chart', 
            'uninstall_helm_chart',
            'switch_context'
        ]
        
        for method_name in methods_to_check:
            if hasattr(k8s_ops, method_name) and callable(getattr(k8s_ops, method_name)):
                logger.info(f"Method {method_name} exists and is callable")
            else:
                logger.error(f"Method {method_name} does not exist or is not callable")
        
        logger.info("\n=== All Tests Completed ===")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_new_methods() 