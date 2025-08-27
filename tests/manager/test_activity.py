from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from freezegun.api import FrozenDateTimeFactory

from yalexs.api_async import ApiAsync
from yalexs.manager.activity import (
    ACTIVITY_DEBOUNCE_COOLDOWN,
    INITIAL_LOCK_RESYNC_TIME,
    UPDATE_SOON,
    ActivityStream,
)
from yalexs.manager.gateway import Gateway

from ..common import fire_time_changed


@pytest.mark.asyncio
async def test_activity_stream_debounce(freezer: FrozenDateTimeFactory) -> None:
    """Test activity stream debounce."""

    api = MagicMock(auto_spec=ApiAsync)
    async_get_house_activities = AsyncMock()
    api.async_get_house_activities = async_get_house_activities
    august_gateway = MagicMock(auto_spec=Gateway)
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

    api = MagicMock(auto_spec=ApiAsync)
    async_get_house_activities = AsyncMock()
    api.async_get_house_activities = async_get_house_activities
    august_gateway = MagicMock(auto_spec=Gateway)
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
