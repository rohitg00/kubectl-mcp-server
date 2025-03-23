# Verify pod state in Kubernetes
is_valid, state = validate_kubernetes_state("pod", pod_name, namespace)
assert is_valid, f"Failed to get pod state: {state}"
assert state["kind"] == "Pod", "Expected resource kind to be 'Pod'"
assert state["metadata"]["name"] == pod_name, f"Expected pod name to be '{pod_name}'" 