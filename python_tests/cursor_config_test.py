#!/usr/bin/env python
"""
This script tests if the Cursor MCP configuration would work correctly.
It reads the Cursor MCP configuration file and tries to execute the command
as Cursor would.
"""

import json
import os
import subprocess
import sys
import time

def load_cursor_config():
    """Load the Cursor MCP configuration file."""
    config_path = os.path.expanduser("~/.cursor/mcp.json")
    if not os.path.exists(config_path):
        print(f"❌ Cursor configuration file not found at {config_path}")
        return None
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        print(f"✅ Successfully loaded Cursor configuration from {config_path}")
        return config
    except Exception as e:
        print(f"❌ Error loading Cursor configuration: {e}")
        return None

def test_cursor_config(config):
    """Test if the command in the Cursor configuration works."""
    if not config or "mcpServers" not in config:
        print("❌ No mcpServers found in configuration")
        return False
    
    for server_name, server_config in config["mcpServers"].items():
        print(f"\nTesting server: {server_name}")
        
        if "command" not in server_config:
            print(f"❌ No command specified for server {server_name}")
            continue
        
        command = server_config["command"]
        args = server_config.get("args", [])
        env = server_config.get("env", {})
        
        # Create environment variables dictionary
        env_dict = os.environ.copy()
        env_dict.update(env)
        
        print(f"Command: {command}")
        print(f"Args: {args}")
        print(f"Environment variables: {env}")
        
        # Try to execute the command
        try:
            print(f"Executing: {command} {' '.join(args)}")
            process = subprocess.Popen(
                [command] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env_dict
            )
            
            # Wait for a short time to see if it starts
            time.sleep(2)
            
            # Check if the process is still running
            if process.poll() is None:
                print(f"✅ Server {server_name} started successfully!")
                print("Terminating the process...")
                process.terminate()
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Server {server_name} failed to start")
                print("STDOUT:", stdout)
                print("STDERR:", stderr)
                return False
        except Exception as e:
            print(f"❌ Error executing command: {e}")
            return False

def main():
    """Main function."""
    print("=== Cursor MCP Configuration Test ===")
    
    config = load_cursor_config()
    if config:
        print("\nConfiguration content:")
        print(json.dumps(config, indent=2))
        
        success = test_cursor_config(config)
        
        if success:
            print("\n✅ Cursor configuration is valid and should work correctly!")
        else:
            print("\n❌ Cursor configuration is not working correctly.")
            print("\nRecommendation:")
            print("1. Update the configuration to use the full path to the Python executable:")
            print(f"""
{{
  "mcpServers": {{
    "kubernetes": {{
      "command": "{sys.executable}",
      "args": ["-m", "kubectl_mcp_tool.cli.cli", "serve"]
    }}
  }}
}}
            """)
            print("2. Or update it to use an absolute path to the kubectl-mcp script:")
            pip_cmd = subprocess.run(
                [sys.executable, "-m", "pip", "show", "kubectl-mcp-tool"],
                capture_output=True,
                text=True
            )
            if pip_cmd.returncode == 0:
                location = None
                for line in pip_cmd.stdout.splitlines():
                    if line.startswith("Location:"):
                        location = line.split(":", 1)[1].strip()
                        break
                
                if location:
                    script_path = os.path.join(location, "kubectl_mcp_tool", "cli", "cli.py")
                    if os.path.exists(script_path):
                        print(f"""
{{
  "mcpServers": {{
    "kubernetes": {{
      "command": "{sys.executable}",
      "args": ["{script_path}", "serve"]
    }}
  }}
}}
                        """)

if __name__ == "__main__":
    main() 