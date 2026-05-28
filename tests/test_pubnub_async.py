"""Tests for the AugustPubNub callback layer."""

from __future__ import annotations

import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pubnub.enums import PNStatusCategory

from yalexs.pubnub_async import AugustPubNub


def _make_status(category: PNStatusCategory) -> SimpleNamespace:
    """Build a minimal PNStatus-like object with the attrs we log."""
    return SimpleNamespace(
        category=category,
        error_data=None,
        error=None,
        status_code=200,
        operation="test",
    )


def _make_message(channel: str, payload: dict, timetoken: int = 16_000_000_000_000_000):
    """Build a minimal PNMessageResult-like object."""
    return SimpleNamespace(
        channel=channel,
        message=payload,
        timetoken=timetoken,
        subscription=None,
        user_metadata=None,
        publisher=None,
    )


def _make_device(channel: str | None, device_id: str = "DEV1") -> SimpleNamespace:
    """Build a minimal DeviceDetail-like object."""
    return SimpleNamespace(pubsub_channel=channel, device_id=device_id)


def test_register_device_with_channel():
    pn = AugustPubNub()
    pn.register_device(_make_device("ch-1", "DEV1"))
    assert list(pn.channels) == ["ch-1"]


def test_register_device_without_channel_is_ignored():
    pn = AugustPubNub()
    pn.register_device(_make_device(None, "DEV1"))
    assert list(pn.channels) == []


def test_subscribe_and_unsubscribe_roundtrip():
    pn = AugustPubNub()
    cb = MagicMock()
    unsub = pn.subscribe(cb)
    assert cb in pn._subscriptions
    unsub()
    assert cb not in pn._subscriptions


def test_message_on_registered_channel_calls_subscribers():
    pn = AugustPubNub()
    pn.register_device(_make_device("ch-1", "DEV1"))
    cb = MagicMock()
    pn.subscribe(cb)

    payload = {"status": "locked"}
    pn.message(MagicMock(), _make_message("ch-1", payload))

    cb.assert_called_once()
    device_id, when, body = cb.call_args.args
    assert device_id == "DEV1"
    assert body is payload
    assert isinstance(when, datetime.datetime)
    assert when.tzinfo is datetime.timezone.utc


def test_message_timetoken_is_converted_to_utc_datetime():
    pn = AugustPubNub()
    pn.register_device(_make_device("ch-1", "DEV1"))
    cb = MagicMock()
    pn.subscribe(cb)

    # timetoken is 100-nanosecond intervals since UNIX epoch
    pn.message(MagicMock(), _make_message("ch-1", {}, timetoken=17_500_000_000_000_000))

    _, when, _ = cb.call_args.args
    expected = datetime.datetime.fromtimestamp(
        17_500_000_000_000_000 / 10_000_000, tz=datetime.timezone.utc
    )
    assert when == expected


def test_message_on_unknown_channel_is_dropped(caplog):
    """Regression test: a message on a channel we never registered must not raise."""
    pn = AugustPubNub()
    cb = MagicMock()
    pn.subscribe(cb)

    with caplog.at_level("DEBUG", logger="yalexs.pubnub_async"):
        pn.message(MagicMock(), _make_message("not-registered", {"foo": "bar"}))

    cb.assert_not_called()
    assert any("unknown channel" in rec.message for rec in caplog.records)


def test_status_falsy_pubnub_marks_disconnected():
    pn = AugustPubNub()
    pn.connected = True
    pn.status(None, _make_status(PNStatusCategory.PNConnectedCategory))
    assert pn.connected is False


def test_status_connected_category_marks_connected():
    pn = AugustPubNub()
    pn.status(MagicMock(), _make_status(PNStatusCategory.PNConnectedCategory))
    assert pn.connected is True


def test_status_should_reconnect_calls_reconnect():
    pn = AugustPubNub()
    pn.connected = True
    pubnub = MagicMock()

    pn.status(pubnub, _make_status(PNStatusCategory.PNNetworkIssuesCategory))

    assert pn.connected is False
    pubnub.reconnect.assert_called_once()


@pytest.mark.parametrize(
    "category",
    [
        PNStatusCategory.PNUnknownCategory,
        PNStatusCategory.PNUnexpectedDisconnectCategory,
        PNStatusCategory.PNNetworkIssuesCategory,
        PNStatusCategory.PNTimeoutCategory,
    ],
)
def test_status_all_reconnect_categories(category):
    pn = AugustPubNub()
    pubnub = MagicMock()
    pn.status(pubnub, _make_status(category))
    assert pn.connected is False
    pubnub.reconnect.assert_called_once()


def test_status_reconnected_fires_empty_refresh_for_every_device():
    """Regression test for Py3.10: datetime.UTC does not exist on 3.10."""
    pn = AugustPubNub()
    pn.register_device(_make_device("ch-1", "DEV1"))
    pn.register_device(_make_device("ch-2", "DEV2"))
    cb = MagicMock()
    pn.subscribe(cb)

    pn.status(MagicMock(), _make_status(PNStatusCategory.PNReconnectedCategory))

    assert pn.connected is True
    assert cb.call_count == 2
    devices_called = {call.args[0] for call in cb.call_args_list}
    assert devices_called == {"DEV1", "DEV2"}
    for call in cb.call_args_list:
        _, when, body = call.args
        assert body == {}
        assert isinstance(when, datetime.datetime)
        assert when.tzinfo is datetime.timezone.utc


def test_presence_only_logs(caplog):
    pn = AugustPubNub()
    with caplog.at_level("DEBUG", logger="yalexs.pubnub_async"):
        pn.presence(MagicMock(), {"event": "join"})
    assert any("presence" in rec.message.lower() for rec in caplog.records)


def test_channels_property_reflects_registration():
    pn = AugustPubNub()
    assert list(pn.channels) == []
    pn.register_device(_make_device("ch-a", "A"))
    pn.register_device(_make_device("ch-b", "B"))
    assert set(pn.channels) == {"ch-a", "ch-b"}
