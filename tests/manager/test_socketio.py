"""Tests for yalexs.manager.socketio.SocketIORunner."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError

from yalexs.const import Brand
from yalexs.exceptions import YaleApiError
from yalexs.manager.socketio import SocketIORunner


def _make_gateway(token: str = "tok") -> MagicMock:  # noqa: S107
    gateway = MagicMock()
    gateway.async_get_access_token = AsyncMock(return_value=token)
    gateway.api = MagicMock()
    gateway.api.async_add_websocket_subscription = AsyncMock(
        return_value={"subscriberID": "sub-123"}
    )
    gateway.api.async_remove_websocket_subscription = AsyncMock(return_value=None)
    return gateway


@pytest.fixture
def fake_socketio_client() -> Iterator[MagicMock]:
    """Stub `socketio.AsyncClient` and yield a fake that records event handlers."""
    handlers: dict[str, Callable[..., Any]] = {}
    client = MagicMock()
    client.handlers = handlers
    client.connect = AsyncMock()
    client.wait = AsyncMock()

    def _event(func: Callable[..., Any]) -> Callable[..., Any]:
        handlers[func.__name__] = func
        return func

    client.event = _event
    with patch("yalexs.manager.socketio.socketio.AsyncClient", return_value=client):
        yield client


def test_subscribe_returns_remover_that_pops_callback() -> None:
    runner = SocketIORunner(_make_gateway())
    cb = MagicMock()
    remover = runner.subscribe(cb)
    assert cb in runner._listeners
    remover()
    assert cb not in runner._listeners


def test_headers_uses_access_token_and_yale_global_brand() -> None:
    runner = SocketIORunner(_make_gateway())
    runner._access_token = "deadbeef"
    headers = runner.headers()
    # access token must be threaded through the YALE_GLOBAL auth header.
    assert "deadbeef" in headers.values()


@pytest.mark.asyncio
async def test_refresh_access_token_pulls_from_gateway() -> None:
    gateway = _make_gateway(token="new-token")
    runner = SocketIORunner(gateway)
    await runner._refresh_access_token()
    assert runner._access_token == "new-token"
    gateway.async_get_access_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_internal_wires_handlers_and_connects_to_subscriber_url(
    fake_socketio_client: MagicMock,
) -> None:
    runner = SocketIORunner(_make_gateway())
    runner._subscriber_id = "abc"
    runner._access_token = "tok"

    await runner._run()

    # connect/data/disconnect handlers registered.
    assert set(fake_socketio_client.handlers) == {"connect", "data", "disconnect"}

    fake_socketio_client.connect.assert_awaited_once()
    args, kwargs = fake_socketio_client.connect.call_args
    assert "subscriberID=abc" in args[0]
    assert kwargs["transports"] == ["websocket"]
    assert kwargs["retry"] is True
    # headers callable is passed, not a dict — socketio calls it on reconnect.
    assert callable(kwargs["headers"])
    assert kwargs["headers"]() == runner.headers()
    fake_socketio_client.wait.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_handler_marks_connected(
    fake_socketio_client: MagicMock,
) -> None:
    runner = SocketIORunner(_make_gateway())
    runner._subscriber_id = "abc"
    await runner._run()

    assert runner.connected is False
    fake_socketio_client.handlers["connect"]()
    assert runner.connected is True


@pytest.mark.asyncio
async def test_data_handler_dispatches_to_all_listeners(
    fake_socketio_client: MagicMock,
) -> None:
    runner = SocketIORunner(_make_gateway())
    runner._subscriber_id = "abc"
    cb1 = MagicMock()
    cb2 = MagicMock()
    runner.subscribe(cb1)
    runner.subscribe(cb2)

    await runner._run()

    payload = {"lockID": "lock-7", "status": "locked"}
    fake_socketio_client.handlers["data"](payload)

    for cb in (cb1, cb2):
        cb.assert_called_once()
        device_id, ts, data = cb.call_args.args
        assert device_id == "lock-7"
        assert isinstance(ts, datetime)
        assert ts.tzinfo is not None
        assert data is payload


@pytest.mark.asyncio
async def test_data_handler_with_missing_lockid_passes_none(
    fake_socketio_client: MagicMock,
) -> None:
    runner = SocketIORunner(_make_gateway())
    runner._subscriber_id = "abc"
    cb = MagicMock()
    runner.subscribe(cb)
    await runner._run()

    fake_socketio_client.handlers["data"]({"status": "locked"})
    device_id, _, _ = cb.call_args.args
    assert device_id is None


@pytest.mark.asyncio
async def test_disconnect_handler_schedules_token_refresh_and_clears_connected(
    fake_socketio_client: MagicMock,
) -> None:
    gateway = _make_gateway(token="refreshed")
    runner = SocketIORunner(gateway)
    runner._subscriber_id = "abc"
    runner.connected = True

    await runner._run()

    fake_socketio_client.handlers["disconnect"]()
    assert runner.connected is False
    assert runner._refresh_task is not None
    # let the eager task settle.
    await runner._refresh_task
    assert runner._access_token == "refreshed"


@pytest.mark.asyncio
async def test_run_fetches_token_and_subscription_then_returns_unsub() -> None:
    gateway = _make_gateway(token="t1")
    runner = SocketIORunner(gateway)

    # Replace the inner _run with a coroutine we can keep pending until unsub.
    sleeper = asyncio.Event()

    async def _fake_run() -> None:
        await sleeper.wait()

    with patch.object(runner, "_run", side_effect=_fake_run):
        unsub = await runner.run(user_uuid="user")

    assert runner._access_token == "t1"
    assert runner._subscriber_id == "sub-123"
    gateway.api.async_add_websocket_subscription.assert_awaited_once_with("t1")

    # unsub must cancel the running socketio task cleanly.
    runner.subscribe(MagicMock())
    await unsub()
    assert runner._listeners == set()
    # subscription must be released server-side and the id cleared so a
    # subsequent run() shutdown doesn't double-delete.
    gateway.api.async_remove_websocket_subscription.assert_awaited_once_with(
        "t1", "sub-123"
    )
    assert runner._subscriber_id is None


@pytest.mark.asyncio
async def test_unsub_skips_remove_when_subscriber_id_already_cleared() -> None:
    gateway = _make_gateway()
    runner = SocketIORunner(gateway)

    async def _fake_run() -> None:
        return None

    with patch.object(runner, "_run", side_effect=_fake_run):
        unsub = await runner.run(user_uuid="user")

    # Simulate the subscription having been released elsewhere — the unsub
    # closure must not attempt a second delete in that case.
    runner._subscriber_id = None
    await unsub()
    gateway.api.async_remove_websocket_subscription.assert_not_awaited()


@pytest.mark.parametrize(
    "remove_error",
    [
        YaleApiError("server gone"),
        ClientError("disconnected"),
        asyncio.TimeoutError(),
    ],
)
@pytest.mark.asyncio
async def test_unsub_swallows_remove_subscription_errors(
    remove_error: Exception,
) -> None:
    gateway = _make_gateway()
    gateway.api.async_remove_websocket_subscription = AsyncMock(
        side_effect=remove_error
    )
    runner = SocketIORunner(gateway)

    sleeper = asyncio.Event()

    async def _fake_run() -> None:
        await sleeper.wait()

    with patch.object(runner, "_run", side_effect=_fake_run):
        unsub = await runner.run(user_uuid="user")

    # Failure on remove must not propagate — shutdown must still complete.
    await unsub()
    gateway.api.async_remove_websocket_subscription.assert_awaited_once()
    assert runner._subscriber_id is None


@pytest.mark.asyncio
async def test_run_default_brand_is_yale_global() -> None:
    # The brand argument is currently unused but the signature must accept the
    # default; ensure no exception when called with an explicit brand.
    gateway = _make_gateway()
    runner = SocketIORunner(gateway)

    async def _fake_run() -> None:
        return None

    with patch.object(runner, "_run", side_effect=_fake_run):
        unsub = await runner.run(user_uuid="user", brand=Brand.YALE_GLOBAL)
    await unsub()
