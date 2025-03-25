#!/usr/bin/env python3
"""
Test script for enhanced features of kubectl-mcp-tool.
"""

import logging
import os
import sys
import subprocess
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="test_enhanced_features.log"
)
logger = logging.getLogger("test-enhanced-features")

# Add console handler for important messages
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def test_cli_output():
    """Test the enhanced CLI output."""
    print("\n=== Testing Enhanced CLI Output ===")
    
    try:
        # Run the CLI output demo
        result = subprocess.run(
            ["python3", "cli_output_demo.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"CLI output test failed: {result.stderr}")
            return False
        
        print("CLI output test results:")
        print(result.stdout)
        
        return True
    except Exception as e:
        print(f"Error during CLI output test: {e}")
        return False

def test_log_analysis():
    """Test the log analysis features."""
    print("\n=== Testing Log Analysis Features ===")
    
    try:
        # Run the log analysis demo
        result = subprocess.run(
            ["python3", "log_analysis_demo.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Log analysis test failed: {result.stderr}")
            return False
        
        print("Log analysis test results:")
        print(result.stdout)
        
        return True
    except Exception as e:
        print(f"Error during log analysis test: {e}")
        return False

def test_context_switching():
    """Test the context switching features."""
    print("\n=== Testing Context Switching Features ===")
    
    try:
        # Run the context switching demo
        result = subprocess.run(
            ["python3", "context_switching_demo.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Context switching test failed: {result.stderr}")
            return False
        
        print("Context switching test results:")
        print(result.stdout)
        
        return True
    except Exception as e:
        print(f"Error during context switching test: {e}")
        return False

def test_comprehensive_demo():
    """Test the comprehensive demo."""
    print("\n=== Testing Comprehensive Demo ===")
    
    try:
        # Run the comprehensive demo
        result = subprocess.run(
            ["python3", "comprehensive_demo.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Comprehensive demo test failed: {result.stderr}")
            return False
        
        print("Comprehensive demo test results:")
        print(result.stdout)
        
        return True
    except Exception as e:
        print(f"Error during comprehensive demo test: {e}")
        return False

def main():
    """Run the enhanced features tests."""
    try:
        # Test enhanced CLI output
        cli_success = test_cli_output()
        
        # Test log analysis features
        log_success = test_log_analysis()
        
        # Test context switching features
        context_success = test_context_switching()
        
        # Test comprehensive demo
        demo_success = test_comprehensive_demo()
        
        # Print summary
        print("\n=== Test Summary ===")
        print(f"Enhanced CLI Output: {'PASS' if cli_success else 'FAIL'}")
        print(f"Log Analysis Features: {'PASS' if log_success else 'FAIL'}")
        print(f"Context Switching Features: {'PASS' if context_success else 'FAIL'}")
        print(f"Comprehensive Demo: {'PASS' if demo_success else 'FAIL'}")
        
        # Return overall success
        return 0 if cli_success and log_success and context_success and demo_success else 1
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
