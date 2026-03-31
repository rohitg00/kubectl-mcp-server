import pytest
from unittest.mock import AsyncMock, MagicMock
from kubectl_mcp_tool.elicit import confirm_destructive, check_write_allowed
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
        set_safety_mode(SafetyMode.READ_ONLY)
        ctx = MagicMock()
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is not None
        assert "read-only" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_disable_destructive_blocks_without_elicitation(self):
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)
        ctx = MagicMock()
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is not None
        assert "destructive" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_normal_mode_proceeds_without_elicitation(self):
        set_safety_mode(SafetyMode.NORMAL)
        ctx = AsyncMock()
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is None
        ctx.elicit.assert_not_called()

    @pytest.mark.asyncio
    async def test_normal_mode_proceeds_even_with_none_ctx(self):
        set_safety_mode(SafetyMode.NORMAL)
        result = await confirm_destructive(None, "Delete pod", "nginx", "default")
        assert result is None

    @pytest.mark.asyncio
    async def test_confirm_mode_elicit_accepted(self):
        set_safety_mode(SafetyMode.CONFIRM)
        ctx = AsyncMock()
        ctx.elicit.return_value = MockElicitResult("accept")
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is None
        ctx.elicit.assert_called_once()

    @pytest.mark.asyncio
    async def test_confirm_mode_elicit_declined(self):
        set_safety_mode(SafetyMode.CONFIRM)
        ctx = AsyncMock()
        ctx.elicit.return_value = MockElicitResult("decline")
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is not None
        assert "cancelled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_confirm_mode_elicit_unsupported_blocks(self):
        set_safety_mode(SafetyMode.CONFIRM)
        ctx = AsyncMock()
        ctx.elicit.side_effect = NotImplementedError("not supported")
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is not None
        assert "doesn't support" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_confirm_mode_blocks_when_ctx_is_none(self):
        set_safety_mode(SafetyMode.CONFIRM)
        result = await confirm_destructive(None, "Delete pod", "nginx")
        assert result is not None
        assert "no client context" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_namespace_omitted_for_cluster_scoped_ops(self):
        set_safety_mode(SafetyMode.CONFIRM)
        ctx = AsyncMock()
        ctx.elicit.return_value = MockElicitResult("accept")
        await confirm_destructive(ctx, "Delete kind cluster", "test-cluster")
        call_args = ctx.elicit.call_args[0][0]
        assert "namespace" not in call_args.lower()

    @pytest.mark.asyncio
    async def test_namespace_included_when_provided(self):
        set_safety_mode(SafetyMode.CONFIRM)
        ctx = AsyncMock()
        ctx.elicit.return_value = MockElicitResult("accept")
        await confirm_destructive(ctx, "Delete pod", "nginx", "production")
        call_args = ctx.elicit.call_args[0][0]
        assert "production" in call_args


class TestCheckWriteAllowed:
    @pytest.fixture(autouse=True)
    def reset_safety(self):
        set_safety_mode(SafetyMode.NORMAL)
        yield
        set_safety_mode(SafetyMode.NORMAL)

    @pytest.mark.asyncio
    async def test_read_only_blocks_writes(self):
        set_safety_mode(SafetyMode.READ_ONLY)
        result = await check_write_allowed()
        assert result is not None
        assert "read-only" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_normal_allows_writes(self):
        set_safety_mode(SafetyMode.NORMAL)
        result = await check_write_allowed()
        assert result is None

    @pytest.mark.asyncio
    async def test_disable_destructive_allows_writes(self):
        set_safety_mode(SafetyMode.DISABLE_DESTRUCTIVE)
        result = await check_write_allowed()
        assert result is None

    @pytest.mark.asyncio
    async def test_confirm_allows_writes(self):
        set_safety_mode(SafetyMode.CONFIRM)
        result = await check_write_allowed()
        assert result is None
