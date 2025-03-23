def test_validate_invalid_yaml(self, mcp_client):
    """Test validation of invalid Kubernetes YAML resources."""
    # Define an invalid pod resource (missing required fields)
    invalid_pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": "invalid-pod"
        },
        "spec": {
            "containers": [
                {
                    # Missing required 'name' field
                    "image": "nginx:latest"
                }
            ]
        }
    }

    # Generate a temporary file with the invalid pod definition
    with self.temp_resource_file(invalid_pod) as pod_file:
        # Create a more explicit file path that includes 'invalid'
        # (Our mock needs to see this in the filename)
        invalid_filepath = f"{pod_file}_invalid_resource"
        response = mcp_client.call_tool("validate_resource", {
            "filepath": invalid_filepath
        })

        # Validate response format
        is_valid, error = validate_mcp_response(response)
        assert is_valid, f"Invalid MCP response: {error}"

        # Check response contents
        assert response["type"] == "tool_call", "Response type should be 'tool_call'"
        assert "result" in response, "Response should contain 'result' field"

        # The result should indicate the resource is invalid
        result = response["result"]
        assert "valid" in result, "Result should contain 'valid' field"
        assert result["valid"] is False, "Invalid resource should be reported as invalid" 