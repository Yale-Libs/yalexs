from __future__ import annotations

import datetime
import random
import ssl
from functools import cache
from typing import TYPE_CHECKING, Union

from .activity import (
    ACTION_BRIDGE_OFFLINE,
    ACTION_BRIDGE_ONLINE,
    ACTIVITY_ACTION_STATES,
    ACTIVITY_MOVING_STATES,
    MOVING_STATES,
    BridgeOperationActivity,
    DoorbellImageCaptureActivity,
    DoorbellMotionActivity,
    DoorOperationActivity,
    LockOperationActivity,
)
from .const import CONFIGURATION_URLS, Brand
from .lock import LockDetail

LockActivityTypes = Union[
    LockOperationActivity, DoorOperationActivity, BridgeOperationActivity
]
DoorbellActivityTypes = Union[
    DoorbellImageCaptureActivity, DoorbellMotionActivity, BridgeOperationActivity
]

if TYPE_CHECKING:
    from .doorbell import DoorbellDetail


def get_latest_activity(
    activity1: LockActivityTypes | None, activity2: LockActivityTypes | None
) -> LockActivityTypes | None:
    """Return the latest activity."""
    return (
        activity2
        if (
            not activity1
            or (
                activity2
                and activity2.action not in ACTIVITY_MOVING_STATES
                and activity1.activity_start_time <= activity2.activity_start_time
            )
        )
        else activity1
    )


def update_lock_detail_from_activity(
    lock_detail: LockDetail,
    activity: LockActivityTypes,
) -> bool:
    """Update the LockDetail from an activity."""
    activity_end_time_utc = as_utc_from_local(activity.activity_end_time)
    if activity.device_id != lock_detail.device_id:
        raise ValueError
    if isinstance(activity, LockOperationActivity):
        if lock_detail.lock_status_datetime and (
            lock_detail.lock_status_datetime > activity_end_time_utc
            or (
                lock_detail.lock_status_datetime == activity_end_time_utc
                and lock_detail.lock_status not in MOVING_STATES
            )
        ):
            return False
        lock_detail.lock_status = ACTIVITY_ACTION_STATES[activity.action]
        lock_detail.lock_status_datetime = activity_end_time_utc
    elif isinstance(activity, DoorOperationActivity):
        if (
            lock_detail.door_state_datetime
            and lock_detail.door_state_datetime >= activity_end_time_utc
        ):
            return False
        lock_detail.door_state = ACTIVITY_ACTION_STATES[activity.action]
        lock_detail.door_state_datetime = activity_end_time_utc
    elif isinstance(activity, BridgeOperationActivity):
        if activity.action == ACTION_BRIDGE_ONLINE:
            lock_detail.set_online(True)
        elif activity.action == ACTION_BRIDGE_OFFLINE:
            lock_detail.set_online(False)
    else:
        raise ValueError

    return True


def update_doorbell_image_from_activity(
    doorbell_detail: DoorbellDetail, activity: DoorbellActivityTypes
) -> bool:
    """Update the DoorDetail from an activity with a new image."""
    if activity.device_id != doorbell_detail.device_id:
        raise ValueError
    if isinstance(activity, (DoorbellImageCaptureActivity, DoorbellMotionActivity)):
        if activity.image_created_at_datetime is None:
            return False

        if (
            doorbell_detail.image_created_at_datetime is None
            or doorbell_detail.image_created_at_datetime
            < activity.image_created_at_datetime
        ):
            doorbell_detail.image_url = activity.image_url
            doorbell_detail.image_created_at_datetime = (
                activity.image_created_at_datetime
            )
            doorbell_detail.content_token = (
                activity.content_token or doorbell_detail.content_token
            )
        else:
            return False
    else:
        raise ValueError

    return True


def as_utc_from_local(dtime: datetime.datetime) -> datetime.datetime:
    """Converts the datetime returned from an activity to UTC."""
    return dtime.astimezone(tz=datetime.timezone.utc)


def get_configuration_url(brand: Brand) -> str:
    """Return the configuration URL for the brand."""
    return CONFIGURATION_URLS[brand]


@cache
def get_ssl_context() -> ssl.SSLContext:
    """Return an SSL context for cloudflare."""
    context = ssl.create_default_context()
    ciphers = [cipher["name"] for cipher in context.get_ciphers()]
    default_ciphers = ciphers[:3]
    backup_ciphers = ciphers[3:]
    random.shuffle(backup_ciphers)
    context.set_ciphers(":".join((*default_ciphers, *backup_ciphers)))
    return context
