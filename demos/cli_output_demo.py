#!/usr/bin/env python3
"""
Demo script for enhanced CLI output formatting.
"""

import json
import logging
import os
import sys
import time
from typing import Dict, Any

from kubectl_mcp_tool.cli_output import CLIOutput

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="cli_output_demo.log"
)
logger = logging.getLogger("cli-output-demo")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def get_pods_data() -> Dict[str, Any]:
    """Get sample pods data for demo."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "get", "pods", "-o", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "command": "kubectl get pods -o json",
                "result": json.loads(result.stdout)
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        logger.error(f"Error getting pods data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_namespaces_data() -> Dict[str, Any]:
    """Get sample namespaces data for demo."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "get", "namespaces", "-o", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "command": "kubectl get namespaces -o json",
                "result": json.loads(result.stdout)
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        logger.error(f"Error getting namespaces data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_deployments_data() -> Dict[str, Any]:
    """Get sample deployments data for demo."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "get", "deployments", "-o", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "command": "kubectl get deployments -o json",
                "result": json.loads(result.stdout)
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        logger.error(f"Error getting deployments data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_contexts_data() -> Dict[str, Any]:
    """Get sample contexts data for demo."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "command": "kubectl config get-contexts -o name",
                "result": result.stdout.strip().split('\n')
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        logger.error(f"Error getting contexts data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_pod_logs_data(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
    """Get sample pod logs data for demo."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "logs", f"--namespace={namespace}", pod_name],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "command": f"kubectl logs --namespace={namespace} {pod_name}",
                "result": result.stdout
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        logger.error(f"Error getting pod logs data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_pod_description_data(pod_name: str, namespace: str = "default") -> Dict[str, Any]:
    """Get sample pod description data for demo."""
    try:
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "describe", "pod", f"--namespace={namespace}", pod_name],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "command": f"kubectl describe pod --namespace={namespace} {pod_name}",
                "result": result.stdout
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        logger.error(f"Error getting pod description data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_command_result_data(command: str) -> Dict[str, Any]:
    """Get sample command result data for demo."""
    try:
        import subprocess
        
        # Split the command into args
        args = command.split()
        
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "command": command,
                "result": result.stdout
            }
        else:
            return {
                "success": False,
                "error": result.stderr.strip()
            }
    except Exception as e:
        logger.error(f"Error getting command result data: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Run the CLI output demo."""
    try:
        # Create the CLI output formatter
        cli_output = CLIOutput()
        
        print("\n=== Enhanced CLI Output Demo ===\n")
        
        # Demo pods display
        print("\n=== Pods Display ===\n")
        pods_data = get_pods_data()
        cli_output.display_pods(pods_data)
        
        # Demo namespaces display
        print("\n=== Namespaces Display ===\n")
        namespaces_data = get_namespaces_data()
        cli_output.display_namespaces(namespaces_data)
        
        # Demo deployments display
        print("\n=== Deployments Display ===\n")
        deployments_data = get_deployments_data()
        cli_output.display_deployments(deployments_data)
        
        # Demo contexts display
        print("\n=== Contexts Display ===\n")
        contexts_data = get_contexts_data()
        cli_output.display_contexts(contexts_data)
        
        # Demo command result display
        print("\n=== Command Result Display ===\n")
        command_result_data = get_command_result_data("kubectl version --client")
        cli_output.display_command_result(command_result_data)
        
        # Demo pod logs display if pods are available
        if pods_data.get("success", False):
            pods = pods_data.get("result", {}).get("items", [])
            if pods:
                pod_name = pods[0].get("metadata", {}).get("name", "")
                namespace = pods[0].get("metadata", {}).get("namespace", "default")
                
                if pod_name:
                    print(f"\n=== Pod Logs Display for {pod_name} ===\n")
                    pod_logs_data = get_pod_logs_data(pod_name, namespace)
                    cli_output.display_pod_logs(pod_logs_data)
                    
                    print(f"\n=== Pod Description Display for {pod_name} ===\n")
                    pod_description_data = get_pod_description_data(pod_name, namespace)
                    cli_output.display_pod_description(pod_description_data)
        
        print("\n=== Demo Complete ===\n")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        print(f"Error in demo: {e}")

if __name__ == "__main__":
    main()
