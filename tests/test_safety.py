"""Tests for safety mode implementation."""

import pytest
from kubectl_mcp_tool.safety import (
    SafetyMode,
    get_safety_mode,
    set_safety_mode,
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
