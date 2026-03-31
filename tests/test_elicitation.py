import pytest
from unittest.mock import AsyncMock, MagicMock
from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode


class MockElicitResult:
    def __init__(self, action):
        self.action = action


class TestConfirmDestructive:
    @pytest.fixture(autouse=True)
    def reset_safety(self):
        set_safety_mode(SafetyMode.NORMAL)
        yield
        set_safety_mode(SafetyMode.NORMAL)

    @pytest.mark.asyncio
    async def test_read_only_blocks_without_elicitation(self):
        from kubectl_mcp_tool.elicit import confirm_destructive
        set_safety_mode(SafetyMode.READ_ONLY)
        ctx = MagicMock()
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is not None
        assert "read-only" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_disable_destructive_blocks_without_elicitation(self):
        from kubectl_mcp_tool.elicit import confirm_destructive
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)
        ctx = MagicMock()
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is not None
        assert "destructive" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_normal_mode_elicit_accepted(self):
        from kubectl_mcp_tool.elicit import confirm_destructive
        set_safety_mode(SafetyMode.NORMAL)
        ctx = AsyncMock()
        ctx.elicit.return_value = MockElicitResult("accept")
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is None
        ctx.elicit.assert_called_once()

    @pytest.mark.asyncio
    async def test_normal_mode_elicit_declined(self):
        from kubectl_mcp_tool.elicit import confirm_destructive
        set_safety_mode(SafetyMode.NORMAL)
        ctx = AsyncMock()
        ctx.elicit.return_value = MockElicitResult("decline")
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is not None
        assert "cancelled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_normal_mode_elicit_unsupported_proceeds(self):
        from kubectl_mcp_tool.elicit import confirm_destructive
        set_safety_mode(SafetyMode.NORMAL)
        ctx = AsyncMock()
        ctx.elicit.side_effect = Exception("Elicitation not supported")
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is None

    @pytest.mark.asyncio
    async def test_confirm_mode_elicit_unsupported_blocks(self):
        from kubectl_mcp_tool.elicit import confirm_destructive
        set_safety_mode(SafetyMode.CONFIRM)
        ctx = AsyncMock()
        ctx.elicit.side_effect = Exception("Elicitation not supported")
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is not None
        assert "doesn't support" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_confirm_mode_elicit_accepted(self):
        from kubectl_mcp_tool.elicit import confirm_destructive
        set_safety_mode(SafetyMode.CONFIRM)
        ctx = AsyncMock()
        ctx.elicit.return_value = MockElicitResult("accept")
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is None
