from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from freezegun.api import FrozenDateTimeFactory

from yalexs.activity import Activity, ActivityType
from yalexs.api_async import ApiAsync
from yalexs.exceptions import AugustApiAIOHTTPError
from yalexs.manager.activity import (
    ACTIVITY_CATCH_UP_FETCH_LIMIT,
    ACTIVITY_DEBOUNCE_COOLDOWN,
    ACTIVITY_STREAM_FETCH_LIMIT,
    INITIAL_LOCK_RESYNC_TIME,
    UPDATE_SOON,
    ActivityStream,
)
from yalexs.manager.gateway import Gateway

from ..common import fire_time_changed


def _make_activity(
    device_id: str,
    activity_type: ActivityType,
    start_time: datetime,
    action: str = "lock",
) -> MagicMock:
    """Build a minimal Activity stand-in with the attrs the stream reads."""
    activity = MagicMock(spec=Activity)
    activity.device_id = device_id
    activity.activity_type = activity_type
    activity.activity_start_time = start_time
    activity.action = action
    return activity


def _build_stream(
    house_ids: set[str] | None = None,
    push_connected: bool = False,
) -> tuple[ActivityStream, MagicMock, AsyncMock]:
    """Construct an ActivityStream with stubbed api/gateway/push."""
    api = MagicMock(spec=ApiAsync)
    async_get_house_activities = AsyncMock()
    api.async_get_house_activities = async_get_house_activities
    gateway = MagicMock(spec=Gateway)
    gateway.async_refresh_access_token_if_needed = AsyncMock()
    gateway.async_get_access_token = AsyncMock(return_value="token")
    push = MagicMock(connected=push_connected)
    return (
        ActivityStream(api, gateway, house_ids or {"house"}, push),
        api,
        async_get_house_activities,
    )


@pytest.mark.asyncio
async def test_activity_stream_debounce(freezer: FrozenDateTimeFactory) -> None:
    """Test activity stream debounce."""

    api = MagicMock(spec=ApiAsync)
    async_get_house_activities = AsyncMock()
    api.async_get_house_activities = async_get_house_activities
    august_gateway = MagicMock(spec=Gateway)
    august_gateway.async_refresh_access_token_if_needed = AsyncMock()
    august_gateway.async_get_access_token = AsyncMock()
    push = MagicMock(connected=False)
    august_gateway.push = push

    activity = ActivityStream(api, august_gateway, {"myhouseid"}, push)
    await activity.async_setup()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 1
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    assert async_get_house_activities.call_count == 1
    freezer.tick(INITIAL_LOCK_RESYNC_TIME)
    fire_time_changed()
    assert async_get_house_activities.call_count == 1
    async_get_house_activities.reset_mock()
    assert "myhouseid" not in activity._schedule_updates

    activity.async_schedule_house_id_refresh("myhouseid")
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 0
    freezer.tick(UPDATE_SOON)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 1
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 2
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 2
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 2
    assert "myhouseid" not in activity._schedule_updates
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 2
    assert "myhouseid" not in activity._schedule_updates

    activity.async_schedule_house_id_refresh("myhouseid")
    await asyncio.sleep(0)
    assert activity._pending_updates["myhouseid"] == 2
    assert async_get_house_activities.call_count == 2
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 3
    assert activity._pending_updates["myhouseid"] == 1

    # If we get another update request, be sure we reset
    # but we do not poll right away and only do 2 polls
    activity.async_schedule_house_id_refresh("myhouseid")
    await asyncio.sleep(0)
    assert activity._pending_updates["myhouseid"] == 2
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert activity._pending_updates["myhouseid"] == 1
    assert async_get_house_activities.call_count == 4
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert activity._pending_updates["myhouseid"] == 0
    assert async_get_house_activities.call_count == 5
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert activity._pending_updates["myhouseid"] == 0
    assert async_get_house_activities.call_count == 5
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 5
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)

    # If we get another update request later, be sure we reset
    # and poll after 1s with 3 polls
    activity.async_schedule_house_id_refresh("myhouseid")
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 5
    assert activity._pending_updates["myhouseid"] == 2
    freezer.tick(UPDATE_SOON)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 6
    assert activity._pending_updates["myhouseid"] == 1
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 7
    assert activity._pending_updates["myhouseid"] == 0
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 7
    assert activity._pending_updates["myhouseid"] == 0
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 7
    assert activity._pending_updates["myhouseid"] == 0
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 7
    assert activity._pending_updates["myhouseid"] == 0


@pytest.mark.asyncio
async def test_activity_stream_debounce_during_init(
    freezer: FrozenDateTimeFactory,
) -> None:
    """Make sure requests during the initial sync get deferred."""

    api = MagicMock(spec=ApiAsync)
    async_get_house_activities = AsyncMock()
    api.async_get_house_activities = async_get_house_activities
    august_gateway = MagicMock(spec=Gateway)
    august_gateway.async_refresh_access_token_if_needed = AsyncMock()
    august_gateway.async_get_access_token = AsyncMock()
    push = MagicMock(connected=False)
    august_gateway.push = push

    activity = ActivityStream(api, august_gateway, {"myhouseid"}, push)
    await activity.async_setup()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 1
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)

    assert async_get_house_activities.call_count == 1

    activity.async_schedule_house_id_refresh("myhouseid")
    assert activity._pending_updates["myhouseid"] == 1
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 1

    activity.async_schedule_house_id_refresh("myhouseid")
    assert activity._pending_updates["myhouseid"] == 1
    freezer.tick(ACTIVITY_DEBOUNCE_COOLDOWN + 1)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 1

    freezer.tick(INITIAL_LOCK_RESYNC_TIME)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 2
    assert "myhouseid" not in activity._schedule_updates

    freezer.tick(INITIAL_LOCK_RESYNC_TIME)
    fire_time_changed()
    await asyncio.sleep(0)
    assert async_get_house_activities.call_count == 2
    assert "myhouseid" not in activity._schedule_updates


@pytest.mark.asyncio
async def test_get_latest_device_activity_unknown_device() -> None:
    """Unknown device returns None."""
    stream, *_ = _build_stream()
    assert (
        stream.get_latest_device_activity("nope", {ActivityType.LOCK_OPERATION}) is None
    )


@pytest.mark.asyncio
async def test_get_latest_device_activity_picks_newest_type() -> None:
    """Returns the activity with the most recent start time among requested types."""
    stream, *_ = _build_stream()
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    older = _make_activity("dev", ActivityType.LOCK_OPERATION, now)
    newer = _make_activity(
        "dev", ActivityType.DOOR_OPERATION, now + timedelta(seconds=10)
    )
    stream._latest_activities["dev"][ActivityType.LOCK_OPERATION] = older
    stream._latest_activities["dev"][ActivityType.DOOR_OPERATION] = newer

    result = stream.get_latest_device_activity(
        "dev", {ActivityType.LOCK_OPERATION, ActivityType.DOOR_OPERATION}
    )
    assert result is newer


@pytest.mark.asyncio
async def test_get_latest_device_activity_missing_type_returns_other() -> None:
    """Missing one of the requested types still returns the available one."""
    stream, *_ = _build_stream()
    activity = _make_activity(
        "dev", ActivityType.LOCK_OPERATION, datetime(2026, 1, 1, tzinfo=timezone.utc)
    )
    stream._latest_activities["dev"][ActivityType.LOCK_OPERATION] = activity
    result = stream.get_latest_device_activity(
        "dev", {ActivityType.LOCK_OPERATION, ActivityType.DOOR_OPERATION}
    )
    assert result is activity


@pytest.mark.asyncio
async def test_get_latest_device_activity_skips_older_after_newer() -> None:
    """When iteration sees the newer entry first, the older one hits the continue branch."""
    stream, *_ = _build_stream()
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    newer = _make_activity(
        "dev", ActivityType.DOOR_OPERATION, now + timedelta(seconds=10)
    )
    older = _make_activity("dev", ActivityType.LOCK_OPERATION, now)
    stream._latest_activities["dev"][ActivityType.DOOR_OPERATION] = newer
    stream._latest_activities["dev"][ActivityType.LOCK_OPERATION] = older

    # Pass an ordered list (newer first) so the older entry deterministically
    # triggers the `<= latest_activity.activity_start_time` continue branch.
    result = stream.get_latest_device_activity(
        "dev", [ActivityType.DOOR_OPERATION, ActivityType.LOCK_OPERATION]
    )
    assert result is newer


@pytest.mark.asyncio
async def test_async_stop_cancels_tasks_and_future_updates() -> None:
    """async_stop cancels pending tasks and scheduled callbacks, sets shutdown."""
    stream, _api, async_get = _build_stream()
    pending: asyncio.Future = asyncio.get_running_loop().create_future()

    async def _hang(*args, **kwargs):
        await pending
        return []

    async_get.side_effect = _hang
    # Skip async_setup (which would block awaiting the slow task) and start a
    # pending update task directly, then schedule a future update.
    stream._start_time = stream._loop.time()
    stream._create_update_task("house")
    stream.async_schedule_house_id_refresh("house")
    assert stream._schedule_updates
    in_flight = next(iter(stream._update_tasks.values()))

    stream.async_stop()

    assert stream._shutdown is True
    assert stream._update_tasks == {}
    assert stream._schedule_updates == {}
    # Let the cancellation propagate.
    with pytest.raises(asyncio.CancelledError):
        await in_flight
    pending.cancel()


@pytest.mark.asyncio
async def test_async_stop_cancels_mixin_interval_and_refresh_task() -> None:
    """async_stop must release the SubscriberMixin interval timer and refresh task.

    Without super().async_stop(), the mixin's call_later handle keeps firing
    _async_scheduled_refresh after teardown, leaking timers across HA reloads.
    """
    stream, _api, _async_get = _build_stream()
    # Subscribe so the mixin schedules its interval.
    stream.async_subscribe_device_id("device1", MagicMock())
    assert stream._unsub_interval is not None
    # Simulate one scheduled refresh tick populating the mixin task.
    stream._refresh_task = stream._loop.create_task(asyncio.sleep(60))

    refresh_task = stream._refresh_task
    interval = stream._unsub_interval

    stream.async_stop()

    assert stream._unsub_interval is None
    # call_later handle must be cancelled to stop future ticks.
    assert interval.cancelled()
    # Drain the cancelled task.
    with pytest.raises(asyncio.CancelledError):
        await refresh_task
    assert refresh_task.cancelled()


@pytest.mark.asyncio
async def test_async_refresh_skips_when_shutdown() -> None:
    """_async_refresh is a no-op once shutdown."""
    stream, _api, _async_get = _build_stream()
    stream._shutdown = True
    await stream._async_refresh()
    stream._august_gateway.async_refresh_access_token_if_needed.assert_not_awaited()


@pytest.mark.asyncio
async def test_async_first_refresh_skips_when_push_connected() -> None:
    """When push is connected, no catch-up fetch happens."""
    stream, _api, async_get = _build_stream(push_connected=True)
    await stream.async_setup()
    await asyncio.sleep(0)
    assert async_get.call_count == 0
    assert stream.push_updates_connected is True


@pytest.mark.asyncio
async def test_async_first_refresh_skips_house_with_running_update() -> None:
    """_async_first_refresh must skip houses that already have a running update.

    Covers the activity.py:137->136 partial branch — the `if not
    self._update_running(house_id)` False arc (update IS running, fall
    straight back to the for-loop) was previously never exercised because
    every existing test entered the if body.
    """
    stream, _api, async_get = _build_stream(house_ids={"busy"})
    async_get.return_value = []
    # Pre-seed an unfinished Future as the "busy" task; _update_running checks
    # `.done()`, so a pending Future is enough to make the guard return True
    # without scheduling any new work.
    pending: asyncio.Future = asyncio.get_running_loop().create_future()
    stream._update_tasks["busy"] = pending
    assert stream._update_running("busy")

    await stream._async_first_refresh()
    await asyncio.sleep(0)

    # The pre-seeded pending Future was NOT replaced — no new task scheduled,
    # async_get was never called for "busy".
    assert stream._update_tasks["busy"] is pending
    assert async_get.call_count == 0
    pending.cancel()


@pytest.mark.asyncio
async def test_create_update_task_raises_when_running() -> None:
    """Creating a duplicate update task raises RuntimeError."""
    stream, _api, async_get = _build_stream()
    pending: asyncio.Future = asyncio.get_running_loop().create_future()

    async def _hang(*args, **kwargs):
        await pending
        return []

    async_get.side_effect = _hang
    stream._create_update_task("house")
    assert stream._update_running("house")
    with pytest.raises(RuntimeError, match="Update already running"):
        stream._create_update_task("house")
    stream.async_stop()
    pending.cancel()


@pytest.mark.asyncio
async def test_schedule_update_cancels_existing_handle() -> None:
    """Scheduling a new update cancels the previously-scheduled handle."""
    stream, _api, _async_get = _build_stream()
    await stream.async_setup()
    await asyncio.sleep(0)
    stream.async_schedule_house_id_refresh("house")
    first_handle = stream._schedule_updates["house"]
    stream.async_schedule_house_id_refresh("house")
    second_handle = stream._schedule_updates["house"]
    assert first_handle is not second_handle
    assert first_handle.cancelled()
    stream.async_stop()


@pytest.mark.asyncio
async def test_schedule_update_replaces_existing_handle() -> None:
    """_async_schedule_update cancels and replaces an already-scheduled handle."""
    stream, *_ = _build_stream()
    now = stream._loop.time()
    stream._pending_updates["house"] = 1
    stream._async_schedule_update("house", now, 60.0)
    first = stream._schedule_updates["house"]
    # Second call replaces the handle without going through the public refresh API.
    stream._async_schedule_update("house", now, 30.0)
    second = stream._schedule_updates["house"]
    assert first is not second
    assert first.cancelled()
    second.cancel()


@pytest.mark.asyncio
async def test_schedule_update_callback_reschedules_when_recent() -> None:
    """If the callback fires while we updated recently, it reschedules itself."""
    stream, *_ = _build_stream()
    stream._start_time = stream._loop.time()
    stream._pending_updates["house"] = 1
    # Pretend we just updated so _updated_recently is True.
    stream._last_update_time["house"] = stream._loop.time()
    stream._async_schedule_update_callback("house")
    # The callback must have re-scheduled rather than created an update task.
    assert "house" in stream._schedule_updates
    assert "house" not in stream._update_tasks
    stream._schedule_updates["house"].cancel()


@pytest.mark.asyncio
async def test_schedule_update_noop_when_shutdown() -> None:
    """_async_schedule_update bails immediately after shutdown."""
    stream, *_ = _build_stream()
    stream._shutdown = True
    stream._async_schedule_update("house", 0.0, 1.0)
    assert "house" not in stream._schedule_updates


@pytest.mark.asyncio
async def test_update_house_id_skips_when_shutdown() -> None:
    """_async_update_house_id returns early under shutdown."""
    stream, _api, async_get = _build_stream()
    stream._shutdown = True
    await stream._async_update_house_id("house")
    async_get.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [AugustApiAIOHTTPError("boom"), ClientError("boom")])
async def test_update_house_id_swallows_request_errors(
    error: AugustApiAIOHTTPError | ClientError,
) -> None:
    """API errors are logged and processing continues without raising."""
    stream, _api, async_get = _build_stream()
    async_get.side_effect = error
    await stream._async_update_house_id("house")


@pytest.mark.asyncio
async def test_update_house_id_signals_subscribers() -> None:
    """When new activities arrive, subscribers for each updated device are signalled."""
    stream, _api, async_get = _build_stream()
    activity = _make_activity(
        "dev-1",
        ActivityType.LOCK_OPERATION,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        action="lock",
    )
    async_get.return_value = [activity]
    callback = MagicMock()
    stream.async_subscribe_device_id("dev-1", callback)

    await stream._async_update_house_id("house")

    callback.assert_called_once()
    stream.async_stop()


@pytest.mark.asyncio
async def test_process_newer_skips_duplicate_activity() -> None:
    """An identical activity already stored is not re-emitted."""
    stream, *_ = _build_stream()
    first = _make_activity(
        "dev",
        ActivityType.LOCK_OPERATION,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        action="lock",
    )
    stream._latest_activities["dev"][ActivityType.LOCK_OPERATION] = first

    older = _make_activity(
        "dev",
        ActivityType.LOCK_OPERATION,
        datetime(2025, 12, 31, tzinfo=timezone.utc),
        action="lock",
    )
    updated = stream.async_process_newer_device_activities([older])
    assert updated == set()
    assert stream._latest_activities["dev"][ActivityType.LOCK_OPERATION] is first


@pytest.mark.asyncio
async def test_process_newer_stores_new_activity() -> None:
    """A newer activity overwrites the stored one and the device id is reported."""
    stream, *_ = _build_stream()
    older = _make_activity(
        "dev",
        ActivityType.LOCK_OPERATION,
        datetime(2025, 12, 31, tzinfo=timezone.utc),
        action="lock",
    )
    stream._latest_activities["dev"][ActivityType.LOCK_OPERATION] = older

    newer = _make_activity(
        "dev",
        ActivityType.LOCK_OPERATION,
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        action="lock",
    )
    updated = stream.async_process_newer_device_activities([newer])
    assert updated == {"dev"}
    assert stream._latest_activities["dev"][ActivityType.LOCK_OPERATION] is newer


@pytest.mark.asyncio
async def test_activity_limit_switches_after_first_update() -> None:
    """Before the first update the catch-up limit is used; afterwards the stream limit."""
    stream, *_ = _build_stream()
    assert stream._activity_limit() == ACTIVITY_CATCH_UP_FETCH_LIMIT
    stream._did_first_update = True
    assert stream._activity_limit() == ACTIVITY_STREAM_FETCH_LIMIT
