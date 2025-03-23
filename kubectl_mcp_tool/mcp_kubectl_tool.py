import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Union

import anyio
import click
from mcp.server.lowlevel import Server
from mcp.types import TextContent, ImageContent, EmbeddedResource
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("kubectl-mcp-tool")

# Initialize Rich console
console = Console()

def _run_kubectl_command(command: List[str]) -> str:
    """Run a kubectl command and return the output."""
    try:
        result = subprocess.run(
            ["kubectl"] + command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running kubectl command: {e.stderr}")
        return f"Error: {e.stderr}"

def format_kubectl_output(output: str, resource_type: str = "") -> str:
    """Format kubectl output with Rich styling."""
    # If output is empty or just whitespace, return as is
    if not output or output.isspace():
        return output
    
    # Check if output is in table format (has header and rows)
    lines = output.strip().split('\n')
    if len(lines) >= 2 and not lines[0].startswith(('Error', 'Warning')):
        # Try to parse as table
        try:
            # Extract headers
            headers = lines[0].split()
            
            # Create Rich table
            table = Table(title=f"Kubernetes {resource_type or 'Resources'}")
            
            # Add columns
            for header in headers:
                table.add_column(header, style="cyan bold")
            
            # Add rows
            for line in lines[1:]:
                if line.strip():  # Skip empty lines
                    # Split by whitespace, but be smarter about it
                    row_data = []
                    current_line = line.strip()
                    for header in headers:
                        if not current_line:
                            row_data.append("")
                            continue
                        
                        # Find where this column should end
                        if header == headers[-1]:  # Last column takes rest of line
                            row_data.append(current_line)
                            current_line = ""
                        else:
                            # Try to find a reasonable split point
                            split_point = len(header) + 1
                            while split_point < len(current_line) and current_line[split_point].isspace():
                                split_point += 1
                            
                            # Get data for this column
                            col_data = current_line[:split_point].strip()
                            row_data.append(col_data)
                            current_line = current_line[split_point:].strip()
                    
                    # Apply color based on status if present
                    if 'STATUS' in headers:
                        status_idx = headers.index('STATUS')
                        if status_idx < len(row_data):
                            status = row_data[status_idx]
                            if 'Running' in status or 'Active' in status or 'Completed' in status:
                                row_data[status_idx] = f"[green]{status}[/green]"
                            elif 'Pending' in status or 'ContainerCreating' in status:
                                row_data[status_idx] = f"[yellow]{status}[/yellow]"
                            elif 'Error' in status or 'Failed' in status or 'CrashLoopBackOff' in status:
                                row_data[status_idx] = f"[red]{status}[/red]"
                    
                    table.add_row(*row_data)
            
            # Render table to string
            with console.capture() as capture:
                console.print(table)
            return capture.get()
        
        except Exception as e:
            # If table parsing fails, fall back to original output
            logger.debug(f"Table parsing failed: {e}")
    
    # For non-table output (like create/delete confirmations)
    if "created" in output or "configured" in output:
        styled_output = output.replace("created", "[green]created[/green]")
        styled_output = styled_output.replace("configured", "[green]configured[/green]")
        with console.capture() as capture:
            console.print(Panel(styled_output, title="Success", border_style="green"))
        return capture.get()
    elif "deleted" in output:
        styled_output = output.replace("deleted", "[yellow]deleted[/yellow]")
        with console.capture() as capture:
            console.print(Panel(styled_output, title="Resource Deleted", border_style="yellow"))
        return capture.get()
    elif "scaled" in output:
        styled_output = output.replace("scaled", "[blue]scaled[/blue]")
        with console.capture() as capture:
            console.print(Panel(styled_output, title="Scaling Complete", border_style="blue"))
        return capture.get()
    elif "Error" in output or "error" in output:
        with console.capture() as capture:
            console.print(Panel(output, title="Error", border_style="red"))
        return capture.get()
    else:
        # For other outputs, just wrap in a panel
        with console.capture() as capture:
            console.print(Panel(output, title="Kubectl Output"))
        return capture.get()

# Tool handlers
async def get_pods(
    namespace: str = "",
    pod_name: str = "",
    output_format: str = "wide"
) -> str:
    """Get information about pods in a namespace."""
    command = ["get", "pods"]
    if pod_name:
        command.append(pod_name)
    if namespace:
        command.extend(["-n", namespace])
    command.extend(["-o", output_format])
    
    return _run_kubectl_command(command)

async def create_pod(
    pod_yaml: str,
    namespace: str = ""
) -> str:
    """Create a pod in a namespace."""
    # Write the YAML to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp_file:
        tmp_file.write(pod_yaml)
        tmp_file_path = tmp_file.name
    
    command = ["apply", "-f", tmp_file_path]
    if namespace:
        command.extend(["-n", namespace])
    
    result = _run_kubectl_command(command)
    
    # Clean up the temporary file
    os.unlink(tmp_file_path)
    
    return result

async def delete_pod(
    pod_name: str,
    namespace: str = ""
) -> str:
    """Delete a pod in a namespace."""
    command = ["delete", "pod", pod_name]
    if namespace:
        command.extend(["-n", namespace])
    
    return _run_kubectl_command(command)

async def scale_deployment(
    deployment_name: str,
    replicas: int = 1,
    namespace: str = ""
) -> str:
    """Scale a deployment up or down."""
    command = ["scale", f"deployment/{deployment_name}", f"--replicas={replicas}"]
    if namespace:
        command.extend(["-n", namespace])
    
    return _run_kubectl_command(command)

async def get_namespaces(
    namespace_name: str = "",
    output_format: str = "wide"
) -> str:
    """Get information about namespaces."""
    command = ["get", "namespaces"]
    if namespace_name:
        command.append(namespace_name)
    command.extend(["-o", output_format])
    
    return _run_kubectl_command(command)

async def create_namespace(
    namespace_name: str
) -> str:
    """Create a namespace."""
    command = ["create", "namespace", namespace_name]
    
    return _run_kubectl_command(command)

async def delete_namespace(
    namespace_name: str
) -> str:
    """Delete a namespace."""
    command = ["delete", "namespace", namespace_name]
    
    return _run_kubectl_command(command)

async def apply_manifest(
    manifest: str
) -> str:
    """Apply a Kubernetes manifest."""
    # Write the YAML to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp_file:
        tmp_file.write(manifest)
        tmp_file_path = tmp_file.name
    
    command = ["apply", "-f", tmp_file_path]
    
    result = _run_kubectl_command(command)
    
    # Clean up the temporary file
    os.unlink(tmp_file_path)
    
    return result

async def get_resources(
    resource_type: str,
    resource_name: str = "",
    namespace: str = "",
    output_format: str = "wide"
) -> str:
    """Get information about Kubernetes resources."""
    command = ["get", resource_type]
    if resource_name:
        command.append(resource_name)
    if namespace:
        command.extend(["-n", namespace])
    command.extend(["-o", output_format])
    
    return _run_kubectl_command(command)

async def describe_resource(
    resource_type: str,
    resource_name: str,
    namespace: str = ""
) -> str:
    """Describe a Kubernetes resource."""
    command = ["describe", resource_type, resource_name]
    if namespace:
        command.extend(["-n", namespace])
    
    return _run_kubectl_command(command)

@click.command()
@click.option("--port", "-p", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    app = Server("kubectl-mcp-tool")
    
    # Register all kubectl tools
    @app.call_tool()
    async def get_pods_tool(
        namespace: str = "",
        pod_name: str = "",
        output_format: str = "wide"
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Get information about pods in a namespace.
        
        Args:
            namespace: The namespace to get pods from. If not provided, uses the current namespace.
            pod_name: The name of the pod to get information about. If not provided, gets all pods.
            output_format: The output format (json, yaml, wide, etc.). Defaults to wide.
        """
        result = await get_pods(namespace, pod_name, output_format)
        formatted_result = format_kubectl_output(result, "Pods")
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def create_pod_tool(
        pod_yaml: str,
        namespace: str = ""
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Create a pod in a namespace.
        
        Args:
            pod_yaml: The YAML definition of the pod to create.
            namespace: The namespace to create the pod in. If not provided, uses the current namespace.
        """
        result = await create_pod(pod_yaml, namespace)
        formatted_result = format_kubectl_output(result, "Pod Creation")
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def delete_pod_tool(
        pod_name: str,
        namespace: str = ""
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Delete a pod in a namespace.
        
        Args:
            pod_name: The name of the pod to delete.
            namespace: The namespace of the pod to delete. If not provided, uses the current namespace.
        """
        result = await delete_pod(pod_name, namespace)
        formatted_result = format_kubectl_output(result, "Pod Deletion")
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def scale_deployment_tool(
        deployment_name: str,
        replicas: int = 1,
        namespace: str = ""
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Scale a deployment up or down.
        
        Args:
            deployment_name: The name of the deployment to scale.
            replicas: The number of replicas to scale to.
            namespace: The namespace of the deployment to scale. If not provided, uses the current namespace.
        """
        result = await scale_deployment(deployment_name, replicas, namespace)
        formatted_result = format_kubectl_output(result, "Deployment Scaling")
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def get_namespaces_tool(
        namespace_name: str = "",
        output_format: str = "wide"
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Get information about namespaces.
        
        Args:
            namespace_name: The name of the namespace to get information about. If not provided, gets all namespaces.
            output_format: The output format (json, yaml, wide, etc.). Defaults to wide.
        """
        result = await get_namespaces(namespace_name, output_format)
        formatted_result = format_kubectl_output(result, "Namespaces")
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def create_namespace_tool(
        namespace_name: str
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Create a namespace.
        
        Args:
            namespace_name: The name of the namespace to create.
        """
        result = await create_namespace(namespace_name)
        formatted_result = format_kubectl_output(result, "Namespace Creation")
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def delete_namespace_tool(
        namespace_name: str
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Delete a namespace.
        
        Args:
            namespace_name: The name of the namespace to delete.
        """
        result = await delete_namespace(namespace_name)
        formatted_result = format_kubectl_output(result, "Namespace Deletion")
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def apply_manifest_tool(
        manifest: str
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Apply a Kubernetes manifest.
        
        Args:
            manifest: The YAML manifest to apply.
        """
        result = await apply_manifest(manifest)
        formatted_result = format_kubectl_output(result, "Manifest Application")
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def get_resources_tool(
        resource_type: str,
        resource_name: str = "",
        namespace: str = "",
        output_format: str = "wide"
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Get information about Kubernetes resources.
        
        Args:
            resource_type: The type of resource to get information about (deployment, service, pod, node, etc.).
            resource_name: The name of the resource to get information about. If not provided, gets all resources of the given type.
            namespace: The namespace of the resource to get information about. If not provided, uses the current namespace.
            output_format: The output format (json, yaml, wide, etc.). Defaults to wide.
        """
        result = await get_resources(resource_type, resource_name, namespace, output_format)
        formatted_result = format_kubectl_output(result, resource_type)
        return [TextContent(type="text", text=formatted_result)]
    
    @app.call_tool()
    async def describe_resource_tool(
        resource_type: str,
        resource_name: str,
        namespace: str = ""
    ) -> list[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Describe a Kubernetes resource.
        
        Args:
            resource_type: The type of resource to describe (deployment, service, pod, node, etc.).
            resource_name: The name of the resource to describe.
            namespace: The namespace of the resource to describe. If not provided, uses the current namespace.
        """
        result = await describe_resource(resource_type, resource_name, namespace)
        formatted_result = format_kubectl_output(result, f"{resource_type} Description")
        return [TextContent(type="text", text=formatted_result)]
    
    logger.info(f"Starting kubectl MCP server with {transport} transport on port {port}")
    if transport == "stdio":
        from mcp.server.stdio import stdio_server
        
        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        
        anyio.run(arun)
    else:
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        
        sse = SseServerTransport("/messages/")
        
        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        
        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )
        
        import uvicorn
        
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    return 0

if __name__ == "__main__":
    sys.exit(main())
