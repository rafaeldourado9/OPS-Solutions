"""
Unit tests for MessageDebouncer.

Uses a fake Redis implementation to avoid requiring a real Redis server.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.redis_client import MessageDebouncer


# ---------------------------------------------------------------------------
# Fake Redis
# ---------------------------------------------------------------------------


class FakeRedis:
    """Minimal in-memory Redis replacement for testing."""

    def __init__(self):
        self._data: dict[str, list] = {}
        self._strings: dict[str, str] = {}

    def pipeline(self):
        return FakePipeline(self)

    async def eval(self, script: str, num_keys: int, *keys) -> list:
        """Simulate the Lua drain script: LRANGE + DEL."""
        key = keys[0]
        result = list(self._data.get(key, []))
        self._data.pop(key, None)
        return result

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._strings[key] = value

    async def get(self, key: str):
        return self._strings.get(key)


class FakePipeline:
    def __init__(self, redis: FakeRedis):
        self._redis = redis
        self._cmds: list = []

    def rpush(self, key: str, value: str):
        self._cmds.append(("rpush", key, value))
        return self

    def setex(self, key: str, ttl: int, value: str):
        self._cmds.append(("setex", key, ttl, value))
        return self

    async def execute(self):
        for cmd in self._cmds:
            if cmd[0] == "rpush":
                _, key, value = cmd
                self._redis._data.setdefault(key, []).append(value)
            elif cmd[0] == "setex":
                _, key, ttl, value = cmd
                self._redis._strings[key] = value
        return [1] * len(self._cmds)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMessageDebouncer:
    @pytest.mark.asyncio
    async def test_push_message_adds_to_buffer(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        await debouncer.push_message("chat1", '{"text": "oi"}')

        assert "buffer:chat1" in redis._data
        assert redis._data["buffer:chat1"] == ['{"text": "oi"}']

    @pytest.mark.asyncio
    async def test_push_multiple_messages_accumulates(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        await debouncer.push_message("chat1", "msg1")
        await debouncer.push_message("chat1", "msg2")
        await debouncer.push_message("chat1", "msg3")

        assert len(redis._data["buffer:chat1"]) == 3

    @pytest.mark.asyncio
    async def test_get_and_clear_buffer_drains_atomically(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        await debouncer.push_message("chat1", "msg1")
        await debouncer.push_message("chat1", "msg2")

        result = await debouncer.get_and_clear_buffer("chat1")

        assert result == ["msg1", "msg2"]
        # Buffer should be gone after drain
        assert redis._data.get("buffer:chat1", []) == []

    @pytest.mark.asyncio
    async def test_get_and_clear_empty_buffer_returns_empty(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        result = await debouncer.get_and_clear_buffer("nonexistent")
        assert result == []

    @pytest.mark.asyncio
    async def test_set_and_get_active_task(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        await debouncer.set_active_task("chat1", "task-abc")
        task_id = await debouncer.get_active_task("chat1")
        assert task_id == "task-abc"

    @pytest.mark.asyncio
    async def test_is_task_active_returns_true_when_current(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        await debouncer.set_active_task("chat1", "task-xyz")
        assert await debouncer.is_task_active("chat1", "task-xyz") is True

    @pytest.mark.asyncio
    async def test_is_task_active_returns_false_when_superseded(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        await debouncer.set_active_task("chat1", "task-new")
        assert await debouncer.is_task_active("chat1", "task-old") is False

    @pytest.mark.asyncio
    async def test_debounce_key_has_ttl(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        await debouncer.push_message("chat1", "msg")

        # The debounce key should be set
        assert "debounce:chat1" in redis._strings

    @pytest.mark.asyncio
    async def test_different_chats_are_isolated(self):
        redis = FakeRedis()
        debouncer = MessageDebouncer(redis, debounce_seconds=2.5)

        await debouncer.push_message("chat1", "msg for 1")
        await debouncer.push_message("chat2", "msg for 2")

        buf1 = await debouncer.get_and_clear_buffer("chat1")
        buf2 = await debouncer.get_and_clear_buffer("chat2")

        assert buf1 == ["msg for 1"]
        assert buf2 == ["msg for 2"]
