import pytest
from unittest.mock import AsyncMock, MagicMock
from kubectl_mcp_tool.elicit import confirm_destructive, check_write_allowed
from kubectl_mcp_tool.safety import SafetyMode, set_safety_mode


class MockElicitResult:
    def __init__(self, action, data=None):
        self.action = action
        self.data = data


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
        ctx.elicit.return_value = MockElicitResult("accept", True)
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert result is None
        ctx.elicit.assert_called_once()
        assert ctx.elicit.call_args.kwargs["response_type"] is bool

    @pytest.mark.asyncio
    async def test_confirm_mode_accept_without_true_value_is_cancelled(self):
        set_safety_mode(SafetyMode.CONFIRM)
        ctx = AsyncMock()
        ctx.elicit.return_value = MockElicitResult("accept", False)
        result = await confirm_destructive(ctx, "Delete pod", "nginx", "default")
        assert "cancelled" in result["error"].lower()

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


class TestModernProtocolGuard:
    @pytest.fixture(autouse=True)
    def confirm_mode(self):
        set_safety_mode(SafetyMode.CONFIRM)
        yield
        set_safety_mode(SafetyMode.NORMAL)

    def _ctx(self, responses=None, state=None):
        ctx = MagicMock()
        ctx.request_context.protocol_version = "2026-07-28"
        ctx.input_responses = responses
        ctx.request_state = state
        return ctx

    @pytest.mark.asyncio
    async def test_first_round_returns_input_required(self):
        from mcp.types import InputRequiredResult
        result = await confirm_destructive(self._ctx(), "Delete pod", "nginx", "default")
        assert isinstance(result, InputRequiredResult)
        assert "confirm" in result.input_requests
        assert "nginx" in result.input_requests["confirm"].params.message

    @pytest.mark.asyncio
    async def test_accepted_answer_bound_to_same_operation(self):
        first = await confirm_destructive(self._ctx(), "Delete pod", "nginx", "default")
        answer = MagicMock(action="accept", content={"confirm": True})
        approved = await confirm_destructive(self._ctx({"confirm": answer}, first.request_state), "Delete pod", "nginx", "default")
        assert approved is None
        replayed = await confirm_destructive(self._ctx({"confirm": answer}, first.request_state), "Delete pod", "other", "default")
        assert replayed is not None and not isinstance(replayed, dict)

    @pytest.mark.asyncio
    async def test_declined_answer_cancels(self):
        first = await confirm_destructive(self._ctx(), "Delete pod", "nginx")
        answer = MagicMock(action="decline", content=None)
        result = await confirm_destructive(self._ctx({"confirm": answer}, first.request_state), "Delete pod", "nginx")
        assert "cancelled" in result["error"].lower()


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
