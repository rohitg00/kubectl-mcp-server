#!/usr/bin/env python3
"""
Direct kubectl test script using the rich library for formatting.
"""

import subprocess
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def run_kubectl_command(command):
    """Run a kubectl command and return the output."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print(f"[bold red]Error output:[/bold red] {e.stderr}")
        return None

def display_pods():
    """Display pods with rich formatting."""
    console.print("\n[bold cyan]Getting pods:[/bold cyan]")
    
    # Get pods in JSON format
    output = run_kubectl_command(["kubectl", "get", "pods", "-o", "json"])
    if not output:
        return
    
    # Parse JSON output
    pods_data = json.loads(output)
    
    # Create a table
    table = Table(title="Kubernetes Pods")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Ready", style="yellow")
    table.add_column("Restarts", style="red")
    table.add_column("Age", style="blue")
    
    # Add rows
    for pod in pods_data["items"]:
        name = pod["metadata"]["name"]
        status = pod["status"]["phase"]
        
        # Calculate ready containers
        containers = pod["spec"]["containers"]
        container_statuses = pod["status"].get("containerStatuses", [])
        ready_count = sum(1 for container in container_statuses if container["ready"])
        ready = f"{ready_count}/{len(containers)}"
        
        # Get restart count
        restarts = sum(container["restartCount"] for container in container_statuses)
        
        # Calculate age
        creation_timestamp = pod["metadata"]["creationTimestamp"]
        age = creation_timestamp  # Simplified for demo
        
        table.add_row(name, status, ready, str(restarts), age)
    
    console.print(table)

def display_namespaces():
    """Display namespaces with rich formatting."""
    console.print("\n[bold cyan]Getting namespaces:[/bold cyan]")
    
    # Get namespaces in JSON format
    output = run_kubectl_command(["kubectl", "get", "namespaces", "-o", "json"])
    if not output:
        return
    
    # Parse JSON output
    namespaces_data = json.loads(output)
    
    # Create a table
    table = Table(title="Kubernetes Namespaces")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Age", style="blue")
    
    # Add rows
    for namespace in namespaces_data["items"]:
        name = namespace["metadata"]["name"]
        status = namespace["status"]["phase"]
        
        # Calculate age
        creation_timestamp = namespace["metadata"]["creationTimestamp"]
        age = creation_timestamp  # Simplified for demo
        
        table.add_row(name, status, age)
    
    console.print(table)

def display_deployments():
    """Display deployments with rich formatting."""
    console.print("\n[bold cyan]Getting deployments:[/bold cyan]")
    
    # Get deployments in JSON format
    output = run_kubectl_command(["kubectl", "get", "deployments", "-o", "json"])
    if not output:
        return
    
    # Parse JSON output
    deployments_data = json.loads(output)
    
    # Create a table
    table = Table(title="Kubernetes Deployments")
    table.add_column("Name", style="cyan")
    table.add_column("Ready", style="yellow")
    table.add_column("Up-to-date", style="green")
    table.add_column("Available", style="blue")
    table.add_column("Age", style="magenta")
    
    # Add rows
    for deployment in deployments_data["items"]:
        name = deployment["metadata"]["name"]
        
        # Get ready/desired replicas
        ready = deployment["status"].get("readyReplicas", 0)
        desired = deployment["spec"]["replicas"]
        ready_status = f"{ready}/{desired}"
        
        # Get updated replicas
        updated = deployment["status"].get("updatedReplicas", 0)
        
        # Get available replicas
        available = deployment["status"].get("availableReplicas", 0)
        
        # Calculate age
        creation_timestamp = deployment["metadata"]["creationTimestamp"]
        age = creation_timestamp  # Simplified for demo
        
        table.add_row(name, ready_status, str(updated), str(available), age)
    
    console.print(table)

def main():
    """Main function."""
    console.print(Panel.fit("Direct kubectl Test", border_style="green"))
    
    # Display pods
    display_pods()
    
    # Display namespaces
    display_namespaces()
    
    # Display deployments
    display_deployments()
    
    console.print(Panel.fit("Test completed successfully!", border_style="green"))

if __name__ == "__main__":
    main() 