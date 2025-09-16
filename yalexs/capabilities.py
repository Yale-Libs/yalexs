"""Device capabilities type definitions."""

from typing import Any, TypedDict


class LockCapabilities(TypedDict, total=False):
    """TypedDict for lock capabilities."""

    concurrentBLE: int
    batteryType: str
    doorSense: bool
    hasMagnetometer: bool
    hasIntegratedWiFi: bool
    scheduledSmartAlerts: bool
    standalone: bool
    bluetooth: bool
    slotRange: Any  # Can be None or other values
    integratedKeypad: bool
    entryCodeSlots: bool
    pinSlotMax: int
    pinSlotMin: int
    supportsRFID: bool
    supportsRFIDLegacy: bool
    supportsRFIDCredential: bool
    supportsRFIDOnlyAccess: bool
    supportsRFIDWithCode: bool
    supportsSecureMode: bool
    supportsSecureModeCodeDisable: bool
    supportsSecureModeMobileControl: bool
    supportsFingerprintCredential: bool
    supportsDeliveryMode: bool
    supportsSchedulePerUser: bool
    supportsFingerprintOnlyAccess: bool
    batteryLifeMS: int
    supportedPartners: list[str]
    unlatch: bool


class CapabilitiesResponse(TypedDict, total=False):
    """TypedDict for the full capabilities API response."""

    lock: LockCapabilities
