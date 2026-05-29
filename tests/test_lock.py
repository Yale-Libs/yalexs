"""Tests for yalexs.lock setter validation and small helpers."""

from __future__ import annotations

import datetime
import json
import os
from typing import Any

import pytest

from yalexs.bridge import BridgeStatus
from yalexs.lock import (
    Lock,
    LockDetail,
    LockDoorStatus,
    LockStatus,
    determine_door_state,
    determine_lock_status,
    door_state_to_string,
)


def _load_fixture(name: str) -> dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "fixtures", name)
    with open(path) as fp:
        return json.load(fp)


@pytest.fixture
def online_lock() -> LockDetail:
    return LockDetail(_load_fixture("get_lock.online.json"))


@pytest.fixture
def offline_lock() -> LockDetail:
    return LockDetail(_load_fixture("get_lock.offline.json"))


def test_lock_repr_includes_identity() -> None:
    lock = Lock(
        "lock-id-1",
        {
            "LockName": "Front Door",
            "HouseID": "house-1",
            "UserType": "superuser",
        },
    )
    rendered = repr(lock)
    assert "lock-id-1" in rendered
    assert "Front Door" in rendered
    assert "house-1" in rendered
    assert lock.is_operable is True


def test_lock_is_operable_false_for_regular_user() -> None:
    lock = Lock(
        "lock-id-2",
        {"LockName": "Back Door", "HouseID": "house-1", "UserType": "user"},
    )
    assert lock.is_operable is False


def test_lock_status_setter_rejects_non_enum(online_lock: LockDetail) -> None:
    # Python 3.11 raises TypeError on `"str" in EnumClass`; 3.12+ returns False
    # and the setter then raises ValueError. Accept either.
    with pytest.raises((TypeError, ValueError)):
        online_lock.lock_status = "definitely-not-a-status"  # type: ignore[assignment]


def test_lock_status_setter_accepts_enum(online_lock: LockDetail) -> None:
    online_lock.lock_status = LockStatus.UNLOCKED
    assert online_lock.lock_status is LockStatus.UNLOCKED


def test_lock_status_datetime_setter_rejects_non_datetime(
    online_lock: LockDetail,
) -> None:
    with pytest.raises(ValueError):
        online_lock.lock_status_datetime = "2024-01-01"  # type: ignore[assignment]


def test_lock_status_datetime_setter_accepts_datetime(
    online_lock: LockDetail,
) -> None:
    when = datetime.datetime(2024, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc)
    online_lock.lock_status_datetime = when
    assert online_lock.lock_status_datetime == when


def test_door_state_setter_rejects_non_enum(online_lock: LockDetail) -> None:
    # Python 3.11 raises TypeError on `"str" in EnumClass`; 3.12+ returns False
    # and the setter then raises ValueError. Accept either.
    with pytest.raises((TypeError, ValueError)):
        online_lock.door_state = "definitely-not-a-door-state"  # type: ignore[assignment]


def test_door_state_setter_unknown_does_not_enable_doorsense(
    offline_lock: LockDetail,
) -> None:
    # Offline fixture has no doorState → doorsense starts False.
    # Setting UNKNOWN must NOT flip the underlying flag on.
    assert offline_lock._doorsense is False  # type: ignore[attr-defined]
    offline_lock.door_state = LockDoorStatus.UNKNOWN
    assert offline_lock.door_state is LockDoorStatus.UNKNOWN
    assert offline_lock._doorsense is False  # type: ignore[attr-defined]


def test_door_state_setter_non_unknown_enables_doorsense(
    offline_lock: LockDetail,
) -> None:
    assert offline_lock._doorsense is False  # type: ignore[attr-defined]
    offline_lock.door_state = LockDoorStatus.CLOSED
    assert offline_lock.door_state is LockDoorStatus.CLOSED
    assert offline_lock._doorsense is True  # type: ignore[attr-defined]


def test_door_state_datetime_setter_rejects_non_datetime(
    online_lock: LockDetail,
) -> None:
    with pytest.raises(ValueError):
        online_lock.door_state_datetime = 12345  # type: ignore[assignment]


def test_door_state_datetime_setter_accepts_datetime(
    online_lock: LockDetail,
) -> None:
    when = datetime.datetime(2024, 5, 6, 7, 8, 9, tzinfo=datetime.timezone.utc)
    online_lock.door_state_datetime = when
    assert online_lock.door_state_datetime == when


def test_set_online_no_bridge_is_noop(online_lock: LockDetail) -> None:
    # Drop the bridge to simulate a lock without one and confirm no exception.
    online_lock._bridge = None  # type: ignore[attr-defined]
    online_lock.set_online(True)
    online_lock.set_online(False)
    assert online_lock.bridge_is_online is False


def test_set_online_with_bridge_delegates_to_bridge_status() -> None:
    lock = LockDetail(_load_fixture("get_lock.online_with_doorsense.json"))
    bridge = lock.bridge
    assert bridge is not None and bridge.status is not None
    lock.set_online(False)
    assert bridge.status.current is BridgeStatus.OFFLINE
    lock.set_online(True)
    assert bridge.status.current is BridgeStatus.ONLINE


def test_get_user_returns_data_when_present(online_lock: LockDetail) -> None:
    online_lock._data["users"] = {"abc": {"FirstName": "Alice"}}  # type: ignore[attr-defined]
    assert online_lock.get_user("abc") == {"FirstName": "Alice"}


def test_get_user_returns_none_when_missing(online_lock: LockDetail) -> None:
    assert online_lock.get_user("does-not-exist") is None


def test_offline_key_and_slot_none_when_no_offline_keys() -> None:
    data = _load_fixture("get_lock.online.json")
    data.pop("OfflineKeys", None)
    lock = LockDetail(data)
    assert lock.offline_keys == {}
    assert lock.loaded_offline_keys == []
    assert lock.offline_key is None
    assert lock.offline_slot is None


def test_offline_key_and_slot_returned_when_present() -> None:
    data = _load_fixture("get_lock.online.json")
    data["OfflineKeys"] = {
        "loaded": [{"key": "deadbeef", "slot": 3}],
    }
    lock = LockDetail(data)
    assert lock.offline_key == "deadbeef"
    assert lock.offline_slot == 3


def test_offline_key_none_when_loaded_entry_missing_key() -> None:
    data = _load_fixture("get_lock.online.json")
    data["OfflineKeys"] = {"loaded": [{"slot": 1}]}
    lock = LockDetail(data)
    assert lock.offline_key is None
    assert lock.offline_slot == 1


def test_offline_slot_none_when_loaded_entry_missing_slot() -> None:
    data = _load_fixture("get_lock.online.json")
    data["OfflineKeys"] = {"loaded": [{"key": "abc"}]}
    lock = LockDetail(data)
    assert lock.offline_key == "abc"
    assert lock.offline_slot is None


def test_door_state_to_string_open_and_closed() -> None:
    assert door_state_to_string(LockDoorStatus.OPEN) == "dooropen"
    assert door_state_to_string(LockDoorStatus.CLOSED) == "doorclosed"


def test_door_state_to_string_rejects_other_states() -> None:
    with pytest.raises(ValueError):
        door_state_to_string(LockDoorStatus.UNKNOWN)
    with pytest.raises(ValueError):
        door_state_to_string(LockDoorStatus.DISABLED)


def test_determine_lock_status_known_states_and_fallback() -> None:
    assert determine_lock_status("locked") is LockStatus.LOCKED
    assert determine_lock_status("kAugLockState_Unlatched") is LockStatus.UNLATCHED
    assert determine_lock_status("unlocked") is LockStatus.UNLOCKED
    assert determine_lock_status("kAugLockState_Locking") is LockStatus.LOCKING
    assert determine_lock_status("kAugLockState_Unlocking") is LockStatus.UNLOCKING
    assert determine_lock_status("kAugLockState_Unlatching") is LockStatus.UNLATCHING
    assert determine_lock_status("FAILED_BRIDGE_ERROR_LOCK_JAMMED") is LockStatus.JAMMED
    assert determine_lock_status("bogus") is LockStatus.UNKNOWN


def test_determine_door_state_known_states_and_fallback() -> None:
    assert determine_door_state("closed") is LockDoorStatus.CLOSED
    assert determine_door_state("open") is LockDoorStatus.OPEN
    assert determine_door_state("init") is LockDoorStatus.DISABLED
    assert determine_door_state(None) is LockDoorStatus.DISABLED
    assert determine_door_state("bogus") is LockDoorStatus.UNKNOWN
