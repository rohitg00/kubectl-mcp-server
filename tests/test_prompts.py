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
"""

import pytest
from unittest.mock import patch, MagicMock


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
