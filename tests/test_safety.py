"""Tests for safety mode implementation."""

import pytest
from kubectl_mcp_tool.safety import (
    SafetyMode,
    get_safety_mode,
    set_safety_mode,
    is_operation_allowed,
    check_safety_mode,
    get_mode_info,
    WRITE_OPERATIONS,
    DESTRUCTIVE_OPERATIONS,
)


class TestSafetyMode:
    """Test safety mode enum and state management."""

    def setup_method(self):
        """Reset safety mode to NORMAL before each test."""
        set_safety_mode(SafetyMode.NORMAL)

    def test_default_mode_is_normal(self):
        """Test that default safety mode is NORMAL."""
        assert get_safety_mode() == SafetyMode.NORMAL

    def test_set_read_only_mode(self):
        """Test setting read-only mode."""
        set_safety_mode(SafetyMode.READ_ONLY)
        assert get_safety_mode() == SafetyMode.READ_ONLY

    def test_set_disable_destructive_mode(self):
        """Test setting disable-destructive mode."""
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)
        assert get_safety_mode() == SafetyMode.DISABLE_DESTRUCTIVE


class TestOperationAllowed:
    """Test is_operation_allowed function."""

    def setup_method(self):
        """Reset safety mode to NORMAL before each test."""
        set_safety_mode(SafetyMode.NORMAL)

    def test_all_operations_allowed_in_normal_mode(self):
        """Test that all operations are allowed in NORMAL mode."""
        for op in WRITE_OPERATIONS | DESTRUCTIVE_OPERATIONS:
            allowed, reason = is_operation_allowed(op)
            assert allowed is True
            assert reason == ""

    def test_read_operations_allowed_in_all_modes(self):
        """Test that read operations are allowed in all modes."""
        read_ops = ["get_pods", "list_namespaces", "describe_deployment", "get_logs"]

        for mode in SafetyMode:
            set_safety_mode(mode)
            for op in read_ops:
                allowed, reason = is_operation_allowed(op)
                assert allowed is True

    def test_write_operations_blocked_in_read_only_mode(self):
        """Test that write operations are blocked in READ_ONLY mode."""
        set_safety_mode(SafetyMode.READ_ONLY)

        for op in WRITE_OPERATIONS:
            allowed, reason = is_operation_allowed(op)
            assert allowed is False
            assert "read-only mode" in reason

    def test_destructive_operations_blocked_in_read_only_mode(self):
        """Test that destructive operations are blocked in READ_ONLY mode."""
        set_safety_mode(SafetyMode.READ_ONLY)

        for op in DESTRUCTIVE_OPERATIONS:
            allowed, reason = is_operation_allowed(op)
            assert allowed is False
            assert "read-only mode" in reason

    def test_write_operations_allowed_in_disable_destructive_mode(self):
        """Test that non-destructive write operations are allowed in DISABLE_DESTRUCTIVE mode."""
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)

        # Operations that are write but not destructive
        non_destructive_writes = WRITE_OPERATIONS - DESTRUCTIVE_OPERATIONS
        for op in non_destructive_writes:
            allowed, reason = is_operation_allowed(op)
            assert allowed is True

    def test_destructive_operations_blocked_in_disable_destructive_mode(self):
        """Test that destructive operations are blocked in DISABLE_DESTRUCTIVE mode."""
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)

        for op in DESTRUCTIVE_OPERATIONS:
            allowed, reason = is_operation_allowed(op)
            assert allowed is False
            assert "destructive operations are disabled" in reason


class TestCheckSafetyModeDecorator:
    """Test the check_safety_mode decorator."""

    def setup_method(self):
        """Reset safety mode to NORMAL before each test."""
        set_safety_mode(SafetyMode.NORMAL)

    def test_decorator_allows_in_normal_mode(self):
        """Test that decorated function executes in NORMAL mode."""
        @check_safety_mode
        def delete_pod():
            return {"success": True, "message": "Pod deleted"}

        result = delete_pod()
        assert result["success"] is True
        assert result["message"] == "Pod deleted"

    def test_decorator_blocks_write_in_read_only_mode(self):
        """Test that decorated function is blocked in READ_ONLY mode."""
        set_safety_mode(SafetyMode.READ_ONLY)

        @check_safety_mode
        def run_pod():
            return {"success": True, "message": "Pod created"}

        result = run_pod()
        assert result["success"] is False
        assert "blocked" in result["error"]
        assert result["blocked_by"] == "read_only"
        assert result["operation"] == "run_pod"

    def test_decorator_blocks_destructive_in_disable_destructive_mode(self):
        """Test that destructive operations are blocked."""
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)

        @check_safety_mode
        def delete_deployment():
            return {"success": True, "message": "Deployment deleted"}

        result = delete_deployment()
        assert result["success"] is False
        assert "blocked" in result["error"]
        assert result["blocked_by"] == "disable_destructive"

    def test_decorator_allows_non_destructive_write_in_disable_destructive_mode(self):
        """Test that non-destructive writes are allowed in DISABLE_DESTRUCTIVE mode."""
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)

        @check_safety_mode
        def scale_deployment():
            return {"success": True, "message": "Deployment scaled"}

        result = scale_deployment()
        assert result["success"] is True


class TestGetModeInfo:
    """Test get_mode_info function."""

    def setup_method(self):
        """Reset safety mode to NORMAL before each test."""
        set_safety_mode(SafetyMode.NORMAL)

    def test_normal_mode_info(self):
        """Test mode info in NORMAL mode."""
        info = get_mode_info()
        assert info["mode"] == "normal"
        assert "All operations allowed" in info["description"]
        assert info["blocked_operations"] == []

    def test_read_only_mode_info(self):
        """Test mode info in READ_ONLY mode."""
        set_safety_mode(SafetyMode.READ_ONLY)
        info = get_mode_info()
        assert info["mode"] == "read_only"
        assert "read" in info["description"].lower()
        assert len(info["blocked_operations"]) > 0
        assert "delete_pod" in info["blocked_operations"]
        assert "run_pod" in info["blocked_operations"]

    def test_disable_destructive_mode_info(self):
        """Test mode info in DISABLE_DESTRUCTIVE mode."""
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)
        info = get_mode_info()
        assert info["mode"] == "disable_destructive"
        assert "delete" in info["description"].lower()
        assert len(info["blocked_operations"]) > 0
        assert "delete_pod" in info["blocked_operations"]
        # Non-destructive writes should not be blocked
        assert "scale_deployment" not in info["blocked_operations"]


class TestOperationCategories:
    """Test that operations are categorized correctly."""

    def test_all_destructive_ops_are_write_ops(self):
        """Test that all destructive operations are also write operations."""
        for op in DESTRUCTIVE_OPERATIONS:
            assert op in WRITE_OPERATIONS, f"{op} is destructive but not in WRITE_OPERATIONS"

    def test_expected_write_operations_exist(self):
        """Test that expected write operations are defined."""
        expected = [
            "run_pod", "delete_pod",
            "scale_deployment", "restart_deployment",
            "install_helm_chart", "uninstall_helm_chart",
            "apply_manifest", "delete_resource",
        ]
        for op in expected:
            assert op in WRITE_OPERATIONS, f"Expected {op} in WRITE_OPERATIONS"

    def test_expected_destructive_operations_exist(self):
        """Test that expected destructive operations are defined."""
        expected = [
            "delete_pod", "delete_deployment", "delete_namespace",
            "delete_resource", "uninstall_helm_chart",
        ]
        for op in expected:
            assert op in DESTRUCTIVE_OPERATIONS, f"Expected {op} in DESTRUCTIVE_OPERATIONS"
