"""Tests for device capabilities functionality."""

from typing import Any

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses

from yalexs.api_async import ApiAsync
from yalexs.api_common import API_GET_CAPABILITIES_URL, ApiCommon
from yalexs.capabilities import CapabilitiesResponse
from yalexs.const import DEFAULT_BRAND
from yalexs.lock import LockDetail

ACCESS_TOKEN = "test-token"


@pytest.mark.asyncio
async def test_async_get_device_capabilities() -> None:
    """Test fetching device capabilities from the API."""
    capabilities_response: CapabilitiesResponse = {
        "lock": {
            "concurrentBLE": 2,
            "batteryType": "AA",
            "doorSense": True,
            "hasMagnetometer": False,
            "hasIntegratedWiFi": False,
            "scheduledSmartAlerts": True,
            "standalone": False,
            "bluetooth": True,
            "slotRange": None,
            "integratedKeypad": True,
            "entryCodeSlots": True,
            "pinSlotMax": 100,
            "pinSlotMin": 1,
            "supportsRFID": True,
            "supportsRFIDLegacy": False,
            "supportsRFIDCredential": True,
            "supportsRFIDOnlyAccess": True,
            "supportsRFIDWithCode": False,
            "supportsSecureMode": False,
            "supportsSecureModeCodeDisable": False,
            "supportsSecureModeMobileControl": False,
            "supportsFingerprintCredential": True,
            "supportsDeliveryMode": False,
            "supportsSchedulePerUser": True,
            "supportsFingerprintOnlyAccess": True,
            "batteryLifeMS": 21513600000,
            "supportedPartners": [],
            "unlatch": True,
        }
    }

    serial_number = "TEST123"

    with aioresponses() as mock:
        mock.get(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_CAPABILITIES_URL)
            + f"?serialNumber={serial_number}&topLevelHost=true",
            payload=capabilities_response,
        )

        async with ClientSession() as session:
            api = ApiAsync(session)
            capabilities = await api.async_get_lock_capabilities(
                ACCESS_TOKEN, serial_number
            )

            assert capabilities == capabilities_response
            assert capabilities["lock"]["unlatch"] is True


def test_lock_detail_unlatch_supported_with_capabilities() -> None:
    """Test that LockDetail uses capabilities for unlatch_supported when available."""
    lock_data: dict[str, Any] = {
        "LockID": "test-lock-id",
        "LockName": "Test Lock",
        "HouseID": "test-house",
        "SerialNumber": "ABC123",
        "currentFirmwareVersion": "1.0.0",
        "Type": 5,  # Type that doesn't normally support unlatch
        "battery": 0.85,
        "LockStatus": {"status": "locked", "doorState": "closed"},
    }

    # Create lock detail without capabilities
    lock_detail = LockDetail(lock_data)

    # Should be False based on Type
    assert lock_detail.unlatch_supported is False

    # Set capabilities that indicate unlatch is supported
    capabilities: CapabilitiesResponse = {
        "lock": {
            "unlatch": True,
            "doorSense": True,
            "batteryType": "AA",
        }
    }
    lock_detail.set_capabilities(capabilities)

    # Now should be True based on capabilities
    assert lock_detail.unlatch_supported is True


def test_lock_detail_unlatch_supported_fallback_to_type() -> None:
    """Test that LockDetail falls back to Type-based check when no capabilities."""
    lock_data: dict[str, Any] = {
        "LockID": "test-lock-id",
        "LockName": "Test Lock",
        "HouseID": "test-house",
        "SerialNumber": "ABC123",
        "currentFirmwareVersion": "1.0.0",
        "Type": 17,  # Type 17 supports unlatch
        "battery": 0.85,
        "LockStatus": {"status": "locked", "doorState": "closed"},
    }

    # Create lock detail without capabilities
    lock_detail = LockDetail(lock_data)

    # Should be True based on Type 17
    assert lock_detail.unlatch_supported is True


def test_lock_detail_unlatch_supported_capabilities_override() -> None:
    """Test that capabilities override Type-based unlatch support."""
    lock_data: dict[str, Any] = {
        "LockID": "test-lock-id",
        "LockName": "Test Lock",
        "HouseID": "test-house",
        "SerialNumber": "ABC123",
        "currentFirmwareVersion": "1.0.0",
        "Type": 17,  # Type 17 normally supports unlatch
        "battery": 0.85,
        "LockStatus": {"status": "locked", "doorState": "closed"},
    }

    # Create lock detail
    lock_detail = LockDetail(lock_data)

    # Should be True based on Type 17
    assert lock_detail.unlatch_supported is True

    # Set capabilities that indicate unlatch is NOT supported
    capabilities: CapabilitiesResponse = {
        "lock": {
            "unlatch": False,  # Override: not supported
            "doorSense": True,
            "batteryType": "AA",
        }
    }
    lock_detail.set_capabilities(capabilities)

    # Now should be False based on capabilities override
    assert lock_detail.unlatch_supported is False


def test_lock_detail_set_capabilities() -> None:
    """Test setting capabilities on a lock detail."""
    lock_data: dict[str, Any] = {
        "LockID": "test-lock-id",
        "LockName": "Test Lock",
        "HouseID": "test-house",
        "SerialNumber": "ABC123",
        "currentFirmwareVersion": "1.0.0",
        "Type": 5,
        "battery": 0.85,
        "LockStatus": {"status": "locked", "doorState": "closed"},
    }

    lock_detail = LockDetail(lock_data)

    # Initially no capabilities
    assert lock_detail._capabilities is None

    # Set capabilities
    capabilities: CapabilitiesResponse = {
        "lock": {
            "unlatch": True,
            "doorSense": True,
            "batteryType": "AA",
            "pinSlotMax": 100,
            "pinSlotMin": 1,
        }
    }
    lock_detail.set_capabilities(capabilities)

    # Verify capabilities are stored
    assert lock_detail._capabilities == capabilities
    assert lock_detail._capabilities["lock"]["unlatch"] is True
