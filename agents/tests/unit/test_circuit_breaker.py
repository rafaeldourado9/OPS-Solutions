"""
Unit tests for CircuitBreaker.
"""

from __future__ import annotations

import asyncio

import pytest

from infrastructure.circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState


async def _ok() -> str:
    return "ok"


async def _fail() -> str:
    raise ValueError("boom")


class TestCircuitBreaker:
    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_call_passes_through(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        result = await cb.call(_ok)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_failure_increments_count(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        with pytest.raises(ValueError):
            await cb.call(_fail)
        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        for _ in range(3):
            with pytest.raises(ValueError):
                await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self):
        cb = CircuitBreaker(name="test", failure_threshold=1)
        with pytest.raises(ValueError):
            await cb.call(_fail)
        # Now open
        with pytest.raises(CircuitOpenError):
            await cb.call(_ok)

    @pytest.mark.asyncio
    async def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)
        with pytest.raises(ValueError):
            await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

        await asyncio.sleep(0.02)  # Wait for recovery timeout

        # Next call should be allowed (HALF_OPEN probe)
        result = await cb.call(_ok)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failed_probe_keeps_open(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.01)
        with pytest.raises(ValueError):
            await cb.call(_fail)

        await asyncio.sleep(0.02)

        # Probe fails → stays OPEN
        with pytest.raises(ValueError):
            await cb.call(_fail)
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_success_resets_failure_count(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        with pytest.raises(ValueError):
            await cb.call(_fail)
        with pytest.raises(ValueError):
            await cb.call(_fail)
        # Still CLOSED after 2 failures
        assert cb.state == CircuitState.CLOSED

        # Success resets
        await cb.call(_ok)
        assert cb.failure_count == 0

    def test_manual_reset(self):
        cb = CircuitBreaker(name="test", failure_threshold=1)
        cb._state = CircuitState.OPEN
        cb._failure_count = 5
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0


class TestRetryUtility:
    @pytest.mark.asyncio
    async def test_retry_succeeds_on_first_attempt(self):
        from infrastructure.retry import retry

        calls = []

        async def func():
            calls.append(1)
            return "done"

        result = await retry(func, max_retries=3, base_delay=0)
        assert result == "done"
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_retry_retries_on_failure(self):
        from infrastructure.retry import retry

        calls = []

        async def func():
            calls.append(1)
            if len(calls) < 3:
                raise ValueError("not yet")
            return "done"

        result = await retry(func, max_retries=3, base_delay=0, jitter=False)
        assert result == "done"
        assert len(calls) == 3

    @pytest.mark.asyncio
    async def test_retry_raises_after_max_retries(self):
        from infrastructure.retry import retry

        async def always_fails():
            raise ValueError("always")

        with pytest.raises(ValueError, match="always"):
            await retry(always_fails, max_retries=2, base_delay=0, jitter=False)

    @pytest.mark.asyncio
    async def test_with_retry_decorator(self):
        from infrastructure.retry import with_retry

        calls = []

        @with_retry(max_retries=2, base_delay=0, jitter=False)
        async def func():
            calls.append(1)
            if len(calls) < 2:
                raise RuntimeError("retry me")
            return "ok"

        result = await func()
        assert result == "ok"
        assert len(calls) == 2


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_allows_within_limit(self):
        from tests.unit.test_debouncer import FakeRedis
        from infrastructure.rate_limiter import RateLimiter

        redis = _FakeRateLimiterRedis()
        limiter = RateLimiter(redis, max_messages=5, window_seconds=60)

        for _ in range(5):
            assert await limiter.is_allowed("5511@c.us") is True

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self):
        from infrastructure.rate_limiter import RateLimiter

        redis = _FakeRateLimiterRedis()
        limiter = RateLimiter(redis, max_messages=3, window_seconds=60)

        for _ in range(3):
            await limiter.is_allowed("5511@c.us")

        # 4th message should be blocked
        assert await limiter.is_allowed("5511@c.us") is False

    @pytest.mark.asyncio
    async def test_different_chats_are_independent(self):
        from infrastructure.rate_limiter import RateLimiter

        redis = _FakeRateLimiterRedis()
        limiter = RateLimiter(redis, max_messages=2, window_seconds=60)

        await limiter.is_allowed("chat1@c.us")
        await limiter.is_allowed("chat1@c.us")
        # chat1 is at limit but chat2 should still be allowed
        assert await limiter.is_allowed("chat2@c.us") is True

    @pytest.mark.asyncio
    async def test_fails_open_on_redis_error(self):
        from infrastructure.rate_limiter import RateLimiter

        class BrokenRedis:
            async def incr(self, key): raise ConnectionError("Redis down")
            async def expire(self, key, ttl): pass

        limiter = RateLimiter(BrokenRedis(), max_messages=1, window_seconds=60)
        # Should allow (fail open) rather than block
        assert await limiter.is_allowed("5511@c.us") is True


class _FakeRateLimiterRedis:
    """Minimal fake Redis for rate limiter tests."""

    def __init__(self):
        self._counters: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    async def expire(self, key: str, ttl: int) -> None:
        pass  # TTL not simulated — tests reset per instance

    async def get(self, key: str):
        val = self._counters.get(key)
        return str(val).encode() if val is not None else None

    async def delete(self, key: str) -> None:
        self._counters.pop(key, None)
