"""Tests for safety mode implementation."""

import pytest
from kubectl_mcp_tool.safety import (
    SafetyMode,
    get_safety_mode,
    set_safety_mode,
    get_mode_info,
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

    def test_read_only_mode_info(self):
        """Test mode info in READ_ONLY mode."""
        set_safety_mode(SafetyMode.READ_ONLY)
        info = get_mode_info()
        assert info["mode"] == "read_only"
        assert "read" in info["description"].lower()

    def test_disable_destructive_mode_info(self):
        """Test mode info in DISABLE_DESTRUCTIVE mode."""
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)
        info = get_mode_info()
        assert info["mode"] == "disable_destructive"
        assert "delete" in info["description"].lower()
