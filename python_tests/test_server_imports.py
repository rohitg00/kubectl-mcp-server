#!/usr/bin/env python3
"""
Test script to verify server module imports work correctly after reorganization.
"""

import os
import sys
import importlib
import inspect

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_server_imports():
    """Test importing server modules."""
    server_modules = [
        "compatible_servers.fast_cursor_server",
        "compatible_servers.fast_windsurf_server",
        "compatible_servers.simple_cursor_server",
        "compatible_servers.simple_windsurf_server",
        "compatible_servers.simple_mcp_server",
        "compatible_servers.simplified_mcp_implementation"
    ]
    
    print("Testing server module imports:")
    
    for module_name in server_modules:
        try:
            module = importlib.import_module(module_name)
            functions = [name for name, obj in inspect.getmembers(module) if inspect.isfunction(obj)]
            classes = [name for name, obj in inspect.getmembers(module) if inspect.isclass(obj)]
            
            print(f"✅ {module_name}: Successfully imported")
            print(f"   Functions: {', '.join(functions)}")
            print(f"   Classes: {', '.join(classes)}")
        except ImportError as e:
            print(f"❌ {module_name}: Import failed - {e}")
    
    # Test the convenience scripts
    try:
        from cursor_server import main as cursor_main
        print("✅ cursor_server.py: Successfully imported")
    except ImportError as e:
        print(f"❌ cursor_server.py: Import failed - {e}")
    
    try:
        from windsurf_server import main as windsurf_main
        print("✅ windsurf_server.py: Successfully imported")
    except ImportError as e:
        print(f"❌ windsurf_server.py: Import failed - {e}")

if __name__ == "__main__":
    test_server_imports() 