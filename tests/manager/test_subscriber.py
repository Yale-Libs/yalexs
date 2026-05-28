"""Tests for yalexs.manager.subscriber.SubscriberMixin."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from freezegun.api import FrozenDateTimeFactory

from yalexs.manager.subscriber import SubscriberMixin

from ..common import fire_time_changed


class _Subscriber(SubscriberMixin):
    """Concrete subscriber that records refresh calls."""

    def __init__(self, update_interval: timedelta) -> None:
        super().__init__(update_interval)
        self.refresh_calls = 0

    async def _async_refresh(self) -> None:
        self.refresh_calls += 1


@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe_schedules_and_cancels_interval() -> None:
    sub = _Subscriber(timedelta(seconds=30))
    cb = MagicMock()

    assert sub._unsub_interval is None
    unsub = sub.async_subscribe_device_id("lock1", cb)
    assert sub._unsub_interval is not None
    assert cb in sub._subscriptions["lock1"]

    unsub()
    assert "lock1" not in sub._subscriptions
    assert sub._unsub_interval is None


@pytest.mark.asyncio
async def test_subscribe_second_callback_keeps_existing_interval() -> None:
    sub = _Subscriber(timedelta(seconds=30))
    cb1 = MagicMock()
    cb2 = MagicMock()

    sub.async_subscribe_device_id("lock1", cb1)
    first_handle = sub._unsub_interval
    sub.async_subscribe_device_id("lock1", cb2)
    # Second subscribe must NOT reset the timer — existing handle preserved.
    assert sub._unsub_interval is first_handle
    assert {cb1, cb2} == sub._subscriptions["lock1"]


@pytest.mark.asyncio
async def test_unsubscribe_keeps_device_with_remaining_callbacks() -> None:
    sub = _Subscriber(timedelta(seconds=30))
    cb1 = MagicMock()
    cb2 = MagicMock()
    sub.async_subscribe_device_id("lock1", cb1)
    sub.async_subscribe_device_id("lock1", cb2)

    sub.async_unsubscribe_device_id("lock1", cb1)
    # Device key must remain because cb2 is still subscribed.
    assert sub._subscriptions["lock1"] == {cb2}
    assert sub._unsub_interval is not None


@pytest.mark.asyncio
async def test_unsubscribe_leaves_other_device_subscriptions_intact() -> None:
    sub = _Subscriber(timedelta(seconds=30))
    cb1 = MagicMock()
    cb2 = MagicMock()

    sub.async_subscribe_device_id("lock1", cb1)
    sub.async_subscribe_device_id("lock2", cb2)
    handle = sub._unsub_interval

    sub.async_unsubscribe_device_id("lock1", cb1)
    assert "lock1" not in sub._subscriptions
    assert cb2 in sub._subscriptions["lock2"]
    # Interval must stay alive while another device still has subscribers.
    assert sub._unsub_interval is handle


@pytest.mark.asyncio
async def test_signal_device_id_update_invokes_callbacks() -> None:
    sub = _Subscriber(timedelta(seconds=30))
    cb1 = MagicMock()
    cb2 = MagicMock()
    other = MagicMock()

    sub.async_subscribe_device_id("lock1", cb1)
    sub.async_subscribe_device_id("lock1", cb2)
    sub.async_subscribe_device_id("lock2", other)

    sub.async_signal_device_id_update("lock1")
    cb1.assert_called_once_with()
    cb2.assert_called_once_with()
    other.assert_not_called()


@pytest.mark.asyncio
async def test_signal_device_id_update_unknown_device_is_noop() -> None:
    sub = _Subscriber(timedelta(seconds=30))
    # No subscribers at all — must not raise.
    sub.async_signal_device_id_update("ghost")


@pytest.mark.asyncio
async def test_scheduled_refresh_fires_periodically(
    freezer: FrozenDateTimeFactory,
) -> None:
    sub = _Subscriber(timedelta(seconds=1))
    cb = MagicMock()
    sub.async_subscribe_device_id("lock1", cb)

    assert sub.refresh_calls == 0
    freezer.tick(2)
    fire_time_changed()
    await asyncio.sleep(0)
    assert sub.refresh_calls == 1
    # _async_scheduled_refresh reschedules itself.
    assert sub._unsub_interval is not None
    assert sub._refresh_task is not None

    freezer.tick(2)
    fire_time_changed()
    await asyncio.sleep(0)
    assert sub.refresh_calls == 2

    sub.async_stop()


@pytest.mark.asyncio
async def test_async_stop_cancels_refresh_task_and_interval(
    freezer: FrozenDateTimeFactory,
) -> None:
    sub = _Subscriber(timedelta(seconds=1))
    sub.async_subscribe_device_id("lock1", MagicMock())

    freezer.tick(2)
    fire_time_changed()
    await asyncio.sleep(0)
    assert sub._refresh_task is not None
    assert sub._unsub_interval is not None

    sub.async_stop()
    assert sub._unsub_interval is None
    assert sub._refresh_task.cancelled() or sub._refresh_task.done()


@pytest.mark.asyncio
async def test_async_stop_accepts_arbitrary_args(
    freezer: FrozenDateTimeFactory,
) -> None:
    # async_stop is wired as a shutdown listener that may receive event args.
    sub = _Subscriber(timedelta(seconds=1))
    sub.async_subscribe_device_id("lock1", MagicMock())
    freezer.tick(2)
    fire_time_changed()
    await asyncio.sleep(0)
    # Must accept and ignore positional arguments without raising.
    sub.async_stop("shutdown-event")


@pytest.mark.asyncio
async def test_cancel_update_interval_is_idempotent() -> None:
    sub = _Subscriber(timedelta(seconds=30))
    # No interval scheduled yet — must not raise.
    sub._async_cancel_update_interval()
    assert sub._unsub_interval is None

    sub.async_subscribe_device_id("lock1", MagicMock())
    sub._async_cancel_update_interval()
    sub._async_cancel_update_interval()  # second call on a None handle
    assert sub._unsub_interval is None


@pytest.mark.asyncio
async def test_setup_listeners_replaces_existing_interval() -> None:
    sub = _Subscriber(timedelta(seconds=30))
    sub.async_subscribe_device_id("lock1", MagicMock())
    first = sub._unsub_interval
    sub._async_setup_listeners()
    assert sub._unsub_interval is not None
    assert sub._unsub_interval is not first
    assert first.cancelled()
