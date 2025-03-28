#!/usr/bin/env python
"""
Test script to check if the kubectl-mcp-tool module can be run correctly.
This simulates how Cursor would invoke the module.
"""

import sys
import subprocess
import os

def test_module_invocation():
    """Test if the module can be invoked with 'python -m'."""
    print("Testing module invocation with 'python -m kubectl_mcp_tool.cli.cli serve'")
    
    # Get the Python executable path
    python_exe = sys.executable
    print(f"Using Python: {python_exe}")
    
    # Run the command with subprocess
    try:
        # Start the process but don't wait for it to complete
        process = subprocess.Popen(
            [python_exe, "-m", "kubectl_mcp_tool.cli.cli", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for a short time to see if it starts
        import time
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is None:
            print("✅ Module started successfully!")
            print("Terminating the process...")
            process.terminate()
            return True
        else:
            stdout, stderr = process.communicate()
            print("❌ Module failed to start")
            print("STDOUT:", stdout)
            print("STDERR:", stderr)
            return False
    except Exception as e:
        print(f"❌ Error running the module: {e}")
        return False

def print_environment_info():
    """Print information about the environment."""
    print("\n=== Environment Information ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if the module is importable
    try:
        import kubectl_mcp_tool
        print(f"✅ kubectl_mcp_tool module found at: {kubectl_mcp_tool.__file__}")
    except ImportError as e:
        print(f"❌ kubectl_mcp_tool module not found: {e}")
    
    # Check PATH environment variable
    print(f"PATH: {os.environ.get('PATH', '')}")

if __name__ == "__main__":
    print("=== kubectl-mcp-tool Module Test ===")
    success = test_module_invocation()
    print_environment_info()
    
    print("\n=== Recommendation ===")
    if success:
        print("The module can be invoked correctly. Cursor should be able to use it with this configuration:")
        print("""
{
  "mcpServers": {
    "kubernetes": {
      "command": "python",
      "args": ["-m", "kubectl_mcp_tool.cli.cli", "serve"]
    }
  }
}
        """)
    else:
        print("The module could not be invoked correctly. Try these solutions:")
        print("1. Make sure kubectl_mcp_tool is installed correctly")
        print("2. Try using an absolute path to the Python executable in the Cursor configuration")
        print("3. Check the installation logs for any errors") 