import asyncio
from kubectl_mcp_tool.mcp_kubectl_tool import create_pod

pod_yaml = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
  - name: test-container
    image: nginx:latest
"""

# Run the create_pod command asynchronously with a specified namespace
result = asyncio.run(create_pod(pod_yaml, namespace="default"))
print(result)
