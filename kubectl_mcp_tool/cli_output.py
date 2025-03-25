#!/usr/bin/env python3
"""
CLI output formatting for kubectl-mcp-tool.

This module provides rich terminal formatting for kubectl command output,
inspired by k9s and k8sgpt for enhanced user experience.
"""

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Tuple

from rich.console import Console, RenderableType
from rich.table import Table, Column
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.syntax import Syntax
from rich.box import Box, ROUNDED, HEAVY, DOUBLE
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.tree import Tree
from rich.prompt import Prompt
from rich.style import Style
from rich.highlighter import ReprHighlighter
from rich import box

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="cli_output.log"
)
logger = logging.getLogger("cli-output")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

class CLIOutput:
    """Class for formatting kubectl command output with beautiful and enhanced style."""
    
    # Status color mapping
    STATUS_COLORS = {
        "Running": "green",
        "Pending": "yellow",
        "Succeeded": "blue",
        "Failed": "red",
        "Unknown": "magenta",
        "Completed": "green",
        "Error": "red",
        "Warning": "yellow",
        "CrashLoopBackOff": "red bold",
        "Terminating": "yellow",
        "Active": "green",
        "Inactive": "red",
    }
    
    # Resource type icons
    RESOURCE_ICONS = {
        "pod": "📦",
        "deployment": "🚀",
        "service": "🔌",
        "namespace": "🏠",
        "node": "💻",
        "configmap": "📝",
        "secret": "🔒",
        "persistentvolume": "💾",
        "persistentvolumeclaim": "📂",
        "ingress": "🌐",
        "job": "⏱️",
        "cronjob": "🔄",
        "daemonset": "👥",
        "statefulset": "📊",
        "replicaset": "📋",
        "default": "🔷",
    }
    
    def __init__(self):
        """Initialize the CLIOutput class."""
        self.console = Console()
        self.highlighter = ReprHighlighter()
        self.layout = Layout()
        logger.info("CLI Output initialized with beautiful and enhanced style")
    
    def calculate_age(self, timestamp_str: str) -> str:
        """
        Calculate age from timestamp.
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            Human-readable age string
        """
        if not timestamp_str:
            return "N/A"
            
        try:
            # Parse the timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            
            # Calculate the difference
            diff = now - timestamp
            
            # Format the age
            if diff.days > 365:
                years = diff.days // 365
                return f"{years}y"
            elif diff.days > 30:
                months = diff.days // 30
                return f"{months}m"
            elif diff.days > 0:
                return f"{diff.days}d"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}h"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}m"
            else:
                return f"{diff.seconds}s"
        except Exception as e:
            logger.error(f"Error calculating age: {e}")
            return "N/A"
    
    def display_pods(self, pods_data: Dict[str, Any], interactive: bool = True) -> str:
        """
        Display pods in a rich table with k9s-style formatting.
        
        Args:
            pods_data: Dictionary containing pods data from kubectl
            interactive: Whether to display in interactive mode
            
        Returns:
            Rendered table as a string
        """
        # Create a styled header
        header = Text("✨ Kubernetes Pods ✨", style="bold cyan")
        self.console.print(header, justify="center")
        
        # Create the table with a heavy box style
        table = Table(box=box.HEAVY, show_header=True, header_style="bold cyan")
        
        # Add columns with icons
        table.add_column("📦 Name", style="cyan bold")
        table.add_column("⚡ Ready", style="yellow")
        table.add_column("🚦 Status", style="green")
        table.add_column("🔄 Restarts", style="red")
        table.add_column("⏱️ Age", style="blue")
        table.add_column("🌐 IP", style="magenta")
        table.add_column("💻 Node", style="cyan")
        
        if not pods_data.get("success", False):
            error_message = pods_data.get("error", "Unknown error")
            error_panel = Panel(
                f"[bold red]{error_message}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error: {error_message}"
        
        try:
            pods = pods_data.get("result", {}).get("items", [])
            
            if not pods:
                empty_panel = Panel(
                    "[yellow]No pods found in the current namespace[/yellow]",
                    title="[bold yellow]Empty Result[/bold yellow]",
                    border_style="yellow",
                    box=box.HEAVY
                )
                self.console.print(empty_panel)
                return "No pods found"
            
            # Add a progress spinner for loading effect
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Processing pods...[/bold green]"),
                transient=True,
            ) as progress:
                task = progress.add_task("Processing", total=len(pods))
                
                for pod in pods:
                    progress.update(task, advance=1)
                    time.sleep(0.05)  # Small delay for visual effect
                    
                    name = pod.get("metadata", {}).get("name", "")
                    status_phase = pod.get("status", {}).get("phase", "")
                    
                    # Get detailed status
                    container_statuses = pod.get("status", {}).get("containerStatuses", [])
                    detailed_status = status_phase
                    
                    # Check for container issues
                    for container in container_statuses:
                        waiting = container.get("state", {}).get("waiting", {})
                        if waiting:
                            reason = waiting.get("reason", "")
                            if reason:
                                detailed_status = reason
                                break
                    
                    # Calculate ready containers
                    containers = pod.get("spec", {}).get("containers", [])
                    ready_count = sum(1 for status in container_statuses if status.get("ready", False))
                    total_count = len(containers)
                    ready = f"{ready_count}/{total_count}"
                    
                    # Get restart count
                    restarts = sum(status.get("restartCount", 0) for status in container_statuses)
                    
                    # Get pod age
                    creation_timestamp = pod.get("metadata", {}).get("creationTimestamp", "")
                    age = self.calculate_age(creation_timestamp)
                    
                    # Get pod IP
                    pod_ip = pod.get("status", {}).get("podIP", "")
                    
                    # Get node name
                    node_name = pod.get("spec", {}).get("nodeName", "")
                    
                    # Set status color based on phase or detailed status
                    status_style = self.STATUS_COLORS.get(detailed_status, self.STATUS_COLORS.get(status_phase, "white"))
                    
                    # Add emoji indicators based on status
                    status_indicator = "✅ " if status_phase == "Running" and ready_count == total_count else ""
                    if status_phase == "Pending":
                        status_indicator = "⏳ "
                    elif status_phase == "Failed" or "Error" in detailed_status or "BackOff" in detailed_status:
                        status_indicator = "❌ "
                    elif status_phase == "Succeeded":
                        status_indicator = "🎉 "
                    
                    # Format name with emoji
                    name_text = Text(f"{self.RESOURCE_ICONS['pod']} {name}")
                    
                    # Format ready count with color
                    ready_text = Text(ready)
                    if ready_count < total_count:
                        ready_text.stylize("yellow")
                    else:
                        ready_text.stylize("green")
                    
                    # Format status with color
                    status_text = Text(f"{status_indicator}{detailed_status}")
                    status_text.stylize(status_style)
                    
                    # Format restart count with color
                    restart_text = Text(str(restarts))
                    if restarts > 5:
                        restart_text.stylize("red bold")
                    elif restarts > 0:
                        restart_text.stylize("yellow")
                    else:
                        restart_text.stylize("green")
                    
                    table.add_row(
                        name_text,
                        ready_text,
                        status_text,
                        restart_text,
                        age,
                        pod_ip or "N/A",
                        node_name or "N/A"
                    )
            
            # Add a footer with helpful information
            footer = Text("Press Ctrl+C to exit | Use kubectl describe pod <name> for details", style="italic")
            
            # Print the table with a panel
            self.console.print(table)
            self.console.print(footer, justify="center")
            
            # If interactive mode is enabled, allow selection
            if interactive:
                try:
                    pod_names = [pod.get("metadata", {}).get("name", "") for pod in pods]
                    if pod_names:
                        self.console.print("\n[bold cyan]Select a pod for more details:[/bold cyan]")
                        for i, name in enumerate(pod_names, 1):
                            self.console.print(f"[cyan]{i}.[/cyan] {name}")
                        
                        # This is just for display in the demo - in a real implementation,
                        # we would use Prompt.ask() to get user input
                        self.console.print("[dim]Enter pod number or press Enter to skip...[/dim]")
                except KeyboardInterrupt:
                    pass
            
            return str(table)
        
        except Exception as e:
            logger.error(f"Error displaying pods: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Displaying Pods[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error displaying pods: {e}"
    
    def display_namespaces(self, namespaces_data: Dict[str, Any], interactive: bool = True) -> str:
        """
        Display namespaces in a rich table with k9s-style formatting.
        
        Args:
            namespaces_data: Dictionary containing namespaces data from kubectl
            interactive: Whether to display in interactive mode
            
        Returns:
            Rendered table as a string
        """
        # Create a styled header
        header = Text("🏠 Kubernetes Namespaces 🏠", style="bold cyan")
        self.console.print(header, justify="center")
        
        # Create the table with a heavy box style
        table = Table(box=box.HEAVY, show_header=True, header_style="bold cyan")
        
        # Add columns with icons
        table.add_column("🏠 Name", style="cyan bold")
        table.add_column("🚦 Status", style="green")
        table.add_column("⏱️ Age", style="blue")
        table.add_column("📊 Pods", style="magenta")
        
        if not namespaces_data.get("success", False):
            error_message = namespaces_data.get("error", "Unknown error")
            error_panel = Panel(
                f"[bold red]{error_message}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error: {error_message}"
        
        try:
            namespaces = namespaces_data.get("result", {}).get("items", [])
            
            if not namespaces:
                empty_panel = Panel(
                    "[yellow]No namespaces found in the cluster[/yellow]",
                    title="[bold yellow]Empty Result[/bold yellow]",
                    border_style="yellow",
                    box=box.HEAVY
                )
                self.console.print(empty_panel)
                return "No namespaces found"
            
            # Add a progress spinner for loading effect
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Processing namespaces...[/bold green]"),
                transient=True,
            ) as progress:
                task = progress.add_task("Processing", total=len(namespaces))
                
                for namespace in namespaces:
                    progress.update(task, advance=1)
                    time.sleep(0.05)  # Small delay for visual effect
                    
                    name = namespace.get("metadata", {}).get("name", "")
                    status_phase = namespace.get("status", {}).get("phase", "")
                    
                    # Get namespace age
                    creation_timestamp = namespace.get("metadata", {}).get("creationTimestamp", "")
                    age = self.calculate_age(creation_timestamp)
                    
                    # Get pod count (in a real implementation, this would be fetched from the API)
                    # For demo purposes, we'll use a placeholder
                    pod_count = "N/A"
                    
                    # Set status color based on phase
                    status_style = self.STATUS_COLORS.get(status_phase, "white")
                    
                    # Add emoji indicators based on status
                    status_indicator = "✅ " if status_phase == "Active" else "❌ "
                    
                    # Format name with emoji
                    name_text = Text(f"{self.RESOURCE_ICONS['namespace']} {name}")
                    
                    # Format status with color
                    status_text = Text(f"{status_indicator}{status_phase}")
                    status_text.stylize(status_style)
                    
                    table.add_row(
                        name_text,
                        status_text,
                        age,
                        pod_count
                    )
            
            # Add a footer with helpful information
            footer = Text("Press Ctrl+C to exit | Use kubectl describe namespace <name> for details", style="italic")
            
            # Print the table with a panel
            self.console.print(table)
            self.console.print(footer, justify="center")
            
            # If interactive mode is enabled, allow selection
            if interactive:
                try:
                    namespace_names = [namespace.get("metadata", {}).get("name", "") for namespace in namespaces]
                    if namespace_names:
                        self.console.print("\n[bold cyan]Select a namespace to switch to:[/bold cyan]")
                        for i, name in enumerate(namespace_names, 1):
                            self.console.print(f"[cyan]{i}.[/cyan] {name}")
                        
                        # This is just for display in the demo - in a real implementation,
                        # we would use Prompt.ask() to get user input
                        self.console.print("[dim]Enter namespace number or press Enter to skip...[/dim]")
                except KeyboardInterrupt:
                    pass
            
            return str(table)
        
        except Exception as e:
            logger.error(f"Error displaying namespaces: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Displaying Namespaces[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error displaying namespaces: {e}"
    
    def display_deployments(self, deployments_data: Dict[str, Any], interactive: bool = True) -> str:
        """
        Display deployments in a rich table with k9s-style formatting.
        
        Args:
            deployments_data: Dictionary containing deployments data from kubectl
            interactive: Whether to display in interactive mode
            
        Returns:
            Rendered table as a string
        """
        # Create a styled header
        header = Text("🚀 Kubernetes Deployments 🚀", style="bold cyan")
        self.console.print(header, justify="center")
        
        # Create the table with a heavy box style
        table = Table(box=box.HEAVY, show_header=True, header_style="bold cyan")
        
        # Add columns with icons
        table.add_column("🚀 Name", style="cyan bold")
        table.add_column("⚡ Ready", style="yellow")
        table.add_column("🔄 Up-to-date", style="green")
        table.add_column("✅ Available", style="blue")
        table.add_column("⏱️ Age", style="magenta")
        table.add_column("🔍 Strategy", style="cyan")
        
        if not deployments_data.get("success", False):
            error_message = deployments_data.get("error", "Unknown error")
            error_panel = Panel(
                f"[bold red]{error_message}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error: {error_message}"
        
        try:
            deployments = deployments_data.get("result", {}).get("items", [])
            
            if not deployments:
                empty_panel = Panel(
                    "[yellow]No deployments found in the current namespace[/yellow]",
                    title="[bold yellow]Empty Result[/bold yellow]",
                    border_style="yellow",
                    box=box.HEAVY
                )
                self.console.print(empty_panel)
                return "No deployments found"
            
            # Add a progress spinner for loading effect
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Processing deployments...[/bold green]"),
                transient=True,
            ) as progress:
                task = progress.add_task("Processing", total=len(deployments))
                
                for deployment in deployments:
                    progress.update(task, advance=1)
                    time.sleep(0.05)  # Small delay for visual effect
                    
                    name = deployment.get("metadata", {}).get("name", "")
                    
                    # Get deployment status
                    status = deployment.get("status", {})
                    replicas = status.get("replicas", 0)
                    ready_replicas = status.get("readyReplicas", 0) or 0
                    updated_replicas = status.get("updatedReplicas", 0) or 0
                    available_replicas = status.get("availableReplicas", 0) or 0
                    
                    # Get deployment strategy
                    strategy = deployment.get("spec", {}).get("strategy", {}).get("type", "RollingUpdate")
                    
                    # Get deployment age
                    creation_timestamp = deployment.get("metadata", {}).get("creationTimestamp", "")
                    age = self.calculate_age(creation_timestamp)
                    
                    # Format ready count with color
                    ready = f"{ready_replicas}/{replicas}"
                    ready_text = Text(ready)
                    if ready_replicas < replicas:
                        ready_text.stylize("yellow")
                    else:
                        ready_text.stylize("green")
                    
                    # Format name with emoji
                    name_text = Text(f"{self.RESOURCE_ICONS['deployment']} {name}")
                    
                    # Format updated replicas with color
                    updated_text = Text(str(updated_replicas))
                    if updated_replicas < replicas:
                        updated_text.stylize("yellow")
                    else:
                        updated_text.stylize("green")
                    
                    # Format available replicas with color
                    available_text = Text(str(available_replicas))
                    if available_replicas < replicas:
                        available_text.stylize("yellow")
                    else:
                        available_text.stylize("green")
                    
                    # Format strategy with color
                    strategy_text = Text(strategy)
                    if strategy == "RollingUpdate":
                        strategy_text.stylize("green")
                    elif strategy == "Recreate":
                        strategy_text.stylize("yellow")
                    else:
                        strategy_text.stylize("blue")
                    
                    table.add_row(
                        name_text,
                        ready_text,
                        updated_text,
                        available_text,
                        age,
                        strategy_text
                    )
            
            # Add a footer with helpful information
            footer = Text("Press Ctrl+C to exit | Use kubectl describe deployment <name> for details", style="italic")
            
            # Print the table with a panel
            self.console.print(table)
            self.console.print(footer, justify="center")
            
            # If interactive mode is enabled, allow selection
            if interactive:
                try:
                    deployment_names = [deployment.get("metadata", {}).get("name", "") for deployment in deployments]
                    if deployment_names:
                        self.console.print("\n[bold cyan]Select a deployment for more details:[/bold cyan]")
                        for i, name in enumerate(deployment_names, 1):
                            self.console.print(f"[cyan]{i}.[/cyan] {name}")
                        
                        # This is just for display in the demo - in a real implementation,
                        # we would use Prompt.ask() to get user input
                        self.console.print("[dim]Enter deployment number or press Enter to skip...[/dim]")
                except KeyboardInterrupt:
                    pass
            
            return str(table)
        
        except Exception as e:
            logger.error(f"Error displaying deployments: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Displaying Deployments[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error displaying deployments: {e}"
    
    def display_pod_logs(self, logs_data: Dict[str, Any], highlight_errors: bool = True) -> str:
        """
        Display pod logs in a rich panel with k9s-style formatting.
        
        Args:
            logs_data: Dictionary containing logs data from kubectl
            highlight_errors: Whether to highlight errors in the logs
            
        Returns:
            Rendered panel as a string
        """
        if not logs_data.get("success", False):
            error_message = logs_data.get("error", "Unknown error")
            error_panel = Panel(
                f"[bold red]{error_message}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error: {error_message}"
        
        try:
            logs = logs_data.get("result", "")
            command = logs_data.get("command", "")
            pod_name = command.split()[-1] if command else "Unknown Pod"
            
            if not logs:
                empty_panel = Panel(
                    "[yellow]No logs found for this pod[/yellow]",
                    title=f"[bold yellow]Empty Logs: {pod_name}[/bold yellow]",
                    border_style="yellow",
                    box=box.HEAVY
                )
                self.console.print(empty_panel)
                return "No logs found"
            
            # Create a styled header
            header = Text(f"📜 Logs for Pod: {pod_name} 📜", style="bold cyan")
            self.console.print(header, justify="center")
            
            # Process logs for highlighting
            if highlight_errors:
                # Highlight error patterns
                processed_logs = ""
                for line in logs.split("\n"):
                    # Check for error patterns
                    if re.search(r"(?i)error|exception|fail|fatal|panic", line):
                        processed_logs += f"[bold red]{line}[/bold red]\n"
                    elif re.search(r"(?i)warn|warning", line):
                        processed_logs += f"[bold yellow]{line}[/bold yellow]\n"
                    elif re.search(r"(?i)info", line):
                        processed_logs += f"[green]{line}[/green]\n"
                    elif re.search(r"(?i)debug", line):
                        processed_logs += f"[blue]{line}[/blue]\n"
                    else:
                        processed_logs += f"{line}\n"
                
                # Create a panel with the processed logs
                panel = Panel(
                    processed_logs,
                    title=f"[bold blue]{command}[/bold blue]",
                    subtitle="[italic]Press Ctrl+C to exit | Errors are highlighted in red[/italic]",
                    border_style="cyan",
                    box=box.HEAVY
                )
            else:
                # Use syntax highlighting
                syntax = Syntax(logs, "log", theme="monokai", line_numbers=True)
                panel = Panel(
                    syntax,
                    title=f"[bold blue]{command}[/bold blue]",
                    subtitle="[italic]Press Ctrl+C to exit | Use --highlight-errors for error highlighting[/italic]",
                    border_style="cyan",
                    box=box.HEAVY
                )
            
            # Add a progress spinner for loading effect
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Processing logs...[/bold green]"),
                transient=True,
            ) as progress:
                task = progress.add_task("Processing", total=1)
                time.sleep(0.5)  # Small delay for visual effect
                progress.update(task, advance=1)
            
            # Print the panel
            self.console.print(panel)
            
            # Add a footer with helpful information
            footer = Text("Use kubectl logs -f <pod> to follow logs in real-time", style="italic")
            self.console.print(footer, justify="center")
            
            return str(panel)
        
        except Exception as e:
            logger.error(f"Error displaying logs: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Displaying Logs[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error displaying logs: {e}"
    
    def display_pod_description(self, description_data: Dict[str, Any]) -> str:
        """
        Display pod description in a rich panel with k9s-style formatting.
        
        Args:
            description_data: Dictionary containing pod description data from kubectl
        
        Returns:
            Rendered panel as a string
        """
        if not description_data.get("success", False):
            error_message = description_data.get("error", "Unknown error")
            error_panel = Panel(
                f"[bold red]{error_message}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error: {error_message}"
        
        try:
            description = description_data.get("result", "")
            command = description_data.get("command", "")
            pod_name = command.split()[-1] if command else "Unknown Pod"
            
            if not description:
                empty_panel = Panel(
                    "[yellow]No description found for this pod[/yellow]",
                    title=f"[bold yellow]Empty Description: {pod_name}[/bold yellow]",
                    border_style="yellow",
                    box=box.HEAVY
                )
                self.console.print(empty_panel)
                return "No description found"
            
            # Create a styled header
            header = Text(f"🔍 Pod Description: {pod_name} 🔍", style="bold cyan")
            self.console.print(header, justify="center")
            
            # Process the description to highlight important sections
            processed_description = ""
            in_metadata = False
            in_spec = False
            in_status = False
            
            for line in description.split("\n"):
                if "Metadata:" in line:
                    in_metadata = True
                    in_spec = False
                    in_status = False
                    processed_description += f"[bold cyan]{line}[/bold cyan]\n"
                elif "Spec:" in line:
                    in_metadata = False
                    in_spec = True
                    in_status = False
                    processed_description += f"[bold green]{line}[/bold green]\n"
                elif "Status:" in line:
                    in_metadata = False
                    in_spec = False
                    in_status = True
                    processed_description += f"[bold magenta]{line}[/bold magenta]\n"
                elif in_metadata:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        processed_description += f"  [cyan]{key}:[/cyan]{value}\n"
                    else:
                        processed_description += f"  {line}\n"
                elif in_spec:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        processed_description += f"  [green]{key}:[/green]{value}\n"
                    else:
                        processed_description += f"  {line}\n"
                elif in_status:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        processed_description += f"  [magenta]{key}:[/magenta]{value}\n"
                    else:
                        processed_description += f"  {line}\n"
                else:
                    processed_description += f"{line}\n"
            
            # Create a panel with the processed description
            panel = Panel(
                processed_description,
                title=f"[bold blue]{command}[/bold blue]",
                subtitle="[italic]Press Ctrl+C to exit[/italic]",
                border_style="cyan",
                box=box.HEAVY
            )
            
            # Add a progress spinner for loading effect
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Processing description...[/bold green]"),
                transient=True,
            ) as progress:
                task = progress.add_task("Processing", total=1)
                time.sleep(0.5)  # Small delay for visual effect
                progress.update(task, advance=1)
            
            # Print the panel
            self.console.print(panel)
            
            # Add a footer with helpful information
            footer = Text("Use kubectl edit pod <name> to modify the pod configuration", style="italic")
            self.console.print(footer, justify="center")
            
            return str(panel)
        
        except Exception as e:
            logger.error(f"Error displaying pod description: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Displaying Pod Description[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error displaying pod description: {e}"
    
    def display_contexts(self, contexts_data: Dict[str, Any], interactive: bool = True) -> str:
        """
        Display contexts in a rich table with k9s-style formatting.
        
        Args:
            contexts_data: Dictionary containing contexts data from kubectl
            interactive: Whether to display in interactive mode
            
        Returns:
            Rendered table as a string
        """
        # Create a styled header
        header = Text("🌐 Kubernetes Contexts 🌐", style="bold cyan")
        self.console.print(header, justify="center")
        
        # Create the table with a heavy box style
        table = Table(box=box.HEAVY, show_header=True, header_style="bold cyan")
        
        # Add columns with icons
        table.add_column("🔑 Name", style="cyan bold")
        table.add_column("✓ Current", style="green")
        
        if not contexts_data.get("success", False):
            error_message = contexts_data.get("error", "Unknown error")
            error_panel = Panel(
                f"[bold red]{error_message}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error: {error_message}"
        
        try:
            contexts = contexts_data.get("result", [])
            current_context = None
            
            # Get current context
            current_context_data = self.get_current_context()
            if current_context_data.get("success", False):
                current_context = current_context_data.get("result", "")
            
            if not contexts:
                empty_panel = Panel(
                    "[yellow]No contexts found in kubeconfig[/yellow]",
                    title="[bold yellow]Empty Result[/bold yellow]",
                    border_style="yellow",
                    box=box.HEAVY
                )
                self.console.print(empty_panel)
                return "No contexts found"
            
            # Add a progress spinner for loading effect
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Processing contexts...[/bold green]"),
                transient=True,
            ) as progress:
                task = progress.add_task("Processing", total=len(contexts))
                
                for context in contexts:
                    progress.update(task, advance=1)
                    time.sleep(0.05)  # Small delay for visual effect
                    
                    is_current = context == current_context
                    current_marker = "✅" if is_current else ""
                    
                    # Format name with emoji
                    name_text = Text(f"{self.RESOURCE_ICONS.get('default', '🔷')} {context}")
                    if is_current:
                        name_text.stylize("bold cyan")
                    
                    # Format current marker with emoji
                    current_text = Text(current_marker)
                    if is_current:
                        current_text.stylize("bold green")
                    
                    table.add_row(
                        name_text,
                        current_text
                    )
            
            # Add a footer with helpful information
            footer = Text("Press Ctrl+C to exit | Use kubectl config use-context <name> to switch contexts", style="italic")
            
            # Print the table with a panel
            self.console.print(table)
            self.console.print(footer, justify="center")
            
            # If interactive mode is enabled, allow selection
            if interactive:
                try:
                    if contexts:
                        self.console.print("\n[bold cyan]Select a context to switch to:[/bold cyan]")
                        for i, context_name in enumerate(contexts, 1):
                            marker = " (current)" if context_name == current_context else ""
                            self.console.print(f"[cyan]{i}.[/cyan] {context_name}{marker}")
                        
                        # This is just for display in the demo - in a real implementation,
                        # we would use Prompt.ask() to get user input
                        self.console.print("[dim]Enter context number or press Enter to skip...[/dim]")
                except KeyboardInterrupt:
                    pass
            
            return str(table)
        
        except Exception as e:
            logger.error(f"Error displaying contexts: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Displaying Contexts[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error displaying contexts: {e}"
    
    def get_current_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            Dictionary containing the current context
        """
        try:
            import subprocess
            
            result = subprocess.run(
                ["kubectl", "config", "current-context"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "result": result.stdout.strip()
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr.strip()
                }
        except Exception as e:
            logger.error(f"Error getting current context: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_log_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """
        Format log analysis results with k9s-style formatting.
        
        Args:
            analysis_data: Dictionary containing log analysis results
            
        Returns:
            Formatted string representation of the analysis
        """
        if not analysis_data.get("success", False):
            error_message = analysis_data.get("error", "Unknown error")
            error_panel = Panel(
                f"[bold red]{error_message}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error: {error_message}"
        
        try:
            analysis = analysis_data.get("result", {})
            command = analysis_data.get("command", "")
            
            # Create a styled header
            header = Text("🔍 Log Analysis Results 🔍", style="bold cyan")
            self.console.print(header, justify="center")
            
            # Create sections for different types of findings
            code_smells = analysis.get("code_smells", [])
            errors = analysis.get("errors", [])
            summary = analysis.get("summary", "")
            recommendations = analysis.get("recommendations", [])
            
            # Display code smells
            if code_smells:
                smells_table = Table(box=box.HEAVY, show_header=True, header_style="bold yellow")
                smells_table.add_column("🐞 Type", style="yellow")
                smells_table.add_column("📝 Description", style="white")
                smells_table.add_column("💡 Recommendation", style="cyan")
                
                for smell in code_smells:
                    smells_table.add_row(
                        smell.get("type", ""),
                        smell.get("description", ""),
                        smell.get("recommendation", "")
                    )
                
                self.console.print("\n[bold yellow]Code Smells:[/bold yellow]")
                self.console.print(smells_table)
            
            # Display errors
            if errors:
                errors_table = Table(box=box.HEAVY, show_header=True, header_style="bold red")
                errors_table.add_column("❌ Type", style="red")
                errors_table.add_column("📄 Line", style="white")
                errors_table.add_column("ℹ️ Explanation", style="cyan")
                
                for error in errors:
                    errors_table.add_row(
                        error.get("type", ""),
                        error.get("line", ""),
                        error.get("explanation", "")
                    )
                
                self.console.print("\n[bold red]Errors:[/bold red]")
                self.console.print(errors_table)
            
            # Display summary
            if summary:
                summary_panel = Panel(
                    f"[cyan]{summary}[/cyan]",
                    title="[bold cyan]Summary[/bold cyan]",
                    border_style="cyan",
                    box=box.HEAVY
                )
                self.console.print("\n")
                self.console.print(summary_panel)
            
            # Display recommendations
            if recommendations:
                recommendations_panel = Panel(
                    "\n".join(f"[green]•[/green] {rec}" for rec in recommendations),
                    title="[bold green]Recommendations[/bold green]",
                    border_style="green",
                    box=box.HEAVY
                )
                self.console.print("\n")
                self.console.print(recommendations_panel)
            
            return "Log analysis completed successfully"
            
        except Exception as e:
            logger.error(f"Error formatting log analysis: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Formatting Analysis[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error formatting log analysis: {e}"
    
    def format_pod_status(self, pod_data: Dict[str, Any]) -> str:
        """
        Format pod status with k9s-style formatting.
        
        Args:
            pod_data: Dictionary containing pod data
            
        Returns:
            Formatted string representation of pod status
        """
        try:
            # Extract pod information
            name = pod_data.get("metadata", {}).get("name", "")
            namespace = pod_data.get("metadata", {}).get("namespace", "")
            status = pod_data.get("status", {})
            phase = status.get("phase", "")
            container_statuses = status.get("containerStatuses", [])
            
            # Calculate ready containers
            ready_count = sum(1 for status in container_statuses if status.get("ready", False))
            total_count = len(container_statuses)
            ready = f"{ready_count}/{total_count}"
            
            # Get restart count
            restarts = sum(status.get("restartCount", 0) for status in container_statuses)
            
            # Format status with color
            status_style = self.STATUS_COLORS.get(phase, "white")
            status_text = Text(phase)
            status_text.stylize(status_style)
            
            # Add emoji indicators
            status_indicator = "✅ " if phase == "Running" and ready_count == total_count else ""
            if phase == "Pending":
                status_indicator = "⏳ "
            elif phase == "Failed" or "Error" in phase:
                status_indicator = "❌ "
            elif phase == "Succeeded":
                status_indicator = "🎉 "
            
            # Create the output panel
            panel = Panel(
                f"{self.RESOURCE_ICONS['pod']} Name: [cyan]{name}[/cyan]\n"
                f"📍 Namespace: [blue]{namespace}[/blue]\n"
                f"🚦 Status: {status_indicator}{status_text}\n"
                f"⚡ Ready: [{'green' if ready_count == total_count else 'yellow'}]{ready}[/]\n"
                f"🔄 Restarts: [{'red bold' if restarts > 5 else 'yellow' if restarts > 0 else 'green'}]{restarts}[/]",
                title="[bold cyan]Pod Status[/bold cyan]",
                border_style="cyan",
                box=box.HEAVY
            )
            
            # Print the panel
            self.console.print(panel)
            
            return str(panel)
            
        except Exception as e:
            logger.error(f"Error formatting pod status: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Formatting Pod Status[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error formatting pod status: {e}"
    
    def format_namespace_status(self, namespace_data: Dict[str, Any]) -> str:
        """
        Format namespace status with k9s-style formatting.
        
        Args:
            namespace_data: Dictionary containing namespace data
            
        Returns:
            Formatted string representation of namespace status
        """
        try:
            # Extract namespace information
            name = namespace_data.get("metadata", {}).get("name", "")
            status = namespace_data.get("status", {})
            phase = status.get("phase", "")
            
            # Format status with color
            status_style = self.STATUS_COLORS.get(phase, "white")
            status_text = Text(phase)
            status_text.stylize(status_style)
            
            # Add emoji indicators
            status_indicator = "✅ " if phase == "Active" else "❌ "
            
            # Create the output panel
            panel = Panel(
                f"{self.RESOURCE_ICONS['namespace']} Name: [cyan]{name}[/cyan]\n"
                f"🚦 Status: {status_indicator}{status_text}",
                title="[bold cyan]Namespace Status[/bold cyan]",
                border_style="cyan",
                box=box.HEAVY
            )
            
            # Print the panel
            self.console.print(panel)
            
            return str(panel)
            
        except Exception as e:
            logger.error(f"Error formatting namespace status: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Formatting Namespace Status[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error formatting namespace status: {e}"
    
    def display_command_result(self, result_data: Dict[str, Any]) -> str:
        """
        Display a generic command result in a rich panel with k9s-style formatting.
        
        Args:
            result_data: Dictionary containing command result data from kubectl
        
        Returns:
            Rendered panel as a string
        """
        if not result_data.get("success", False):
            error_message = result_data.get("error", "Unknown error")
            error_panel = Panel(
                f"[bold red]{error_message}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error: {error_message}"
        
        try:
            result = result_data.get("result", "")
            command = result_data.get("command", "")
            
            if not result:
                empty_panel = Panel(
                    "[yellow]No result found for this command[/yellow]",
                    title="[bold yellow]Empty Result[/bold yellow]",
                    border_style="yellow",
                    box=box.HEAVY
                )
                self.console.print(empty_panel)
                return "No result found"
            
            # Create a styled header
            header = Text(f"⚙️ Command Result: {command} ⚙️", style="bold cyan")
            self.console.print(header, justify="center")
            
            # Add a progress spinner for loading effect
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Processing result...[/bold green]"),
                transient=True,
            ) as progress:
                task = progress.add_task("Processing", total=1)
                time.sleep(0.3)  # Small delay for visual effect
                progress.update(task, advance=1)
            
            # Format the result with syntax highlighting if possible
            try:
                # Try to parse as JSON for pretty formatting
                if result.strip().startswith('{') or result.strip().startswith('['):
                    try:
                        json_data = json.loads(result)
                        formatted_result = json.dumps(json_data, indent=2)
                        syntax = Syntax(formatted_result, "json", theme="monokai", line_numbers=True)
                        result_content = syntax
                    except json.JSONDecodeError:
                        result_content = result
                elif result.strip().startswith('<') and result.strip().endswith('>'):
                    # Might be XML or HTML
                    syntax = Syntax(result, "xml", theme="monokai", line_numbers=True)
                    result_content = syntax
                elif re.search(r"^\w+\s+\w+\s+\d+\s+\d+:\d+:\d+", result):
                    # Looks like a table output
                    result_content = result
                else:
                    result_content = result
            except Exception:
                result_content = result
            
            # Create a panel with the result
            panel = Panel(
                result_content,
                title=f"[bold blue]{command}[/bold blue]",
                subtitle="[italic]Press Ctrl+C to exit[/italic]",
                border_style="cyan",
                box=box.HEAVY
            )
            
            # Print the panel
            self.console.print(panel)
            
            # Add a footer with helpful information
            footer = Text("Use kubectl --help for more information on available commands", style="italic")
            self.console.print(footer, justify="center")
            
            return str(panel)
        
        except Exception as e:
            logger.error(f"Error displaying command result: {e}")
            error_panel = Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]Error Displaying Command Result[/bold red]",
                border_style="red",
                box=box.HEAVY
            )
            self.console.print(error_panel)
            return f"Error displaying command result: {e}"
