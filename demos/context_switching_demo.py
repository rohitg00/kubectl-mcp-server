#!/usr/bin/env python3
"""
Demo script for context switching features.
"""

import json
import logging
import os
import sys
import time
from typing import Dict, Any

from kubectl_mcp_tool.context_switcher.context_manager import ContextManager
from kubectl_mcp_tool.context_switcher.namespace_manager import NamespaceManager
from kubectl_mcp_tool.cli_output import CLIOutput

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="context_switching_demo.log"
)
logger = logging.getLogger("context-switching-demo")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def main():
    """Run the context switching demo."""
    try:
        # Create the context and namespace managers
        context_manager = ContextManager()
        namespace_manager = NamespaceManager()
        cli_output = CLIOutput()
        
        print("\n=== Context Switching Demo ===\n")
        
        # Get available contexts
        print("Fetching available contexts...")
        contexts = context_manager.get_contexts()
        
        if not contexts:
            print("No contexts found.")
            return
        
        # Display available contexts
        print(f"Found {len(contexts)} contexts.")
        print("\nAvailable contexts:")
        
        for i, context in enumerate(contexts, 1):
            print(f"{i}. {context}")
        
        # Get current context
        current_context = context_manager.get_current_context()
        print(f"\nCurrent context: {current_context}")
        
        # Get context details
        print("\nContext details:")
        context_details = context_manager.get_context_details(current_context)
        
        if context_details.get("success", False):
            print(context_details.get("result", ""))
        else:
            print(f"Error getting context details: {context_details.get('error', 'Unknown error')}")
        
        # Get available namespaces
        print("\nFetching available namespaces...")
        namespaces_data = namespace_manager.get_namespaces()
        
        if namespaces_data.get("success", False):
            namespaces = namespaces_data.get("result", [])
            
            if namespaces:
                print(f"Found {len(namespaces)} namespaces.")
                print("\nAvailable namespaces:")
                
                for i, namespace in enumerate(namespaces, 1):
                    print(f"{i}. {namespace}")
            else:
                print("No namespaces found.")
        else:
            print(f"Error getting namespaces: {namespaces_data.get('error', 'Unknown error')}")
        
        # Get current namespace
        current_namespace_data = namespace_manager.get_current_namespace()
        
        if current_namespace_data.get("success", False):
            current_namespace = current_namespace_data.get("result", "default")
            print(f"\nCurrent namespace: {current_namespace}")
        else:
            print(f"Error getting current namespace: {current_namespace_data.get('error', 'Unknown error')}")
        
        # Switch namespace
        if namespaces_data.get("success", False):
            namespaces = namespaces_data.get("result", [])
            
            if namespaces:
                # Find a namespace to switch to (different from current)
                target_namespace = None
                
                for namespace in namespaces:
                    if namespace != current_namespace_data.get("result", "default"):
                        target_namespace = namespace
                        break
                
                if target_namespace:
                    print(f"\nSwitching to namespace: {target_namespace}")
                    switch_result = namespace_manager.switch_namespace(target_namespace)
                    
                    if switch_result.get("success", False):
                        print(f"Successfully switched to namespace: {target_namespace}")
                        print(f"Result: {switch_result.get('result', '')}")
                    else:
                        print(f"Error switching namespace: {switch_result.get('error', 'Unknown error')}")
                else:
                    print("No alternative namespace found to switch to.")
        
        # Switch back to original namespace
        if current_namespace_data.get("success", False):
            original_namespace = current_namespace_data.get("result", "default")
            print(f"\nSwitching back to original namespace: {original_namespace}")
            switch_result = namespace_manager.switch_namespace(original_namespace)
            
            if switch_result.get("success", False):
                print(f"Successfully switched back to namespace: {original_namespace}")
                print(f"Result: {switch_result.get('result', '')}")
            else:
                print(f"Error switching namespace: {switch_result.get('error', 'Unknown error')}")
        
        # Create a new namespace
        new_namespace = f"demo-ns-{int(time.time())}"
        print(f"\nCreating new namespace: {new_namespace}")
        create_result = namespace_manager.create_namespace(new_namespace)
        
        if create_result.get("success", False):
            print(f"Successfully created namespace: {new_namespace}")
            print(f"Result: {create_result.get('result', '')}")
            
            # Switch to the new namespace
            print(f"\nSwitching to new namespace: {new_namespace}")
            switch_result = namespace_manager.switch_namespace(new_namespace)
            
            if switch_result.get("success", False):
                print(f"Successfully switched to namespace: {new_namespace}")
                print(f"Result: {switch_result.get('result', '')}")
            else:
                print(f"Error switching namespace: {switch_result.get('error', 'Unknown error')}")
            
            # Delete the new namespace
            print(f"\nDeleting namespace: {new_namespace}")
            delete_result = namespace_manager.delete_namespace(new_namespace)
            
            if delete_result.get("success", False):
                print(f"Successfully deleted namespace: {new_namespace}")
                print(f"Result: {delete_result.get('result', '')}")
            else:
                print(f"Error deleting namespace: {delete_result.get('error', 'Unknown error')}")
        else:
            print(f"Error creating namespace: {create_result.get('error', 'Unknown error')}")
        
        # Switch back to original namespace
        if current_namespace_data.get("success", False):
            original_namespace = current_namespace_data.get("result", "default")
            print(f"\nSwitching back to original namespace: {original_namespace}")
            switch_result = namespace_manager.switch_namespace(original_namespace)
            
            if switch_result.get("success", False):
                print(f"Successfully switched back to namespace: {original_namespace}")
                print(f"Result: {switch_result.get('result', '')}")
            else:
                print(f"Error switching namespace: {switch_result.get('error', 'Unknown error')}")
        
        print("\n=== Demo Complete ===\n")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        print(f"Error in demo: {e}")

if __name__ == "__main__":
    main()
