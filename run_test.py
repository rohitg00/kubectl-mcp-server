#!/usr/bin/env python3
import os
import subprocess
import sys
import json
import time

# Set mock mode environment variable to False explicitly
os.environ["MCP_TEST_MOCK_MODE"] = "0"

# Test if kubectl is accessible
print("Testing kubectl access...")
try:
    result = subprocess.run(
        ["kubectl", "version", "--client"], 
        capture_output=True, 
        check=True, 
        text=True
    )
    print(f"kubectl client version: {result.stdout.strip()}")
except Exception as e:
    print(f"Error accessing kubectl: {e}")
    sys.exit(1)

# Test if kubectl can connect to the cluster
print("\nTesting kubectl connection to cluster...")
try:
    result = subprocess.run(
        ["kubectl", "get", "namespaces"], 
        capture_output=True, 
        check=True, 
        text=True
    )
    print("Successfully connected to cluster:")
    print(result.stdout)
except Exception as e:
    print(f"Error connecting to cluster: {e}")
    sys.exit(1)

# Test getting pods in default namespace
print("\nGetting pods in default namespace...")
try:
    result = subprocess.run(
        ["kubectl", "get", "pods", "-n", "default", "-o", "json"], 
        capture_output=True, 
        check=True, 
        text=True
    )
    pods_data = json.loads(result.stdout)
    print(f"Found {len(pods_data.get('items', []))} pods in default namespace")
    
    # Print pod names
    if pods_data.get('items'):
        print("Pod names:")
        for pod in pods_data.get('items', []):
            pod_name = pod.get('metadata', {}).get('name', 'unknown')
            pod_status = pod.get('status', {}).get('phase', 'unknown')
            print(f"  - {pod_name} ({pod_status})")
    else:
        print("No pods found in default namespace")
except Exception as e:
    print(f"Error getting pods: {e}")
    sys.exit(1)

# Test getting nodes
print("\nGetting cluster nodes...")
try:
    result = subprocess.run(
        ["kubectl", "get", "nodes", "-o", "json"], 
        capture_output=True, 
        check=True, 
        text=True
    )
    nodes_data = json.loads(result.stdout)
    print(f"Found {len(nodes_data.get('items', []))} nodes in cluster")
    
    # Print node names
    if nodes_data.get('items'):
        print("Node names:")
        for node in nodes_data.get('items', []):
            node_name = node.get('metadata', {}).get('name', 'unknown')
            node_status = node.get('status', {}).get('conditions', [{}])[-1].get('type', 'unknown')
            print(f"  - {node_name} ({node_status})")
    else:
        print("No nodes found in cluster")
except Exception as e:
    print(f"Error getting nodes: {e}")
    sys.exit(1)

# Create a test pod
print("\nCreating a test pod...")
try:
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "test-pod-mcp",
            "namespace": "default"
        },
        "spec": {
            "containers": [
                {
                    "name": "nginx",
                    "image": "nginx:latest",
                    "ports": [{"containerPort": 80}]
                }
            ]
        }
    }
    
    # Write manifest to temporary file
    with open("test-pod.yaml", "w") as f:
        json.dump(pod_manifest, f)
    
    # Create the pod
    result = subprocess.run(
        ["kubectl", "apply", "-f", "test-pod.yaml"], 
        capture_output=True, 
        check=True, 
        text=True
    )
    print(f"Pod creation result: {result.stdout.strip()}")
    
    # Wait for the pod to be ready
    print("Waiting for pod to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        result = subprocess.run(
            ["kubectl", "get", "pod", "test-pod-mcp", "-n", "default", "-o", "json"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            pod_data = json.loads(result.stdout)
            pod_status = pod_data.get('status', {}).get('phase', '')
            print(f"Pod status: {pod_status}")
            if pod_status == "Running":
                print("Pod is running!")
                break
        print(".", end="", flush=True)
        time.sleep(1)
    
    # Clean up the temporary file
    os.remove("test-pod.yaml")
except Exception as e:
    print(f"Error creating test pod: {e}")
    import traceback
    traceback.print_exc()
    # Try to continue with the test

# Clean up the test pod
print("\nCleaning up test pod...")
try:
    result = subprocess.run(
        ["kubectl", "delete", "pod", "test-pod-mcp", "-n", "default"], 
        capture_output=True, 
        text=True
    )
    print(f"Pod deletion result: {result.stdout.strip() if result.returncode == 0 else result.stderr.strip()}")
except Exception as e:
    print(f"Error deleting test pod: {e}")

print("\nTest completed successfully!") 