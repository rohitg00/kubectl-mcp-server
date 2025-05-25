#!/usr/bin/env python3
"""
Run all MCP tests for kubectl-mcp-tool.
This script manages the test execution and generates a report.
"""

import os
import sys
import time
import logging
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def _ensure_kubectl_available() -> bool:
    """Return True if a usable `kubectl` is on PATH.

    If `kubectl` is missing but `minikube` is present and functional, create a
    temporary wrapper script named `kubectl` that forwards all invocations to
    `minikube kubectl --`.  The wrapper directory is prepended to the current
    process's PATH so that any child process (pytest, helper scripts, etc.)
    automatically uses it without code changes elsewhere.
    """
    import shutil
    import tempfile
    import os
    import subprocess
    import stat

    # Fast-path: real kubectl already present
    if shutil.which("kubectl"):
        return True

    # Fallback: use `minikube kubectl --` if available
    if shutil.which("minikube"):
        try:
            subprocess.run(
                ["minikube", "kubectl", "--", "version", "--client"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            return False

        temp_dir = tempfile.mkdtemp(prefix="kubectl_wrapper_")
        wrapper_path = os.path.join(temp_dir, "kubectl")
        with open(wrapper_path, "w", encoding="utf-8") as fh:
            fh.write("#!/usr/bin/env bash\nexec minikube kubectl -- \"$@\"\n")
        os.chmod(wrapper_path, stat.S_IRWXU)
        # Prepend to PATH
        os.environ["PATH"] = f"{temp_dir}:{os.environ.get('PATH', '')}"
        logger.info("Using minikube kubectl wrapper at %s", wrapper_path)
        return True

    # Neither kubectl nor minikube available
    return False

def check_dependencies(mock_mode=False):
    """Check if all required dependencies are installed."""
    # Ensure kubectl (or a wrapper) is available when not in mock mode
    if not mock_mode:
        if not _ensure_kubectl_available():
            logger.error("kubectl not found and minikube fallback failed")
            return False

    required_commands = ["python"] if mock_mode else ["python"]  # kubectl handled separately

    for cmd in required_commands:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(f"Required command '{cmd}' not found or not working")
            return False

    # Additional kubectl validation when not in mock mode
    if not mock_mode:
        try:
            subprocess.run(
                ["kubectl", "version", "--client"],
                capture_output=True,
                check=True,
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("kubectl command failed even after wrapper setup")
            return False

    # Check Python packages
    required_packages = ["pytest", "requests"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            logger.error(f"Required Python package '{package}' not installed")
            return False
    
    # Check kubectl connection (unless in mock mode)
    if not mock_mode:
        try:
            result = subprocess.run(
                ["kubectl", "get", "namespaces"], 
                capture_output=True, check=True, text=True
            )
            if "default" not in result.stdout:
                logger.error("kubectl cannot connect to cluster or list namespaces")
                return False
        except subprocess.CalledProcessError:
            logger.error("kubectl cannot connect to cluster")
            return False
    else:
        logger.info("Running in mock mode - skipping kubectl cluster connectivity check")
        
    return True

def run_test_module(module_path, verbose=False, mock_mode=False):
    """Run a single test module using pytest."""
    logger.info(f"Running test module: {module_path}")
    
    cmd = ["python", "-m", "pytest", module_path]
    if verbose:
        cmd.extend(["-v"])
    
    # Add test directory to Python path
    env = os.environ.copy()
    test_dir = Path(module_path).parent
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{test_dir}:{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = str(test_dir)
    
    # Set mock mode environment variable if needed
    if mock_mode:
        env["MCP_TEST_MOCK_MODE"] = "1"
    
    try:
        result = subprocess.run(cmd, env=env, text=True, capture_output=True)
        logger.info(f"Test result: {'Passed' if result.returncode == 0 else 'Failed'}")
        
        if verbose or result.returncode != 0:
            # Print output for verbose mode or if tests fail
            print("\n" + "="*80)
            print(f"TEST MODULE: {module_path}")
            print("="*80)
            
            if result.stdout:
                print("\nSTDOUT:")
                print(result.stdout)
                
            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)
                
        return (module_path, result.returncode == 0, result.stdout, result.stderr)
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return (module_path, False, "", str(e))

def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Run MCP tests for kubectl-mcp-tool")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--module", "-m", help="Run specific test module")
    parser.add_argument("--report", "-r", action="store_true", help="Generate HTML report")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without requiring Kubernetes cluster")
    args = parser.parse_args()
    
    # Ensure all dependencies are available
    logger.info("Checking dependencies...")
    if not check_dependencies(args.mock):
        logger.error("Dependency check failed. Please install required dependencies.")
        return 1
    
    # Find test modules
    test_dir = Path(__file__).parent
    if args.module:
        test_modules = [Path(args.module)]
    else:
        # Find all test modules that start with "test_mcp"
        test_modules = list(test_dir.glob("test_mcp_*.py"))
    
    if not test_modules:
        logger.error("No test modules found")
        return 1
        
    logger.info(f"Found {len(test_modules)} test modules to run")
    
    # Start testing
    start_time = time.time()
    results = []
    
    for module in test_modules:
        results.append(run_test_module(module, args.verbose, args.mock))
    
    # Calculate overall results
    end_time = time.time()
    total_time = end_time - start_time
    passed = sum(1 for _, success, _, _ in results if success)
    failed = len(results) - passed
    
    # Print summary
    print("\n" + "="*80)
    print(f"TEST SUMMARY")
    print("="*80)
    print(f"Total modules: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.2f} seconds")
    print("="*80)
    
    # Print details of failures
    if failed > 0:
        print("\nFAILED MODULES:")
        for module, success, _, _ in results:
            if not success:
                print(f"  - {module}")
    
    # Generate HTML report if requested
    if args.report:
        logger.info("Generating HTML report...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = test_dir / f"mcp_test_report_{timestamp}.html"
        
        with open(report_path, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>MCP Test Report - {timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ margin: 20px 0; padding: 10px; background-color: #f0f0f0; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .module {{ margin: 20px 0; padding: 10px; border: 1px solid #ddd; }}
        .module-header {{ display: flex; justify-content: space-between; }}
        .output {{ background-color: #f8f8f8; padding: 10px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>MCP Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Total modules: {len(results)}</p>
        <p>Passed: <span class="pass">{passed}</span></p>
        <p>Failed: <span class="fail">{failed}</span></p>
        <p>Total time: {total_time:.2f} seconds</p>
    </div>
""")
            
            # Add each module's results
            for module, success, stdout, stderr in results:
                status_class = "pass" if success else "fail"
                status_text = "PASSED" if success else "FAILED"
                
                f.write(f"""
    <div class="module">
        <div class="module-header">
            <h3>{module}</h3>
            <span class="{status_class}">{status_text}</span>
        </div>
        <div class="output">
            <h4>Output:</h4>
            {stdout}
            
            {stderr if stderr else ""}
        </div>
    </div>
""")
            
            f.write("""
</body>
</html>
""")
            
            logger.info(f"Report generated: {report_path}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 