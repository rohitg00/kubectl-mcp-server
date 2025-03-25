#!/usr/bin/env python3
"""
Comprehensive demo script for kubectl-mcp-tool.

This script demonstrates all features of the kubectl-mcp-tool, including:
- Natural language processing for kubectl operations
- Enhanced CLI output formatting with rich terminal styling
- Log analysis features for detecting code smells and explaining errors
- Context and namespace switching using kubectx integration
"""

import json
import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from kubectl_mcp_tool.natural_language import process_query
from kubectl_mcp_tool.cli_output import CLIOutput
from kubectl_mcp_tool.log_analysis.log_analyzer import LogAnalyzer
from kubectl_mcp_tool.context_switcher.context_manager import ContextManager
from kubectl_mcp_tool.context_switcher.namespace_manager import NamespaceManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="comprehensive_demo.log"
)
logger = logging.getLogger("comprehensive-demo")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def section_header(title: str):
    """Display a section header."""
    console = Console()
    console.print()
    console.print(Panel(Text(title, style="bold cyan"), border_style="cyan"))
    console.print()

def demo_natural_language():
    """Demonstrate natural language processing for kubectl operations."""
    section_header("Natural Language Processing for kubectl Operations")
    
    console = Console()
    cli_output = CLIOutput()
    
    queries = [
        "get all pods",
        "show namespaces",
        "list deployments",
        "describe pod nginx-pod in namespace default",
        "scale deployment nginx to 3 replicas",
        "switch to namespace kube-system",
        "get logs from pod nginx-pod container nginx"
    ]
    
    for query in queries:
        console.print(f"[bold green]Query:[/bold green] {query}")
        
        try:
            # Process the query
            result = process_query(query)
            
            console.print(f"[bold yellow]Command:[/bold yellow] {result.get('command', 'Unknown')}")
            
            # Display result using rich formatting
            if "pods" in query:
                cli_output.display_pods(result)
            elif "namespaces" in query:
                cli_output.display_namespaces(result)
            elif "deployments" in query:
                cli_output.display_deployments(result)
            elif "describe" in query:
                cli_output.display_pod_description(result)
            elif "scale" in query:
                cli_output.display_command_result(result)
            elif "switch" in query:
                cli_output.display_command_result(result)
            elif "logs" in query:
                cli_output.display_pod_logs(result)
            else:
                cli_output.display_command_result(result)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
        
        console.print()
        time.sleep(1)  # Pause for readability

def demo_log_analysis():
    """Demonstrate log analysis features."""
    section_header("Log Analysis Features")
    
    console = Console()
    log_analyzer = LogAnalyzer()
    
    # Get available pods
    try:
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "get", "pods", "--all-namespaces", "-o", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            pods_data = json.loads(result.stdout)
            pod_items = pods_data.get("items", [])
            
            if pod_items:
                # Select a pod for analysis
                selected_pod = pod_items[0]
                pod_name = selected_pod.get("metadata", {}).get("name", "")
                namespace = selected_pod.get("metadata", {}).get("namespace", "default")
                
                console.print(f"[bold green]Analyzing logs for pod:[/bold green] {pod_name} in namespace: {namespace}")
                
                # Get containers in the pod
                containers = []
                for container in selected_pod.get("spec", {}).get("containers", []):
                    container_name = container.get("name", "")
                    if container_name:
                        containers.append(container_name)
                
                if containers:
                    container_name = containers[0]
                    console.print(f"[bold green]Container:[/bold green] {container_name}")
                    
                    # Analyze logs
                    analysis = log_analyzer.analyze_logs(pod_name, namespace, container_name, 100)
                    
                    if analysis.get("success", False):
                        result = analysis.get("result", {})
                        
                        # Display summary
                        console.print(f"[bold green]Summary:[/bold green] {result.get('summary', 'No summary available.')}")
                        
                        # Display code smells
                        code_smells = result.get("code_smells", [])
                        if code_smells:
                            console.print(f"\n[bold green]Detected {len(code_smells)} code smells:[/bold green]")
                            
                            for i, code_smell in enumerate(code_smells, 1):
                                console.print(f"{i}. [bold yellow]{code_smell.get('type', 'Unknown')}:[/bold yellow] {code_smell.get('description', '')}")
                                console.print(f"   [bold cyan]Recommendation:[/bold cyan] {code_smell.get('recommendation', '')}")
                        else:
                            console.print("\n[bold green]No code smells detected.[/bold green]")
                        
                        # Display errors
                        errors = result.get("errors", [])
                        if errors:
                            console.print(f"\n[bold green]Detected {len(errors)} errors:[/bold green]")
                            
                            for i, error in enumerate(errors, 1):
                                console.print(f"{i}. [bold red]{error.get('type', 'Unknown')}:[/bold red] {error.get('line', '')}")
                                console.print(f"   [bold cyan]Explanation:[/bold cyan] {error.get('explanation', '')}")
                        else:
                            console.print("\n[bold green]No errors detected.[/bold green]")
                        
                        # Display recommendations
                        recommendations = result.get("recommendations", [])
                        if recommendations:
                            console.print(f"\n[bold green]Recommendations ({len(recommendations)}):[/bold green]")
                            
                            for i, recommendation in enumerate(recommendations, 1):
                                console.print(f"{i}. {recommendation}")
                        else:
                            console.print("\n[bold green]No recommendations available.[/bold green]")
                    else:
                        console.print(f"[bold red]Error analyzing logs:[/bold red] {analysis.get('error', 'Unknown error')}")
                else:
                    console.print("[bold yellow]No containers found in the pod.[/bold yellow]")
            else:
                console.print("[bold yellow]No pods found in the cluster.[/bold yellow]")
                
                # Use sample logs for demonstration
                console.print("\n[bold green]Using sample logs for demonstration:[/bold green]")
                
                sample_logs = """
2023-03-15T10:15:30 ERROR Failed to connect to database: Connection refused
2023-03-15T10:16:45 WARNING Memory usage above 80%
2023-03-15T10:17:20 ERROR Exception in thread "main" java.lang.NullPointerException
2023-03-15T10:18:10 INFO Pod nginx-pod started successfully
2023-03-15T10:19:05 ERROR CrashLoopBackOff: Back-off restarting failed container
                """
                
                # Detect code smells
                code_smells = log_analyzer._detect_code_smells(sample_logs)
                
                if code_smells:
                    console.print(f"\n[bold green]Detected {len(code_smells)} code smells:[/bold green]")
                    
                    for i, code_smell in enumerate(code_smells, 1):
                        console.print(f"{i}. [bold yellow]{code_smell.get('type', 'Unknown')}:[/bold yellow] {code_smell.get('description', '')}")
                        console.print(f"   [bold cyan]Recommendation:[/bold cyan] {code_smell.get('recommendation', '')}")
                else:
                    console.print("\n[bold green]No code smells detected.[/bold green]")
                
                # Detect errors
                errors = log_analyzer._detect_errors(sample_logs)
                
                if errors:
                    console.print(f"\n[bold green]Detected {len(errors)} errors:[/bold green]")
                    
                    for i, error in enumerate(errors, 1):
                        console.print(f"{i}. [bold red]{error.get('type', 'Unknown')}:[/bold red] {error.get('line', '')}")
                        console.print(f"   [bold cyan]Explanation:[/bold cyan] {error.get('explanation', '')}")
                else:
                    console.print("\n[bold green]No errors detected.[/bold green]")
        else:
            console.print(f"[bold red]Error getting pods:[/bold red] {result.stderr}")
            
            # Use sample logs for demonstration
            console.print("\n[bold green]Using sample logs for demonstration:[/bold green]")
            
            sample_logs = """
2023-03-15T10:15:30 ERROR Failed to connect to database: Connection refused
2023-03-15T10:16:45 WARNING Memory usage above 80%
2023-03-15T10:17:20 ERROR Exception in thread "main" java.lang.NullPointerException
2023-03-15T10:18:10 INFO Pod nginx-pod started successfully
2023-03-15T10:19:05 ERROR CrashLoopBackOff: Back-off restarting failed container
            """
            
            # Detect code smells
            code_smells = log_analyzer._detect_code_smells(sample_logs)
            
            if code_smells:
                console.print(f"\n[bold green]Detected {len(code_smells)} code smells:[/bold green]")
                
                for i, code_smell in enumerate(code_smells, 1):
                    console.print(f"{i}. [bold yellow]{code_smell.get('type', 'Unknown')}:[/bold yellow] {code_smell.get('description', '')}")
                    console.print(f"   [bold cyan]Recommendation:[/bold cyan] {code_smell.get('recommendation', '')}")
            else:
                console.print("\n[bold green]No code smells detected.[/bold green]")
            
            # Detect errors
            errors = log_analyzer._detect_errors(sample_logs)
            
            if errors:
                console.print(f"\n[bold green]Detected {len(errors)} errors:[/bold green]")
                
                for i, error in enumerate(errors, 1):
                    console.print(f"{i}. [bold red]{error.get('type', 'Unknown')}:[/bold red] {error.get('line', '')}")
                    console.print(f"   [bold cyan]Explanation:[/bold cyan] {error.get('explanation', '')}")
            else:
                console.print("\n[bold green]No errors detected.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error in log analysis demo:[/bold red] {str(e)}")

def demo_context_switching():
    """Demonstrate context and namespace switching."""
    section_header("Context and Namespace Switching")
    
    console = Console()
    context_manager = ContextManager()
    namespace_manager = NamespaceManager()
    cli_output = CLIOutput()
    
    # Get available contexts
    try:
        contexts = context_manager.get_contexts()
        
        if contexts:
            console.print(f"[bold green]Available contexts ({len(contexts)}):[/bold green]")
            
            for i, context in enumerate(contexts, 1):
                console.print(f"{i}. {context}")
            
            # Get current context
            current_context = context_manager.get_current_context()
            console.print(f"\n[bold green]Current context:[/bold green] {current_context}")
            
            # Get context details
            console.print("\n[bold green]Context details:[/bold green]")
            context_details = context_manager.get_context_details(current_context)
            
            if context_details.get("success", False):
                console.print(context_details.get("result", ""))
            else:
                console.print(f"[bold red]Error getting context details:[/bold red] {context_details.get('error', 'Unknown error')}")
        else:
            console.print("[bold yellow]No contexts found.[/bold yellow]")
        
        # Get available namespaces
        namespaces_data = namespace_manager.get_namespaces()
        
        if namespaces_data.get("success", False):
            namespaces = namespaces_data.get("result", [])
            
            if namespaces:
                console.print(f"\n[bold green]Available namespaces ({len(namespaces)}):[/bold green]")
                
                for i, namespace in enumerate(namespaces, 1):
                    console.print(f"{i}. {namespace}")
                
                # Get current namespace
                current_namespace_data = namespace_manager.get_current_namespace()
                
                if current_namespace_data.get("success", False):
                    current_namespace = current_namespace_data.get("result", "default")
                    console.print(f"\n[bold green]Current namespace:[/bold green] {current_namespace}")
                else:
                    console.print(f"[bold red]Error getting current namespace:[/bold red] {current_namespace_data.get('error', 'Unknown error')}")
                
                # Switch namespace
                target_namespace = None
                
                for namespace in namespaces:
                    if namespace != current_namespace_data.get("result", "default"):
                        target_namespace = namespace
                        break
                
                if target_namespace:
                    console.print(f"\n[bold green]Switching to namespace:[/bold green] {target_namespace}")
                    switch_result = namespace_manager.switch_namespace(target_namespace)
                    
                    if switch_result.get("success", False):
                        console.print(f"[bold green]Successfully switched to namespace:[/bold green] {target_namespace}")
                        console.print(f"[bold cyan]Result:[/bold cyan] {switch_result.get('result', '')}")
                    else:
                        console.print(f"[bold red]Error switching namespace:[/bold red] {switch_result.get('error', 'Unknown error')}")
                    
                    # Switch back to original namespace
                    if current_namespace_data.get("success", False):
                        original_namespace = current_namespace_data.get("result", "default")
                        console.print(f"\n[bold green]Switching back to original namespace:[/bold green] {original_namespace}")
                        switch_result = namespace_manager.switch_namespace(original_namespace)
                        
                        if switch_result.get("success", False):
                            console.print(f"[bold green]Successfully switched back to namespace:[/bold green] {original_namespace}")
                            console.print(f"[bold cyan]Result:[/bold cyan] {switch_result.get('result', '')}")
                        else:
                            console.print(f"[bold red]Error switching namespace:[/bold red] {switch_result.get('error', 'Unknown error')}")
                else:
                    console.print("[bold yellow]No alternative namespace found to switch to.[/bold yellow]")
            else:
                console.print("[bold yellow]No namespaces found.[/bold yellow]")
        else:
            console.print(f"[bold red]Error getting namespaces:[/bold red] {namespaces_data.get('error', 'Unknown error')}")
    except Exception as e:
        console.print(f"[bold red]Error in context switching demo:[/bold red] {str(e)}")

def demo_enhanced_cli_output():
    """Demonstrate enhanced CLI output formatting."""
    section_header("Enhanced CLI Output Formatting")
    
    console = Console()
    cli_output = CLIOutput()
    
    try:
        # Get pods
        console.print("[bold green]Getting pods with enhanced CLI output:[/bold green]")
        
        import subprocess
        
        result = subprocess.run(
            ["kubectl", "get", "pods", "--all-namespaces", "-o", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            pods_data = {
                "success": True,
                "command": "kubectl get pods --all-namespaces -o json",
                "result": json.loads(result.stdout)
            }
            
            cli_output.display_pods(pods_data)
        else:
            console.print(f"[bold red]Error getting pods:[/bold red] {result.stderr}")
        
        # Get namespaces
        console.print("\n[bold green]Getting namespaces with enhanced CLI output:[/bold green]")
        
        result = subprocess.run(
            ["kubectl", "get", "namespaces", "-o", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            namespaces_data = {
                "success": True,
                "command": "kubectl get namespaces -o json",
                "result": json.loads(result.stdout)
            }
            
            cli_output.display_namespaces(namespaces_data)
        else:
            console.print(f"[bold red]Error getting namespaces:[/bold red] {result.stderr}")
        
        # Get deployments
        console.print("\n[bold green]Getting deployments with enhanced CLI output:[/bold green]")
        
        result = subprocess.run(
            ["kubectl", "get", "deployments", "--all-namespaces", "-o", "json"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            deployments_data = {
                "success": True,
                "command": "kubectl get deployments --all-namespaces -o json",
                "result": json.loads(result.stdout)
            }
            
            cli_output.display_deployments(deployments_data)
        else:
            console.print(f"[bold red]Error getting deployments:[/bold red] {result.stderr}")
    except Exception as e:
        console.print(f"[bold red]Error in enhanced CLI output demo:[/bold red] {str(e)}")

def demo_mcp_integration():
    """Demonstrate MCP integration."""
    section_header("Model Context Protocol (MCP) Integration")
    
    console = Console()
    
    console.print("[bold green]The kubectl-mcp-tool implements the Model Context Protocol (MCP) specification,[/bold green]")
    console.print("[bold green]allowing it to be used with AI assistants like Claude, Cursor, and Windsurf.[/bold green]")
    
    console.print("\n[bold cyan]MCP Tool Registration:[/bold cyan]")
    console.print("The tool registers the following capabilities with MCP clients:")
    console.print("1. Natural language processing for kubectl operations")
    console.print("2. Pod management (get, describe, delete)")
    console.print("3. Namespace management (get, create, delete, switch)")
    console.print("4. Deployment management (get, scale, create)")
    console.print("5. Context switching")
    console.print("6. Log analysis")
    
    console.print("\n[bold cyan]MCP Transport Protocols:[/bold cyan]")
    console.print("The tool supports the following MCP transport protocols:")
    console.print("1. stdio - For Cursor integration")
    console.print("2. SSE (Server-Sent Events) - For Windsurf integration")
    
    console.print("\n[bold cyan]Example MCP Tool Call:[/bold cyan]")
    console.print("""
{
    "jsonrpc": "2.0",
    "id": "call",
    "method": "mcp.tool.call",
    "params": {
        "name": "process_natural_language",
        "input": {
            "query": "get all pods"
        }
    }
}
    """)
    
    console.print("\n[bold cyan]Example MCP Tool Response:[/bold cyan]")
    console.print("""
{
    "jsonrpc": "2.0",
    "id": "call",
    "result": {
        "command": "kubectl get pods --all-namespaces",
        "result": "NAMESPACE     NAME                               READY   STATUS    RESTARTS   AGE\\ndefault       nginx-pod                         1/1     Running   0          10m\\nkube-system   coredns-558bd4d5db-d9bnp          1/1     Running   0          30m"
    }
}
    """)

def main():
    """Run the comprehensive demo."""
    console = Console()
    
    try:
        # Display welcome message
        console.print(Panel(Text("kubectl-mcp-tool Comprehensive Demo", style="bold magenta"), border_style="magenta"))
        
        # Demonstrate enhanced CLI output formatting
        demo_enhanced_cli_output()
        
        # Demonstrate natural language processing
        demo_natural_language()
        
        # Demonstrate log analysis
        demo_log_analysis()
        
        # Demonstrate context switching
        demo_context_switching()
        
        # Demonstrate MCP integration
        demo_mcp_integration()
        
        # Final message
        console.print(Panel(Text("Demo completed successfully!", style="bold green"), border_style="green"))
    except KeyboardInterrupt:
        console.print("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        console.print(f"[bold red]Error in demo:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()
