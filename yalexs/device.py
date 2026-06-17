from __future__ import annotations

from typing import Any

from ._compat import cached_property


class Device:
    """Base class for all devices."""

    def __init__(self, device_id: str, device_name: str, house_id: str) -> None:
        self._device_id = device_id
        self._device_name = device_name
        self._house_id = house_id

    @cached_property
    def device_id(self) -> str:
        return self._device_id

    @cached_property
    def device_name(self) -> str:
        return self._device_name

    @cached_property
    def house_id(self) -> str:
        return self._house_id


class DeviceDetail:
    def __init__(
        self,
        device_id: str,
        device_name: str | None,
        house_id: str,
        serial_number: str | None,
        firmware_version: str,
        pubsub_channel: str | None,
        data: dict[str, Any],
    ) -> None:
        self._device_id = device_id
        self._device_name = device_name
        self._house_id = house_id
        self._serial_number = serial_number
        self._firmware_version = firmware_version
        self._pubsub_channel = pubsub_channel
        self._data = data

    @cached_property
    def raw(self) -> dict[str, Any]:
        return self._data

    @cached_property
    def device_id(self) -> str:
        return self._device_id

    @cached_property
    def device_name(self) -> str | None:
        return self._device_name

    @cached_property
    def house_id(self) -> str:
        return self._house_id

    @cached_property
    def serial_number(self) -> str | None:
        return self._serial_number

    @cached_property
    def firmware_version(self) -> str:
        return self._firmware_version

    @cached_property
    def pubsub_channel(self) -> str | None:
        return self._pubsub_channel
