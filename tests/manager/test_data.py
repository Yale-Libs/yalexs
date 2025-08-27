"""Test the manager data module."""

import logging
from datetime import datetime
from unittest.mock import Mock, patch

from yalexs.activity import SOURCE_PUBNUB, SOURCE_WEBSOCKET
from yalexs.manager.data import YaleXSData


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
