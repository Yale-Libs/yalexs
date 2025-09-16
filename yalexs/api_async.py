"""Api calls for sync."""

from __future__ import annotations

import asyncio
import logging
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .capabilities import CapabilitiesResponse

from aiohttp import (
    ClientConnectionError,
    ClientOSError,
    ClientResponse,
    ClientResponseError,
    ClientSession,
    ClientSSLError,
    ServerDisconnectedError,
)

from .activity import ActivityTypes
from .alarm import Alarm, AlarmDevice, ArmState
from .api_common import (
    API_EXCEPTION_RETRY_TIME,
    API_LOCK_ASYNC_URL,
    API_LOCK_URL,
    API_RETRY_ATTEMPTS,
    API_RETRY_TIME,
    API_STATUS_ASYNC_URL,
    API_UNLATCH_ASYNC_URL,
    API_UNLATCH_URL,
    API_UNLOCK_ASYNC_URL,
    API_UNLOCK_URL,
    HEADER_ACCEPT_VERSION,
    HYPER_BRIDGE_PARAM,
    ApiCommon,
    _api_headers,
    _convert_lock_result_to_activities,
    _process_activity_json,
    _process_alarm_devices_json,
    _process_alarms_json,
    _process_doorbells_json,
    _process_locks_json,
)
from .const import DEFAULT_BRAND, HEADER_ACCESS_TOKEN, HEADER_AUGUST_ACCESS_TOKEN
from .doorbell import Doorbell, DoorbellDetail
from .exceptions import InvalidAuth, YaleApiError
from .lock import (
    Lock,
    LockDetail,
    LockDoorStatus,
    LockStatus,
    determine_door_state,
    determine_lock_status,
)
from .pin import Pin

_LOGGER = logging.getLogger(__name__)


def _obscure_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Obscure the payload for logging."""
    if payload is None:
        return None
    if "password" in payload:
        payload = payload.copy()
        payload["password"] = "****"  # nosec
    return payload


def _obscure_headers(headers: dict[str, Any]) -> dict[str, Any]:
    """Obscure the headers for logging."""
    if headers is None:
        return None
    for obscure_header in (
        "x-august-access-token",
        "x-access-token",
        "x-august-api-key",
        "x-api-key",
    ):
        if obscure_header in headers:
            headers = headers.copy()
            headers[obscure_header] = "****"
    return headers


class ApiAsync(ApiCommon):
    """Async api."""

    def __init__(
        self,
        aiohttp_session: ClientSession,
        timeout=10,
        command_timeout=60,
        brand=DEFAULT_BRAND,
    ) -> None:
        self._timeout = timeout
        self._command_timeout = command_timeout
        self._aiohttp_session = aiohttp_session
        super().__init__(brand)

    async def async_get_session(
        self, install_id: str, identifier: str, password: str
    ) -> ClientResponse:
        return await self._async_dict_to_api(
            self._build_get_session_request(install_id, identifier, password)
        )

    async def async_send_verification_code(
        self, access_token: str, login_method: str, username: str
    ) -> ClientResponse:
        return await self._async_dict_to_api(
            self._build_send_verification_code_request(
                access_token, login_method, username
            )
        )

    async def async_validate_verification_code(
        self,
        access_token: str,
        login_method: str,
        username: str,
        verification_code: str,
    ) -> ClientResponse:
        return await self._async_dict_to_api(
            self._build_validate_verification_code_request(
                access_token, login_method, username, verification_code
            )
        )

    async def async_get_doorbells(self, access_token: str) -> list[Doorbell]:
        if not self.brand_supports_doorbells:
            return []
        response = await self._async_dict_to_api(
            self._build_get_doorbells_request(access_token)
        )
        return _process_doorbells_json(await response.json())

    async def async_get_doorbell_detail(
        self, access_token: str, doorbell_id: str
    ) -> DoorbellDetail:
        response = await self._async_dict_to_api(
            self._build_get_doorbell_detail_request(access_token, doorbell_id)
        )
        return DoorbellDetail(await response.json())

    async def async_wakeup_doorbell(
        self, access_token: str, doorbell_id: str
    ) -> ClientResponse:
        await self._async_dict_to_api(
            self._build_wakeup_doorbell_request(access_token, doorbell_id)
        )
        return True

    async def async_get_user(self, access_token: str) -> dict[str, Any]:
        response = await self._async_dict_to_api(
            self._build_get_user_request(access_token)
        )
        return await response.json()

    async def async_get_houses(self, access_token: str) -> ClientResponse:
        return await self._async_dict_to_api(
            self._build_get_houses_request(access_token)
        )

    async def async_get_house(self, access_token: str, house_id: str) -> dict[str, Any]:
        response = await self._async_dict_to_api(
            self._build_get_house_request(access_token, house_id)
        )
        return await response.json()

    async def async_get_house_activities(
        self, access_token: str, house_id: str, limit: int = 8
    ) -> list[ActivityTypes]:
        response = await self._async_dict_to_api(
            self._build_get_house_activities_request(
                access_token, house_id, limit=limit
            )
        )
        return _process_activity_json(await response.json())

    async def async_get_locks(self, access_token: str) -> list[Lock]:
        response = await self._async_dict_to_api(
            self._build_get_locks_request(access_token)
        )
        return _process_locks_json(await response.json())

    async def async_get_operable_locks(self, access_token: str) -> list[Lock]:
        locks = await self.async_get_locks(access_token)

        return [lock for lock in locks if lock.is_operable]

    async def async_get_lock_detail(
        self, access_token: str, lock_id: str
    ) -> LockDetail:
        response = await self._async_dict_to_api(
            self._build_get_lock_detail_request(access_token, lock_id)
        )
        return LockDetail(await response.json())

    async def async_get_lock_status(
        self, access_token: str, lock_id: str, door_status=False
    ) -> LockStatus:
        response = await self._async_dict_to_api(
            self._build_get_lock_status_request(access_token, lock_id)
        )
        json_dict = await response.json()

        if door_status:
            return (
                determine_lock_status(json_dict.get("status")),
                determine_door_state(json_dict.get("doorState")),
            )

        return determine_lock_status(json_dict.get("status"))

    async def async_get_lock_door_status(
        self, access_token: str, lock_id: str, lock_status=False
    ) -> LockDoorStatus | tuple[LockDoorStatus, LockStatus]:
        response = await self._async_dict_to_api(
            self._build_get_lock_status_request(access_token, lock_id)
        )
        json_dict = await response.json()

        if lock_status:
            return (
                determine_door_state(json_dict.get("doorState")),
                determine_lock_status(json_dict.get("status")),
            )

        return determine_door_state(json_dict.get("doorState"))

    async def async_get_pins(self, access_token: str, lock_id: str) -> list[Pin]:
        response = await self._async_dict_to_api(
            self._build_get_pins_request(access_token, lock_id)
        )
        json_dict = await response.json()

        return [Pin(pin_json) for pin_json in json_dict.get("loaded", [])]

    async def async_get_lock_capabilities(
        self, access_token: str, serial_number: str
    ) -> CapabilitiesResponse:
        response = await self._async_dict_to_api(
            self._build_get_capabilities_request(access_token, serial_number)
        )
        return await response.json()

    async def _async_call_lock_operation(
        self, url_str: str, access_token: str, lock_id: str
    ) -> dict[str, Any]:
        response = await self._async_dict_to_api(
            self._build_call_lock_operation_request(
                url_str, access_token, lock_id, self._command_timeout
            )
        )
        return await response.json()

    async def _async_call_async_lock_operation(
        self, url_str: str, access_token: str, lock_id: str
    ) -> str:
        """Call an operation that will queue."""
        response = await self._async_dict_to_api(
            self._build_call_lock_operation_request(
                url_str, access_token, lock_id, self._command_timeout
            )
        )
        return await response.text()

    async def _async_lock(self, access_token: str, lock_id: str) -> str:
        return await self._async_call_lock_operation(
            API_LOCK_URL, access_token, lock_id
        )

    async def async_lock(self, access_token: str, lock_id: str) -> str:
        """Execute a remote lock operation.

        Returns a LockStatus state.
        """
        return determine_lock_status(
            (await self._async_lock(access_token, lock_id)).get("status")
        )

    async def async_lock_async(
        self, access_token: str, lock_id: str, hyper_bridge=True
    ) -> str:
        """Queue a remote lock operation and get the response via pubnub."""
        if hyper_bridge:
            return await self._async_call_async_lock_operation(
                f"{API_LOCK_ASYNC_URL}{HYPER_BRIDGE_PARAM}", access_token, lock_id
            )
        return await self._async_call_async_lock_operation(
            API_LOCK_ASYNC_URL, access_token, lock_id
        )

    async def async_lock_return_activities(
        self, access_token: str, lock_id: str
    ) -> list[ActivityTypes]:
        """Execute a remote lock operation.

        Returns an array of one or more yalexs.activity.Activity objects

        If the lock supports door sense one of the activities
        will include the current door state.
        """
        return _convert_lock_result_to_activities(
            await self._async_lock(access_token, lock_id)
        )

    async def _async_unlatch(self, access_token: str, lock_id: str) -> dict[str, Any]:
        return await self._async_call_lock_operation(
            API_UNLATCH_URL, access_token, lock_id
        )

    async def async_unlatch(self, access_token: str, lock_id: str) -> LockStatus:
        """Execute a remote unlatch operation.

        Returns a LockStatus state.
        """
        return determine_lock_status(
            (await self._async_unlatch(access_token, lock_id)).get("status")
        )

    async def async_unlatch_async(
        self, access_token: str, lock_id: str, hyper_bridge=True
    ) -> str:
        """Queue a remote unlatch operation and get the response via pubnub."""
        if hyper_bridge:
            return await self._async_call_async_lock_operation(
                f"{API_UNLATCH_ASYNC_URL}{HYPER_BRIDGE_PARAM}", access_token, lock_id
            )
        return await self._async_call_async_lock_operation(
            API_UNLATCH_ASYNC_URL, access_token, lock_id
        )

    async def async_unlatch_return_activities(
        self, access_token: str, lock_id: str
    ) -> list[ActivityTypes]:
        """Execute a remote lock operation.

        Returns an array of one or more yalexs.activity.Activity objects

        If the lock supports door sense one of the activities
        will include the current door state.
        """
        return _convert_lock_result_to_activities(
            await self._async_unlatch(access_token, lock_id)
        )

    async def _async_unlock(self, access_token: str, lock_id: str) -> dict[str, Any]:
        return await self._async_call_lock_operation(
            API_UNLOCK_URL, access_token, lock_id
        )

    async def async_unlock(self, access_token: str, lock_id: str) -> LockStatus:
        """Execute a remote unlock operation.

        Returns a LockStatus state.
        """
        return determine_lock_status(
            (await self._async_unlock(access_token, lock_id)).get("status")
        )

    async def async_unlock_async(
        self, access_token: str, lock_id: str, hyper_bridge=True
    ) -> str:
        """Queue a remote unlock operation and get the response via pubnub."""
        if hyper_bridge:
            return await self._async_call_async_lock_operation(
                f"{API_UNLOCK_ASYNC_URL}{HYPER_BRIDGE_PARAM}", access_token, lock_id
            )
        return await self._async_call_async_lock_operation(
            API_UNLOCK_ASYNC_URL, access_token, lock_id
        )

    async def async_unlock_return_activities(
        self, access_token: str, lock_id: str
    ) -> list[ActivityTypes]:
        """Execute a remote lock operation.

        Returns an array of one or more yalexs.activity.Activity objects

        If the lock supports door sense one of the activities
        will include the current door state.
        """
        return _convert_lock_result_to_activities(
            await self._async_unlock(access_token, lock_id)
        )

    async def async_status_async(
        self, access_token: str, lock_id: str, hyper_bridge=True
    ) -> str:
        """Queue a remote unlock operation and get the status via pubnub."""
        if hyper_bridge:
            return await self._async_call_async_lock_operation(
                f"{API_STATUS_ASYNC_URL}{HYPER_BRIDGE_PARAM}", access_token, lock_id
            )
        return await self._async_call_async_lock_operation(
            API_STATUS_ASYNC_URL, access_token, lock_id
        )

    async def async_get_alarms(self, access_token: str) -> list[Alarm]:
        if not self.brand_supports_alarms:
            return []
        response = await self._async_dict_to_api(
            self._build_get_alarms_request(access_token)
        )
        return _process_alarms_json(await response.json())

    async def async_get_alarm_devices(
        self, access_token: str, alarm: Alarm
    ) -> list[AlarmDevice]:
        if not self.brand_supports_alarms:
            return []
        response = await self._async_dict_to_api(
            self._build_get_alarm_devices_request(
                access_token, alarm_id=alarm.device_id
            )
        )
        return _process_alarm_devices_json(await response.json())

    async def async_arm_alarm(
        self, access_token: str, alarm: Alarm, arm_state: ArmState
    ):
        if not self.brand_supports_alarms:
            return {}
        response = await self._async_dict_to_api(
            self._build_call_alarm_state_request(access_token, alarm, arm_state)
        )
        return await response.json()

    async def async_refresh_access_token(self, access_token: str) -> str:
        """Obtain a new api token."""
        response = await self._async_dict_to_api(
            self._build_refresh_access_token_request(access_token)
        )
        response_headers = response.headers
        return (
            response_headers.get(HEADER_ACCESS_TOKEN)
            or response_headers[HEADER_AUGUST_ACCESS_TOKEN]
        )

    async def async_add_websocket_subscription(
        self, access_token: str
    ) -> dict[str, Any]:
        """Add a websocket subscription."""
        response = await self._async_dict_to_api(
            self._build_websocket_subscribe_request(access_token)
        )
        return await response.json()

    async def async_get_websocket_subscriptions(self, access_token: str) -> str:
        """Get websocket subscriptions."""
        response = await self._async_dict_to_api(
            self._build_websocket_get_request(access_token)
        )
        return await response.text()

    async def _async_dict_to_api(self, api_dict: dict[str, Any]) -> ClientResponse:
        url = api_dict.pop("url")
        method = api_dict.pop("method")
        access_token = api_dict.pop("access_token", None)
        payload = api_dict.get("params") or api_dict.get("json")

        if "headers" not in api_dict:
            api_dict["headers"] = _api_headers(
                access_token=access_token, brand=self.brand
            )

        if "version" in api_dict:
            api_dict["headers"][HEADER_ACCEPT_VERSION] = api_dict["version"]
            del api_dict["version"]

        if "timeout" not in api_dict:
            api_dict["timeout"] = self._timeout

        debug_enabled = _LOGGER.isEnabledFor(logging.DEBUG)

        if debug_enabled:
            _LOGGER.debug(
                "About to call %s with header=%s and payload=%s",
                url,
                _obscure_headers(api_dict["headers"]),
                _obscure_payload(payload),
            )

        attempts = 0
        while attempts < API_RETRY_ATTEMPTS:
            attempts += 1
            try:
                response = await self._aiohttp_session.request(method, url, **api_dict)
            except (
                ClientOSError,
                ClientSSLError,
                ServerDisconnectedError,
                ClientConnectionError,
            ) as ex:
                # Try again if we get disconnected
                # We may get [Errno 104] Connection reset by peer or a
                # transient disconnect/SSL error
                if attempts == API_RETRY_ATTEMPTS:
                    raise YaleApiError(
                        f"Failed to connect to August API: {ex}", ex
                    ) from ex
                await asyncio.sleep(API_EXCEPTION_RETRY_TIME)
                continue
            if debug_enabled:
                _LOGGER.debug(
                    "Received API response from url: %s, code: %s, headers: %s, content: %s",
                    url,
                    response.status,
                    _obscure_headers(response.headers),
                    await response.read(),
                )
            if response.status in (429, 502):
                # 429 - rate limited
                # 502 - bad gateway
                _LOGGER.debug(
                    "API sent a %s (attempt: %d), sleeping and trying again",
                    response.status,
                    attempts,
                )
                await asyncio.sleep(API_RETRY_TIME)
                continue
            break

        _raise_response_exceptions(response)

        return response


def _raise_response_exceptions(response: ClientResponse) -> None:
    """Raise exceptions for known error codes."""
    try:
        response.raise_for_status()
    except ClientResponseError as err:
        if err.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
            raise InvalidAuth(
                f"Authentication failed: Verify brand is correct: {err.message}", err
            ) from err
        if err.status == 422:
            raise YaleApiError(
                f"The operation failed because the bridge (connect) is offline: {err.message}",
                err,
            ) from err
        if err.status == 423:
            raise YaleApiError(
                f"The operation failed because the bridge (connect) is in use: {err.message}",
                err,
            ) from err
        if err.status == 408:
            raise YaleApiError(
                f"The operation timed out because the bridge (connect) failed to respond: {err.message}",
                err,
            ) from err
        raise YaleApiError(
            f"The operation failed with error code {err.status}: {err.message}.", err
        ) from err
