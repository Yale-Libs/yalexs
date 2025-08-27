import logging
from datetime import datetime
from typing import Any

from .activity import (
    ACTION_BRIDGE_OFFLINE,
    ACTION_BRIDGE_ONLINE,
    ACTION_DOOR_CLOSED,
    ACTION_DOOR_OPEN,
    ACTION_DOORBELL_BUTTON_PUSHED,
    ACTION_DOORBELL_IMAGE_CAPTURE,
    ACTION_DOORBELL_MOTION_DETECTED,
    ACTION_LOCK_JAMMED,
    ACTION_LOCK_LOCK,
    ACTION_LOCK_LOCKING,
    ACTION_LOCK_UNLATCH,
    ACTION_LOCK_UNLATCHING,
    ACTION_LOCK_UNLOCK,
    ACTION_LOCK_UNLOCKING,
    SOURCE_PUBNUB,
    ActivityTypes,
)
from .api_common import _activity_from_dict, _datetime_string_to_epoch
from .device import Device
from .doorbell import DOORBELL_STATUS_KEY, DoorbellDetail
from .lock import (
    DOOR_STATE_KEY,
    LOCK_STATUS_KEY,
    LockDetail,
    LockDoorStatus,
    LockStatus,
    determine_door_state,
    determine_lock_status,
)

LOCK_STATUS_TO_ACTION = {
    LockStatus.LOCKED: ACTION_LOCK_LOCK,
    LockStatus.UNLATCHED: ACTION_LOCK_UNLATCH,
    LockStatus.UNLOCKED: ACTION_LOCK_UNLOCK,
    LockStatus.LOCKING: ACTION_LOCK_LOCKING,
    LockStatus.UNLATCHING: ACTION_LOCK_UNLATCHING,
    LockStatus.UNLOCKING: ACTION_LOCK_UNLOCKING,
    LockStatus.JAMMED: ACTION_LOCK_JAMMED,
}

_BRIDGE_ACTIONS = {ACTION_BRIDGE_ONLINE, ACTION_BRIDGE_OFFLINE}


_LOGGER = logging.getLogger(__name__)


def activities_from_pubnub_message(  # noqa: C901
    device: Device,
    date_time: datetime,
    message: dict[str, Any],
    source: str = SOURCE_PUBNUB,
) -> list[ActivityTypes]:
    """Create activities from pubnub."""
    activities: list[ActivityTypes] = []
    activity_dict = {
        "deviceID": device.device_id,
        "house": device.house_id,
        "deviceName": device.device_name,
    }
    info = message.get("info", {})
    context = info.get("context", {})
    accept_user = False
    if "startTime" in info:
        activity_dict["dateTime"] = _datetime_string_to_epoch(info["startTime"])
        accept_user = True
    elif "startDate" in context:
        activity_dict["dateTime"] = _datetime_string_to_epoch(context["startDate"])
        accept_user = True
    else:
        activity_dict["dateTime"] = date_time.timestamp() * 1000

    if isinstance(device, LockDetail):
        activity_dict["deviceType"] = "lock"
        activity_dict["info"] = info
        calling_user_id = message.get("callingUserID")

        # Some locks sometimes send lots of status messages, triggered by the app. Ignore these.
        if (
            info.get("action") == "status"
            and not message.get("error")
            and message.get("result") != "failed"
        ):
            _LOGGER.debug("Not creating lock activity from status push")
            return activities

        # Only accept a UserID if we have a date/time
        # as otherwise it is a duplicate of the previous
        # activity
        if accept_user and calling_user_id:
            activity_dict["callingUser"] = {"UserID": calling_user_id}
        # Mark manual operations so they're not treated as status updates
        elif calling_user_id and calling_user_id.startswith("manual"):
            activity_dict["info"]["manual"] = True
        if "remoteEvent" in message:
            activity_dict["info"]["remote"] = True
        error = message.get("error") or {}
        if error.get("restCode") == 98 or error.get("name") == "ERRNO_BRIDGE_OFFLINE":
            _add_activity(activities, activity_dict, ACTION_BRIDGE_OFFLINE, source)
        elif status := message.get("lockAction", message.get(LOCK_STATUS_KEY)):
            if status in _BRIDGE_ACTIONS:
                _add_activity(activities, activity_dict, status, source)
            if action := LOCK_STATUS_TO_ACTION.get(determine_lock_status(status)):
                _add_activity(activities, activity_dict, action, source)
        if door_state_raw := message.get(DOOR_STATE_KEY):
            door_state = determine_door_state(door_state_raw)
            if door_state == LockDoorStatus.OPEN:
                _add_activity(activities, activity_dict, ACTION_DOOR_OPEN, source)
            elif door_state == LockDoorStatus.CLOSED:
                _add_activity(activities, activity_dict, ACTION_DOOR_CLOSED, source)

    elif isinstance(device, DoorbellDetail):
        activity_dict["deviceType"] = "doorbell"
        info = activity_dict["info"] = message.get("data", {})
        info.setdefault("image", info.get("result", {}))
        info.setdefault("started", activity_dict["dateTime"])
        info.setdefault("ended", activity_dict["dateTime"])

        if (status := message.get(DOORBELL_STATUS_KEY)) and status in (
            ACTION_DOORBELL_MOTION_DETECTED,
            ACTION_DOORBELL_IMAGE_CAPTURE,
            ACTION_DOORBELL_BUTTON_PUSHED,
        ):
            _add_activity(activities, activity_dict, status, source)

    return activities


def _add_activity(
    activities: list[ActivityTypes],
    activity_dict: dict[str, Any],
    action: str,
    source: str,
) -> None:
    """Add an activity."""
    activity_dict = activity_dict.copy()
    activity_dict["action"] = action
    activities.append(
        _activity_from_dict(source, activity_dict, _LOGGER.isEnabledFor(logging.DEBUG))
    )
