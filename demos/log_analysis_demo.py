#!/usr/bin/env python3
"""
Demo script for log analysis features.
"""

import json
import logging
import os
import sys
import time
from typing import Dict, Any

from kubectl_mcp_tool.log_analysis.log_analyzer import LogAnalyzer
from kubectl_mcp_tool.cli_output import CLIOutput

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_analysis_demo.log"
)
logger = logging.getLogger("log-analysis-demo")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def main():
    """Run the log analysis demo."""
    try:
        # Create the log analyzer
        log_analyzer = LogAnalyzer()
        cli_output = CLIOutput()
        
        print("\n=== Log Analysis Demo ===\n")
        
        # Get available pods
        print("Fetching available pods...")
        pods_data = get_pods()
        
        if not pods_data.get("success", False):
            print(f"Error fetching pods: {pods_data.get('error', 'Unknown error')}")
            return
        
        pod_items = pods_data.get("result", {}).get("items", [])
        
        if not pod_items:
            print("No pods found in the cluster.")
            return
        
        # Display available pods
        print(f"Found {len(pod_items)} pods in the cluster.")
        print("\nAvailable pods:")
        
        for i, pod in enumerate(pod_items, 1):
            pod_name = pod.get("metadata", {}).get("name", "")
            namespace = pod.get("metadata", {}).get("namespace", "default")
            status = pod.get("status", {}).get("phase", "Unknown")
            
            print(f"{i}. {pod_name} (namespace: {namespace}, status: {status})")
        
        # Select a pod for analysis
        selected_pod_idx = 0
        
        try:
            selected_pod_idx = int(input("\nSelect a pod for log analysis (enter number): ")) - 1
            
            if selected_pod_idx < 0 or selected_pod_idx >= len(pod_items):
                print("Invalid selection. Using the first pod.")
                selected_pod_idx = 0
        except (ValueError, IndexError):
            print("Invalid selection. Using the first pod.")
            selected_pod_idx = 0
        
        selected_pod = pod_items[selected_pod_idx]
        pod_name = selected_pod.get("metadata", {}).get("name", "")
        namespace = selected_pod.get("metadata", {}).get("namespace", "default")
        
        print(f"\nAnalyzing logs for pod: {pod_name} in namespace: {namespace}")
        
        # Get containers in the pod
        containers = []
        for container in selected_pod.get("spec", {}).get("containers", []):
            container_name = container.get("name", "")
            if container_name:
                containers.append(container_name)
        
        if not containers:
            print("No containers found in the pod.")
            return
        
        print(f"Found {len(containers)} containers in the pod: {', '.join(containers)}")
        
        # Analyze logs for each container
        for container_name in containers:
            print(f"\n=== Analyzing logs for container: {container_name} ===\n")
            
            # Analyze logs
            analysis = log_analyzer.analyze_logs(pod_name, namespace, container_name, 100)
            
            if not analysis.get("success", False):
                print(f"Error analyzing logs: {analysis.get('error', 'Unknown error')}")
                continue
            
            # Display analysis results
            result = analysis.get("result", {})
            
            # Display summary
            print(f"Summary: {result.get('summary', 'No summary available.')}")
            
            # Display code smells
            code_smells = result.get("code_smells", [])
            if code_smells:
                print(f"\nDetected {len(code_smells)} code smells:")
                
                for i, code_smell in enumerate(code_smells, 1):
                    print(f"{i}. {code_smell.get('type', 'Unknown')}: {code_smell.get('description', '')}")
                    print(f"   Recommendation: {code_smell.get('recommendation', '')}")
            else:
                print("\nNo code smells detected.")
            
            # Display errors
            errors = result.get("errors", [])
            if errors:
                print(f"\nDetected {len(errors)} errors:")
                
                for i, error in enumerate(errors, 1):
                    print(f"{i}. {error.get('type', 'Unknown')}: {error.get('line', '')}")
                    print(f"   Explanation: {error.get('explanation', '')}")
            else:
                print("\nNo errors detected.")
            
            # Display recommendations
            recommendations = result.get("recommendations", [])
            if recommendations:
                print(f"\nRecommendations ({len(recommendations)}):")
                
                for i, recommendation in enumerate(recommendations, 1):
                    print(f"{i}. {recommendation}")
            else:
                print("\nNo recommendations available.")
        
        print("\n=== Demo Complete ===\n")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        print(f"Error in demo: {e}")

def get_pods() -> Dict[str, Any]:
    """Get pods from the cluster."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "get", "pods", "--all-namespaces", "-o", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "command": "kubectl get pods --all-namespaces -o json",
                "result": json.loads(result.stdout)
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        logger.error(f"Error getting pods: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    main()
