"""Tests for yalexs.alarm."""

from __future__ import annotations

from typing import Any

import pytest

from yalexs.alarm import Alarm, AlarmDevice, ArmState


def _alarm_data(**overrides: Any) -> dict[str, Any]:
    data = {
        "location": "Main House",
        "houseID": "house-1",
        "pubsubChannel": "chan-abc",
        "serialNumber": "SN12345",
        "status": "ARMED",
        "areaIDs": ["area-1", "area-2"],
    }
    data.update(overrides)
    return data


def _alarm_device_data(
    *,
    status_overrides: dict[str, Any] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "firmwareVersion": "1.2.3",
        "online": True,
        "contactOpen": False,
        "fault": False,
        "tamperOpen": False,
        "lowBattery": False,
    }
    if status_overrides:
        status.update(status_overrides)
    data = {
        "_id": "dev-1",
        "name": "Front Door Sensor",
        "alarmID": "alarm-1",
        "serialNumber": "DEV-SN-9",
        "pubsubChannel": "dev-channel",
        "type": "contact-sensor",
        "status": status,
    }
    data.update(overrides)
    return data


class TestArmState:
    def test_values(self) -> None:
        assert ArmState.Away.value == "FULL_ARM"
        assert ArmState.Home.value == "PARTIAL_ARM"
        assert ArmState.Disarm.value == "DISARM"

    def test_construct_from_value(self) -> None:
        assert ArmState("FULL_ARM") is ArmState.Away
        assert ArmState("PARTIAL_ARM") is ArmState.Home
        assert ArmState("DISARM") is ArmState.Disarm


class TestAlarm:
    def test_attributes(self) -> None:
        alarm = Alarm("alarm-1", _alarm_data())
        assert alarm.device_id == "alarm-1"
        assert alarm.device_name == "Main House"
        assert alarm.house_id == "house-1"
        assert alarm.pubsub_channel == "chan-abc"
        assert alarm.serial_number == "SN12345"
        assert alarm.status == "ARMED"
        assert alarm.areaIDs == ["area-1", "area-2"]

    def test_repr(self) -> None:
        alarm = Alarm("alarm-1", _alarm_data(location="Garage"))
        rep = repr(alarm)
        assert "alarm-1" in rep
        assert "Garage" in rep
        assert "house-1" in rep
        assert rep.startswith("Alarm(")

    def test_missing_required_field_raises(self) -> None:
        data = _alarm_data()
        del data["pubsubChannel"]
        with pytest.raises(KeyError):
            Alarm("alarm-x", data)


class TestAlarmDevice:
    def test_attributes(self) -> None:
        dev = AlarmDevice(_alarm_device_data())
        assert dev.device_id == "dev-1"
        assert dev.device_name == "Front Door Sensor"
        assert dev.house_id == "alarm-1"
        assert dev.serial_number == "DEV-SN-9"
        assert dev.firmware_version == "1.2.3"
        assert dev.pubsub_channel == "dev-channel"
        assert dev.model == "contact-sensor"

    def test_status_flags_defaults(self) -> None:
        dev = AlarmDevice(_alarm_device_data())
        assert dev.is_online is True
        assert dev.contact_open is False
        assert dev.fault is False
        assert dev.tamperOpen is False

    def test_status_flags_truthy(self) -> None:
        dev = AlarmDevice(
            _alarm_device_data(
                status_overrides={
                    "online": False,
                    "contactOpen": True,
                    "fault": True,
                    "tamperOpen": True,
                }
            )
        )
        assert dev.is_online is False
        assert dev.contact_open is True
        assert dev.fault is True
        assert dev.tamperOpen is True

    def test_status_flags_missing_keys_default_false(self) -> None:
        # Drop the optional booleans entirely; properties must default to False.
        dev = AlarmDevice(
            _alarm_device_data(
                status_overrides={
                    "online": False,
                    "contactOpen": False,
                    "fault": False,
                    "tamperOpen": False,
                }
            )
        )
        # Now strip them post-init to assert .get() default kicks in.
        dev._status = {"firmwareVersion": "1.2.3"}
        # Clear cached_property values so the .get() default path runs.
        for attr in ("is_online", "contact_open", "fault", "tamperOpen"):
            dev.__dict__.pop(attr, None)
        assert dev.is_online is False
        assert dev.contact_open is False
        assert dev.fault is False
        assert dev.tamperOpen is False

    def test_battery_level_normal(self) -> None:
        dev = AlarmDevice(_alarm_device_data())
        assert dev.battery_level == 100

    def test_battery_level_low(self) -> None:
        dev = AlarmDevice(
            _alarm_device_data(status_overrides={"lowBattery": True})
        )
        assert dev.battery_level == 10

    def test_battery_level_missing_low_battery_key(self) -> None:
        data = _alarm_device_data()
        data["status"].pop("lowBattery", None)
        dev = AlarmDevice(data)
        assert dev.battery_level == 100

    def test_repr(self) -> None:
        dev = AlarmDevice(_alarm_device_data())
        rep = repr(dev)
        assert "dev-1" in rep
        assert "Front Door Sensor" in rep
        assert "contact-sensor" in rep
        assert "alarm-1" in rep
        assert rep.startswith("AlarmDevice(")

    def test_raw_data_preserved(self) -> None:
        data = _alarm_device_data()
        dev = AlarmDevice(data)
        assert dev.raw is data

    def test_missing_pubsub_channel_is_none(self) -> None:
        data = _alarm_device_data()
        data.pop("pubsubChannel")
        dev = AlarmDevice(data)
        assert dev.pubsub_channel is None

    def test_missing_required_field_raises(self) -> None:
        data = _alarm_device_data()
        del data["alarmID"]
        with pytest.raises(KeyError):
            AlarmDevice(data)
