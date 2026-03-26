from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from adapters.inbound.websocket.connection_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


def _mock_websocket():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


async def test_connect_and_push(manager):
    tenant_id = uuid4()
    ws = _mock_websocket()

    await manager.connect(tenant_id, ws)
    assert manager.active_connections_count(tenant_id) == 1

    await manager.push_to_tenant(tenant_id, "test_event", {"key": "value"})
    ws.send_text.assert_called_once()
    sent = ws.send_text.call_args[0][0]
    assert '"type": "test_event"' in sent
    assert '"key": "value"' in sent


async def test_disconnect_removes_connection(manager):
    tenant_id = uuid4()
    ws = _mock_websocket()

    await manager.connect(tenant_id, ws)
    manager.disconnect(tenant_id, ws)
    assert manager.active_connections_count(tenant_id) == 0


async def test_push_to_multiple_connections(manager):
    tenant_id = uuid4()
    ws1 = _mock_websocket()
    ws2 = _mock_websocket()

    await manager.connect(tenant_id, ws1)
    await manager.connect(tenant_id, ws2)
    assert manager.active_connections_count(tenant_id) == 2

    await manager.push_to_tenant(tenant_id, "msg", {"x": 1})
    ws1.send_text.assert_called_once()
    ws2.send_text.assert_called_once()


async def test_push_cleans_dead_connections(manager):
    tenant_id = uuid4()
    ws_good = _mock_websocket()
    ws_dead = _mock_websocket()
    ws_dead.send_text.side_effect = RuntimeError("connection closed")

    await manager.connect(tenant_id, ws_good)
    await manager.connect(tenant_id, ws_dead)

    await manager.push_to_tenant(tenant_id, "test", {})

    # Dead connection should be removed
    assert manager.active_connections_count(tenant_id) == 1
    ws_good.send_text.assert_called_once()


async def test_push_no_connections_is_noop(manager):
    # Should not raise
    await manager.push_to_tenant(uuid4(), "event", {"data": True})


async def test_tenant_isolation(manager):
    t1 = uuid4()
    t2 = uuid4()
    ws1 = _mock_websocket()
    ws2 = _mock_websocket()

    await manager.connect(t1, ws1)
    await manager.connect(t2, ws2)

    await manager.push_to_tenant(t1, "msg", {})

    ws1.send_text.assert_called_once()
    ws2.send_text.assert_not_called()
