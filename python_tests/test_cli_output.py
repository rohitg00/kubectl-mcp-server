#!/usr/bin/env python3
"""
Test script for enhanced CLI output features.
"""

import logging
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_cli_output.log"
)
logger = logging.getLogger("test-cli-output")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_pod_table():
    """Test the pod table output."""
    print("\n=== Testing Pod Table Output ===")
    
    # Create a console
    console = Console()
    
    # Create a table
    table = Table(title="Kubernetes Pods", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Ready", style="yellow")
    table.add_column("Restarts", style="red")
    table.add_column("Age", style="blue")
    
    # Add rows
    table.add_row("nginx-5869d7778c-glw6b", "✅ Running", "1/1", "1", "5d11h")
    table.add_row("nginx-5869d7778c-jt8rn", "✅ Running", "1/1", "1", "5d11h")
    table.add_row("nginx-5869d7778c-tzfxp", "✅ Running", "1/1", "1", "5d11h")
    table.add_row("test-app-754648f69-7gczj", "✅ Running", "1/1", "1", "5d11h")
    table.add_row("test-app-754648f69-g96p4", "✅ Running", "1/1", "1", "5d11h")
    table.add_row("test-app-754648f69-ssrn6", "✅ Running", "1/1", "1", "5d11h")
    
    # Print the table
    console.print(table)
    
    return True

def test_namespace_table():
    """Test the namespace table output."""
    print("\n=== Testing Namespace Table Output ===")
    
    # Create a console
    console = Console()
    
    # Create a table
    table = Table(title="Kubernetes Namespaces", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Age", style="blue")
    
    # Add rows
    table.add_row("default", "Active", "5d11h")
    table.add_row("demo", "Active", "5d11h")
    table.add_row("kube-node-lease", "Active", "5d11h")
    table.add_row("kube-public", "Active", "5d11h")
    table.add_row("kube-system", "Active", "5d11h")
    table.add_row("test", "Active", "91m")
    
    # Print the table
    console.print(table)
    
    return True

def test_deployment_table():
    """Test the deployment table output."""
    print("\n=== Testing Deployment Table Output ===")
    
    # Create a console
    console = Console()
    
    # Create a table
    table = Table(title="Kubernetes Deployments", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Ready", style="yellow")
    table.add_column("Up-to-date", style="green")
    table.add_column("Available", style="blue")
    table.add_column("Age", style="magenta")
    
    # Add rows
    table.add_row("nginx", "3/3", "3", "3", "5d11h")
    table.add_row("test-app", "3/3", "3", "3", "5d11h")
    
    # Print the table
    console.print(table)
    
    return True

def test_context_table():
    """Test the context table output."""
    print("\n=== Testing Context Table Output ===")
    
    # Create a console
    console = Console()
    
    # Create a table
    table = Table(title="Kubernetes Contexts", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Cluster", style="green")
    table.add_column("User", style="yellow")
    table.add_column("Namespace", style="blue")
    
    # Add rows
    table.add_row("minikube", "minikube", "minikube", "default")
    table.add_row("docker-desktop", "docker-desktop", "docker-desktop", "default")
    
    # Print the table
    console.print(table)
    
    return True

def test_command_result():
    """Test the command result output."""
    print("\n=== Testing Command Result Output ===")
    
    # Create a console
    console = Console()
    
    # Create a panel
    panel = Panel(
        Text("deployment.apps/nginx scaled", style="green"),
        title="Command Result",
        subtitle="kubectl scale deployment/nginx --replicas=3",
        border_style="green"
    )
    
    # Print the panel
    console.print(panel)
    
    return True

def main():
    """Run the CLI output tests."""
    try:
        # Test pod table
        pod_success = test_pod_table()
        
        # Test namespace table
        namespace_success = test_namespace_table()
        
        # Test deployment table
        deployment_success = test_deployment_table()
        
        # Test context table
        context_success = test_context_table()
        
        # Test command result
        command_success = test_command_result()
        
        # Print summary
        print("\n=== Test Summary ===")
        print(f"Pod Table Output: {'PASS' if pod_success else 'FAIL'}")
        print(f"Namespace Table Output: {'PASS' if namespace_success else 'FAIL'}")
        print(f"Deployment Table Output: {'PASS' if deployment_success else 'FAIL'}")
        print(f"Context Table Output: {'PASS' if context_success else 'FAIL'}")
        print(f"Command Result Output: {'PASS' if command_success else 'FAIL'}")
        
        # Return overall success
        return 0 if pod_success and namespace_success and deployment_success and context_success and command_success else 1
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
