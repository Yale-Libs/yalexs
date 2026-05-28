"""Test the manager data module."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from _pytest.logging import LogCaptureFixture
from aiohttp import ClientError, ClientResponseError

from yalexs.activity import SOURCE_PUBNUB, SOURCE_WEBSOCKET
from yalexs.capabilities import CapabilitiesResponse
from yalexs.const import Brand
from yalexs.doorbell import ContentTokenExpired
from yalexs.exceptions import AugustApiAIOHTTPError, YaleApiError
from yalexs.lock import LockDetail, LockOperation
from yalexs.manager.data import YaleXSData
from yalexs.manager.exceptions import CannotConnect


class MockYaleXSData(YaleXSData):
    """Mock implementation of YaleXSData with mocked abstract method."""

    def async_offline_key_discovered(self, detail) -> None:
        """Mock implementation of abstract method."""


class TestPushStateTracking:
    """Test push state tracking functionality."""

    def setup_method(self):
        """Set up test fixtures."""

        # Create a simple object with just the method and state dict we need
        class TestData:
            def __init__(self):
                self._last_push_state = {}

            # Bind the actual method from YaleXSData
            _is_unchanged_push_state = YaleXSData._is_unchanged_push_state

        self.data = TestData()
        self.device_id = "test_device_id"

    def test_pubnub_initial_status_update_sets_baseline(self):
        """Test that the first PubNub status update sets the baseline state."""
        # First status update should set baseline
        message1 = {
            "status": "locked",
            "doorState": "closed",
        }

        # Mock activities that are all status updates
        mock_activity1 = Mock()
        mock_activity1.is_status = True

        # First call - no previous state
        result1 = self.data._is_unchanged_push_state(
            self.device_id, message1, SOURCE_PUBNUB, [mock_activity1]
        )
        # Should not skip (need to process) and should track the state
        assert result1 is False

        # Verify state was tracked
        state_key = f"{self.device_id}:{SOURCE_PUBNUB}"
        assert state_key in self.data._last_push_state
        assert self.data._last_push_state[state_key] == {
            "lock": "locked",
            "door": "closed",
        }

    def test_pubnub_duplicate_status_update_skipped(self):
        """Test that duplicate PubNub status updates are skipped."""
        message = {
            "status": "locked",
            "doorState": "closed",
        }

        # Set initial state
        state_key = f"{self.device_id}:{SOURCE_PUBNUB}"
        self.data._last_push_state[state_key] = {
            "lock": "locked",
            "door": "closed",
        }

        # Mock activities that are all status updates
        mock_activity = Mock()
        mock_activity.is_status = True

        # Same state status update - should be skipped
        result = self.data._is_unchanged_push_state(
            self.device_id, message, SOURCE_PUBNUB, [mock_activity]
        )
        assert result is True  # Should skip

        # State should not have changed
        assert self.data._last_push_state[state_key] == {
            "lock": "locked",
            "door": "closed",
        }

    def test_pubnub_changed_status_update_not_tracked(self):
        """Test that changed PubNub status updates are processed but not tracked."""
        # Set initial state
        state_key = f"{self.device_id}:{SOURCE_PUBNUB}"
        self.data._last_push_state[state_key] = {
            "lock": "locked",
            "door": "closed",
        }

        # Different state in status update
        message = {
            "status": "unlocked",
            "doorState": "open",
        }

        # Mock activities that are all status updates
        mock_activity = Mock()
        mock_activity.is_status = True

        result = self.data._is_unchanged_push_state(
            self.device_id, message, SOURCE_PUBNUB, [mock_activity]
        )
        assert result is False  # Should process (state changed)

        # State should NOT have been updated (status updates don't track)
        assert self.data._last_push_state[state_key] == {
            "lock": "locked",
            "door": "closed",
        }

    def test_pubnub_real_action_updates_tracking(self):
        """Test that real PubNub actions update state tracking."""
        # Set initial state
        state_key = f"{self.device_id}:{SOURCE_PUBNUB}"
        self.data._last_push_state[state_key] = {
            "lock": "locked",
            "door": "closed",
        }

        # Real unlock action
        message = {
            "status": "unlocked",
            "doorState": "closed",
            "info": {"action": "unlock"},
            "callingUserID": "user123",
        }

        # Mock activity that is NOT a status update
        mock_activity = Mock()
        mock_activity.is_status = False

        result = self.data._is_unchanged_push_state(
            self.device_id, message, SOURCE_PUBNUB, [mock_activity]
        )
        assert result is False  # Should process

        # State SHOULD have been updated (real action)
        assert self.data._last_push_state[state_key] == {
            "lock": "unlocked",
            "door": "closed",
        }

    def test_status_update_between_real_actions_doesnt_interfere(self):
        """Test that status updates between real actions don't interfere with detection."""
        state_key = f"{self.device_id}:{SOURCE_PUBNUB}"

        # Step 1: Real unlock action
        message1 = {
            "status": "unlocked",
            "doorState": "closed",
        }
        mock_activity1 = Mock()
        mock_activity1.is_status = False

        result1 = self.data._is_unchanged_push_state(
            self.device_id, message1, SOURCE_PUBNUB, [mock_activity1]
        )
        assert result1 is False
        assert self.data._last_push_state[state_key] == {
            "lock": "unlocked",
            "door": "closed",
        }

        # Step 2: Status update with same state
        message2 = {
            "status": "unlocked",
            "doorState": "closed",
        }
        mock_activity2 = Mock()
        mock_activity2.is_status = True

        result2 = self.data._is_unchanged_push_state(
            self.device_id, message2, SOURCE_PUBNUB, [mock_activity2]
        )
        assert result2 is True  # Should skip (unchanged)
        assert self.data._last_push_state[state_key] == {
            "lock": "unlocked",
            "door": "closed",
        }  # State unchanged

        # Step 3: Real lock action
        message3 = {
            "status": "locked",
            "doorState": "closed",
        }
        mock_activity3 = Mock()
        mock_activity3.is_status = False

        result3 = self.data._is_unchanged_push_state(
            self.device_id, message3, SOURCE_PUBNUB, [mock_activity3]
        )
        assert result3 is False  # Should process (real action with changed state)
        assert self.data._last_push_state[state_key] == {
            "lock": "locked",
            "door": "closed",
        }  # State updated

    def test_websocket_always_tracks_state(self):
        """Test that WebSocket messages always track state changes."""
        state_key = f"{self.device_id}:{SOURCE_WEBSOCKET}"

        # First WebSocket message
        message1 = {
            "lockAction": "locked",
            "doorState": "closed",
        }

        result1 = self.data._is_unchanged_push_state(
            self.device_id, message1, SOURCE_WEBSOCKET, []
        )
        assert result1 is False
        assert self.data._last_push_state[state_key] == {
            "lock": "locked",
            "door": "closed",
        }

        # Same state - should skip
        result2 = self.data._is_unchanged_push_state(
            self.device_id, message1, SOURCE_WEBSOCKET, []
        )
        assert result2 is True

        # Different state - should process and track
        message2 = {
            "lockAction": "unlocked",
            "doorState": "open",
        }
        result3 = self.data._is_unchanged_push_state(
            self.device_id, message2, SOURCE_WEBSOCKET, []
        )
        assert result3 is False
        assert self.data._last_push_state[state_key] == {
            "lock": "unlocked",
            "door": "open",
        }

    def test_separate_tracking_per_source(self):
        """Test that state is tracked separately for each source."""
        pubnub_key = f"{self.device_id}:{SOURCE_PUBNUB}"
        websocket_key = f"{self.device_id}:{SOURCE_WEBSOCKET}"

        # Set PubNub state
        pubnub_message = {
            "status": "locked",
            "doorState": "closed",
        }
        mock_activity = Mock()
        mock_activity.is_status = False

        self.data._is_unchanged_push_state(
            self.device_id, pubnub_message, SOURCE_PUBNUB, [mock_activity]
        )

        # Set different WebSocket state
        websocket_message = {
            "lockAction": "unlocked",
            "doorState": "open",
        }
        self.data._is_unchanged_push_state(
            self.device_id, websocket_message, SOURCE_WEBSOCKET, []
        )

        # Verify states are tracked separately
        assert self.data._last_push_state[pubnub_key] == {
            "lock": "locked",
            "door": "closed",
        }
        assert self.data._last_push_state[websocket_key] == {
            "lock": "unlocked",
            "door": "open",
        }

    def test_unchanged_state_still_processes_newer_activities(self, caplog):
        """Test that unchanged state messages still process if they have newer activities."""

        # Create a more complete mock data object with required methods
        class TestDataWithMethods:
            def __init__(self):
                self._last_push_state = {}
                self._device_detail_by_id = {}
                self.activity_stream = Mock()
                self.activity_stream.async_process_newer_device_activities = Mock(
                    return_value=True
                )
                self.activity_stream.async_schedule_house_id_refresh = Mock()

            # Bind the actual methods from YaleXSData
            _is_unchanged_push_state = YaleXSData._is_unchanged_push_state
            _async_handle_push_message = YaleXSData._async_handle_push_message

            def get_device_detail(self, device_id):
                return self._device_detail_by_id.get(device_id)

            def async_signal_device_id_update(self, device_id):
                pass

        data = TestDataWithMethods()
        device_id = "test_device"

        # Create a mock device
        mock_device = Mock()
        mock_device.device_id = device_id
        mock_device.house_id = "test_house"
        data._device_detail_by_id[device_id] = mock_device

        # Set initial state
        state_key = f"{device_id}:{SOURCE_PUBNUB}"
        data._last_push_state[state_key] = {
            "lock": "locked",
            "door": "closed",
        }

        # Message with same state but newer timestamp (would have newer activities)
        message = {
            "status": "locked",
            "doorState": "closed",
            "callingUserID": "manuallock",
        }

        # Mock activity that is not a status update
        mock_activity = Mock()
        mock_activity.is_status = False
        mock_activity.action = "lock"

        with (
            patch(
                "yalexs.manager.data.activities_from_pubnub_message"
            ) as mock_activities_func,
            caplog.at_level(logging.DEBUG),
        ):
            mock_activities_func.return_value = [mock_activity]

            # Call the push message handler
            data._async_handle_push_message(
                device_id, datetime.now(timezone.utc), message, SOURCE_PUBNUB
            )

            # Verify activities were processed even though state unchanged
            assert data.activity_stream.async_process_newer_device_activities.called
            assert data.activity_stream.async_process_newer_device_activities.call_args[
                0
            ][0] == [mock_activity]

            # Verify we logged that state was unchanged
            assert any(
                "Skipping unchanged" in record.message for record in caplog.records
            )

            # Verify house refresh was NOT scheduled (because unchanged)
            assert not data.activity_stream.async_schedule_house_id_refresh.called


class TestPushMessageForUnknownDevice:
    """Push messages for devices not in _device_detail_by_id are dropped, not raised."""

    def _build_data(self) -> Any:
        class TestData:
            def __init__(self):
                self._last_push_state = {}
                self._device_detail_by_id = {}
                self.activity_stream = Mock()
                self.activity_stream.async_process_newer_device_activities = Mock(
                    return_value=True
                )
                self.activity_stream.async_schedule_house_id_refresh = Mock()
                self.signaled: list[str] = []

            _is_unchanged_push_state = YaleXSData._is_unchanged_push_state
            _async_handle_push_message = YaleXSData._async_handle_push_message
            async_push_message = YaleXSData.async_push_message
            get_device_detail = YaleXSData.get_device_detail

            def async_signal_device_id_update(self, device_id):
                self.signaled.append(device_id)

        return TestData()

    def test_unknown_device_id_logs_debug_and_returns(self, caplog):
        data = self._build_data()
        message = {"status": "locked", "doorState": "closed"}

        with (
            patch(
                "yalexs.manager.data.activities_from_pubnub_message"
            ) as mock_activities_func,
            caplog.at_level(logging.DEBUG),
        ):
            data._async_handle_push_message(
                "MISSING_LOCK_ID", datetime.now(timezone.utc), message, SOURCE_PUBNUB
            )

        # We should not have tried to build activities for an unknown device.
        assert not mock_activities_func.called
        # We should not have signaled any update for a device we do not know.
        assert data.signaled == []
        # And we should have logged the skip at debug level.
        assert any(
            "unknown device" in record.message and "MISSING_LOCK_ID" in record.message
            for record in caplog.records
        )

    def test_unknown_device_id_via_async_push_message_does_not_raise(self, caplog):
        """Regression for GH#325: async_push_message must swallow unknown ids quietly.

        Before the fix this path raised KeyError out of _async_handle_push_message,
        was caught by the outer except Exception, and logged a full stack trace on
        every push for the unknown device — flooding logs and (per the bug report)
        coinciding with BLE reconnect failures until the integration was reloaded.
        After the fix the inner handler short-circuits at DEBUG level and no
        ERROR-level traceback is produced.
        """
        data = self._build_data()
        message = {"status": "locked", "doorState": "closed"}

        with (
            patch("yalexs.manager.data.activities_from_pubnub_message"),
            caplog.at_level(logging.DEBUG),
        ):
            data.async_push_message(
                "MISSING_LOCK_ID", datetime.now(timezone.utc), message, SOURCE_PUBNUB
            )

        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert error_records == []

    def test_known_device_id_still_processed(self):
        """Sanity check: the new guard must not break the happy path."""
        data = self._build_data()
        device_id = "KNOWN_LOCK_ID"
        mock_device = Mock()
        mock_device.device_id = device_id
        mock_device.house_id = "house"
        data._device_detail_by_id[device_id] = mock_device

        mock_activity = Mock()
        mock_activity.is_status = False
        mock_activity.action = "lock"

        with patch(
            "yalexs.manager.data.activities_from_pubnub_message",
            return_value=[mock_activity],
        ):
            data._async_handle_push_message(
                device_id,
                datetime.now(timezone.utc),
                {"status": "locked", "doorState": "closed"},
                SOURCE_PUBNUB,
            )

        assert data.activity_stream.async_process_newer_device_activities.called
        assert data.signaled == [device_id]


@pytest.mark.asyncio
async def test_fetch_lock_capabilities() -> None:
    """Test that lock capabilities are fetched and set correctly."""
    # Create mock gateway and API
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test-token")

    mock_api = Mock()
    mock_gateway.api = mock_api
    mock_gateway.api.brand = Brand.YALE_HOME  # Set brand for capability fetching

    # Create MockYaleXSData instance
    data = MockYaleXSData(mock_gateway)

    # Create mock lock details
    lock_detail_1 = Mock(spec=LockDetail)
    lock_detail_1.device_name = "Front Door"
    lock_detail_1.set_capabilities = Mock()

    lock_detail_2 = Mock(spec=LockDetail)
    lock_detail_2.device_name = "Back Door"
    lock_detail_2.set_capabilities = Mock()

    # Set up device details
    # Note: lock_id is the serial number for locks
    data._device_detail_by_id = {
        "SERIAL1": lock_detail_1,
        "SERIAL2": lock_detail_2,
        "doorbell1": Mock(),  # Not a lock, should be skipped
    }
    data._locks_by_id = {
        "SERIAL1": Mock(),
        "SERIAL2": Mock(),
    }

    # Mock API responses
    capabilities_1: CapabilitiesResponse = {
        "lock": {
            "unlatch": True,
            "doorSense": True,
            "batteryType": "AA",
        }
    }
    capabilities_2: CapabilitiesResponse = {
        "lock": {
            "unlatch": False,
            "doorSense": False,
            "batteryType": "CR123",
        }
    }

    # Configure mock API
    async def mock_get_capabilities(token: str, serial: str) -> CapabilitiesResponse:
        if serial == "SERIAL1":
            return capabilities_1
        if serial == "SERIAL2":
            return capabilities_2
        raise ValueError(f"Unknown serial: {serial}")

    mock_api.async_get_lock_capabilities = AsyncMock(side_effect=mock_get_capabilities)

    # Call the method
    await data._async_fetch_lock_capabilities()

    # Verify API was called with correct parameters
    assert mock_api.async_get_lock_capabilities.call_count == 2
    mock_api.async_get_lock_capabilities.assert_any_call("test-token", "SERIAL1")
    mock_api.async_get_lock_capabilities.assert_any_call("test-token", "SERIAL2")

    # Verify capabilities were set on lock details
    lock_detail_1.set_capabilities.assert_called_once_with(capabilities_1)
    lock_detail_2.set_capabilities.assert_called_once_with(capabilities_2)


@pytest.mark.asyncio
async def test_fetch_lock_capabilities_with_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that capability fetch errors are handled gracefully."""
    # Create mock gateway and API
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test-token")

    mock_api = Mock()
    mock_gateway.api = mock_api
    mock_gateway.api.brand = Brand.YALE_HOME  # Set brand for capability fetching

    # Create MockYaleXSData instance
    data = MockYaleXSData(mock_gateway)

    # Create mock lock detail
    lock_detail = Mock(spec=LockDetail)
    lock_detail.device_name = "Front Door"
    lock_detail.set_capabilities = Mock()

    # Set up device details (lock_id is serial number)
    data._device_detail_by_id = {
        "SERIAL1": lock_detail,
    }
    data._locks_by_id = {
        "SERIAL1": Mock(),
    }

    # Mock API to raise an error

    mock_api.async_get_lock_capabilities = AsyncMock(
        side_effect=ClientError("API Error")
    )

    # Call the method with logging
    with caplog.at_level(logging.WARNING):
        await data._async_fetch_lock_capabilities()

    # Verify API was called
    mock_api.async_get_lock_capabilities.assert_called_once_with(
        "test-token", "SERIAL1"
    )

    # Verify capabilities were NOT set due to error
    lock_detail.set_capabilities.assert_not_called()

    # Verify error was logged
    assert "Failed to fetch capabilities for lock Front Door" in caplog.text
    assert "API Error" in caplog.text


@pytest.mark.asyncio
async def test_fetch_lock_capabilities_skips_non_locks() -> None:
    """Test that non-lock devices are skipped when fetching capabilities."""
    # Create mock gateway and API
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test-token")

    mock_api = Mock()
    mock_gateway.api = mock_api
    mock_gateway.api.brand = Brand.YALE_HOME  # Set brand for capability fetching

    # Create MockYaleXSData instance
    data = MockYaleXSData(mock_gateway)

    # Create mock lock detail
    lock_detail = Mock(spec=LockDetail)
    lock_detail.device_name = "Front Door"
    lock_detail.set_capabilities = Mock()

    # Set up device details with mixed devices
    data._device_detail_by_id = {
        "SERIAL1": lock_detail,  # This is a lock
        "doorbell1": Mock(),  # This is not a lock
        "doorbell2": Mock(),  # This is not a lock
    }
    data._locks_by_id = {
        "SERIAL1": Mock(),  # Only this one is a lock
    }

    # Mock API response
    capabilities: CapabilitiesResponse = {
        "lock": {
            "unlatch": True,
            "doorSense": True,
            "batteryType": "AA",
        }
    }

    mock_api.async_get_lock_capabilities = AsyncMock(return_value=capabilities)

    # Call the method
    await data._async_fetch_lock_capabilities()

    # Verify API was called only once (for the lock, not the doorbells)
    mock_api.async_get_lock_capabilities.assert_called_once_with(
        "test-token", "SERIAL1"
    )

    # Verify capabilities were set only on the lock
    lock_detail.set_capabilities.assert_called_once_with(capabilities)


@pytest.mark.asyncio
async def test_fetch_lock_capabilities_sequential_execution() -> None:
    """Test that capabilities are fetched sequentially, not in parallel."""
    # Create mock gateway and API
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test-token")

    mock_api = Mock()
    mock_gateway.api = mock_api
    mock_gateway.api.brand = Brand.YALE_HOME  # Set brand for capability fetching

    # Create MockYaleXSData instance
    data = MockYaleXSData(mock_gateway)

    # Create mock lock details
    lock_detail_1 = Mock(spec=LockDetail)
    lock_detail_1.device_name = "Front Door"
    lock_detail_1.set_capabilities = Mock()

    lock_detail_2 = Mock(spec=LockDetail)
    lock_detail_2.device_name = "Back Door"
    lock_detail_2.set_capabilities = Mock()

    lock_detail_3 = Mock(spec=LockDetail)
    lock_detail_3.device_name = "Side Door"
    lock_detail_3.set_capabilities = Mock()

    # Set up device details
    data._device_detail_by_id = {
        "SERIAL1": lock_detail_1,
        "SERIAL2": lock_detail_2,
        "SERIAL3": lock_detail_3,
    }
    data._locks_by_id = {
        "SERIAL1": Mock(),
        "SERIAL2": Mock(),
        "SERIAL3": Mock(),
    }

    # Track call order
    call_order: list[str] = []

    async def mock_get_capabilities(token: str, serial: str) -> CapabilitiesResponse:
        call_order.append(serial)
        return {"lock": {"unlatch": True}}

    mock_api.async_get_lock_capabilities = AsyncMock(side_effect=mock_get_capabilities)

    # Call the method
    await data._async_fetch_lock_capabilities()

    # Verify all were called in sequence
    assert call_order == ["SERIAL1", "SERIAL2", "SERIAL3"]
    assert mock_api.async_get_lock_capabilities.call_count == 3


@pytest.mark.asyncio
async def test_august_brand_does_not_fetch_capabilities():
    """Test that August brand does not fetch device capabilities."""
    # Create mock gateway with August brand
    mock_gateway = AsyncMock()
    mock_gateway.brand = Brand.AUGUST  # August brand
    mock_gateway.access_token = "test-token"
    mock_gateway.async_get_access_token = AsyncMock(return_value="test-token")

    mock_api = Mock()
    mock_gateway.api = mock_api
    mock_gateway.api.brand = Brand.AUGUST  # Set August brand for API

    # Create MockYaleXSData instance
    data = MockYaleXSData(mock_gateway)

    # Set up test locks
    lock1 = {
        "LockID": "ABC1",
        "LockName": "Lock 1",
        "HouseID": "house1",
        "SerialNumber": "SERIAL1",
        "Type": 5,
        "battery": 0.8,
        "currentFirmwareVersion": "1.0.0",
        "LockStatus": {"status": "locked"},
    }
    lock2 = {
        "LockID": "ABC2",
        "LockName": "Lock 2",
        "HouseID": "house1",
        "SerialNumber": "SERIAL2",
        "Type": 17,
        "battery": 0.9,
        "currentFirmwareVersion": "1.0.0",
        "LockStatus": {"status": "unlocked"},
    }

    data._lock_details = {
        "ABC1": LockDetail(lock1),
        "ABC2": LockDetail(lock2),
    }

    # Mock the capabilities fetch - should not be called
    mock_api.async_get_lock_capabilities = AsyncMock()

    # Call the method
    await data._async_fetch_lock_capabilities()

    # Verify the capabilities method was NOT called for August brand
    assert mock_api.async_get_lock_capabilities.call_count == 0


@pytest.mark.asyncio
async def test_fetch_lock_capabilities_handles_404_and_409_errors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that 404 and 409 errors are handled gracefully when fetching capabilities."""
    # Create mock gateway and API
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test-token")

    mock_api = Mock()
    mock_gateway.api = mock_api
    mock_gateway.api.brand = Brand.YALE_HOME  # Set brand for capability fetching

    # Create MockYaleXSData instance
    data = MockYaleXSData(mock_gateway)

    # Create mock lock details
    lock_detail_404 = Mock(spec=LockDetail)
    lock_detail_404.device_name = "Lock 404"
    lock_detail_404.set_capabilities = Mock()

    lock_detail_409 = Mock(spec=LockDetail)
    lock_detail_409.device_name = "Lock 409"
    lock_detail_409.set_capabilities = Mock()

    # Set up device details
    data._device_detail_by_id = {
        "SERIAL404": lock_detail_404,
        "SERIAL409": lock_detail_409,
    }
    data._locks_by_id = {
        "SERIAL404": Mock(),
        "SERIAL409": Mock(),
    }

    # Mock API to raise 404 and 409 errors
    async def mock_get_capabilities(token: str, serial: str) -> None:
        if serial == "SERIAL404":
            error = YaleApiError(
                "The operation failed with error code 404: Device info not found.",
                ClientResponseError(
                    request_info=Mock(),
                    history=(),
                    status=404,
                    message="Device info not found",
                ),
            )
            raise error
        if serial == "SERIAL409":
            error = YaleApiError(
                "The operation failed with error code 409: Cannot infer deviceType from serial number.",
                ClientResponseError(
                    request_info=Mock(),
                    history=(),
                    status=409,
                    message="Cannot infer deviceType from serial number.",
                ),
            )
            raise error

    mock_api.async_get_lock_capabilities = AsyncMock(side_effect=mock_get_capabilities)

    # Call the method with debug logging
    with caplog.at_level(logging.DEBUG):
        await data._async_fetch_lock_capabilities()

    # Verify API was called for both locks
    assert mock_api.async_get_lock_capabilities.call_count == 2

    # Verify capabilities were NOT set due to errors
    lock_detail_404.set_capabilities.assert_not_called()
    lock_detail_409.set_capabilities.assert_not_called()

    # Verify debug messages were logged (not warnings)
    assert "Cannot fetch capabilities for lock Lock 404 (HTTP 404)" in caplog.text
    assert "Cannot fetch capabilities for lock Lock 409 (HTTP 409)" in caplog.text
    # Verify no warning logs for these expected errors
    warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(warning_records) == 0


@pytest.mark.asyncio
async def test_fetch_lock_capabilities_handles_other_errors_with_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that non-404/409 errors are logged as warnings when fetching capabilities."""
    # Create mock gateway and API
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test-token")

    mock_api = Mock()
    mock_gateway.api = mock_api
    mock_gateway.api.brand = Brand.YALE_HOME  # Set brand for capability fetching

    # Create MockYaleXSData instance
    data = MockYaleXSData(mock_gateway)

    # Create mock lock details
    lock_detail_401 = Mock(spec=LockDetail)
    lock_detail_401.device_name = "Lock 401"
    lock_detail_401.set_capabilities = Mock()

    lock_detail_500 = Mock(spec=LockDetail)
    lock_detail_500.device_name = "Lock 500"
    lock_detail_500.set_capabilities = Mock()

    # Set up device details
    data._device_detail_by_id = {
        "SERIAL401": lock_detail_401,
        "SERIAL500": lock_detail_500,
    }
    data._locks_by_id = {
        "SERIAL401": Mock(),
        "SERIAL500": Mock(),
    }

    # Mock API to raise 401 and 500 errors
    async def mock_get_capabilities(token: str, serial: str) -> None:
        if serial == "SERIAL401":
            error = YaleApiError(
                "The operation failed with error code 401: Unauthorized.",
                ClientResponseError(
                    request_info=Mock(),
                    history=(),
                    status=401,
                    message="Unauthorized",
                ),
            )
            raise error
        if serial == "SERIAL500":
            error = YaleApiError(
                "The operation failed with error code 500: Internal Server Error.",
                ClientResponseError(
                    request_info=Mock(),
                    history=(),
                    status=500,
                    message="Internal Server Error",
                ),
            )
            raise error

    mock_api.async_get_lock_capabilities = AsyncMock(side_effect=mock_get_capabilities)

    # Call the method with warning logging
    with caplog.at_level(logging.WARNING):
        await data._async_fetch_lock_capabilities()

    # Verify API was called for both locks
    assert mock_api.async_get_lock_capabilities.call_count == 2

    # Verify capabilities were NOT set due to errors
    lock_detail_401.set_capabilities.assert_not_called()
    lock_detail_500.set_capabilities.assert_not_called()

    # Verify warning messages were logged for non-404/409 errors
    assert "Failed to fetch capabilities for lock Lock 401 (HTTP 401)" in caplog.text
    assert "Failed to fetch capabilities for lock Lock 500 (HTTP 500)" in caplog.text

    # Verify these are logged as warnings, not debug
    warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(warning_records) == 2


@pytest.mark.asyncio
async def test_fetch_lock_capabilities_handles_network_errors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that network errors like ClientError and TimeoutError are handled gracefully."""
    # Create mock gateway and API
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test-token")

    mock_api = Mock()
    mock_gateway.api = mock_api
    mock_gateway.api.brand = Brand.YALE_HOME  # Set brand for capability fetching

    # Create MockYaleXSData instance
    data = MockYaleXSData(mock_gateway)

    # Create mock lock details
    lock_detail_timeout = Mock(spec=LockDetail)
    lock_detail_timeout.device_name = "Lock Timeout"
    lock_detail_timeout.set_capabilities = Mock()

    lock_detail_network = Mock(spec=LockDetail)
    lock_detail_network.device_name = "Lock Network"
    lock_detail_network.set_capabilities = Mock()

    # Set up device details
    data._device_detail_by_id = {
        "SERIAL_TIMEOUT": lock_detail_timeout,
        "SERIAL_NETWORK": lock_detail_network,
    }
    data._locks_by_id = {
        "SERIAL_TIMEOUT": Mock(),
        "SERIAL_NETWORK": Mock(),
    }

    # Mock API to raise TimeoutError and ClientError
    async def mock_get_capabilities(token: str, serial: str) -> None:
        if serial == "SERIAL_TIMEOUT":
            raise TimeoutError("Request timed out")
        if serial == "SERIAL_NETWORK":
            raise ClientError("Network error")

    mock_api.async_get_lock_capabilities = AsyncMock(side_effect=mock_get_capabilities)

    # Call the method with warning logging
    with caplog.at_level(logging.WARNING):
        await data._async_fetch_lock_capabilities()

    # Verify API was called for both locks
    assert mock_api.async_get_lock_capabilities.call_count == 2

    # Verify capabilities were NOT set due to errors
    lock_detail_timeout.set_capabilities.assert_not_called()
    lock_detail_network.set_capabilities.assert_not_called()

    # Verify warning messages were logged for network errors
    assert (
        "Failed to fetch capabilities for lock Lock Timeout: Request timed out"
        in caplog.text
    )
    assert (
        "Failed to fetch capabilities for lock Lock Network: Network error"
        in caplog.text
    )

    # Verify these are logged as warnings
    warning_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(warning_records) == 2


@pytest.mark.asyncio
async def test_async_operate_lock_wait_mode() -> None:
    """Test async_operate_lock LOCK operation when waiting for response."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    # Mock the individual lock operation methods
    data.async_lock = AsyncMock(return_value=["lock_activity"])
    data.async_lock_async = AsyncMock(return_value="lock_request_id")

    device_id = "test_device"

    # Mock device detail without unlatch support
    mock_detail = Mock(spec=LockDetail)
    mock_detail.unlatch_supported = False
    data.get_device_detail = Mock(return_value=mock_detail)

    result = await data.async_operate_lock(
        device_id, LockOperation.LOCK, push_updates_connected=False
    )

    assert result == ["lock_activity"]
    data.async_lock.assert_called_once_with(device_id)
    data.async_lock_async.assert_not_called()


@pytest.mark.asyncio
async def test_async_operate_lock_push_mode() -> None:
    """Test async_operate_lock LOCK operation with push updates (no wait)."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    # Mock the individual lock operation methods
    data.async_lock = AsyncMock(return_value=["lock_activity"])
    data.async_lock_async = AsyncMock(return_value="lock_request_id")

    device_id = "test_device"

    # Mock device detail without unlatch support
    mock_detail = Mock(spec=LockDetail)
    mock_detail.unlatch_supported = False
    data.get_device_detail = Mock(return_value=mock_detail)

    result = await data.async_operate_lock(
        device_id, LockOperation.LOCK, push_updates_connected=True, hyper_bridge=True
    )

    assert result == []  # Returns empty list when not waiting
    data.async_lock.assert_not_called()
    data.async_lock_async.assert_called_once_with(device_id, True)


@pytest.mark.asyncio
async def test_async_operate_unlock_no_unlatch_support() -> None:
    """Test async_operate_lock UNLOCK operation when device doesn't support unlatch."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    # Mock the individual lock operation methods
    data.async_unlock = AsyncMock(return_value=["unlock_activity"])
    data.async_unlatch = AsyncMock(return_value=["unlatch_activity"])

    device_id = "test_device"

    # Mock device detail without unlatch support
    mock_detail = Mock(spec=LockDetail)
    mock_detail.unlatch_supported = False
    data.get_device_detail = Mock(return_value=mock_detail)

    result = await data.async_operate_lock(
        device_id, LockOperation.UNLOCK, push_updates_connected=False
    )

    assert result == ["unlock_activity"]
    data.async_unlock.assert_called_once_with(device_id)
    data.async_unlatch.assert_not_called()


@pytest.mark.asyncio
async def test_async_operate_unlock_with_unlatch_support() -> None:
    """Test async_operate_lock UNLOCK operation when device supports unlatch (should call unlatch)."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    # Mock the individual lock operation methods
    data.async_unlock = AsyncMock(return_value=["unlock_activity"])
    data.async_unlatch = AsyncMock(return_value=["unlatch_activity"])

    device_id = "test_device"

    # Mock device detail WITH unlatch support
    mock_detail = Mock(spec=LockDetail)
    mock_detail.unlatch_supported = True
    data.get_device_detail = Mock(return_value=mock_detail)

    result = await data.async_operate_lock(
        device_id, LockOperation.UNLOCK, push_updates_connected=False
    )

    # When unlatch is supported, UNLOCK should call unlatch!
    assert result == ["unlatch_activity"]
    data.async_unlatch.assert_called_once_with(device_id)
    data.async_unlock.assert_not_called()


@pytest.mark.asyncio
async def test_async_operate_open_no_unlatch_support() -> None:
    """Test async_operate_lock OPEN operation when device doesn't support unlatch."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    # Mock the individual lock operation methods
    data.async_unlock = AsyncMock(return_value=["unlock_activity"])
    data.async_unlatch = AsyncMock(return_value=["unlatch_activity"])

    device_id = "test_device"

    # Mock device detail without unlatch support
    mock_detail = Mock(spec=LockDetail)
    mock_detail.unlatch_supported = False
    data.get_device_detail = Mock(return_value=mock_detail)

    result = await data.async_operate_lock(
        device_id, LockOperation.OPEN, push_updates_connected=False
    )

    assert result == ["unlatch_activity"]
    data.async_unlatch.assert_called_once_with(device_id)
    data.async_unlock.assert_not_called()


@pytest.mark.asyncio
async def test_async_operate_open_with_unlatch_support() -> None:
    """Test async_operate_lock OPEN operation when device supports unlatch (should call unlock)."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    # Mock the individual lock operation methods
    data.async_unlock = AsyncMock(return_value=["unlock_activity"])
    data.async_unlatch = AsyncMock(return_value=["unlatch_activity"])

    device_id = "test_device"

    # Mock device detail WITH unlatch support
    mock_detail = Mock(spec=LockDetail)
    mock_detail.unlatch_supported = True
    data.get_device_detail = Mock(return_value=mock_detail)

    result = await data.async_operate_lock(
        device_id, LockOperation.OPEN, push_updates_connected=False
    )

    # When unlatch is supported, OPEN should call unlock!
    assert result == ["unlock_activity"]
    data.async_unlock.assert_called_once_with(device_id)
    data.async_unlatch.assert_not_called()


@pytest.mark.asyncio
async def test_async_operate_lock_all_operations_with_push() -> None:
    """Test async_operate_lock all operations with push updates enabled."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    # Mock all async operation methods
    data.async_lock_async = AsyncMock(return_value="lock_request_id")
    data.async_unlock_async = AsyncMock(return_value="unlock_request_id")
    data.async_unlatch_async = AsyncMock(return_value="unlatch_request_id")

    device_id = "test_device"

    # Mock device detail with unlatch support
    mock_detail = Mock(spec=LockDetail)
    mock_detail.unlatch_supported = True
    data.get_device_detail = Mock(return_value=mock_detail)

    # Test LOCK operation
    result = await data.async_operate_lock(
        device_id, LockOperation.LOCK, push_updates_connected=True
    )
    assert result == []
    data.async_lock_async.assert_called_once_with(device_id, True)

    # Reset mocks
    data.async_lock_async.reset_mock()
    data.async_unlock_async.reset_mock()
    data.async_unlatch_async.reset_mock()

    # Test UNLOCK (should call unlatch_async when unlatch supported)
    result = await data.async_operate_lock(
        device_id, LockOperation.UNLOCK, push_updates_connected=True
    )
    assert result == []
    data.async_unlatch_async.assert_called_once_with(device_id, True)

    # Reset mocks
    data.async_lock_async.reset_mock()
    data.async_unlock_async.reset_mock()
    data.async_unlatch_async.reset_mock()

    # Test OPEN (should call unlock_async when unlatch supported)
    result = await data.async_operate_lock(
        device_id, LockOperation.OPEN, push_updates_connected=True
    )
    assert result == []
    data.async_unlock_async.assert_called_once_with(device_id, True)


@pytest.mark.asyncio
async def test_async_operate_lock_invalid_operation() -> None:
    """Test async_operate_lock with invalid operation raises ValueError."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    device_id = "test_device"

    # Mock device detail
    mock_detail = Mock(spec=LockDetail)
    mock_detail.unlatch_supported = False
    data.get_device_detail = Mock(return_value=mock_detail)

    # Create an invalid operation
    invalid_op: Any = Mock()
    invalid_op.value = "invalid"

    with pytest.raises(ValueError, match="Invalid operation"):
        await data.async_operate_lock(
            device_id, invalid_op, push_updates_connected=False
        )


@pytest.mark.asyncio
async def test_async_operate_lock_no_device_detail() -> None:
    """Test async_operate_lock when get_device_detail returns None."""
    mock_gateway = Mock()
    mock_gateway.async_get_access_token = AsyncMock(return_value="test_token")
    mock_api = Mock()

    data = MockYaleXSData(mock_gateway, mock_api)

    # Mock the individual lock operation methods
    data.async_unlock = AsyncMock(return_value=["unlock_activity"])
    data.async_unlatch = AsyncMock(return_value=["unlatch_activity"])

    device_id = "test_device"

    # Mock get_device_detail to return None
    data.get_device_detail = Mock(return_value=None)

    result = await data.async_operate_lock(
        device_id, LockOperation.UNLOCK, push_updates_connected=False
    )

    # Should use normal mapping (unlock -> unlock)
    assert result == ["unlock_activity"]
    data.async_unlock.assert_called_once_with(device_id)
    data.async_unlatch.assert_not_called()


# ---------------------------------------------------------------------------
# Coverage for setup, refresh, lifecycle, doorbell image, and inoperative
# device removal paths in YaleXSData.
# ---------------------------------------------------------------------------


def _make_gateway(brand: Brand = Brand.AUGUST) -> Mock:
    """Build a Mock gateway whose .api is itself a Mock with brand attribute."""
    gateway = Mock()
    gateway.async_get_access_token = AsyncMock(return_value="token")
    gateway.api = Mock()
    gateway.api.brand = brand
    return gateway


@pytest.mark.asyncio
async def test_async_setup_filters_inoperative_and_starts_initial_sync() -> None:
    """async_setup pulls locks/doorbells, removes those without details, then kicks
    off the initial sync.
    """
    gateway = _make_gateway(Brand.AUGUST)

    lock_a = Mock(device_id="lockA", house_id="houseA")
    lock_b = Mock(device_id="lockB", house_id="houseA")
    doorbell = Mock(device_id="bellA", house_id="houseA")

    gateway.api.async_get_operable_locks = AsyncMock(return_value=[lock_a, lock_b])
    gateway.api.async_get_doorbells = AsyncMock(return_value=[doorbell])

    data = MockYaleXSData(gateway)

    async def fake_refresh(device_ids: list[str]) -> None:
        # only lockA gets details — lockB and doorbell drop off
        data._device_detail_by_id = {
            "lockA": Mock(
                spec=LockDetail, bridge=Mock(hyper_bridge=False), keypad=None
            ),
        }

    with (
        patch.object(
            data, "_async_refresh_device_detail_by_ids", side_effect=fake_refresh
        ),
        patch.object(data, "async_setup_activity_stream", new=AsyncMock()),
        patch(
            "yalexs.manager.data._RateLimitChecker.check_rate_limit", new=AsyncMock()
        ),
        patch("yalexs.manager.data._RateLimitChecker.register_wakeup", new=AsyncMock()),
        patch.object(
            data, "_async_status_async", new=AsyncMock(return_value="ok")
        ) as status_call,
    ):
        await data.async_setup()
        # Yield once so the initial-sync eager task can run to completion.
        await asyncio.sleep(0)

    assert "lockA" in data._locks_by_id
    assert "lockB" not in data._locks_by_id
    assert "bellA" not in data._doorbells_by_id
    assert data._house_ids == {"houseA"}
    # _initial_sync_task should have been scheduled and run.
    assert data._initial_sync_task is not None
    status_call.assert_called()


@pytest.mark.asyncio
async def test_async_setup_yale_global_fetches_capabilities_and_skips_sync() -> None:
    """YALE_GLOBAL brand: capability fetch runs, initial-sync task is not scheduled."""
    gateway = _make_gateway(Brand.YALE_GLOBAL)
    lock = Mock(device_id="L1", house_id="H1")
    gateway.api.async_get_operable_locks = AsyncMock(return_value=[lock])
    gateway.api.async_get_doorbells = AsyncMock(return_value=[])

    data = MockYaleXSData(gateway)
    lock_detail = Mock(spec=LockDetail, bridge=Mock(hyper_bridge=True))

    async def fake_refresh(device_ids: list[str]) -> None:
        data._device_detail_by_id = {"L1": lock_detail}

    with (
        patch.object(
            data, "_async_refresh_device_detail_by_ids", side_effect=fake_refresh
        ),
        patch.object(data, "async_setup_activity_stream", new=AsyncMock()),
        patch.object(
            data, "_async_fetch_lock_capabilities", new=AsyncMock()
        ) as fetch_caps,
        patch(
            "yalexs.manager.data._RateLimitChecker.check_rate_limit", new=AsyncMock()
        ),
        patch("yalexs.manager.data._RateLimitChecker.register_wakeup", new=AsyncMock()),
    ):
        await data.async_setup()

    fetch_caps.assert_awaited_once()
    assert data._initial_sync_task is None


@pytest.mark.asyncio
async def test_async_setup_activity_stream_yale_global_uses_socketio() -> None:
    gateway = _make_gateway(Brand.YALE_GLOBAL)
    gateway.api.async_get_user = AsyncMock(return_value={"UserID": "user-1"})
    data = MockYaleXSData(gateway)
    data._device_detail_by_id = {}

    unsub = AsyncMock()
    fake_runner = Mock()
    fake_runner.subscribe = Mock()
    fake_runner.run = AsyncMock(return_value=unsub)

    fake_stream = Mock()
    fake_stream.async_setup = AsyncMock()

    with (
        patch(
            "yalexs.manager.data.SocketIORunner", return_value=fake_runner
        ) as sio_cls,
        patch("yalexs.manager.data.ActivityStream", return_value=fake_stream),
    ):
        await data.async_setup_activity_stream()

    sio_cls.assert_called_once_with(gateway)
    fake_runner.subscribe.assert_called_once()
    fake_runner.run.assert_awaited_once_with("user-1", Brand.YALE_GLOBAL)
    assert data._push_unsub is unsub
    assert data.activity_stream is fake_stream


@pytest.mark.asyncio
async def test_async_setup_activity_stream_august_uses_pubnub_and_registers_devices() -> (
    None
):
    gateway = _make_gateway(Brand.AUGUST)
    gateway.api.async_get_user = AsyncMock(return_value={"UserID": "u2"})
    data = MockYaleXSData(gateway)
    dev1 = Mock()
    dev2 = Mock()
    data._device_detail_by_id = {"a": dev1, "b": dev2}

    unsub = AsyncMock()
    fake_pubnub = Mock()
    fake_pubnub.register_device = Mock()
    fake_pubnub.subscribe = Mock()
    fake_pubnub.run = AsyncMock(return_value=unsub)

    fake_stream = Mock()
    fake_stream.async_setup = AsyncMock()

    with (
        patch("yalexs.manager.data.AugustPubNub", return_value=fake_pubnub),
        patch("yalexs.manager.data.ActivityStream", return_value=fake_stream),
    ):
        await data.async_setup_activity_stream()

    assert fake_pubnub.register_device.call_count == 2
    fake_pubnub.run.assert_awaited_once_with("u2", Brand.AUGUST)
    assert data._push_unsub is unsub


@pytest.mark.asyncio
async def test_async_initial_sync_logs_unexpected_but_swallows_known_errors(
    caplog: LogCaptureFixture,
) -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    detail = Mock(bridge=Mock(hyper_bridge=False))
    data._device_detail_by_id = {"d1": detail, "d2": detail, "d3": detail}
    data._locks_by_id = {"d1": Mock(), "d2": Mock(), "d3": Mock()}

    async def _status(device_id: str, hyper_bridge: bool) -> str:
        if device_id == "d1":
            raise TimeoutError("timeout-marker")
        if device_id == "d2":
            return "ok"
        raise RuntimeError("boom")

    with (
        patch.object(data, "_async_status_async", side_effect=_status),
        caplog.at_level(logging.WARNING),
    ):
        await data._async_initial_sync()

    assert "Unexpected exception during initial sync" in caplog.text
    assert "boom" in caplog.text
    # The known TimeoutError must NOT have triggered a warning of its own.
    assert "timeout-marker" not in caplog.text


@pytest.mark.asyncio
async def test_async_stop_cancels_initial_sync_and_invokes_push_unsub() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    activity_stream = Mock()
    activity_stream.async_stop = Mock()
    data.activity_stream = activity_stream

    async def _never() -> None:
        await asyncio.sleep(10)

    data._initial_sync_task = asyncio.create_task(_never())
    push_unsub = AsyncMock()
    data._push_unsub = push_unsub

    await data.async_stop()

    assert data._shutdown is True
    activity_stream.async_stop.assert_called_once()
    assert data._initial_sync_task.cancelled()
    push_unsub.assert_awaited_once()


@pytest.mark.asyncio
async def test_properties_doorbells_locks_and_get_device_detail() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    door = Mock()
    lock = Mock()
    detail = Mock()
    data._doorbells_by_id = {"d": door}
    data._locks_by_id = {"l": lock}
    data._device_detail_by_id = {"l": detail}

    assert list(data.doorbells) == [door]
    assert list(data.locks) == [lock]
    assert data.get_device_detail("l") is detail


@pytest.mark.asyncio
async def test_async_refresh_returns_when_shutdown() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    data._shutdown = True
    with patch.object(
        data, "_async_refresh_device_detail_by_ids", new=AsyncMock()
    ) as inner:
        await data._async_refresh()
    inner.assert_not_called()


@pytest.mark.asyncio
async def test_async_refresh_delegates_to_subscriptions() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    data._subscriptions["dev1"].add(lambda: None)
    data._subscriptions["dev2"].add(lambda: None)

    with patch.object(
        data, "_async_refresh_device_detail_by_ids", new=AsyncMock()
    ) as inner:
        await data._async_refresh()

    inner.assert_awaited_once()
    arg = inner.await_args.args[0]
    assert set(arg) == {"dev1", "dev2"}


@pytest.mark.asyncio
async def test_refresh_device_details_logs_and_continues_on_known_errors(
    caplog: LogCaptureFixture,
) -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    seen: list[str] = []

    async def _per(device_id: str) -> None:
        seen.append(device_id)
        if device_id == "to":
            raise TimeoutError
        if device_id == "client":
            raise ClientResponseError(Mock(), (), status=500, message="boom")
        if device_id == "conn":
            raise CannotConnect

    with (
        patch.object(data, "_async_refresh_device_detail_by_id", side_effect=_per),
        caplog.at_level(logging.WARNING),
    ):
        await data._async_refresh_device_detail_by_ids(["to", "client", "conn", "ok"])

    assert seen == ["to", "client", "conn", "ok"]
    assert "Timed out" in caplog.text
    assert "Error from august api during refresh of device" in caplog.text


@pytest.mark.asyncio
async def test_refresh_camera_by_id_calls_update_for_doorbell() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    doorbell = Mock()
    data._doorbells_by_id = {"bell": doorbell}
    gateway.api.async_get_doorbell_detail = AsyncMock()

    with patch.object(data, "_async_update_device_detail", new=AsyncMock()) as inner:
        await data.refresh_camera_by_id("bell")

    inner.assert_awaited_once_with(doorbell, gateway.api.async_get_doorbell_detail)


@pytest.mark.asyncio
async def test_push_updates_connected_reflects_stream_state() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    assert data.push_updates_connected is False
    stream = Mock()
    stream.push_updates_connected = True
    data.activity_stream = stream
    assert data.push_updates_connected is True


@pytest.mark.asyncio
async def test_refresh_device_detail_by_id_short_circuits_on_shutdown() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    data._shutdown = True
    with patch.object(data, "_async_update_device_detail", new=AsyncMock()) as inner:
        await data._async_refresh_device_detail_by_id("dev")
    inner.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_device_detail_by_id_lock_path_restores_live_attrs() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    lock_id = "L1"
    lock_obj = Mock()
    data._locks_by_id = {lock_id: lock_obj}

    lock_detail = Mock(spec=LockDetail)
    lock_detail.door_state = "open"
    lock_detail.door_state_datetime = "dt1"
    lock_detail.lock_status = "locked"
    lock_detail.lock_status_datetime = "dt2"
    lock_detail.keypad = None
    data._device_detail_by_id = {lock_id: lock_detail}

    new_detail = Mock(spec=LockDetail)
    new_detail.door_state = "wrong"
    new_detail.door_state_datetime = "wrong"
    new_detail.lock_status = "wrong"
    new_detail.lock_status_datetime = "wrong"
    new_detail.keypad = None
    new_detail.offline_key = None

    stream = Mock()
    stream.push_updates_connected = True
    data.activity_stream = stream

    async def _update(device: Any, api_call: Any) -> None:
        data._device_detail_by_id[lock_id] = new_detail

    signals: list[str] = []
    with (
        patch.object(data, "_async_update_device_detail", side_effect=_update),
        patch.object(data, "async_signal_device_id_update", side_effect=signals.append),
    ):
        await data._async_refresh_device_detail_by_id(lock_id)

    # Live attrs were re-applied after the update overwrote them.
    assert new_detail.door_state == "open"
    assert new_detail.lock_status == "locked"
    assert signals == [lock_id]


@pytest.mark.asyncio
async def test_refresh_device_detail_by_id_lock_propagates_keypad_into_index() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    data._locks_by_id = {"L": Mock()}
    data.activity_stream = None  # so push_updates_connected branch is skipped

    keypad = Mock()
    keypad.device_id = "KP1"
    new_detail = Mock(spec=LockDetail)
    new_detail.keypad = keypad
    new_detail.offline_key = None
    data._device_detail_by_id = {"L": Mock(spec=LockDetail)}

    async def _update(device: Any, api_call: Any) -> None:
        data._device_detail_by_id["L"] = new_detail

    with (
        patch.object(data, "_async_update_device_detail", side_effect=_update),
        patch.object(data, "async_signal_device_id_update"),
    ):
        await data._async_refresh_device_detail_by_id("L")

    assert data._device_detail_by_id["KP1"] is keypad


@pytest.mark.asyncio
async def test_refresh_device_detail_by_id_doorbell_branch() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    doorbell = Mock()
    data._doorbells_by_id = {"B": doorbell}
    gateway.api.async_get_doorbell_detail = AsyncMock()

    with (
        patch.object(data, "_async_update_device_detail", new=AsyncMock()) as inner,
        patch.object(data, "async_signal_device_id_update") as signal,
    ):
        await data._async_refresh_device_detail_by_id("B")

    inner.assert_awaited_once_with(doorbell, gateway.api.async_get_doorbell_detail)
    signal.assert_called_once_with("B")


@pytest.mark.asyncio
async def test_async_update_device_detail_happy_path_stores_detail() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    device = Mock(device_id="d", device_name="Front")
    detail = Mock(spec=LockDetail)
    detail.offline_key = None
    api_call = AsyncMock(return_value=detail)

    await data._async_update_device_detail(device, api_call)

    api_call.assert_awaited_once_with("token", "d")
    assert data._device_detail_by_id["d"] is detail


@pytest.mark.asyncio
async def test_async_update_device_detail_invokes_offline_key_hook() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    data.async_offline_key_discovered = Mock()

    device = Mock(device_id="d", device_name="Front")
    detail = Mock(spec=LockDetail)
    detail.offline_key = "abc"
    api_call = AsyncMock(return_value=detail)

    await data._async_update_device_detail(device, api_call)

    data.async_offline_key_discovered.assert_called_once_with(detail)


@pytest.mark.asyncio
async def test_async_update_device_detail_returns_early_on_client_error(
    caplog: LogCaptureFixture,
) -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    device = Mock(device_id="d", device_name="Front")
    api_call = AsyncMock(side_effect=ClientError("net down"))

    with caplog.at_level(logging.ERROR):
        await data._async_update_device_detail(device, api_call)

    # Should not have stored anything because we bailed out.
    assert "d" not in data._device_detail_by_id
    assert "Request error trying to retrieve" in caplog.text


@pytest.mark.asyncio
async def test_get_device_and_get_device_name_resolve_both_indexes() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    lock = Mock(device_name="LockyMcLockface")
    doorbell = Mock(device_name="Belly")
    data._locks_by_id = {"L": lock}
    data._doorbells_by_id = {"B": doorbell}

    assert data.get_device("L") is lock
    assert data.get_device("B") is doorbell
    assert data.get_device("missing") is None
    assert data._get_device_name("L") == "LockyMcLockface"
    assert data._get_device_name("B") == "Belly"
    assert data._get_device_name("missing") is None


@pytest.mark.parametrize(
    ("method_name", "api_attr", "args", "returns_activities"),
    [
        ("async_lock", "async_lock_return_activities", (), True),
        ("async_unlock", "async_unlock_return_activities", (), True),
        ("async_unlatch", "async_unlatch_return_activities", (), True),
        ("async_lock_async", "async_lock_async", (True,), False),
        ("async_unlock_async", "async_unlock_async", (True,), False),
        ("async_unlatch_async", "async_unlatch_async", (True,), False),
    ],
)
@pytest.mark.asyncio
async def test_simple_lock_operations_delegate_to_api(
    method_name: str,
    api_attr: str,
    args: tuple[Any, ...],
    returns_activities: bool,
) -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    sentinel = ["activity"] if returns_activities else "request-id"
    api_method = AsyncMock(return_value=sentinel)
    setattr(gateway.api, api_attr, api_method)

    result = await getattr(data, method_name)("dev", *args)

    assert result == sentinel
    api_method.assert_awaited_once()


@pytest.mark.asyncio
async def test_status_async_wraps_underlying_call_with_rate_limit() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    gateway.api.async_status_async = AsyncMock(return_value="rid")

    with (
        patch(
            "yalexs.manager.data._RateLimitChecker.check_rate_limit", new=AsyncMock()
        ) as chk,
        patch(
            "yalexs.manager.data._RateLimitChecker.register_wakeup", new=AsyncMock()
        ) as reg,
    ):
        result = await data.async_status_async("dev", True)

    assert result == "rid"
    chk.assert_awaited_once_with("token")
    reg.assert_awaited_once_with("token")


@pytest.mark.asyncio
async def test_async_call_api_op_wraps_aiohttp_errors_with_device_name() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    data._locks_by_id = {"L": Mock(device_name="Front Door")}

    async def boom(*_: Any, **__: Any) -> None:
        raise AugustApiAIOHTTPError("nope")

    with pytest.raises(Exception) as exc_info:
        await data._async_call_api_op_requires_bridge("L", boom)
    assert "Front Door" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_call_api_op_falls_back_to_device_id_when_unknown() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    async def boom(*_: Any, **__: Any) -> None:
        raise AugustApiAIOHTTPError("nope")

    with pytest.raises(Exception) as exc_info:
        await data._async_call_api_op_requires_bridge("UNKNOWN", boom)
    assert "DeviceID: UNKNOWN" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_get_doorbell_image_happy_path() -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    doorbell = Mock()
    doorbell.async_get_doorbell_image = AsyncMock(return_value=b"png")
    data._device_detail_by_id = {"d": doorbell}

    session = Mock()
    result = await data.async_get_doorbell_image("d", session, timeout=2.0)

    assert result == b"png"
    doorbell.async_get_doorbell_image.assert_awaited_once_with(session, 2.0)


@pytest.mark.asyncio
async def test_async_get_doorbell_image_retries_on_token_expired_for_yale() -> None:
    """Yale brands refresh the content token and retry once."""
    gateway = _make_gateway(Brand.YALE_HOME)
    data = MockYaleXSData(gateway)
    first = Mock()
    first.async_get_doorbell_image = AsyncMock(side_effect=ContentTokenExpired)
    refreshed = Mock()
    refreshed.async_get_doorbell_image = AsyncMock(return_value=b"jpg")

    data._device_detail_by_id = {"d": first}

    async def _refresh(device_id: str) -> None:
        data._device_detail_by_id[device_id] = refreshed

    with patch.object(data, "refresh_camera_by_id", side_effect=_refresh) as ref:
        result = await data.async_get_doorbell_image("d", Mock())

    assert result == b"jpg"
    ref.assert_awaited_once_with("d")


@pytest.mark.asyncio
async def test_async_get_doorbell_image_reraises_for_non_yale_brand() -> None:
    gateway = _make_gateway(Brand.AUGUST)
    data = MockYaleXSData(gateway)
    doorbell = Mock()
    doorbell.async_get_doorbell_image = AsyncMock(side_effect=ContentTokenExpired)
    data._device_detail_by_id = {"d": doorbell}

    with pytest.raises(ContentTokenExpired):
        await data.async_get_doorbell_image("d", Mock())


@pytest.mark.asyncio
async def test_remove_inoperative_doorbells_drops_those_without_details(
    caplog: LogCaptureFixture,
) -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    bell_ok = Mock(device_id="ok", device_name="Front Bell")
    bell_missing = Mock(device_id="missing", device_name="Missing Bell")
    data._doorbells_by_id = {"ok": bell_ok, "missing": bell_missing}
    data._device_detail_by_id = {"ok": Mock()}

    with caplog.at_level(logging.INFO):
        data._remove_inoperative_doorbells()

    assert "ok" in data._doorbells_by_id
    assert "missing" not in data._doorbells_by_id
    assert "Missing Bell" in caplog.text


@pytest.mark.asyncio
async def test_remove_inoperative_locks_keeps_ones_with_bridge_drops_others(
    caplog: LogCaptureFixture,
) -> None:
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    keep = Mock(device_id="keep", device_name="WithBridge")
    no_detail = Mock(device_id="no_detail", device_name="NoDetail")
    no_bridge = Mock(device_id="no_bridge", device_name="NoBridge")
    data._locks_by_id = {
        "keep": keep,
        "no_detail": no_detail,
        "no_bridge": no_bridge,
    }
    keep_detail = Mock(spec=LockDetail, bridge=Mock())
    no_bridge_detail = Mock(spec=LockDetail, bridge=None)
    data._device_detail_by_id = {
        "keep": keep_detail,
        "no_bridge": no_bridge_detail,
    }

    with caplog.at_level(logging.INFO):
        data._remove_inoperative_locks()

    assert "keep" in data._locks_by_id
    assert "no_detail" not in data._locks_by_id
    assert "no_bridge" not in data._locks_by_id
    # When a lock has no bridge we also evict its detail entry.
    assert "no_bridge" not in data._device_detail_by_id
    assert "NoDetail" in caplog.text
    assert "NoBridge" in caplog.text


@pytest.mark.asyncio
async def test_async_push_message_catches_unexpected_exceptions(
    caplog: LogCaptureFixture,
) -> None:
    """Any exception bubbling out of _async_handle_push_message is swallowed and
    logged at ERROR with a traceback so a single bad message can't kill the
    push loop.
    """
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)

    with (
        patch.object(
            data, "_async_handle_push_message", side_effect=RuntimeError("kaboom")
        ),
        caplog.at_level(logging.ERROR),
    ):
        # Should NOT raise.
        data.async_push_message("dev", datetime.now(timezone.utc), {}, SOURCE_PUBNUB)

    assert "Error processing push message" in caplog.text
    assert "kaboom" in caplog.text


@pytest.mark.asyncio
async def test_async_stop_is_safe_when_nothing_was_initialized() -> None:
    """async_stop must tolerate having no activity_stream, no initial-sync task,
    and no push_unsub — i.e. cleanup called before setup completed.
    """
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    # All defaults: activity_stream=None, _initial_sync_task=None, _push_unsub=None
    await data.async_stop()
    assert data._shutdown is True


@pytest.mark.asyncio
async def test_async_handle_push_message_status_only_short_circuits() -> None:
    """When the device produces only is_status activities and state is unchanged,
    the for-loop body must be entered but exit via the early `return` (line 302)
    without scheduling any house refresh.
    """
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    device = Mock(device_id="d", house_id="h")
    data._device_detail_by_id = {"d": device}

    stream = Mock()
    stream.async_process_newer_device_activities = Mock(return_value=True)
    stream.async_schedule_house_id_refresh = Mock()
    data.activity_stream = stream

    status_activity = Mock(is_status=True)

    # Seed the state tracker so the next call detects "unchanged" and returns
    # before the for-loop that would schedule refreshes.
    state_key = f"d:{SOURCE_PUBNUB}"
    data._last_push_state[state_key] = {"lock": "locked", "door": "closed"}

    with (
        patch(
            "yalexs.manager.data.activities_from_pubnub_message",
            return_value=[status_activity],
        ),
        patch.object(data, "async_signal_device_id_update"),
    ):
        data._async_handle_push_message(
            "d",
            datetime.now(timezone.utc),
            {"status": "locked", "doorState": "closed"},
            SOURCE_PUBNUB,
        )

    stream.async_schedule_house_id_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_handle_push_message_logs_and_skips_status_activities_when_state_changed() -> (
    None
):
    """When the message represents a real (changed) state but the activities list
    contains a status update, that status entry is logged and `continue`d past
    while only non-status activities trigger a house refresh.
    """
    gateway = _make_gateway()
    data = MockYaleXSData(gateway)
    device = Mock(device_id="d", house_id="h")
    data._device_detail_by_id = {"d": device}

    stream = Mock()
    stream.async_process_newer_device_activities = Mock(return_value=True)
    stream.async_schedule_house_id_refresh = Mock()
    data.activity_stream = stream

    status_act = Mock(is_status=True)
    real_act = Mock(is_status=False)

    with (
        patch(
            "yalexs.manager.data.activities_from_pubnub_message",
            return_value=[status_act, real_act],
        ),
        patch.object(data, "async_signal_device_id_update"),
    ):
        data._async_handle_push_message(
            "d",
            datetime.now(timezone.utc),
            {"status": "locked", "doorState": "closed"},
            SOURCE_PUBNUB,
        )

    stream.async_schedule_house_id_refresh.assert_called_once_with("h")


def _make_bare_push_state_holder() -> Any:
    """Build a minimal object bound to YaleXSData._is_unchanged_push_state."""

    class _D:
        _is_unchanged_push_state = YaleXSData._is_unchanged_push_state

        def __init__(self) -> None:
            self._last_push_state: dict[str, Any] = {}

    return _D()


def test_is_unchanged_push_state_websocket_without_relevant_fields_is_processed() -> (
    None
):
    data = _make_bare_push_state_holder()
    assert (
        data._is_unchanged_push_state("d", {"unrelated": "x"}, SOURCE_WEBSOCKET, [])
        is False
    )


def test_is_unchanged_push_state_pubnub_without_relevant_fields_is_processed() -> None:
    data = _make_bare_push_state_holder()
    assert (
        data._is_unchanged_push_state("d", {"unrelated": "x"}, SOURCE_PUBNUB, [])
        is False
    )
