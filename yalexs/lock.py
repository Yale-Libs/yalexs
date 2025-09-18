from __future__ import annotations

import datetime
from enum import Enum
from typing import TYPE_CHECKING

from ._compat import cached_property
from .bridge import BridgeDetail, BridgeStatus
from .device import Device, DeviceDetail
from .keypad import KeypadDetail
from .time import parse_datetime
from .users import cache_user_info

if TYPE_CHECKING:
    from .capabilities import CapabilitiesResponse

LOCKED_STATUS = ("lock", "locked", "kAugLockState_Locked", "kAugLockState_SecureMode")
LOCKING_STATUS = ("kAugLockState_Locking",)
UNLATCHED_STATUS = ("unlatched", "kAugLockState_Unlatched")
UNLATCHING_STATUS = ("kAugLockState_Unlatching",)
UNLOCKED_STATUS = ("unlock", "unlocked", "kAugLockState_Unlocked")
UNLOCKING_STATUS = ("kAugLockState_Unlocking",)
JAMMED_STATUS = (
    "kAugLockState_UnknownStaticPosition",
    "FAILED_BRIDGE_ERROR_LOCK_JAMMED",
)

CLOSED_STATUS = ("closed", "kAugLockDoorState_Closed", "kAugDoorState_Closed")
OPEN_STATUS = ("open", "kAugLockDoorState_Open", "kAugDoorState_Open")
DISABLE_STATUS = ("init", "kAugDoorState_Init", "", None)

LOCK_STATUS_KEY = "status"
DOOR_STATE_KEY = "doorState"

DOORMAN_MODEL_TYPES = {7, 10}
UNLATCH_MODEL_TYPES = {17}


# Type 7 is a doorman
# Type 10 is a doorman in the Swedish market
# Type 17 is a Linus L2
class Lock(Device):
    def __init__(self, device_id, data):
        super().__init__(
            device_id,
            data["LockName"],
            data["HouseID"],
        )
        self._user_type = data["UserType"]

    @cached_property
    def is_operable(self):
        return self._user_type == "superuser"

    def __repr__(self):
        return f"Lock(id={self.device_id}, name={self.device_name}, house_id={self.house_id})"


class LockDetail(DeviceDetail):
    def __init__(self, data):
        super().__init__(
            data["LockID"],
            data["LockName"],
            data["HouseID"],
            data["SerialNumber"],
            data["currentFirmwareVersion"],
            data.get("pubsubChannel"),
            data,
        )

        if "Bridge" in data:
            self._bridge = BridgeDetail(self.house_id, data["Bridge"])
        else:
            self._bridge = None

        self._doorsense = False
        self._lock_status = LockStatus.UNKNOWN
        self._door_state = LockDoorStatus.UNKNOWN
        self._lock_status_datetime = None
        self._door_state_datetime = None
        self._model = None

        if "LockStatus" in data:
            lock_status = data["LockStatus"]

            self._lock_status = determine_lock_status(lock_status.get(LOCK_STATUS_KEY))
            self._door_state = determine_door_state(lock_status.get(DOOR_STATE_KEY))

            if "dateTime" in lock_status:
                self._lock_status_datetime = parse_datetime(lock_status["dateTime"])
                self._door_state_datetime = self._lock_status_datetime

            if (
                DOOR_STATE_KEY in lock_status
                and self._door_state != LockDoorStatus.DISABLED
            ):
                self._doorsense = True

        if "keypad" in data:
            keypad_name = data["LockName"] + " Keypad"
            self._keypad_detail = KeypadDetail(
                self.house_id, keypad_name, data["keypad"]
            )
        else:
            self._keypad_detail = None

        self._battery_level = int(100 * data["battery"])

        if "users" in data:
            for uuid, user_data in data["users"].items():
                cache_user_info(uuid, user_data)

        if "skuNumber" in data:
            self._model = data["skuNumber"]
        self._data = data
        self._capabilities: CapabilitiesResponse | None = None

    @cached_property
    def model(self):
        return self._model

    @cached_property
    def doorbell(self) -> bool:
        return self._data["Type"] in DOORMAN_MODEL_TYPES

    @cached_property
    def unlatch_supported(self) -> bool:
        # Check capabilities first if available
        if self._capabilities and "lock" in self._capabilities:
            return self._capabilities["lock"].get("unlatch", False)
        # Fall back to type-based check
        return self._data["Type"] in UNLATCH_MODEL_TYPES

    @cached_property
    def battery_level(self):
        return self._battery_level

    @cached_property
    def keypad(self):
        return self._keypad_detail

    @cached_property
    def bridge(self):
        return self._bridge

    @property
    def bridge_is_online(self):
        if self._bridge is None:
            return False

        # Old style bridge that does not report current status
        # This may have been updated but I do not have a Gen2
        # doorbell to test with yet.
        if self._bridge.status is None and self._bridge.operative:
            return True

        if (
            self._bridge.status is not None
            and self._bridge.status.current == BridgeStatus.ONLINE
        ):
            return True

        return False

    @cached_property
    def doorsense(self):
        return self._doorsense

    @property
    def lock_status(self):
        return self._lock_status

    @lock_status.setter
    def lock_status(self, var):
        """Update the lock status (usually form the activity log)."""
        if var not in LockStatus:
            raise ValueError
        self._lock_status = var

    @property
    def lock_status_datetime(self):
        return self._lock_status_datetime

    @lock_status_datetime.setter
    def lock_status_datetime(self, var):
        """Update the lock status datetime (usually form the activity log)."""
        if not isinstance(var, datetime.date):
            raise ValueError
        self._lock_status_datetime = var

    @property
    def door_state(self):
        return self._door_state

    @door_state.setter
    def door_state(self, var):
        """Update the door state (usually form the activity log)."""
        if var not in LockDoorStatus:
            raise ValueError
        self._door_state = var
        if var != LockDoorStatus.UNKNOWN:
            self._doorsense = True

    @property
    def door_state_datetime(self):
        return self._door_state_datetime

    @door_state_datetime.setter
    def door_state_datetime(self, var):
        """Update the door state datetime (usually form the activity log)."""
        if not isinstance(var, datetime.date):
            raise ValueError
        self._door_state_datetime = var

    def set_online(self, state):
        """Called when the lock comes back online or goes offline."""
        if not self._bridge:
            return
        self._bridge.set_online(state)

    def get_user(self, user_id):
        """Lookup user data by id."""
        return self._data.get("users", {}).get(user_id)

    def set_capabilities(self, capabilities: CapabilitiesResponse) -> None:
        """Set the lock capabilities."""
        self._capabilities = capabilities
        # Clear the cached unlatch_supported property since it may have changed
        self.__dict__.pop("unlatch_supported", None)

    @cached_property
    def offline_keys(self) -> dict:
        return self._data.get("OfflineKeys", {})

    @cached_property
    def loaded_offline_keys(self) -> list[dict]:
        return self.offline_keys.get("loaded", [])

    @cached_property
    def offline_key(self) -> str | None:
        loaded_offline_keys = self.loaded_offline_keys
        if loaded_offline_keys and "key" in loaded_offline_keys[0]:
            return loaded_offline_keys[0]["key"]
        return None

    @cached_property
    def offline_slot(self) -> int | None:
        loaded_offline_keys = self.loaded_offline_keys
        if loaded_offline_keys and "slot" in loaded_offline_keys[0]:
            return loaded_offline_keys[0]["slot"]
        return None

    @cached_property
    def mac_address(self) -> str | None:
        mac = self._data.get("macAddress")
        return mac.upper() if mac else None


class LockStatus(Enum):
    LOCKED = "locked"
    UNLATCHED = "unlatched"
    UNLOCKED = "unlocked"
    UNKNOWN = "unknown"
    LOCKING = "locking"
    UNLATCHING = "unlatching"
    UNLOCKING = "unlocking"
    JAMMED = "jammed"


class LockDoorStatus(Enum):
    CLOSED = "closed"
    OPEN = "open"
    UNKNOWN = "unknown"
    DISABLED = "disabled"


class LockOperation(Enum):
    LOCK = "lock"
    UNLOCK = "unlock"
    OPEN = "open"


def determine_lock_status(status: str) -> LockStatus:
    if status in LOCKED_STATUS:
        return LockStatus.LOCKED
    if status in UNLATCHED_STATUS:
        return LockStatus.UNLATCHED
    if status in UNLOCKED_STATUS:
        return LockStatus.UNLOCKED
    if status in UNLATCHING_STATUS:
        return LockStatus.UNLATCHING
    if status in UNLOCKING_STATUS:
        return LockStatus.UNLOCKING
    if status in LOCKING_STATUS:
        return LockStatus.LOCKING
    if status in JAMMED_STATUS:
        return LockStatus.JAMMED
    return LockStatus.UNKNOWN


def determine_door_state(status):
    if status in CLOSED_STATUS:
        return LockDoorStatus.CLOSED
    if status in OPEN_STATUS:
        return LockDoorStatus.OPEN
    if status in DISABLE_STATUS:
        return LockDoorStatus.DISABLED
    return LockDoorStatus.UNKNOWN


def door_state_to_string(door_status):
    """Returns the normalized value that determine_door_state represents."""
    if door_status == LockDoorStatus.OPEN:
        return "dooropen"
    if door_status == LockDoorStatus.CLOSED:
        return "doorclosed"
    raise ValueError
