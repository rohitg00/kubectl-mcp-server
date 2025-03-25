#!/usr/bin/env python3
"""
Test script for context switching features.
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
    filename="test_context_switching.log"
)
logger = logging.getLogger("test-context-switching")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_context_manager():
    """Test the context manager functionality."""
    print("\n=== Testing Context Manager ===")
    
    try:
        # Import the context manager
        from kubectl_mcp_tool.context_switcher.context_manager import ContextManager
        
        # Create a context manager
        context_manager = ContextManager()
        
        # Create a console
        console = Console()
        
        # Get contexts
        contexts = context_manager.get_contexts()
        
        # Create a table for contexts
        context_table = Table(title="Kubernetes Contexts", show_header=True, header_style="bold magenta")
        context_table.add_column("Name", style="cyan")
        
        # Add rows
        if contexts:
            for context in contexts:
                context_table.add_row(context)
        else:
            context_table.add_row("No contexts found")
        
        # Print the table
        console.print(context_table)
        
        # Get current context
        current_context = context_manager.get_current_context()
        
        # Create a panel for current context
        if current_context.get("success", False):
            current_context_panel = Panel(
                Text(current_context.get("result", ""), style="green"),
                title="Current Context",
                border_style="green"
            )
        else:
            current_context_panel = Panel(
                Text(current_context.get("error", "Unknown error"), style="red"),
                title="Current Context Error",
                border_style="red"
            )
        
        # Print the panel
        console.print(current_context_panel)
        
        return True
    except Exception as e:
        print(f"Error testing context manager: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_namespace_manager():
    """Test the namespace manager functionality."""
    print("\n=== Testing Namespace Manager ===")
    
    try:
        # Import the namespace manager
        from kubectl_mcp_tool.context_switcher.namespace_manager import NamespaceManager
        
        # Create a namespace manager
        namespace_manager = NamespaceManager()
        
        # Create a console
        console = Console()
        
        # Get namespaces
        namespaces = namespace_manager.get_namespaces()
        
        # Create a table for namespaces
        namespace_table = Table(title="Kubernetes Namespaces", show_header=True, header_style="bold magenta")
        namespace_table.add_column("Name", style="cyan")
        
        # Add rows
        if namespaces.get("success", False):
            for namespace in namespaces.get("result", []):
                namespace_table.add_row(namespace)
        else:
            namespace_table.add_row(namespaces.get("error", "Unknown error"))
        
        # Print the table
        console.print(namespace_table)
        
        # Get current namespace
        current_namespace = namespace_manager.get_current_namespace()
        
        # Create a panel for current namespace
        if current_namespace.get("success", False):
            current_namespace_panel = Panel(
                Text(current_namespace.get("result", ""), style="green"),
                title="Current Namespace",
                border_style="green"
            )
        else:
            current_namespace_panel = Panel(
                Text(current_namespace.get("error", "Unknown error"), style="red"),
                title="Current Namespace Error",
                border_style="red"
            )
        
        # Print the panel
        console.print(current_namespace_panel)
        
        return True
    except Exception as e:
        print(f"Error testing namespace manager: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the context switching tests."""
    try:
        # Test context manager
        context_success = test_context_manager()
        
        # Test namespace manager
        namespace_success = test_namespace_manager()
        
        # Print summary
        print("\n=== Test Summary ===")
        print(f"Context Manager: {'PASS' if context_success else 'FAIL'}")
        print(f"Namespace Manager: {'PASS' if namespace_success else 'FAIL'}")
        
        # Return overall success
        return 0 if context_success and namespace_success else 1
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
