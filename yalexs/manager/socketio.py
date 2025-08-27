import asyncio
import logging
import sys
from collections.abc import Callable, Coroutine
from contextlib import suppress
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import socketio

from ..api_common import api_auth_headers
from ..backports.tasks import create_eager_task
from ..const import Brand

if sys.version_info < (3, 11):
    UTC = timezone.utc
else:
    from datetime import UTC

_LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .gateway import Gateway

UpdateCallbackType = Callable[[str, datetime, dict[str, Any]], None]


class SocketIORunner:
    """Run the socketio client."""

    def __init__(self, gateway: "Gateway") -> None:
        """Initialize the socketio client."""
        self.gateway = gateway
        self._listeners: set[UpdateCallbackType] = set()
        self._access_token = None
        self.connected = False
        self._subscriber_id: str | None = None
        self._refresh_task: asyncio.Task | None = None

    def subscribe(self, callback: UpdateCallbackType) -> Callable[[], None]:
        """Add a listener."""
        self._listeners.add(callback)

        def _remove_listener():
            self._listeners.remove(callback)

        return _remove_listener

    def headers(self) -> dict[str, str]:
        """Get the headers."""
        return api_auth_headers(self._access_token, brand=Brand.YALE_GLOBAL)

    async def _refresh_access_token(self) -> None:
        """Refresh the access token."""
        self._access_token = await self.gateway.async_get_access_token()

    async def _run(self) -> None:
        """Run the socketio client."""
        sio = socketio.AsyncClient()

        @sio.event
        def connect() -> None:
            _LOGGER.debug("websocket connection established")
            self.connected = True

        @sio.event
        def data(data: dict[str, Any]) -> None:
            _LOGGER.debug("message received with %s", data)
            now = datetime.now(UTC)
            device_id = data.get("lockID")
            for listener in self._listeners:
                listener(device_id, now, data)

        @sio.event
        def disconnect() -> None:
            _LOGGER.debug("disconnected from server")
            self._refresh_task = create_eager_task(self._refresh_access_token())
            self.connected = False

        await sio.connect(
            f"https://websocket.aaecosystem.com/?subscriberID={self._subscriber_id}",
            retry=True,
            transports=["websocket"],
            headers=self.headers,
        )
        await sio.wait()

    async def run(
        self, user_uuid: str, brand: Brand = Brand.YALE_GLOBAL
    ) -> Callable[[], Coroutine[Any, Any, None]]:
        """Create a socketio session."""
        self._access_token = await self.gateway.async_get_access_token()
        api = self.gateway.api
        sub_info = await api.async_add_websocket_subscription(self._access_token)
        _LOGGER.debug("sub_info: %s", sub_info)
        self._subscriber_id = sub_info["subscriberID"]
        _LOGGER.debug("subscriberID: %s", self._subscriber_id)
        socketio_task = create_eager_task(self._run())

        async def _async_unsub():
            _LOGGER.debug("Shutting down socketio")
            socketio_task.cancel()
            self._listeners.clear()
            with suppress(asyncio.CancelledError):
                await socketio_task
            _LOGGER.debug("socketio stopped")

        return _async_unsub
