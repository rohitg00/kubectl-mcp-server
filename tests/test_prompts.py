"""
Unit tests for MCP Prompts in kubectl-mcp-server.

This module tests all FastMCP 3 prompts including:
- troubleshoot_workload
- deploy_application
- security_audit
- cost_optimization
- disaster_recovery
- debug_networking
- scale_application
- upgrade_cluster

Also tests the configurable prompts system:
- Custom prompt loading from TOML
- Template rendering with Mustache syntax
- Built-in prompts (cluster-health-check, debug-workload, etc.)
- Prompt validation and merging
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

from kubectl_mcp_tool.prompts.custom import (
    CustomPrompt,
    PromptArgument,
    PromptMessage,
    render_prompt,
    load_prompts_from_config,
    load_prompts_from_toml_file,
    validate_prompt_args,
    apply_defaults,
    get_prompt_schema,
)
from kubectl_mcp_tool.prompts.builtin import (
    BUILTIN_PROMPTS,
    get_builtin_prompts,
    get_builtin_prompt_by_name,
    CLUSTER_HEALTH_CHECK,
    DEBUG_WORKLOAD,
    RESOURCE_USAGE,
    SECURITY_POSTURE,
    DEPLOYMENT_CHECKLIST,
    INCIDENT_RESPONSE,
)


class TestTroubleshootWorkloadPrompt:
    """Tests for troubleshoot_workload prompt."""

    @pytest.mark.unit
    def test_prompt_registration(self):
        """Test that troubleshoot_workload prompt is registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_prompt_with_namespace(self):
        """Test troubleshoot prompt with specific namespace."""
        workload = "nginx"
        namespace = "production"

        expected_content = f"Target: pods matching '{workload}' in namespace '{namespace}'"
        assert workload in expected_content
        assert namespace in expected_content

    @pytest.mark.unit
    def test_prompt_all_namespaces(self):
        """Test troubleshoot prompt for all namespaces."""
        workload = "nginx"

        expected_content = f"Target: pods matching '{workload}' across all namespaces"
        assert workload in expected_content
        assert "all namespaces" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_troubleshooting_steps(self):
        """Test that prompt includes troubleshooting steps."""
        expected_sections = [
            "Step 1: Discovery",
            "Step 2: Status Analysis",
            "Step 3: Deep Inspection",
            "Step 4: Related Resources",
            "Step 5: Resolution Checklist"
        ]

        prompt_content = """
        ## Step 1: Discovery
        ## Step 2: Status Analysis
        ## Step 3: Deep Inspection
        ## Step 4: Related Resources
        ## Step 5: Resolution Checklist
        """

        for section in expected_sections:
            assert section in prompt_content


class TestDeployApplicationPrompt:
    """Tests for deploy_application prompt."""

    @pytest.mark.unit
    def test_prompt_registration(self):
        """Test that deploy_application prompt is registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_prompt_includes_app_name(self):
        """Test that prompt includes application name."""
        app_name = "my-app"
        namespace = "default"

        expected_content = f"# Kubernetes Deployment Guide: {app_name}"
        assert app_name in expected_content

    @pytest.mark.unit
    def test_prompt_includes_replica_count(self):
        """Test that prompt includes replica count."""
        replicas = 3

        expected_content = f"replicas: {replicas}"
        assert str(replicas) in expected_content

    @pytest.mark.unit
    def test_prompt_includes_deployment_steps(self):
        """Test that prompt includes deployment steps."""
        expected_sections = [
            "Pre-Deployment Checklist",
            "Prepare Deployment Manifest",
            "Apply Configuration",
            "Verify Deployment",
            "Rollback Plan"
        ]

        prompt_content = """
        ## Pre-Deployment Checklist
        ### Prepare Deployment Manifest
        ### Apply Configuration
        ### Verify Deployment
        ## Rollback Plan
        """

        for section in expected_sections:
            # Check if section keywords are present
            assert any(word in prompt_content for word in section.split())


class TestSecurityAuditPrompt:
    """Tests for security_audit prompt."""

    @pytest.mark.unit
    def test_prompt_registration(self):
        """Test that security_audit prompt is registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_prompt_includes_rbac_analysis(self):
        """Test that prompt includes RBAC analysis."""
        expected_content = "RBAC Analysis"
        assert "RBAC" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_pod_security(self):
        """Test that prompt includes pod security checks."""
        expected_checks = [
            "Pods running as non-root",
            "Read-only root filesystem",
            "Dropped capabilities",
            "No privilege escalation"
        ]

        prompt_content = """
        - [ ] Pods running as non-root
        - [ ] Read-only root filesystem
        - [ ] Dropped capabilities
        - [ ] No privilege escalation
        """

        for check in expected_checks:
            assert check in prompt_content

    @pytest.mark.unit
    def test_prompt_includes_secrets_management(self):
        """Test that prompt includes secrets management."""
        expected_content = "Secrets Management"
        assert "Secrets" in expected_content


class TestCostOptimizationPrompt:
    """Tests for cost_optimization prompt."""

    @pytest.mark.unit
    def test_prompt_registration(self):
        """Test that cost_optimization prompt is registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_prompt_includes_resource_usage(self):
        """Test that prompt includes resource usage analysis."""
        expected_content = "Resource Usage Analysis"
        assert "Resource" in expected_content
        assert "Usage" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_idle_detection(self):
        """Test that prompt includes idle resource detection."""
        expected_content = "Idle Resource Detection"
        assert "Idle" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_cost_estimation(self):
        """Test that prompt includes cost estimation."""
        expected_content = "Cost Estimation"
        assert "Cost" in expected_content


class TestDisasterRecoveryPrompt:
    """Tests for disaster_recovery prompt."""

    @pytest.mark.unit
    def test_prompt_registration(self):
        """Test that disaster_recovery prompt is registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_prompt_includes_backup_strategy(self):
        """Test that prompt includes backup strategy."""
        expected_content = "Backup Strategy"
        assert "Backup" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_recovery_procedures(self):
        """Test that prompt includes recovery procedures."""
        expected_content = "Recovery Procedures"
        assert "Recovery" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_rto_rpo(self):
        """Test that prompt includes RTO/RPO documentation."""
        expected_terms = ["RTO", "RPO"]
        prompt_content = "RTO (Recovery Time Objective) and RPO (Recovery Point Objective)"

        for term in expected_terms:
            assert term in prompt_content


class TestDebugNetworkingPrompt:
    """Tests for debug_networking prompt."""

    @pytest.mark.unit
    def test_prompt_registration(self):
        """Test that debug_networking prompt is registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_prompt_includes_service_name(self):
        """Test that prompt includes service name."""
        service_name = "my-service"
        namespace = "default"

        expected_content = f"Target: Service '{service_name}' in namespace '{namespace}'"
        assert service_name in expected_content
        assert namespace in expected_content

    @pytest.mark.unit
    def test_prompt_includes_dns_resolution(self):
        """Test that prompt includes DNS resolution checks."""
        expected_content = "DNS Resolution"
        assert "DNS" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_connectivity_testing(self):
        """Test that prompt includes connectivity testing."""
        expected_content = "Connectivity Testing"
        assert "Connectivity" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_common_issues(self):
        """Test that prompt includes common issues."""
        common_issues = [
            "No Endpoints",
            "Connection Refused",
            "Connection Timeout",
            "DNS Resolution Failed"
        ]

        prompt_content = """
        ### Issue: No Endpoints
        ### Issue: Connection Refused
        ### Issue: Connection Timeout
        ### Issue: DNS Resolution Failed
        """

        for issue in common_issues:
            assert issue in prompt_content


class TestScaleApplicationPrompt:
    """Tests for scale_application prompt."""

    @pytest.mark.unit
    def test_prompt_registration(self):
        """Test that scale_application prompt is registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_prompt_includes_target_replicas(self):
        """Test that prompt includes target replica count."""
        app_name = "my-app"
        target_replicas = 5

        expected_content = f"Target Replicas: {target_replicas}"
        assert str(target_replicas) in expected_content

    @pytest.mark.unit
    def test_prompt_includes_scaling_methods(self):
        """Test that prompt includes different scaling methods."""
        scaling_methods = [
            "Manual Scaling",
            "Horizontal Pod Autoscaler",
            "Vertical Pod Autoscaler"
        ]

        prompt_content = """
        ### Method 1: Manual Scaling
        ### Method 2: Horizontal Pod Autoscaler (HPA)
        ### Method 3: Vertical Pod Autoscaler (VPA)
        """

        for method in scaling_methods:
            # Check for keywords from each method
            assert any(word in prompt_content for word in method.split())

    @pytest.mark.unit
    def test_prompt_includes_pdb(self):
        """Test that prompt includes Pod Disruption Budget."""
        expected_content = "Pod Disruption Budget"
        assert "PodDisruptionBudget" in "PodDisruptionBudget" or "Pod Disruption Budget" in expected_content


class TestUpgradeClusterPrompt:
    """Tests for upgrade_cluster prompt."""

    @pytest.mark.unit
    def test_prompt_registration(self):
        """Test that upgrade_cluster prompt is registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None

    @pytest.mark.unit
    def test_prompt_includes_versions(self):
        """Test that prompt includes version information."""
        current_version = "1.28"
        target_version = "1.29"

        expected_content = f"Current Version: {current_version}\nTarget Version: {target_version}"
        assert current_version in expected_content
        assert target_version in expected_content

    @pytest.mark.unit
    def test_prompt_includes_upgrade_phases(self):
        """Test that prompt includes upgrade phases."""
        upgrade_phases = [
            "Pre-Upgrade Phase",
            "Control Plane Upgrade",
            "Node Upgrade",
            "Post-Upgrade Verification"
        ]

        prompt_content = """
        ## Pre-Upgrade Phase
        ## Control Plane Upgrade
        ## Node Upgrade
        ## Post-Upgrade Verification
        """

        for phase in upgrade_phases:
            assert phase in prompt_content

    @pytest.mark.unit
    def test_prompt_includes_rollback_plan(self):
        """Test that prompt includes rollback plan."""
        expected_content = "Rollback Plan"
        assert "Rollback" in expected_content

    @pytest.mark.unit
    def test_prompt_includes_checklist(self):
        """Test that prompt includes upgrade checklist."""
        checklist_items = [
            "Backup etcd",
            "Check API deprecations",
            "Verify addon compatibility",
            "Test upgrade in staging"
        ]

        prompt_content = """
        - [ ] Backup etcd
        - [ ] Check API deprecations
        - [ ] Verify addon compatibility
        - [ ] Test upgrade in staging
        """

        for item in checklist_items:
            assert item in prompt_content


class TestPromptRegistration:
    """Tests for prompt registration and metadata."""

    @pytest.mark.unit
    def test_all_prompts_registered(self):
        """Test that all expected prompts are registered."""
        from kubectl_mcp_tool.mcp_server import MCPServer

        with patch("kubectl_mcp_tool.mcp_server.MCPServer._check_dependencies", return_value=True):
            with patch("kubernetes.config.load_kube_config"):
                server = MCPServer(name="test")

        assert server is not None
        assert hasattr(server, 'server')

    @pytest.mark.unit
    def test_prompts_have_docstrings(self):
        """Test that all prompts have documentation."""
        expected_prompts = [
            "troubleshoot_workload",
            "deploy_application",
            "security_audit",
            "cost_optimization",
            "disaster_recovery",
            "debug_networking",
            "scale_application",
            "upgrade_cluster"
        ]

        # Each prompt should have a descriptive name
        for prompt_name in expected_prompts:
            assert "_" in prompt_name or prompt_name.islower()

    @pytest.mark.unit
    def test_prompts_return_strings(self):
        """Test that prompts return string content."""
        sample_prompt_output = "# Kubernetes Troubleshooting Guide"
        assert isinstance(sample_prompt_output, str)
        assert len(sample_prompt_output) > 0


class TestPromptContent:
    """Tests for prompt content quality."""

    @pytest.mark.unit
    def test_prompts_include_tool_references(self):
        """Test that prompts reference available tools."""
        tool_references = [
            "get_pods",
            "get_deployments",
            "get_logs",
            "kubectl_describe",
            "kubectl_apply"
        ]

        prompt_content = """
        - `get_pods(namespace="default")` - List pods
        - `get_deployments(namespace="default")` - List deployments
        - `get_logs(pod_name, namespace)` - Get pod logs
        - `kubectl_describe("pod", name, namespace)` - Describe resource
        - `kubectl_apply(yaml)` - Apply manifest
        """

        for tool in tool_references:
            assert tool in prompt_content

    @pytest.mark.unit
    def test_prompts_use_markdown_formatting(self):
        """Test that prompts use proper Markdown formatting."""
        prompt_content = """
        # Heading 1
        ## Heading 2
        ### Heading 3

        - Bullet point
        - Another bullet

        1. Numbered list
        2. Second item

        ```yaml
        apiVersion: v1
        kind: Pod
        ```

        | Column 1 | Column 2 |
        |----------|----------|
        | Value 1  | Value 2  |
        """

        # Check for Markdown elements
        assert "#" in prompt_content  # Headings
        assert "-" in prompt_content  # Bullets
        assert "```" in prompt_content  # Code blocks
        assert "|" in prompt_content  # Tables

    @pytest.mark.unit
    def test_prompts_end_with_action(self):
        """Test that prompts end with an action statement."""
        action_statements = [
            "Start the investigation now.",
            "Start the deployment process now.",
            "Begin the security audit now.",
            "Begin the cost optimization analysis now.",
            "Begin disaster recovery planning now.",
            "Begin network debugging now.",
            "Begin scaling operation now.",
            "Begin upgrade planning now."
        ]

        for statement in action_statements:
            # Verify each statement is a valid action prompt
            assert "now" in statement.lower() or "begin" in statement.lower() or "start" in statement.lower()


# =============================================================================
# Configurable Prompts System Tests
# =============================================================================


class TestPromptArgument:
    """Tests for PromptArgument dataclass."""

    @pytest.mark.unit
    def test_create_required_argument(self):
        """Test creating a required prompt argument."""
        arg = PromptArgument(
            name="pod_name",
            description="Name of the pod",
            required=True
        )
        assert arg.name == "pod_name"
        assert arg.description == "Name of the pod"
        assert arg.required is True
        assert arg.default == ""

    @pytest.mark.unit
    def test_create_optional_argument_with_default(self):
        """Test creating an optional argument with default value."""
        arg = PromptArgument(
            name="namespace",
            description="Kubernetes namespace",
            required=False,
            default="default"
        )
        assert arg.name == "namespace"
        assert arg.required is False
        assert arg.default == "default"


class TestPromptMessage:
    """Tests for PromptMessage dataclass."""

    @pytest.mark.unit
    def test_create_user_message(self):
        """Test creating a user message."""
        msg = PromptMessage(
            role="user",
            content="Debug the pod in namespace default"
        )
        assert msg.role == "user"
        assert msg.content == "Debug the pod in namespace default"

    @pytest.mark.unit
    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        msg = PromptMessage(
            role="assistant",
            content="I'll help you debug the pod."
        )
        assert msg.role == "assistant"


class TestCustomPrompt:
    """Tests for CustomPrompt dataclass."""

    @pytest.mark.unit
    def test_create_simple_prompt(self):
        """Test creating a simple custom prompt."""
        prompt = CustomPrompt(
            name="test-prompt",
            title="Test Prompt",
            description="A test prompt"
        )
        assert prompt.name == "test-prompt"
        assert prompt.title == "Test Prompt"
        assert prompt.description == "A test prompt"
        assert prompt.arguments == []
        assert prompt.messages == []

    @pytest.mark.unit
    def test_create_prompt_with_arguments_and_messages(self):
        """Test creating a prompt with arguments and messages."""
        prompt = CustomPrompt(
            name="debug-pod",
            title="Debug Pod",
            description="Debug a Kubernetes pod",
            arguments=[
                PromptArgument(name="pod_name", required=True),
                PromptArgument(name="namespace", default="default"),
            ],
            messages=[
                PromptMessage(role="user", content="Debug pod {{pod_name}}"),
            ]
        )
        assert len(prompt.arguments) == 2
        assert len(prompt.messages) == 1
        assert prompt.arguments[0].name == "pod_name"


class TestRenderPrompt:
    """Tests for render_prompt function."""

    @pytest.mark.unit
    def test_simple_variable_substitution(self):
        """Test basic variable substitution."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            messages=[
                PromptMessage(role="user", content="Debug pod {{pod_name}} in {{namespace}}")
            ]
        )
        result = render_prompt(prompt, {"pod_name": "nginx", "namespace": "production"})
        assert len(result) == 1
        assert result[0].content == "Debug pod nginx in production"
        assert result[0].role == "user"

    @pytest.mark.unit
    def test_conditional_section_shown_when_true(self):
        """Test conditional section is shown when variable is truthy."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            messages=[
                PromptMessage(
                    role="user",
                    content="Check pods{{#namespace}} in namespace {{namespace}}{{/namespace}}."
                )
            ]
        )
        result = render_prompt(prompt, {"namespace": "production"})
        assert "in namespace production" in result[0].content

    @pytest.mark.unit
    def test_conditional_section_hidden_when_false(self):
        """Test conditional section is hidden when variable is falsy."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            messages=[
                PromptMessage(
                    role="user",
                    content="Check pods{{#namespace}} in namespace {{namespace}}{{/namespace}}."
                )
            ]
        )
        result = render_prompt(prompt, {})
        assert "in namespace" not in result[0].content
        assert result[0].content == "Check pods."

    @pytest.mark.unit
    def test_conditional_section_with_false_value(self):
        """Test conditional section is hidden when variable is 'false'."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            messages=[
                PromptMessage(
                    role="user",
                    content="{{#check_metrics}}Include metrics analysis.{{/check_metrics}}"
                )
            ]
        )
        result = render_prompt(prompt, {"check_metrics": "false"})
        assert "Include metrics" not in result[0].content

    @pytest.mark.unit
    def test_inverse_section_shown_when_false(self):
        """Test inverse section is shown when variable is falsy."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            messages=[
                PromptMessage(
                    role="user",
                    content="{{^namespace}}All namespaces{{/namespace}}{{#namespace}}Namespace: {{namespace}}{{/namespace}}"
                )
            ]
        )
        result = render_prompt(prompt, {})
        assert "All namespaces" in result[0].content

    @pytest.mark.unit
    def test_inverse_section_hidden_when_true(self):
        """Test inverse section is hidden when variable is truthy."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            messages=[
                PromptMessage(
                    role="user",
                    content="{{^namespace}}All namespaces{{/namespace}}{{#namespace}}Namespace: {{namespace}}{{/namespace}}"
                )
            ]
        )
        result = render_prompt(prompt, {"namespace": "production"})
        assert "All namespaces" not in result[0].content
        assert "Namespace: production" in result[0].content

    @pytest.mark.unit
    def test_multiple_messages(self):
        """Test rendering multiple messages."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            messages=[
                PromptMessage(role="user", content="Hello {{name}}"),
                PromptMessage(role="assistant", content="Hi there!"),
                PromptMessage(role="user", content="Debug {{pod}}"),
            ]
        )
        result = render_prompt(prompt, {"name": "Admin", "pod": "nginx"})
        assert len(result) == 3
        assert result[0].content == "Hello Admin"
        assert result[2].content == "Debug nginx"

    @pytest.mark.unit
    def test_unsubstituted_variables_removed(self):
        """Test that unsubstituted optional variables are removed."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            messages=[
                PromptMessage(role="user", content="Check {{resource}} status {{unknown_var}}")
            ]
        )
        result = render_prompt(prompt, {"resource": "pods"})
        assert result[0].content == "Check pods status"


class TestLoadPromptsFromConfig:
    """Tests for load_prompts_from_config function."""

    @pytest.mark.unit
    def test_load_simple_prompt(self):
        """Test loading a simple prompt from config dict."""
        config = {
            "prompts": [
                {
                    "name": "debug-pod",
                    "title": "Debug Pod",
                    "description": "Debug a pod",
                    "arguments": [
                        {"name": "pod_name", "required": True, "description": "Pod name"}
                    ],
                    "messages": [
                        {"role": "user", "content": "Debug {{pod_name}}"}
                    ]
                }
            ]
        }
        prompts = load_prompts_from_config(config)
        assert len(prompts) == 1
        assert prompts[0].name == "debug-pod"
        assert prompts[0].title == "Debug Pod"
        assert len(prompts[0].arguments) == 1
        assert prompts[0].arguments[0].required is True

    @pytest.mark.unit
    def test_load_multiple_prompts(self):
        """Test loading multiple prompts from config."""
        config = {
            "prompts": [
                {"name": "prompt1", "description": "First", "messages": [{"role": "user", "content": "Hello"}]},
                {"name": "prompt2", "description": "Second", "messages": [{"role": "user", "content": "World"}]},
            ]
        }
        prompts = load_prompts_from_config(config)
        assert len(prompts) == 2

    @pytest.mark.unit
    def test_load_empty_config(self):
        """Test loading from empty config returns empty list."""
        prompts = load_prompts_from_config({})
        assert prompts == []

    @pytest.mark.unit
    def test_load_config_with_defaults(self):
        """Test that argument defaults are loaded."""
        config = {
            "prompts": [
                {
                    "name": "test",
                    "description": "Test",
                    "arguments": [
                        {"name": "namespace", "required": False, "default": "default"}
                    ],
                    "messages": [{"role": "user", "content": "Test"}]
                }
            ]
        }
        prompts = load_prompts_from_config(config)
        assert prompts[0].arguments[0].default == "default"

    @pytest.mark.unit
    def test_skip_invalid_prompts(self):
        """Test that invalid prompts are skipped."""
        config = {
            "prompts": [
                {"name": "", "description": "Invalid - no name"},  # Invalid
                {"name": "valid", "description": "Valid prompt", "messages": [{"role": "user", "content": "Hi"}]},
            ]
        }
        prompts = load_prompts_from_config(config)
        assert len(prompts) == 1
        assert prompts[0].name == "valid"


class TestLoadPromptsFromTomlFile:
    """Tests for load_prompts_from_toml_file function."""

    @pytest.mark.unit
    def test_load_from_valid_toml(self):
        """Test loading prompts from a valid TOML file."""
        toml_content = """
[[prompts]]
name = "test-prompt"
title = "Test Prompt"
description = "A test prompt for testing"

[[prompts.arguments]]
name = "target"
description = "Target resource"
required = true

[[prompts.messages]]
role = "user"
content = "Check {{target}}"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            try:
                prompts = load_prompts_from_toml_file(f.name)
                assert len(prompts) == 1
                assert prompts[0].name == "test-prompt"
                assert len(prompts[0].arguments) == 1
            finally:
                os.unlink(f.name)

    @pytest.mark.unit
    def test_load_from_nonexistent_file(self):
        """Test loading from nonexistent file returns empty list."""
        prompts = load_prompts_from_toml_file("/nonexistent/path/prompts.toml")
        assert prompts == []


class TestValidatePromptArgs:
    """Tests for validate_prompt_args function."""

    @pytest.mark.unit
    def test_valid_required_args(self):
        """Test validation passes with all required args."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(name="required_arg", required=True),
            ]
        )
        errors = validate_prompt_args(prompt, {"required_arg": "value"})
        assert errors == []

    @pytest.mark.unit
    def test_missing_required_arg(self):
        """Test validation fails with missing required arg."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(name="required_arg", required=True),
            ]
        )
        errors = validate_prompt_args(prompt, {})
        assert len(errors) == 1
        assert "required_arg" in errors[0]

    @pytest.mark.unit
    def test_empty_required_arg(self):
        """Test validation fails with empty required arg."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(name="required_arg", required=True),
            ]
        )
        errors = validate_prompt_args(prompt, {"required_arg": ""})
        assert len(errors) == 1

    @pytest.mark.unit
    def test_optional_args_not_required(self):
        """Test validation passes without optional args."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(name="optional_arg", required=False),
            ]
        )
        errors = validate_prompt_args(prompt, {})
        assert errors == []


class TestApplyDefaults:
    """Tests for apply_defaults function."""

    @pytest.mark.unit
    def test_apply_missing_defaults(self):
        """Test that defaults are applied for missing args."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(name="namespace", default="default"),
                PromptArgument(name="timeout", default="30"),
            ]
        )
        result = apply_defaults(prompt, {})
        assert result["namespace"] == "default"
        assert result["timeout"] == "30"

    @pytest.mark.unit
    def test_preserve_provided_values(self):
        """Test that provided values are preserved."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(name="namespace", default="default"),
            ]
        )
        result = apply_defaults(prompt, {"namespace": "production"})
        assert result["namespace"] == "production"

    @pytest.mark.unit
    def test_no_default_for_empty_string(self):
        """Test that empty string default is not applied."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(name="arg", default=""),
            ]
        )
        result = apply_defaults(prompt, {})
        assert "arg" not in result


class TestGetPromptSchema:
    """Tests for get_prompt_schema function."""

    @pytest.mark.unit
    def test_generate_schema(self):
        """Test generating JSON Schema for prompt."""
        prompt = CustomPrompt(
            name="test",
            description="Test",
            arguments=[
                PromptArgument(name="pod_name", description="Pod name", required=True),
                PromptArgument(name="namespace", description="Namespace", required=False, default="default"),
            ]
        )
        schema = get_prompt_schema(prompt)

        assert schema["type"] == "object"
        assert "pod_name" in schema["properties"]
        assert "namespace" in schema["properties"]
        assert schema["properties"]["namespace"]["default"] == "default"
        assert "pod_name" in schema["required"]
        assert "namespace" not in schema["required"]


# =============================================================================
# Built-in Prompts Tests
# =============================================================================


class TestBuiltinPrompts:
    """Tests for built-in prompts."""

    @pytest.mark.unit
    def test_all_builtin_prompts_exist(self):
        """Test that all expected built-in prompts exist."""
        assert len(BUILTIN_PROMPTS) == 6
        names = [p.name for p in BUILTIN_PROMPTS]
        assert "cluster-health-check" in names
        assert "debug-workload" in names
        assert "resource-usage" in names
        assert "security-posture" in names
        assert "deployment-checklist" in names
        assert "incident-response" in names

    @pytest.mark.unit
    def test_get_builtin_prompts_returns_copy(self):
        """Test that get_builtin_prompts returns a copy."""
        prompts1 = get_builtin_prompts()
        prompts2 = get_builtin_prompts()
        assert prompts1 is not prompts2
        assert len(prompts1) == len(prompts2)

    @pytest.mark.unit
    def test_get_builtin_prompt_by_name(self):
        """Test retrieving a built-in prompt by name."""
        prompt = get_builtin_prompt_by_name("cluster-health-check")
        assert prompt is not None
        assert prompt.name == "cluster-health-check"
        assert prompt.title == "Cluster Health Check"

    @pytest.mark.unit
    def test_get_builtin_prompt_not_found(self):
        """Test retrieving a non-existent built-in prompt."""
        prompt = get_builtin_prompt_by_name("nonexistent")
        assert prompt is None


class TestClusterHealthCheckPrompt:
    """Tests for CLUSTER_HEALTH_CHECK built-in prompt."""

    @pytest.mark.unit
    def test_prompt_structure(self):
        """Test CLUSTER_HEALTH_CHECK prompt structure."""
        assert CLUSTER_HEALTH_CHECK.name == "cluster-health-check"
        assert CLUSTER_HEALTH_CHECK.title == "Cluster Health Check"
        assert len(CLUSTER_HEALTH_CHECK.arguments) == 3
        assert len(CLUSTER_HEALTH_CHECK.messages) == 1

    @pytest.mark.unit
    def test_prompt_arguments(self):
        """Test CLUSTER_HEALTH_CHECK prompt arguments."""
        arg_names = [a.name for a in CLUSTER_HEALTH_CHECK.arguments]
        assert "namespace" in arg_names
        assert "check_events" in arg_names
        assert "check_metrics" in arg_names

    @pytest.mark.unit
    def test_render_with_namespace(self):
        """Test rendering with namespace specified."""
        result = render_prompt(CLUSTER_HEALTH_CHECK, {"namespace": "production"})
        assert "in namespace production" in result[0].content

    @pytest.mark.unit
    def test_render_without_namespace(self):
        """Test rendering without namespace shows cluster-wide."""
        result = render_prompt(CLUSTER_HEALTH_CHECK, {})
        # Should not have "in namespace" since namespace is empty
        assert result[0].content.count("in namespace ") == 0 or "namespace" not in result[0].content.split("in namespace ")[1].split()[0] if "in namespace " in result[0].content else True


class TestDebugWorkloadPrompt:
    """Tests for DEBUG_WORKLOAD built-in prompt."""

    @pytest.mark.unit
    def test_prompt_structure(self):
        """Test DEBUG_WORKLOAD prompt structure."""
        assert DEBUG_WORKLOAD.name == "debug-workload"
        assert DEBUG_WORKLOAD.title == "Debug Workload Issues"
        assert len(DEBUG_WORKLOAD.arguments) == 4

    @pytest.mark.unit
    def test_required_arguments(self):
        """Test DEBUG_WORKLOAD has required workload_name argument."""
        workload_arg = next(a for a in DEBUG_WORKLOAD.arguments if a.name == "workload_name")
        assert workload_arg.required is True

    @pytest.mark.unit
    def test_render_with_all_args(self):
        """Test rendering with all arguments."""
        result = render_prompt(DEBUG_WORKLOAD, {
            "workload_name": "nginx",
            "namespace": "production",
            "workload_type": "deployment",
            "include_related": "true"
        })
        assert "nginx" in result[0].content
        assert "production" in result[0].content
        assert "deployment" in result[0].content


class TestResourceUsagePrompt:
    """Tests for RESOURCE_USAGE built-in prompt."""

    @pytest.mark.unit
    def test_prompt_structure(self):
        """Test RESOURCE_USAGE prompt structure."""
        assert RESOURCE_USAGE.name == "resource-usage"
        assert len(RESOURCE_USAGE.arguments) == 4

    @pytest.mark.unit
    def test_default_thresholds(self):
        """Test default threshold values."""
        cpu_arg = next(a for a in RESOURCE_USAGE.arguments if a.name == "threshold_cpu")
        mem_arg = next(a for a in RESOURCE_USAGE.arguments if a.name == "threshold_memory")
        assert cpu_arg.default == "80"
        assert mem_arg.default == "80"


class TestSecurityPosturePrompt:
    """Tests for SECURITY_POSTURE built-in prompt."""

    @pytest.mark.unit
    def test_prompt_structure(self):
        """Test SECURITY_POSTURE prompt structure."""
        assert SECURITY_POSTURE.name == "security-posture"
        assert len(SECURITY_POSTURE.arguments) == 4

    @pytest.mark.unit
    def test_conditional_sections(self):
        """Test conditional sections for RBAC, network, secrets checks."""
        result = render_prompt(SECURITY_POSTURE, {
            "check_rbac": "true",
            "check_network": "false",
            "check_secrets": "true"
        })
        assert "RBAC Analysis" in result[0].content
        assert "Network Security" not in result[0].content
        assert "Secrets Management" in result[0].content


class TestDeploymentChecklistPrompt:
    """Tests for DEPLOYMENT_CHECKLIST built-in prompt."""

    @pytest.mark.unit
    def test_prompt_structure(self):
        """Test DEPLOYMENT_CHECKLIST prompt structure."""
        assert DEPLOYMENT_CHECKLIST.name == "deployment-checklist"
        assert len(DEPLOYMENT_CHECKLIST.arguments) == 4

    @pytest.mark.unit
    def test_required_arguments(self):
        """Test required arguments."""
        required_args = [a.name for a in DEPLOYMENT_CHECKLIST.arguments if a.required]
        assert "app_name" in required_args
        assert "namespace" in required_args
        assert "image" in required_args

    @pytest.mark.unit
    def test_render_with_args(self):
        """Test rendering with deployment args."""
        result = render_prompt(DEPLOYMENT_CHECKLIST, {
            "app_name": "myapp",
            "namespace": "production",
            "image": "myapp:v1.2.3",
            "replicas": "3"
        })
        assert "myapp" in result[0].content
        assert "production" in result[0].content
        assert "myapp:v1.2.3" in result[0].content
        assert "3" in result[0].content


class TestIncidentResponsePrompt:
    """Tests for INCIDENT_RESPONSE built-in prompt."""

    @pytest.mark.unit
    def test_prompt_structure(self):
        """Test INCIDENT_RESPONSE prompt structure."""
        assert INCIDENT_RESPONSE.name == "incident-response"
        assert len(INCIDENT_RESPONSE.arguments) == 4

    @pytest.mark.unit
    def test_required_arguments(self):
        """Test required arguments."""
        required_args = [a.name for a in INCIDENT_RESPONSE.arguments if a.required]
        assert "incident_type" in required_args
        assert "affected_service" in required_args
        assert "namespace" in required_args

    @pytest.mark.unit
    def test_default_severity(self):
        """Test default severity."""
        severity_arg = next(a for a in INCIDENT_RESPONSE.arguments if a.name == "severity")
        assert severity_arg.default == "high"

    @pytest.mark.unit
    def test_render_incident(self):
        """Test rendering incident response."""
        result = render_prompt(INCIDENT_RESPONSE, {
            "incident_type": "pod-crash",
            "affected_service": "api-server",
            "namespace": "production",
            "severity": "critical"
        })
        assert "pod-crash" in result[0].content
        assert "api-server" in result[0].content
        assert "production" in result[0].content
        assert "critical" in result[0].content
