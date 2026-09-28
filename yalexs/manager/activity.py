"""Consume the august activity stream."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Iterator
from operator import attrgetter

from aiohttp import ClientError

from ..activity import Activity, ActivityType
from ..api_async import ApiAsync
from ..backports.tasks import create_eager_task
from ..exceptions import AugustApiAIOHTTPError
from ..pubnub_async import AugustPubNub
from ..util import get_latest_activity
from .const import ACTIVITY_UPDATE_INTERVAL
from .gateway import Gateway
from .socketio import SocketIORunner
from .subscriber import SubscriberMixin

_LOGGER = logging.getLogger(__name__)

ACTIVITY_STREAM_FETCH_LIMIT = 10
ACTIVITY_CATCH_UP_FETCH_LIMIT = 2500

INITIAL_LOCK_RESYNC_TIME = 45

# If there is a storm of activity (ie lock, unlock, door open, door close, etc)
# we want to debounce the updates so we don't hammer the activity api too much.
ACTIVITY_DEBOUNCE_COOLDOWN = 4.0

# How long we expect it to take between when we get a WebSocket/PubNub
# message and the activity API to be updated.
UPDATE_SOON = 3.0

# A push tells us a device was operated, but the activity API sometimes has not
# published the matching activity by the time the polls above are done. It has
# been observed to withhold one for over a minute, far outside the debounce
# window, and until it arrives the operation has no operator. Keep asking on a
# widening gap, measured from the end of the previous poll. These only run
# while the API has served nothing new for the pushed device since the push,
# and stop as soon as it does, so a house whose activities publish promptly
# never reaches them.
ACTIVITY_CATCH_UP_DELAYS = (10.0, 30.0, 60.0, 120.0)

NEVER_TIME = -86400.0


class ActivityStream(SubscriberMixin):
    """August activity stream handler."""

    def __init__(
        self,
        api: ApiAsync,
        august_gateway: Gateway,
        house_ids: set[str],
        push: AugustPubNub | SocketIORunner,
    ) -> None:
        """Init activity stream object."""
        super().__init__(ACTIVITY_UPDATE_INTERVAL)
        self._schedule_updates: dict[str, asyncio.TimerHandle] = {}
        self._august_gateway = august_gateway
        self._api = api
        self._house_ids = house_ids
        self._latest_activities: defaultdict[
            str, dict[ActivityType, Activity | None]
        ] = defaultdict(lambda: defaultdict(lambda: None))
        self._did_first_update = False
        self.push = push
        self._update_tasks: dict[str, asyncio.Task] = {}
        self._last_update_time: dict[str, float] = dict.fromkeys(house_ids, NEVER_TIME)
        self._start_time: float | None = None
        self._pending_updates: dict[str, int] = dict.fromkeys(house_ids, 1)
        # Devices a push said were operated, mapped to the refresh generation
        # that asked. A poll only settles a device for refreshes requested
        # before it started. While any remain, the catch up delays keep polling.
        self._awaiting_devices: dict[str, dict[str, int]] = {
            house_id: {} for house_id in house_ids
        }
        self._refresh_generation: dict[str, int] = dict.fromkeys(house_ids, 0)
        self._catch_up_polls: dict[str, int] = dict.fromkeys(house_ids, 0)
        self._loop = asyncio.get_running_loop()
        self._shutdown: bool = False

    async def async_setup(self) -> None:
        """Token refresh check and catch up the activity stream."""
        self._start_time = self._loop.time()
        await self._async_refresh()
        await self._async_first_refresh()
        self._did_first_update = True

    def async_stop(self) -> None:
        """Cleanup any debounces."""
        self._shutdown = True
        for task in self._update_tasks.values():
            task.cancel()
        self._update_tasks.clear()
        self._async_cancel_all_future_updates()
        super().async_stop()

    def _async_cancel_future_updates(self, house_id: str) -> None:
        """Cancel future updates."""
        if handle := self._schedule_updates.pop(house_id, None):
            handle.cancel()
        self._pending_updates[house_id] = 0

    def _async_cancel_all_future_updates(self) -> None:
        """Cancel all future updates."""
        for house_id in self._house_ids:
            self._async_cancel_future_updates(house_id)

    def get_latest_device_activity(
        self, device_id: str, activity_types: set[ActivityType]
    ) -> Activity | None:
        """Return latest activity that is one of the activity_types."""
        if not (latest_device_activities := self._latest_activities.get(device_id)):
            return None

        latest_activity: Activity | None = None

        for activity_type in activity_types:
            if activity := latest_device_activities.get(activity_type):
                if (
                    latest_activity
                    and activity.activity_start_time
                    <= latest_activity.activity_start_time
                ):
                    continue
                latest_activity = activity

        return latest_activity

    @property
    def push_updates_connected(self) -> bool:
        """Return if the push updates are connected."""
        return self.push.connected

    async def _async_refresh(self) -> None:
        """Update the activity stream from August."""
        # This is the only place we refresh the api token
        if self._shutdown:
            return
        await self._august_gateway.async_refresh_access_token_if_needed()
        if not self.push_updates_connected:
            _LOGGER.debug("Push updates are not connected, data will be stale")

    async def _async_first_refresh(self) -> None:
        """Update the activity stream from August for the first time."""
        if self.push_updates_connected:
            _LOGGER.debug("Skipping update because push updates are active")
            return
        _LOGGER.debug("Start retrieving device activities")
        # Await in sequence to avoid hammering the API
        for house_id in self._house_ids:
            if not self._update_running(house_id):
                await self._create_update_task(house_id)

    def _create_update_task(self, house_id: str) -> asyncio.Task:
        """Create an update task."""
        if self._update_running(house_id):
            raise RuntimeError("Update already running")
        self._update_tasks[house_id] = create_eager_task(
            self._async_execute_schedule_update(house_id), loop=self._loop
        )
        return self._update_tasks[house_id]

    def _update_running(self, house_id: str) -> bool:
        """Return if an update is running for the house id."""
        return bool(
            (current_task := self._update_tasks.get(house_id))
            and not current_task.done()
        )

    def _updated_recently(self, house_id: str, now: float) -> bool:
        """Return if the house id was updated recently."""
        return self._last_update_time[house_id] + ACTIVITY_DEBOUNCE_COOLDOWN > now

    def _async_schedule_update_callback(self, house_id: str) -> None:
        """Schedule an update callback."""
        self._schedule_updates.pop(house_id, None)
        now = self._loop.time()
        if delay := self._determine_update_delay(house_id, now, from_callback=True):
            self._async_schedule_update(house_id, now, delay)
            return
        self._create_update_task(house_id)

    def _determine_update_delay(
        self, house_id: str, now: float, from_callback: bool = False
    ) -> float:
        """Return if we should delay the update."""
        if self._updated_recently(house_id, now) or self._update_running(house_id):
            return ACTIVITY_DEBOUNCE_COOLDOWN
        if not self._initial_resync_complete(now):
            return INITIAL_LOCK_RESYNC_TIME
        return 0 if from_callback else UPDATE_SOON

    def _async_schedule_update(self, house_id: str, now: float, delay: float) -> None:
        """Update the activity stream now or in the future if its too soon."""
        if self._shutdown or self._pending_updates[house_id] <= 0:
            return
        _LOGGER.debug(
            "Scheduling update for house id %s in %s seconds", house_id, delay
        )
        # Do not update right away because the activities API is
        # likely not updated yet and we will just get the same
        # activities again. Instead, schedule the update for
        # the future.
        if scheduled := self._schedule_updates.pop(house_id, None):
            scheduled.cancel()
        self._schedule_updates[house_id] = self._loop.call_at(
            now + delay, self._async_schedule_update_callback, house_id
        )

    async def _async_execute_schedule_update(self, house_id: str) -> None:
        """Execute a scheduled update."""
        self._pending_updates[house_id] -= 1
        self._last_update_time[house_id] = self._loop.time()
        # A push that arrives while this poll is in flight announces an
        # operation the poll may have missed, so only settle earlier ones.
        generation = self._refresh_generation[house_id]
        served = await self._async_update_house_id(house_id)
        awaiting = self._awaiting_devices[house_id]
        for device_id in served & awaiting.keys():
            if awaiting[device_id] <= generation:
                del awaiting[device_id]
        now = self._loop.time()
        if (pending_count := self._pending_updates[house_id]) > 0:
            _LOGGER.debug(
                "There are %s pending updates for house id %s", pending_count, house_id
            )
            delay = self._determine_update_delay(house_id, now)
            self._async_schedule_update(house_id, now, delay)
        elif (delay := self._catch_up_delay(house_id)) is not None:
            _LOGGER.debug(
                "Activity api has not caught up for house id %s, polling again in %s seconds",
                house_id,
                delay,
            )
            self._catch_up_polls[house_id] += 1
            self._pending_updates[house_id] = 1
            self._async_schedule_update(house_id, now, delay)

    def _catch_up_delay(self, house_id: str) -> float | None:
        """Return how long to wait before polling for an activity that is late.

        Returns None unless a push scheduled a refresh for a device, no poll
        since has served anything new for it, and we have delays left to spend.
        """
        if not self._awaiting_devices[house_id]:
            return None
        if (poll := self._catch_up_polls[house_id]) >= len(ACTIVITY_CATCH_UP_DELAYS):
            _LOGGER.debug(
                "Giving up waiting for the activity api to catch up for house id %s",
                house_id,
            )
            # Forget them so a later push does not keep polling on their behalf
            self._awaiting_devices[house_id].clear()
            return None
        return ACTIVITY_CATCH_UP_DELAYS[poll]

    def _initial_resync_complete(self, now: float) -> bool:
        """Return if the initial resync is complete."""
        return self._start_time and now - self._start_time > INITIAL_LOCK_RESYNC_TIME

    def _set_update_count(self, house_id: str, now: float) -> None:
        """Set the update count."""
        # Schedule one update soon and a second past the debounce time
        # to ensure we catch the case where the activity
        # api does not update right away and we need to poll
        # it again. Sometimes the lock operator or a doorbell
        # will not show up in the activity stream right away.
        # If neither poll serves the pushed device's activity,
        # ACTIVITY_CATCH_UP_DELAYS keeps asking for a few minutes.
        # Only do additional polls if we are past
        # the initial lock resync time to avoid a storm
        # of activity at setup.
        if not self._initial_resync_complete(now):
            # No resync yet, avoid spamming the API
            update_count = 1
        else:
            # Initial resync complete, we can do 2 updates
            update_count = 2
        self._pending_updates[house_id] = update_count

    def async_schedule_house_id_refresh(
        self, house_id: str, device_id: str | None = None
    ) -> None:
        """Update for a house activities now and once in the future.

        When device_id is given, the activity api owes us an activity for that
        device, and the catch up delays keep polling until it serves one.
        """
        self._async_cancel_future_updates(house_id)
        now = self._loop.time()
        self._refresh_generation[house_id] += 1
        if device_id is not None:
            # Spend a fresh set of catch up delays waiting for it if the polls
            # below come back without it.
            self._awaiting_devices[house_id][device_id] = self._refresh_generation[
                house_id
            ]
            self._catch_up_polls[house_id] = 0
        self._set_update_count(house_id, now)
        delay = self._determine_update_delay(house_id, now)
        self._async_schedule_update(house_id, now, delay)

    def _activity_limit(self) -> bool:
        """Return if the activity limit has been reached."""
        if self._did_first_update:
            return ACTIVITY_STREAM_FETCH_LIMIT
        return ACTIVITY_CATCH_UP_FETCH_LIMIT

    async def _async_update_house_id(self, house_id: str) -> set[str]:
        """Update device activities for a house.

        Returns the ids of devices the api served an activity for that is
        newer than the one we already had. Must only be called from
        _async_execute_schedule_update
        """
        if self._shutdown:
            return set()

        _LOGGER.debug("Updating device activity for house id %s", house_id)
        try:
            activities = await self._api.async_get_house_activities(
                await self._august_gateway.async_get_access_token(),
                house_id,
                limit=self._activity_limit(),
            )
        except (AugustApiAIOHTTPError, ClientError) as ex:
            _LOGGER.error(
                "Request error trying to retrieve activity for house id %s: %s",
                house_id,
                ex,
            )
            # Make sure we process the next house if one of them fails
            return set()

        _LOGGER.debug(
            "Completed retrieving device activities for house id %s", house_id
        )
        served: set[str] = set()
        # Signal between yields so subscribers observe every activity in order.
        for activity in self._iter_newer_device_activities(activities):
            device_id = activity.device_id
            served.add(device_id)
            _LOGGER.debug(
                "async_signal_device_id_update (from activity stream): %s",
                device_id,
            )
            self.async_signal_device_id_update(device_id)
        return served

    def async_process_newer_device_activities(
        self, activities: list[Activity]
    ) -> set[str]:
        """Process activities if they are newer than the last one."""
        return {
            activity.device_id
            for activity in self._iter_newer_device_activities(activities)
        }

    def _iter_newer_device_activities(
        self, activities: list[Activity]
    ) -> Iterator[Activity]:
        """Store and yield newer activities chronologically, one activity at a time.

        This iterator mutates ``_latest_activities`` immediately before each yield
        and must be consumed lazily when subscribers need to observe every update.
        """
        latest_activities = self._latest_activities
        for activity in sorted(activities, key=attrgetter("activity_start_time")):
            device_id = activity.device_id
            activity_type = activity.activity_type
            device_activities = latest_activities[device_id]
            last_activity = device_activities[activity_type]
            if get_latest_activity(activity, last_activity) != activity:
                _LOGGER.debug(
                    "Skipping activity %s for device %s as it is not newer than the last one: %s",
                    activity,
                    device_id,
                    last_activity,
                )
                continue
            device_activities[activity_type] = activity
            yield activity
