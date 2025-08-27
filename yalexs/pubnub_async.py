"""Connect to pubnub."""

import asyncio
import datetime
import logging
from collections.abc import Callable, Coroutine
from functools import partial
from typing import Any

from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNReconnectionPolicy, PNStatusCategory
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNMessageResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import AsyncioSubscriptionManager, PubNubAsyncio

from .const import BRAND_CONFIG, Brand
from .device import DeviceDetail

_LOGGER = logging.getLogger(__name__)

UpdateCallbackType = Callable[[str, datetime.datetime, dict[str, Any]], None]

SHOULD_RECONNECT_CATEGORIES = {
    PNStatusCategory.PNUnknownCategory,
    PNStatusCategory.PNUnexpectedDisconnectCategory,
    PNStatusCategory.PNNetworkIssuesCategory,
    PNStatusCategory.PNTimeoutCategory,
}


class AugustPubNub(SubscribeCallback):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the AugustPubNub."""
        super().__init__(*args, **kwargs)
        self.connected = False
        self._device_channels: dict[str, str] = {}
        self._subscriptions: set[UpdateCallbackType] = set()

    def presence(self, pubnub: AsyncioSubscriptionManager, presence):
        _LOGGER.debug("Received new presence: %s", presence)

    def status(self, pubnub: AsyncioSubscriptionManager, status: PNStatus) -> None:
        if not pubnub:
            self.connected = False
            return

        _LOGGER.debug(
            "Received new status: category=%s error_data=%s error=%s status_code=%s operation=%s",
            status.category,
            status.error_data,
            status.error,
            status.status_code,
            status.operation,
        )

        if status.category in SHOULD_RECONNECT_CATEGORIES:
            self.connected = False
            pubnub.reconnect()

        elif status.category == PNStatusCategory.PNReconnectedCategory:
            self.connected = True
            now = datetime.datetime.now(datetime.UTC)
            # Callback with an empty message to force a refresh
            for callback in self._subscriptions:
                for device_id in self._device_channels.values():
                    callback(device_id, now, {})

        elif status.category == PNStatusCategory.PNConnectedCategory:
            self.connected = True

    def message(
        self, pubnub: AsyncioSubscriptionManager, message: PNMessageResult
    ) -> None:
        # Handle new messages
        device_id = self._device_channels[message.channel]
        _LOGGER.debug(
            "Received new messages on channel %s for device_id: %s with timetoken: %s: %s",
            message.channel,
            device_id,
            message.timetoken,
            message.message,
        )
        dt = datetime.datetime.fromtimestamp(
            int(message.timetoken) / 10000000, tz=datetime.timezone.utc
        )
        for callback in self._subscriptions:
            callback(device_id, dt, message.message)

    def subscribe(self, update_callback: UpdateCallbackType) -> Callable[[], None]:
        """Add an callback subscriber.

        Returns a callable that can be used to unsubscribe.
        """
        self._subscriptions.add(update_callback)
        return partial(self._unsubscribe, update_callback)

    def _unsubscribe(self, update_callback: UpdateCallbackType) -> None:
        self._subscriptions.remove(update_callback)

    def register_device(self, device_detail: DeviceDetail) -> None:
        """Register a device to get updates."""
        if device_detail.pubsub_channel is None:
            return
        self._device_channels[device_detail.pubsub_channel] = device_detail.device_id

    @property
    def channels(self):
        """Return a list of registered channels."""
        return self._device_channels.keys()

    async def run(
        self, user_uuid: str, brand: Brand = Brand.AUGUST
    ) -> Callable[[], Coroutine[Any, Any, None]]:
        """Run the pubnub loop."""
        brand_config = BRAND_CONFIG[brand]
        pnconfig = PNConfiguration()
        pnconfig.subscribe_key = brand_config.pubnub_subscribe_token
        pnconfig.publish_key = brand_config.pubnub_publish_token
        pnconfig.uuid = f"pn-{str(user_uuid).upper()}"
        pnconfig.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
        pubnub = PubNubAsyncio(pnconfig)
        pubnub.add_listener(self)
        pubnub.subscribe().channels(self.channels).execute()

        async def _async_unsub():
            _LOGGER.debug("Removing listeners PubNub")
            pubnub.remove_listener(self)
            _LOGGER.debug("Unsubscribing from PubNub")
            pubnub.unsubscribe_all()
            await asyncio.sleep(0.1)  # Allow the unsubscribe to complete
            _LOGGER.debug("Stopping PubNub")
            await pubnub.stop()
            _LOGGER.debug("PubNub stopped")

        return _async_unsub
