"""Test the manager data module."""

import logging
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiohttp import ClientError, ClientResponseError

from yalexs.activity import SOURCE_PUBNUB, SOURCE_WEBSOCKET
from yalexs.capabilities import CapabilitiesResponse
from yalexs.const import Brand
from yalexs.exceptions import YaleApiError
from yalexs.lock import LockDetail, LockOperation
from yalexs.manager.data import YaleXSData


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
                device_id, datetime.now(), message, SOURCE_PUBNUB
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
