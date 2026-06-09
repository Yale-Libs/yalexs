"""Tests for ``yalexs.bridge`` covering BridgeDetail and BridgeStatusDetail."""

from __future__ import annotations

from yalexs.bridge import BridgeDetail, BridgeStatus, BridgeStatusDetail


def _bridge_data(**overrides):
    data = {
        "_id": "bridge-1",
        "firmwareVersion": "2.10.0",
        "operative": True,
        "hyperBridge": True,
        "status": {
            "current": "online",
            "updated": "2026-05-28T12:00:00.000Z",
            "lastOnline": "2026-05-28T12:00:00.000Z",
            "lastOffline": "2026-05-27T18:00:00.000Z",
        },
    }
    data.update(overrides)
    return data


def test_bridge_detail_exposes_status_and_flags() -> None:
    """BridgeDetail surfaces operative, hyperBridge and a nested BridgeStatusDetail."""
    bridge = BridgeDetail("house-1", _bridge_data())

    assert bridge.device_id == "bridge-1"
    assert bridge.house_id == "house-1"
    assert bridge.firmware_version == "2.10.0"
    assert bridge.operative is True
    assert bridge.hyper_bridge is True

    assert isinstance(bridge.status, BridgeStatusDetail)
    assert bridge.status.current is BridgeStatus.ONLINE


def test_bridge_detail_status_is_none_when_payload_omits_it() -> None:
    """A bridge payload without a ``status`` key leaves the status attribute None."""
    bridge = BridgeDetail(
        "house-1",
        {
            "_id": "bridge-2",
            "firmwareVersion": "2.10.0",
            "operative": False,
        },
    )

    assert bridge.status is None
    assert bridge.operative is False
    # ``hyperBridge`` defaults to False when the payload omits it.
    assert bridge.hyper_bridge is False


def test_bridge_detail_optional_fields_are_none() -> None:
    """Bridges carry no name, serial number or pubsub channel.

    ``BridgeDetail`` passes ``None`` for these to ``DeviceDetail.__init__``,
    so the public accessors must surface ``None`` rather than a string. This
    guards the ``str | None`` contract relied on by typed consumers.
    """
    bridge = BridgeDetail("house-1", _bridge_data())

    assert bridge.device_name is None
    assert bridge.serial_number is None
    assert bridge.pubsub_channel is None


def test_bridge_status_detail_unknown_when_current_missing_or_offline() -> None:
    """Anything other than ``current == "online"`` maps to UNKNOWN at construction."""
    assert BridgeStatusDetail({}).current is BridgeStatus.UNKNOWN
    assert BridgeStatusDetail({"current": "offline"}).current is BridgeStatus.UNKNOWN


def test_bridge_status_detail_timestamps_pass_through() -> None:
    """The updated / last_online / last_offline accessors return the raw values."""
    status = BridgeStatusDetail(
        {
            "current": "online",
            "updated": "2026-05-28T12:00:00.000Z",
            "lastOnline": "2026-05-28T12:00:00.000Z",
            "lastOffline": "2026-05-27T18:00:00.000Z",
        }
    )

    assert status.updated == "2026-05-28T12:00:00.000Z"
    assert status.last_online == "2026-05-28T12:00:00.000Z"
    assert status.last_offline == "2026-05-27T18:00:00.000Z"


def test_bridge_status_detail_timestamps_default_to_none() -> None:
    """Missing timestamp keys leave the cached properties as None."""
    status = BridgeStatusDetail({"current": "online"})

    assert status.updated is None
    assert status.last_online is None
    assert status.last_offline is None


def test_bridge_status_set_online_toggles_current() -> None:
    """set_online flips the cached current state on the status detail."""
    bridge = BridgeDetail("house-1", _bridge_data())
    assert bridge.status.current is BridgeStatus.ONLINE

    bridge.set_online(False)
    assert bridge.status.current is BridgeStatus.OFFLINE

    bridge.set_online(True)
    assert bridge.status.current is BridgeStatus.ONLINE
