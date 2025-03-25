#!/usr/bin/env python3
"""
Full feature demonstration for kubectl-mcp-tool.

This script demonstrates all the key features of kubectl-mcp-tool:
1. Enhanced CLI output with rich formatting
2. Natural language processing for kubectl operations
3. Log analysis with code smell detection
4. Context and namespace switching
5. MCP integration with AI assistants
"""

import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown

from kubectl_mcp_tool.cli_output import CLIOutput
from kubectl_mcp_tool.natural_language import process_query
from kubectl_mcp_tool.context_switcher.context_manager import ContextManager
from kubectl_mcp_tool.context_switcher.namespace_manager import NamespaceManager
from kubectl_mcp_tool.log_analysis.log_analyzer import LogAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="full_feature_demo.log"
)
logger = logging.getLogger("full-feature-demo")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Create Rich console
console = Console()

def print_header(title: str):
    """Print a section header."""
    console.print()
    console.print(Panel(
        Text(title, style="bold cyan", justify="center"),
        border_style="cyan",
        width=100
    ))
    console.print()

def print_subheader(title: str):
    """Print a subsection header."""
    console.print()
    console.print(Text(f"▶ {title}", style="bold yellow"))
    console.print()

def demo_natural_language():
    """Demonstrate natural language processing."""
    print_header("Natural Language Processing for Kubernetes")
    
    cli = CLIOutput()
    
    # Test queries
    queries = [
        "get all pods",
        "show namespaces",
        "list deployments in kube-system namespace",
        "describe the coredns deployment in kube-system",
        "get nodes and their status"
    ]
    
    for query in queries:
        print_subheader(f"Query: '{query}'")
        result = process_query(query)
        
        if result.get("success", False):
            console.print(f"[bold green]Command:[/bold green] {result.get('command', '')}")
            console.print(cli.display_command_result(result))
        else:
            console.print(f"[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
        
        # Add a small delay for better readability
        time.sleep(1)

def demo_context_switching():
    """Demonstrate context switching."""
    print_header("Context and Namespace Management")
    
    context_manager = ContextManager()
    namespace_manager = NamespaceManager()
    cli = CLIOutput()
    
    # Get contexts
    print_subheader("Available Kubernetes Contexts")
    contexts = context_manager.get_contexts()
    
    if contexts:
        table = Table(title="Kubernetes Contexts")
        table.add_column("Context Name", style="cyan")
        table.add_column("Status", style="green")
        
        current_context = context_manager.get_current_context()
        current_context_name = current_context.get("result", "") if current_context.get("success", False) else ""
        
        for context in contexts:
            status = "✓ CURRENT" if context == current_context_name else ""
            table.add_row(context, status)
        
        console.print(table)
    else:
        console.print("[bold red]No contexts found[/bold red]")
    
    # Get namespaces
    print_subheader("Available Kubernetes Namespaces")
    namespaces = namespace_manager.get_namespaces()
    
    if namespaces.get("success", False):
        table = Table(title="Kubernetes Namespaces")
        table.add_column("Namespace", style="cyan")
        table.add_column("Status", style="green")
        
        current_namespace = namespace_manager.get_current_namespace()
        current_namespace_name = current_namespace.get("result", "") if current_namespace.get("success", False) else ""
        
        for namespace in namespaces.get("result", []):
            status = "✓ CURRENT" if namespace == current_namespace_name else ""
            table.add_row(namespace, status)
        
        console.print(table)
    else:
        console.print(f"[bold red]Error:[/bold red] {namespaces.get('error', 'Unknown error')}")

def demo_log_analysis():
    """Demonstrate log analysis."""
    print_header("Kubernetes Log Analysis")
    
    log_analyzer = LogAnalyzer()
    cli = CLIOutput()
    
    # Sample log for analysis
    sample_log = """
    2023-05-15T10:44:41.547Z [WARNING] plugin/kubernetes: starting server with unsynced Kubernetes API
    2023-05-15T10:44:41.547Z [INFO] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/rest/request.go:598: failed to list *v1.Service: Get "https://10.96.0.1:443/api/v1/services?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    2023-05-15T10:44:41.547Z [ERROR] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/tools/cache/reflector.go:167: Failed to watch *v1.Service: failed to list *v1.Service: Get "https://10.96.0.1:443/api/v1/services?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    2023-05-15T10:44:41.547Z [ERROR] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/tools/cache/reflector.go:167: Failed to watch *v1.Namespace: failed to list *v1.Namespace: Get "https://10.96.0.1:443/api/v1/namespaces?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    2023-05-15T10:44:42.547Z [ERROR] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/tools/cache/reflector.go:167: Failed to watch *v1.Namespace: failed to list *v1.Namespace: Get "https://10.96.0.1:443/api/v1/namespaces?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    2023-05-15T10:44:43.547Z [WARNING] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/tools/cache/reflector.go:167: Failed to watch *v1.Namespace: failed to list *v1.Namespace: Get "https://10.96.0.1:443/api/v1/namespaces?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    2023-05-15T10:44:44.547Z [INFO] plugin/kubernetes: pkg/mod/k8s.io/client-go@v0.27.1/rest/request.go:598: failed to list *v1.Service: Get "https://10.96.0.1:443/api/v1/services?limit=500&resourceVersion=0": dial tcp 10.96.0.1:443: i/o timeout
    2023-05-15T10:44:45.547Z [ERROR] plugin/kubernetes: Out of memory: Killed process 1234 (kube-apiserver)
    2023-05-15T10:44:46.547Z [ERROR] plugin/kubernetes: Connection refused: connection timed out
    """
    
    print_subheader("Analyzing Sample Kubernetes Logs")
    
    # Detect error patterns
    patterns = log_analyzer.detect_error_patterns(sample_log)
    
    if patterns:
        table = Table(title="Detected Error Patterns")
        table.add_column("Type", style="cyan")
        table.add_column("Line", style="yellow", no_wrap=False)
        table.add_column("Explanation", style="green", no_wrap=False)
        
        for pattern in patterns:
            table.add_row(
                pattern.get("type", ""),
                pattern.get("line", "")[:50] + "..." if len(pattern.get("line", "")) > 50 else pattern.get("line", ""),
                pattern.get("explanation", "")
            )
        
        console.print(table)
    else:
        console.print("[bold yellow]No error patterns found[/bold yellow]")
    
    # Generate code smells
    code_smells = log_analyzer._detect_code_smells(sample_log)
    
    if code_smells:
        print_subheader("Detected Code Smells")
        
        for smell in code_smells:
            console.print(Panel(
                Text.from_markup(f"[bold red]{smell.get('type', '')}[/bold red]\n\n{smell.get('description', '')}\n\n[bold cyan]Recommendation:[/bold cyan] {smell.get('recommendation', '')}"),
                title=f"Code Smell: {smell.get('type', '')}",
                border_style="red",
                width=100
            ))
    else:
        console.print("[bold yellow]No code smells detected[/bold yellow]")

def demo_mcp_integration():
    """Demonstrate MCP integration."""
    print_header("Model Context Protocol (MCP) Integration")
    
    # Show MCP server information
    print_subheader("MCP Server Configuration")
    
    mcp_info = {
        "name": "kubectl-mcp-tool",
        "version": "1.0.0",
        "transports": ["stdio", "sse"],
        "tools": [
            {"name": "process_natural_language", "description": "Process natural language queries for kubectl operations"},
            {"name": "get_pods", "description": "Get Kubernetes pods"},
            {"name": "get_namespaces", "description": "Get Kubernetes namespaces"},
            {"name": "switch_namespace", "description": "Switch to the specified namespace"},
            {"name": "get_deployments", "description": "Get deployments in the specified namespace"},
            {"name": "scale_deployment", "description": "Scale a deployment to the specified number of replicas"},
            {"name": "describe_pod", "description": "Describe a pod in the specified namespace"},
            {"name": "get_logs", "description": "Get logs from a pod in the specified namespace"}
        ]
    }
    
    table = Table(title="MCP Server Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Name", mcp_info["name"])
    table.add_row("Version", mcp_info["version"])
    table.add_row("Transports", ", ".join(mcp_info["transports"]))
    
    console.print(table)
    
    # Show available tools
    print_subheader("Available MCP Tools")
    
    tools_table = Table(title="MCP Tools")
    tools_table.add_column("Tool Name", style="cyan")
    tools_table.add_column("Description", style="green")
    
    for tool in mcp_info["tools"]:
        tools_table.add_row(tool["name"], tool["description"])
    
    console.print(tools_table)
    
    # Show integration examples
    print_subheader("AI Assistant Integration")
    
    integrations = [
        {
            "name": "Cursor",
            "type": "Code Editor",
            "transport": "stdio",
            "command": "python cursor_compatible_mcp_server.py"
        },
        {
            "name": "Windsurf",
            "type": "AI Assistant",
            "transport": "sse",
            "command": "python windsurf_compatible_mcp_server.py"
        },
        {
            "name": "Claude",
            "type": "AI Assistant",
            "transport": "http",
            "command": "python claude_compatible_mcp_server.py"
        }
    ]
    
    integration_table = Table(title="AI Assistant Integrations")
    integration_table.add_column("Assistant", style="cyan")
    integration_table.add_column("Type", style="yellow")
    integration_table.add_column("Transport", style="green")
    integration_table.add_column("Command", style="magenta")
    
    for integration in integrations:
        integration_table.add_row(
            integration["name"],
            integration["type"],
            integration["transport"],
            integration["command"]
        )
    
    console.print(integration_table)

def main():
    """Run the full feature demonstration."""
    try:
        console.print(Panel(
            Text("kubectl-mcp-tool Full Feature Demonstration", style="bold white", justify="center"),
            border_style="green",
            width=100
        ))
        
        console.print(Markdown("""
        This demonstration showcases the key features of kubectl-mcp-tool:
        
        1. **Natural Language Processing** - Use plain English to interact with Kubernetes
        2. **Enhanced CLI Output** - Beautiful terminal output with rich formatting
        3. **Log Analysis** - Detect code smells and explain errors in plain English
        4. **Context Management** - Easily switch between contexts and namespaces
        5. **MCP Integration** - Seamless integration with AI assistants
        """))
        
        # Run all demos
        demo_natural_language()
        demo_context_switching()
        demo_log_analysis()
        demo_mcp_integration()
        
        console.print()
        console.print(Panel(
            Text("Demonstration Completed Successfully", style="bold green", justify="center"),
            border_style="green",
            width=100
        ))
    except Exception as e:
        logger.error(f"Error in demonstration: {e}")
        console.print(f"[bold red]Error in demonstration:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
