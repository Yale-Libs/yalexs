from __future__ import annotations

import logging
from typing import Any

from ._compat import cached_property
from .backports.enum import StrEnum
from .device import Device, DeviceDetail


class ArmState(StrEnum):
    Away = "FULL_ARM"
    Home = "PARTIAL_ARM"
    Disarm = "DISARM"


_LOGGER = logging.getLogger(__name__)


class Alarm(Device):
    """Class to hold details about an alarm."""

    def __init__(self, device_id: str, data: dict[str, Any]) -> None:
        _LOGGER.info("Alarm init - %s", data["location"])
        super().__init__(device_id, data["location"], data["houseID"])
        self._pubsub_channel = data["pubsubChannel"]
        self._serial_number = data["serialNumber"]
        self._status = data["status"]
        self._areaIDs = data["areaIDs"]

    @cached_property
    def pubsub_channel(self):
        return self._pubsub_channel

    @cached_property
    def serial_number(self):
        return self._serial_number

    @cached_property
    def status(self):
        return self._status

    @cached_property
    def areaIDs(self):
        return self._areaIDs

    def __repr__(self):
        return f"Alarm(id={self.device_id}, name={self.device_name}, house_id={self.house_id})"


class AlarmDevice(DeviceDetail):
    """Class to hold details about a device attached to the alarm."""

    def __init__(self, data: dict[str, Any]) -> None:
        _LOGGER.info("Alarm init - %s (%s)", data["name"], data["type"])
        super().__init__(
            data["_id"],
            data["name"],
            data["alarmID"],
            data["serialNumber"],
            data["status"]["firmwareVersion"],
            data.get("pubsubChannel"),
            data,
        )

        self._status: dict[str, Any] = data["status"]
        self._model = data["type"]

        self._battery_level = 100
        if self._status.get("lowBattery", False):
            self._battery_level = 10

    @cached_property
    def status(self) -> dict[str, Any]:
        return self._status

    @cached_property
    def model(self) -> str:
        return self._model

    @cached_property
    def is_online(self) -> bool:
        return self.status.get("online", False)

    @cached_property
    def contact_open(self) -> bool:
        return self.status.get("contactOpen", False)

    @cached_property
    def fault(self) -> bool:
        return self.status.get("fault", False)

    @cached_property
    def tamperOpen(self) -> bool:
        return self.status.get("tamperOpen", False)

    @cached_property
    def battery_level(self) -> int | None:
        """Return an approximation of the battery percentage."""
        return self._battery_level

    def __repr__(self):
        return f"AlarmDevice(id={self.device_id}, name={self.device_name}, type={self.model}, alarm_id={self.house_id})"
