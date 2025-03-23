#!/usr/bin/env python3
"""
A very simple script to test kubectl commands through the MCP server
"""

import sys
import os
import subprocess

def run_kubectl_command(command="get pods --all-namespaces"):
    """Run a kubectl command using the command line."""
    try:
        full_command = f"kubectl {command}"
        print(f"Running: {full_command}")
        
        result = subprocess.run(
            full_command, 
            shell=True, 
            capture_output=True, 
            text=True,
            env=os.environ.copy()
        )
        
        if result.returncode == 0:
            print("Success!")
            print(result.stdout)
        else:
            print("Command failed:")
            print(result.stderr)
            
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {str(e)}")
        return False

def main():
    # Get the command from command line arguments or use default
    command = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "get pods --all-namespaces"
    run_kubectl_command(command)

if __name__ == "__main__":
    main() 