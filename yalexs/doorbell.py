from __future__ import annotations

import datetime
import logging
from typing import Any

import requests
from aiohttp import ClientSession

from yalexs.exceptions import ContentTokenExpired

from ._compat import cached_property
from .device import Device, DeviceDetail
from .time import parse_datetime

_LOGGER = logging.getLogger(__name__)

DOORBELL_STATUS_KEY = "status"


class Doorbell(Device):
    """Class to hold details about a doorbell."""

    def __init__(self, device_id: str, data: dict[str, Any]) -> None:
        _LOGGER.info("Doorbell init - %s", data["name"])
        super().__init__(device_id, data["name"], data["HouseID"])
        self._serial_number = data["serialNumber"]
        self._status = data["status"]
        recent_image = data.get("recentImage", {})
        self._image_url = recent_image.get("secure_url", None)
        self._has_subscription = data.get("dvrSubscriptionSetupDone", False)
        self._content_token = data.get("contentToken", "")

    @cached_property
    def serial_number(self):
        return self._serial_number

    @cached_property
    def status(self):
        return self._status

    @cached_property
    def is_standby(self):
        return self.status == "standby"

    @cached_property
    def is_online(self):
        return self.status == "doorbell_call_status_online"

    @cached_property
    def image_url(self):
        return self._image_url

    @cached_property
    def has_subscription(self):
        return self._has_subscription

    @cached_property
    def content_token(self):
        return self._content_token

    def __repr__(self):
        return f"Doorbell(id={self.device_id}, name={self.device_name}, house_id={self.house_id})"


class DoorbellDetail(DeviceDetail):
    """Class to hold details about a doorbell."""

    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(
            data["doorbellID"],
            data["name"],
            data["HouseID"],
            data["serialNumber"],
            data["firmwareVersion"],
            data.get("pubsubChannel"),
            data,
        )

        self._status: str = data["status"]
        recent_image: dict[str, Any] = data.get("recentImage", {})
        self._image_url: str | None = recent_image.get("secure_url")
        self._has_subscription: bool = data.get("dvrSubscriptionSetupDone", False)
        self._image_created_at_datetime: datetime.datetime | None = None
        self._model: str | int | None = None
        self._content_token: str = data.get("contentToken", "")

        if "type" in data:
            self._model = data["type"]

        if "created_at" in recent_image:
            self._image_created_at_datetime = parse_datetime(recent_image["created_at"])

        self._battery_level: int | None = None
        if "telemetry" in data:
            telemetry = data["telemetry"]
            if "battery_soc" in telemetry:
                self._battery_level = telemetry.get("battery_soc", None)
            elif telemetry.get("doorbell_low_battery"):
                self._battery_level = 10
            elif "battery" in telemetry:
                battery = telemetry["battery"]
                if battery >= 4:
                    self._battery_level = 100
                elif battery >= 3.75:
                    self._battery_level = 75
                elif battery >= 3.50:
                    self._battery_level = 50
                else:
                    self._battery_level = 25

    @cached_property
    def status(self) -> str:
        return self._status

    @cached_property
    def model(self) -> str | int | None:
        return self._model

    @cached_property
    def is_online(self) -> bool:
        return self.status == "doorbell_call_status_online"

    @cached_property
    def is_standby(self) -> bool:
        return self.status == "standby"

    @property
    def image_created_at_datetime(self) -> datetime.datetime | datetime.date | None:
        return self._image_created_at_datetime

    @image_created_at_datetime.setter
    def image_created_at_datetime(self, var: datetime.date):
        """Update the doorbell image created_at datetime (usually form the activity log)."""
        if not isinstance(var, datetime.date):
            raise ValueError
        self._image_created_at_datetime = var

    @property
    def image_url(self) -> str | None:
        return self._image_url

    @image_url.setter
    def image_url(self, var: str | None) -> None:
        """Update the doorbell image url (usually form the activity log)."""
        _LOGGER.debug("image_url updated for %s", self.device_name)
        self._image_url = var

    @property
    def content_token(self) -> str:
        return self._content_token

    @content_token.setter
    def content_token(self, var: str) -> None:
        _LOGGER.debug("content_token updated for %s", self.device_name)
        self._content_token = var or ""

    @cached_property
    def battery_level(self) -> int | None:
        """Return an approximation of the battery percentage."""
        return self._battery_level

    @cached_property
    def has_subscription(self) -> bool:
        return self._has_subscription

    async def async_get_doorbell_image(
        self, aiohttp_session: ClientSession, timeout: float = 10.0
    ) -> bytes:
        _LOGGER.debug("async_get_doorbell_image %s", self.device_name)
        response = await aiohttp_session.request(
            "get",
            self._image_url,
            timeout=timeout,
            headers={"Authorization": self._content_token or ""},
        )
        if response.status == 401:
            _LOGGER.debug(
                "snapshot get error %s, may need new content token", response.status
            )
            raise ContentTokenExpired
        return await response.read()

    def get_doorbell_image(self, timeout: float = 10.0) -> bytes:
        _LOGGER.debug("get_doorbell_image sync %s", self.device_name)
        return requests.get(
            self._image_url,
            timeout=timeout,
            headers={"Authorization": self._content_token or ""},
        ).content
