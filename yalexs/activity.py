from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Union

from ._compat import cached_property
from .backports.enum import StrEnum
from .lock import LockDoorStatus, LockStatus
from .time import epoch_to_datetime, parse_datetime
from .users import YaleUser, get_user_info

ACTION_LOCK_ONETOUCHLOCK = "onetouchlock"
ACTION_LOCK_ONETOUCHLOCK_2 = "one_touch_lock"
ACTION_LOCK_LOCK = "lock"
ACTION_RF_LOCK = "rf_lock"
ACTION_RF_SECURE = "rf_secure"
ACTION_RF_UNLATCH = "rf_unlatch"
ACTION_RF_UNLOCK = "rf_unlock"
ACTION_LOCK_AUTO_LOCK = "auto_lock"
ACTION_LOCK_BLE_LOCK = "ble_lock"
ACTION_LOCK_BLE_UNLATCH = "ble_unlatch"
ACTION_LOCK_BLE_UNLOCK = "ble_unlock"
ACTION_LOCK_REMOTE_LOCK = "remote_lock"
ACTION_LOCK_REMOTE_UNLATCH = "remote_unlatch"
ACTION_LOCK_REMOTE_UNLOCK = "remote_unlock"
ACTION_LOCK_PIN_LOCK = "pin_lock"
ACTION_LOCK_PIN_UNLATCH = "pin_unlatch"
ACTION_LOCK_PIN_UNLOCK = "pin_unlock"
ACTION_LOCK_MANUAL_LOCK = "manual_lock"
ACTION_LOCK_MANUAL_UNLATCH = "manual_unlatch"
ACTION_LOCK_MANUAL_UNLOCK = "manual_unlock"
ACTION_LOCK_LOCKING = "locking"
ACTION_LOCK_UNLATCH = "unlatch"
ACTION_LOCK_UNLATCHING = "unlatching"
ACTION_LOCK_UNLOCK = "unlock"
ACTION_LOCK_UNLOCKING = "unlocking"
ACTION_LOCK_JAMMED = "jammed"
ACTION_HOMEKEY_LOCK = "homekey_lock"
ACTION_HOMEKEY_UNLATCH = "homekey_unlatch"
ACTION_HOMEKEY_UNLOCK = "homekey_unlock"
ACTION_LINKED_LOCK = "linked_lock"
ACTION_LINKED_UNLOCK = "linked_unlock"
ACTION_LOCK_FINGER_LOCK = "finger_lock"
ACTION_LOCK_FINGER_UNLOCK = "finger_unlock"

ACTION_DOOR_OPEN = "dooropen"
ACTION_DOOR_OPEN_2 = "door_open"
ACTION_DOOR_CLOSED = "doorclosed"
ACTION_DOOR_CLOSE_2 = "door_close"


ACTION_DOORBELL_CALL_INITIATED = "doorbell_call_initiated"
ACTION_DOORBELL_MOTION_DETECTED = "doorbell_motion_detected"
ACTION_DOORBELL_CALL_MISSED = "doorbell_call_missed"
ACTION_DOORBELL_CALL_HANGUP = "doorbell_call_hangup"
ACTION_LOCK_DOORBELL_BUTTON_PUSHED = "lock_accessory_motion_detect"

ACTION_BRIDGE_ONLINE = "associated_bridge_online"  # pubnub only
ACTION_BRIDGE_OFFLINE = "associated_bridge_offline"  # pubnub only
ACTION_DOORBELL_IMAGE_CAPTURE = "imagecapture"  # pubnub only
ACTION_DOORBELL_BUTTON_PUSHED = "buttonpush"  # pubnub only

ACTIVITY_ACTIONS_BRIDGE_OPERATION = {ACTION_BRIDGE_ONLINE, ACTION_BRIDGE_OFFLINE}

ACTIVITY_ACTIONS_DOORBELL_DING = {
    ACTION_DOORBELL_BUTTON_PUSHED,
    ACTION_DOORBELL_CALL_MISSED,
    ACTION_DOORBELL_CALL_HANGUP,
    ACTION_LOCK_DOORBELL_BUTTON_PUSHED,
}
ACTIVITY_ACTIONS_DOORBELL_IMAGE_CAPTURE = {ACTION_DOORBELL_IMAGE_CAPTURE}
ACTIVITY_ACTIONS_DOORBELL_MOTION = {ACTION_DOORBELL_MOTION_DETECTED}
ACTIVITY_ACTIONS_DOORBELL_VIEW = {ACTION_DOORBELL_CALL_INITIATED}
ACTIVITY_ACTIONS_LOCK_OPERATION = {
    ACTION_RF_SECURE,
    ACTION_RF_LOCK,
    ACTION_RF_UNLATCH,
    ACTION_RF_UNLOCK,
    ACTION_HOMEKEY_LOCK,
    ACTION_HOMEKEY_UNLATCH,
    ACTION_HOMEKEY_UNLOCK,
    ACTION_LINKED_LOCK,
    ACTION_LINKED_UNLOCK,
    ACTION_LOCK_AUTO_LOCK,
    ACTION_LOCK_ONETOUCHLOCK,
    ACTION_LOCK_ONETOUCHLOCK_2,
    ACTION_LOCK_LOCK,
    ACTION_LOCK_UNLATCH,
    ACTION_LOCK_UNLOCK,
    ACTION_LOCK_LOCKING,
    ACTION_LOCK_UNLATCHING,
    ACTION_LOCK_UNLOCKING,
    ACTION_LOCK_JAMMED,
    ACTION_LOCK_BLE_LOCK,
    ACTION_LOCK_BLE_UNLATCH,
    ACTION_LOCK_BLE_UNLOCK,
    ACTION_LOCK_REMOTE_LOCK,
    ACTION_LOCK_REMOTE_UNLATCH,
    ACTION_LOCK_REMOTE_UNLOCK,
    ACTION_LOCK_PIN_LOCK,
    ACTION_LOCK_PIN_UNLATCH,
    ACTION_LOCK_PIN_UNLOCK,
    ACTION_LOCK_MANUAL_LOCK,
    ACTION_LOCK_MANUAL_UNLATCH,
    ACTION_LOCK_MANUAL_UNLOCK,
    ACTION_LOCK_FINGER_LOCK,
    ACTION_LOCK_FINGER_UNLOCK,
}


ACTIVITY_TO_FIRST_LAST_NAME = {
    ACTION_RF_SECURE: ("Radio Frequency", "Secure"),
    ACTION_RF_LOCK: ("Radio Frequency", "Lock"),
    ACTION_RF_UNLATCH: ("Radio Frequency", "Unlatch"),
    ACTION_RF_UNLOCK: ("Radio Frequency", "Unlock"),
    ACTION_HOMEKEY_LOCK: ("Homekey", "Lock"),
    ACTION_HOMEKEY_UNLATCH: ("Homekey", "Unlatch"),
    ACTION_HOMEKEY_UNLOCK: ("Homekey", "Unlock"),
    ACTION_LINKED_LOCK: ("Linked", "Lock"),
    ACTION_LINKED_UNLOCK: ("Linked", "Unlock"),
    ACTION_LOCK_AUTO_LOCK: ("Auto", "Lock"),
    ACTION_LOCK_ONETOUCHLOCK: ("One-Touch", "Lock"),
    ACTION_LOCK_ONETOUCHLOCK_2: ("One-Touch", "Lock"),
    ACTION_LOCK_BLE_LOCK: ("Bluetooth", "Lock"),
    ACTION_LOCK_BLE_UNLATCH: ("Bluetooth", "Unlatch"),
    ACTION_LOCK_BLE_UNLOCK: ("Bluetooth", "Unlock"),
    ACTION_LOCK_MANUAL_LOCK: ("Manual", "Lock"),
    ACTION_LOCK_MANUAL_UNLATCH: ("Manual", "Unlatch"),
    ACTION_LOCK_MANUAL_UNLOCK: ("Manual", "Unlock"),
    ACTION_LOCK_FINGER_LOCK: ("Fingerprint", "Lock"),
    ACTION_LOCK_FINGER_UNLOCK: ("Fingerprint", "Unlock"),
    ACTION_LOCK_PIN_LOCK: ("Pin", "Lock"),
    ACTION_LOCK_PIN_UNLATCH: ("Pin", "Unlatch"),
    ACTION_LOCK_PIN_UNLOCK: ("Pin", "Unlock"),
}


ACTIVITY_ACTIONS_DOOR_OPERATION = {
    ACTION_DOOR_CLOSED,
    ACTION_DOOR_OPEN,
    ACTION_DOOR_OPEN_2,
    ACTION_DOOR_CLOSE_2,
}

KEYPAD_ACTIONS = {
    ACTION_LOCK_ONETOUCHLOCK,
    ACTION_LOCK_ONETOUCHLOCK_2,
    ACTION_LOCK_PIN_LOCK,
    ACTION_LOCK_PIN_UNLATCH,
    ACTION_LOCK_PIN_UNLOCK,
    ACTION_LOCK_FINGER_LOCK,
    ACTION_LOCK_FINGER_UNLOCK,
}
REMOTE_ACTIONS = {
    ACTION_LOCK_REMOTE_LOCK,
    ACTION_LOCK_REMOTE_UNLATCH,
    ACTION_LOCK_REMOTE_UNLOCK,
}
AUTO_RELOCK_ACTIONS = {ACTION_LOCK_AUTO_LOCK}

TAG_ACTIONS = {
    ACTION_RF_SECURE,
    ACTION_RF_LOCK,
    ACTION_RF_UNLATCH,
    ACTION_RF_UNLOCK,
    ACTION_HOMEKEY_LOCK,
    ACTION_HOMEKEY_UNLATCH,
    ACTION_HOMEKEY_UNLOCK,
}

MANUAL_ACTIONS = {
    ACTION_LOCK_MANUAL_LOCK,
    ACTION_LOCK_MANUAL_UNLATCH,
    ACTION_LOCK_MANUAL_UNLOCK,
}

ACTIVITY_ACTION_STATES: dict[str, LockStatus | LockDoorStatus] = {
    ACTION_RF_SECURE: LockStatus.LOCKED,
    ACTION_RF_LOCK: LockStatus.LOCKED,
    ACTION_RF_UNLATCH: LockStatus.UNLATCHED,
    ACTION_RF_UNLOCK: LockStatus.UNLOCKED,
    ACTION_HOMEKEY_LOCK: LockStatus.LOCKED,
    ACTION_LINKED_LOCK: LockStatus.LOCKED,
    ACTION_LINKED_UNLOCK: LockStatus.UNLOCKED,
    ACTION_HOMEKEY_UNLATCH: LockStatus.UNLATCHED,
    ACTION_HOMEKEY_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_AUTO_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_ONETOUCHLOCK: LockStatus.LOCKED,
    ACTION_LOCK_ONETOUCHLOCK_2: LockStatus.LOCKED,
    ACTION_LOCK_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_UNLATCH: LockStatus.UNLATCHED,
    ACTION_LOCK_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_LOCKING: LockStatus.LOCKING,
    ACTION_LOCK_UNLATCHING: LockStatus.UNLATCHING,
    ACTION_LOCK_UNLOCKING: LockStatus.UNLOCKING,
    ACTION_LOCK_JAMMED: LockStatus.JAMMED,
    ACTION_DOOR_OPEN: LockDoorStatus.OPEN,
    ACTION_DOOR_CLOSED: LockDoorStatus.CLOSED,
    ACTION_DOOR_OPEN_2: LockDoorStatus.OPEN,
    ACTION_DOOR_CLOSE_2: LockDoorStatus.CLOSED,
    ACTION_LOCK_BLE_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_BLE_UNLATCH: LockStatus.UNLATCHED,
    ACTION_LOCK_BLE_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_REMOTE_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_REMOTE_UNLATCH: LockStatus.UNLATCHED,
    ACTION_LOCK_REMOTE_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_PIN_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_PIN_UNLATCH: LockStatus.UNLATCHED,
    ACTION_LOCK_PIN_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_MANUAL_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_MANUAL_UNLATCH: LockStatus.UNLATCHED,
    ACTION_LOCK_MANUAL_UNLOCK: LockStatus.UNLOCKED,
    ACTION_LOCK_FINGER_LOCK: LockStatus.LOCKED,
    ACTION_LOCK_FINGER_UNLOCK: LockStatus.UNLOCKED,
}


class Source(StrEnum):
    """Source of the activity."""

    LOCK_OPERATE = "lock_operate"
    PUBNUB = "pubnub"
    LOG = "log"
    WEBSOCKET = "websocket"


SOURCE_LOCK_OPERATE = Source.LOCK_OPERATE
SOURCE_PUBNUB = Source.PUBNUB
SOURCE_LOG = Source.LOG
SOURCE_WEBSOCKET = Source.WEBSOCKET

# If we get a lock operation activity with the same time stamp as a moving
# activity we want to use the non-moving activity since its the completed state.
MOVING_STATES: set[LockStatus | LockDoorStatus] = {
    LockStatus.UNLOCKING,
    LockStatus.UNLATCHING,
    LockStatus.LOCKING,
}

ACTIVITY_MOVING_STATES = {
    action
    for action, action_state in ACTIVITY_ACTION_STATES.items()
    if action_state in MOVING_STATES
}


class ActivityType(Enum):
    DOORBELL_MOTION = "doorbell_motion"
    DOORBELL_DING = "doorbell_ding"
    DOORBELL_VIEW = "doorbell_view"
    LOCK_OPERATION = "lock_operation"
    LOCK_OPERATION_WITHOUT_OPERATOR = "lock_operation_without_operator"
    DOOR_OPERATION = "door_operation"
    BRIDGE_OPERATION = "bridge_operation"
    DOORBELL_IMAGE_CAPTURE = "doorbell_image_capture"


class Activity:
    """Base class for activities."""

    def __init__(self, source: str, data: dict[str, Any]) -> None:
        """Initialize activity."""
        self._source = source
        self._data = data

    def __repr__(self):
        """Return the representation."""
        return (
            f"<{self.__class__.__name__} action={self.action} activity_type={self.activity_type} "
            f"activity_start_time={self.activity_start_time} "
            f"device_name={self.device_name}>"
        )

    @cached_property
    def _entities(self) -> dict[str, Any]:
        """Return the entities of the activity."""
        return self._data.get("entities", {})

    @cached_property
    def _info(self) -> dict[str, Any]:
        """Return the info of the activity."""
        return self._data.get("info", {})

    @cached_property
    def was_pushed(self) -> bool:
        """Return if the activity was pushed."""
        return self._source in (SOURCE_PUBNUB, SOURCE_WEBSOCKET)

    @cached_property
    def source(self) -> str:
        """Return the source of the activity."""
        return self._source

    @cached_property
    def activity_type(self) -> ActivityType:
        """Return the type of the activity."""
        return self._activity_type

    @cached_property
    def activity_id(self) -> str | None:
        """Return the ID of the activity."""
        return self._entities.get("activity")

    @cached_property
    def house_id(self) -> str | None:
        """Return the house ID of the activity."""
        return self._entities.get("house")

    @cached_property
    def activity_start_time(self) -> datetime:
        """Return the start time of the activity."""
        data = self._data
        return epoch_to_datetime(data.get("dateTime", data.get("timestamp")))

    @cached_property
    def activity_end_time(self) -> datetime:
        """Return the end time of the activity."""
        return self.activity_start_time

    @cached_property
    def action(self) -> str | None:
        """Return the action of the activity."""
        return self._data.get("action")

    @cached_property
    def device_id(self) -> str | None:
        """Return the ID of the device."""
        return self._data.get("deviceID")

    @cached_property
    def device_name(self) -> str | None:
        """Return the name of the device."""
        return self._data.get("deviceName")

    @cached_property
    def device_type(self) -> str | None:
        """Return the type of the device."""
        return self._data.get("deviceType")

    @cached_property
    def calling_user(self) -> dict[str, Any]:
        """Return the calling user."""
        return self._data.get("callingUser", self._data.get("user", {}))

    @cached_property
    def is_status(self) -> bool:
        """Return if the activity is a status update."""
        # If action is explicitly "status", it's a status update
        if self.action == "status":
            return True
        # If there's a manual operation (Bluetooth lock/unlock), it's NOT a status update
        user_id = self.calling_user.get("UserID", "")
        if user_id and user_id.startswith("manual"):
            return False
        # Check if this was marked as a manual operation (from PubNub without timestamp)
        if self._info.get("manual"):
            return False
        # Empty info typically means status update (except for WebSocket activities)
        return not self._info and self.source != SOURCE_WEBSOCKET


class BaseDoorbellMotionActivity(Activity):
    """Base class for doorbell motion activities."""

    def __repr__(self):
        return (
            f"<{self.__class__.__name__} action={self.action} activity_type={self.activity_type} "
            f"activity_start_time={self.activity_start_time} "
            f"device_name={self.device_name}"
            f"image_url={self.image_url}>"
            f"content_token={self.content_token}"
        )

    @cached_property
    def _image(self) -> dict[str, Any] | None:
        """Return the image of the activity."""
        return self._info.get("image")

    @cached_property
    def _content_token(self) -> str | None:
        """Return the content token of the activity."""
        return self._data.get("doorbell", {}).get("contentToken")

    @cached_property
    def image_url(self):
        """Return the image URL of the activity."""
        image = self._image
        return (None if image is None else image.get("secure_url")) or self._data.get(
            "attachment"
        )

    @cached_property
    def content_token(self):
        """Return the contentToken for the image URL"""
        return self._content_token or ""

    @cached_property
    def image_created_at_datetime(self):
        """Return the image created at datetime."""
        image = self._image
        if image is None:
            return None
        if "created_at" in image:
            return parse_datetime(image["created_at"])
        return self.activity_start_time


class DoorbellMotionActivity(BaseDoorbellMotionActivity):
    """A motion activity."""

    _activity_type = ActivityType.DOORBELL_MOTION


class DoorbellImageCaptureActivity(BaseDoorbellMotionActivity):
    """A motion activity with an image."""

    _activity_type = ActivityType.DOORBELL_IMAGE_CAPTURE


class DoorbellBaseActionActivity(Activity):
    """Base class for doorbell action activities."""

    @cached_property
    def image_url(self):
        """Return the image URL of the activity."""
        return self._info.get("image") or self._info.get("attachment")

    @cached_property
    def activity_start_time(self):
        """Return the start time of the activity."""
        if started := self._info.get("started"):
            return epoch_to_datetime(started)
        return super().activity_start_time

    @cached_property
    def activity_end_time(self):
        """Return the end time of the activity."""
        if ended := self._info.get("ended"):
            return epoch_to_datetime(ended)
        return super().activity_start_time


class DoorbellDingActivity(DoorbellBaseActionActivity):
    """Doorbell ding activity."""

    _activity_type = ActivityType.DOORBELL_DING


class DoorbellViewActivity(DoorbellBaseActionActivity):
    """Doorbell view activity."""

    _activity_type = ActivityType.DOORBELL_VIEW


class LockOperationActivity(Activity):
    """Lock operation activity."""

    _activity_type = ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR

    def __init__(self, source: str, data: dict[str, Any]) -> None:
        """Initialize lock operation activity."""
        super().__init__(source, data)
        operated_by: str | None = None
        calling_user = self.calling_user
        first_name: str | None = calling_user.get("FirstName")
        last_name: str | None = calling_user.get("LastName")

        yale_user = self.yale_user
        if yale_user and first_name is None and last_name is None:
            first_name = yale_user.first_name
            last_name = yale_user.last_name

        # For legacy compatibility, we need to set the first_name and last_name
        # if its a physical or rf lock operation
        if (
            first_name is None
            and last_name is None
            and (first_last := ACTIVITY_TO_FIRST_LAST_NAME.get(self.action))
        ):
            first_name, last_name = first_last

        if first_name and last_name:
            operated_by = f"{first_name} {last_name}"
            self._activity_type = ActivityType.LOCK_OPERATION

        self._operated_by = operated_by

    @cached_property
    def _operator_image_urls(self) -> tuple[str | None, str | None]:
        """Return the image URLs of the lock operator."""
        operator_image_url: str | None = None
        operator_thumbnail_url: str | None = None
        calling_user = self.calling_user

        image_info = calling_user.get("imageInfo") or calling_user
        original = image_info.get("original")

        if type(original) is str:  # pylint: disable=unidiomatic-typecheck
            operator_image_url = original
        elif type(original) is dict:  # pylint: disable=unidiomatic-typecheck
            operator_image_url = original.get("secure_url")
        else:
            operator_image_url = None

        thumbnail = image_info.get("thumbnail")
        if type(thumbnail) is str:  # pylint: disable=unidiomatic-typecheck
            operator_thumbnail_url = thumbnail
        elif type(thumbnail) is dict:  # pylint: disable=unidiomatic-typecheck
            operator_thumbnail_url = thumbnail.get("secure_url")
        else:
            operator_thumbnail_url = None

        yale_user = self.yale_user
        if yale_user and not operator_image_url and not operator_thumbnail_url:
            operator_image_url = yale_user.image_url
            operator_thumbnail_url = yale_user.thumbnail_url

        if not operator_thumbnail_url:
            if icon := self._data.get("icon"):
                operator_thumbnail_url = icon

        if operator_thumbnail_url and not operator_image_url:
            operator_image_url = operator_thumbnail_url
        if operator_image_url and not operator_thumbnail_url:
            operator_thumbnail_url = operator_image_url

        return operator_image_url, operator_thumbnail_url

    def __repr__(self):
        """Return the representation."""
        return (
            f"<{self.__class__.__name__} action={self.action} activity_type={self.activity_type} "
            f"activity_start_time={self.activity_start_time} "
            f"device_name={self.device_name} "
            f"operated_by={self.operated_by} "
            f"operated_remote={self.operated_remote} "
            f"operated_keypad={self.operated_keypad} "
            f"operated_tag={self.operated_tag} "
            f"operated_manual={self.operated_manual} "
            f"operated_autorelock={self.operated_autorelock} "
            f"operator_image_url={self.operator_image_url} "
            f"operator_thumbnail_url={self.operator_thumbnail_url}>"
        )

    @cached_property
    def yale_user(self) -> YaleUser | None:
        """Return the Yale user."""
        return get_user_info(self.user_id)

    @cached_property
    def user_id(self) -> str | None:
        """Return the ID of the user."""
        return self.calling_user.get("UserID")

    @cached_property
    def operated_by(self):
        return self._operated_by

    @cached_property
    def operated_remote(self):
        """Operation was remote."""
        return self._info.get("remote", self.action in REMOTE_ACTIONS)

    @cached_property
    def operated_keypad(self):
        """Operation used keypad."""
        return self._info.get("keypad", self.action in KEYPAD_ACTIONS)

    @cached_property
    def operated_manual(self):
        """Operation done manually using the knob."""
        return self._info.get("manual", self.action in MANUAL_ACTIONS)

    @cached_property
    def operated_tag(self):
        """Operation used rfid tag."""
        return self._info.get("tag", self.action in TAG_ACTIONS)

    @cached_property
    def operated_autorelock(self):
        """Operation done by automatic relock."""
        return self.user_id == "automaticrelock" or self.action in AUTO_RELOCK_ACTIONS

    @cached_property
    def operator_image_url(self):
        """URL to the image of the lock operator."""
        return self._operator_image_urls[0]

    @cached_property
    def operator_thumbnail_url(self):
        """URL to the thumbnail of the lock operator."""
        return self._operator_image_urls[1]


class DoorOperationActivity(Activity):
    """Door operation activity."""

    _activity_type = ActivityType.DOOR_OPERATION


class BridgeOperationActivity(Activity):
    """Bridge operation activity."""

    _activity_type = ActivityType.BRIDGE_OPERATION


ActivityTypes = Union[
    DoorbellDingActivity,
    DoorbellMotionActivity,
    DoorbellImageCaptureActivity,
    DoorbellViewActivity,
    LockOperationActivity,
    DoorOperationActivity,
    BridgeOperationActivity,
]

ACTIONS_TO_CLASS = (
    (ACTIVITY_ACTIONS_DOORBELL_DING, DoorbellDingActivity),
    (ACTIVITY_ACTIONS_DOORBELL_MOTION, DoorbellMotionActivity),
    (ACTIVITY_ACTIONS_DOORBELL_IMAGE_CAPTURE, DoorbellImageCaptureActivity),
    (ACTIVITY_ACTIONS_DOORBELL_VIEW, DoorbellViewActivity),
    (ACTIVITY_ACTIONS_LOCK_OPERATION, LockOperationActivity),
    (ACTIVITY_ACTIONS_DOOR_OPERATION, DoorOperationActivity),
    (ACTIVITY_ACTIONS_BRIDGE_OPERATION, BridgeOperationActivity),
)

ACTION_TO_CLASS: dict[str, ActivityTypes] = {}
for activities, klass in ACTIONS_TO_CLASS:
    for activity in activities:
        ACTION_TO_CLASS[activity] = klass
