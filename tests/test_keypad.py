"""Tests for ``yalexs.keypad`` covering the battery-percentage branches."""

from __future__ import annotations

from yalexs.keypad import (
    BATTERY_LEVEL_FULL,
    BATTERY_LEVEL_LOW,
    BATTERY_LEVEL_MEDIUM,
    KeypadDetail,
)


def _keypad_data(**overrides):
    data = {
        "_id": "keypad-1",
        "serialNumber": "SN-123",
        "currentFirmwareVersion": "1.0.0",
        "batteryRaw": 180,
        "batteryLevel": BATTERY_LEVEL_FULL,
    }
    data.update(overrides)
    return data


def test_keypad_basic_attributes_and_model() -> None:
    """Constructor wires the inherited DeviceDetail fields and the model is fixed."""
    kp = KeypadDetail("house-1", "Front Door Keypad", _keypad_data())

    assert kp.device_id == "keypad-1"
    assert kp.device_name == "Front Door Keypad"
    assert kp.house_id == "house-1"
    assert kp.serial_number == "SN-123"
    assert kp.firmware_version == "1.0.0"
    assert kp.model == "AK-R1"
    assert kp.battery_level == BATTERY_LEVEL_FULL


def test_keypad_battery_percentage_uses_raw_when_present() -> None:
    """When ``batteryRaw`` is provided the raw voltage scales to 0-100."""
    # Raw 180 sits 60/80 of the way between MIN (120) and MAX (200) → 75.
    assert KeypadDetail("h", "k", _keypad_data(batteryRaw=180)).battery_percentage == 75
    # Raw above the max clamps to 100.
    assert (
        KeypadDetail("h", "k", _keypad_data(batteryRaw=999)).battery_percentage == 100
    )
    # Raw below the min clamps to 0.
    assert KeypadDetail("h", "k", _keypad_data(batteryRaw=10)).battery_percentage == 0


def test_keypad_battery_percentage_falls_back_to_level_lookup() -> None:
    """Without ``batteryRaw`` the level enum maps to a representative percentage."""
    assert (
        KeypadDetail(
            "h", "k", _keypad_data(batteryRaw=None, batteryLevel=BATTERY_LEVEL_FULL)
        ).battery_percentage
        == 100
    )
    assert (
        KeypadDetail(
            "h", "k", _keypad_data(batteryRaw=None, batteryLevel=BATTERY_LEVEL_MEDIUM)
        ).battery_percentage
        == 60
    )
    assert (
        KeypadDetail(
            "h", "k", _keypad_data(batteryRaw=None, batteryLevel=BATTERY_LEVEL_LOW)
        ).battery_percentage
        == 10
    )
    # An unknown level falls through the ``.get(..., 0)`` default.
    assert (
        KeypadDetail(
            "h", "k", _keypad_data(batteryRaw=None, batteryLevel="Bogus")
        ).battery_percentage
        == 0
    )


def test_keypad_battery_percentage_returns_none_when_no_signal() -> None:
    """Both raw and level missing → percentage is unknowable, returns None."""
    kp = KeypadDetail("h", "k", _keypad_data(batteryRaw=None, batteryLevel=None))
    assert kp.battery_percentage is None
