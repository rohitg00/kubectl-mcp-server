# Kubectl MCP Tool - Comprehensive MCP Testing Strategy

This document outlines a systematic approach to test the kubectl-mcp-tool's MCP integration across all feature categories.

## Testing Objectives

1. Validate that all features work correctly through the MCP protocol interface
2. Ensure proper error handling and response formatting
3. Test both synchronous and asynchronous operations
4. Verify correct behavior under various cluster states and configurations

## Test Environment Setup

### Prerequisites

- Isolated test Kubernetes cluster (minikube, kind, or k3d)
- Python test environment with pytest
- MCP client simulator for request generation

### Test Namespace Management

- Create dedicated test namespaces with retry logic
- Implement proper cleanup to ensure test isolation
- Handle namespace creation failures gracefully

```python
def setup_test_namespace(max_retries=3, prefix="mcp-test-"):
    """Create a test namespace with retry logic"""
    import time
    import uuid
    import subprocess
    
    namespace = f"{prefix}{int(time.time())}"
    
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["kubectl", "create", "namespace", namespace],
                check=True, capture_output=True, text=True
            )
            print(f"Created namespace {namespace}")
            return namespace
        except subprocess.CalledProcessError as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {e.stderr}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2)  # Wait before retry
```

## Test Categories

### 1. Core Kubernetes Operations Tests

- Connection to cluster
- Resource CRUD operations (pods, deployments, services)
- Namespace management
- Port forwarding
- Helm operations

### 2. Natural Language Processing Tests

- Command intent extraction
- Context-aware commands
- Fallback mechanisms

### 3. Monitoring Tests

- Resource utilization tracking
- Health checks
- Event monitoring

### 4. Security Tests

- RBAC validation
- Security context auditing
- Network policy assessment

### 5. Diagnostics Tests

- Error analysis
- Resource constraint identification
- Configuration validation

## Test Structure

```python
class TestMCPKubectl:
    """Test MCP Kubectl Tool functionality through MCP protocol"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment once for all tests"""
        # Start MCP server in test mode
        # Configure test client
    
    def setup_method(self):
        """Set up before each test"""
        # Create test namespace
        # Set up test resources if needed
    
    def teardown_method(self):
        """Clean up after each test"""
        # Delete test resources
        # Clean up namespace
    
    # Test methods for different features
    def test_get_pods(self):
        """Test getting pods through MCP"""
        # Implementation
    
    def test_create_deployment(self):
        """Test creating a deployment through MCP"""
        # Implementation
```

## MCP Client Simulator

We'll implement a simple MCP client simulator to generate MCP-compliant requests:

```python
class MCPClientSimulator:
    """Simulate an MCP client for testing"""
    
    def __init__(self, server_url=None, stdio_cmd=None):
        """Initialize the simulator"""
        self.server_url = server_url
        self.stdio_cmd = stdio_cmd
        self.session_id = str(uuid.uuid4())
    
    def list_tools(self):
        """List available tools from the MCP server"""
        # Implementation
    
    def call_tool(self, tool_name, arguments):
        """Call a tool on the MCP server"""
        # Implementation
```

## Test Data Generation

For predictable testing, we'll create test data generators:

```python
def generate_test_pod():
    """Generate a test pod specification"""
    # Implementation

def generate_test_deployment():
    """Generate a test deployment specification"""
    # Implementation
```

## Validation Utilities

Functions to validate MCP responses:

```python
def validate_mcp_response(response, expected_schema=None):
    """Validate that an MCP response meets expected format"""
    # Implementation

def validate_kubernetes_state(resource_type, name, namespace, expected_state):
    """Validate that Kubernetes resources match expected state"""
    # Implementation
```

## Test Execution Plan

1. **Phase 1**: Basic connectivity and CRUD operations
2. **Phase 2**: Namespace management and context awareness
3. **Phase 3**: Advanced features (monitoring, security, diagnostics)
4. **Phase 4**: Error handling and edge cases
5. **Phase 5**: Performance and load testing

## Continuous Integration

- Add CI pipeline to run MCP tests on PRs
- Generate test coverage reports
- Track feature-by-feature test status

## Implementation Timeline

1. Basic test framework and environment setup - 2 days
2. Core operations tests - 3 days
3. Advanced feature tests - 5 days
4. Error handling and edge cases - 2 days
5. CI integration - 1 day

Total estimated time: 13 days 

## Implementation Status

The test framework has been fully implemented with the following components:

1. **MCP Client Simulator** (`mcp_client_simulator.py`)
   - Simulates an MCP client for testing
   - Supports both HTTP and stdio transports
   - Provides methods for listing tools and calling tools

2. **Test Utilities** (`test_utils.py`)
   - Provides namespace management with retry logic
   - Includes resource generation functions
   - Contains validation utilities for MCP responses and Kubernetes states

3. **Test Runner** (`run_mcp_tests.py`)
   - Manages test execution
   - Checks dependencies before running tests
   - Generates HTML test reports

4. **Feature-Specific Test Modules**:
   - Core Kubernetes Operations (`test_mcp_core.py`)
   - Security Operations (`test_mcp_security.py`)
   - Monitoring Capabilities (`test_mcp_monitoring.py`)
   - Natural Language Processing (`test_mcp_nlp.py`)
   - Diagnostics Features (`test_mcp_diagnostics.py`)

### Running the Tests

To run all tests:
```bash
./python_tests/run_mcp_tests.py
```

To run a specific test module:
```bash
./python_tests/run_mcp_tests.py --module python_tests/test_mcp_core.py
```

To generate an HTML report:
```bash
./python_tests/run_mcp_tests.py --report
```

### Test Coverage

The implemented tests cover all five major feature categories:

1. **Core Kubernetes Operations**
   - Namespace management
   - Pod and deployment operations
   - Resource API exploration

2. **Security Operations**
   - RBAC validation and management
   - ServiceAccount operations
   - Pod security context auditing

3. **Monitoring Capabilities**
   - Event monitoring
   - Resource utilization tracking
   - Node and pod health monitoring

4. **Natural Language Processing**
   - Simple and complex query handling
   - Context-aware operations
   - Mock data support
   - Explanation generation

5. **Diagnostics Features**
   - YAML validation
   - Resource issue analysis
   - Probe validation
   - Cluster diagnostics

### Next Steps

1. **CI Integration**: Add these tests to CI/CD pipeline
2. **Performance Testing**: Implement load and performance test scenarios
3. **Edge Cases**: Expand test coverage for error conditions and edge cases
4. **Documentation**: Generate comprehensive test documentation from test executions 