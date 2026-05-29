"""Tests for ``yalexs.doorbell`` covering the long-tail branches."""

from __future__ import annotations

import datetime
import json
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from yalexs.doorbell import Doorbell, DoorbellDetail
from yalexs.exceptions import ContentTokenExpired


def load_fixture(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as fptr:
        return fptr.read()


def _doorbell_summary() -> dict:
    """Pick one entry from get_doorbells.json — the keyed summary format."""
    data = json.loads(load_fixture("get_doorbells.json"))
    return next(iter(data.values()))


def test_doorbell_status_helpers_and_repr() -> None:
    """Doorbell exposes status, is_online/is_standby, content_token, repr."""
    payload = _doorbell_summary()
    payload["contentToken"] = "tok-abc"

    doorbell = Doorbell("did-1", payload)

    assert doorbell.status == "doorbell_call_status_online"
    assert doorbell.is_online is True
    assert doorbell.is_standby is False
    assert doorbell.content_token == "tok-abc"
    rep = repr(doorbell)
    assert "Doorbell(" in rep and "did-1" in rep

    payload["status"] = "standby"
    standby = Doorbell("did-2", payload)
    assert standby.is_standby is True
    assert standby.is_online is False


def test_doorbell_detail_battery_soc_takes_precedence() -> None:
    """When ``battery_soc`` is present the raw value is used as percentage."""
    data = json.loads(load_fixture("get_doorbell.battery_full.json"))
    data["telemetry"] = {"battery_soc": 42}

    detail = DoorbellDetail(data)

    assert detail.battery_level == 42


def test_doorbell_detail_battery_thresholds_75_50_25() -> None:
    """Battery voltage thresholds map to the documented percentage buckets."""
    base = json.loads(load_fixture("get_doorbell.battery_full.json"))

    for voltage, expected in ((3.80, 75), (3.55, 50), (3.20, 25)):
        data = json.loads(json.dumps(base))
        data["telemetry"] = {"battery": voltage}
        assert DoorbellDetail(data).battery_level == expected


def test_doorbell_detail_battery_level_none_when_no_signal() -> None:
    """Detail leaves battery_level None when telemetry is absent or empty."""
    base = json.loads(load_fixture("get_doorbell.battery_full.json"))

    no_telemetry = json.loads(json.dumps(base))
    no_telemetry.pop("telemetry", None)
    assert DoorbellDetail(no_telemetry).battery_level is None

    empty_telemetry = json.loads(json.dumps(base))
    empty_telemetry["telemetry"] = {}
    assert DoorbellDetail(empty_telemetry).battery_level is None


def test_doorbell_detail_image_created_at_setter_rejects_non_date() -> None:
    """The image_created_at_datetime setter validates the input type."""
    detail = DoorbellDetail(json.loads(load_fixture("get_doorbell.battery_full.json")))

    with pytest.raises(ValueError):
        detail.image_created_at_datetime = "not-a-date"

    now = datetime.datetime(2026, 5, 28, 12, 0, 0, tzinfo=datetime.timezone.utc)
    detail.image_created_at_datetime = now
    assert detail.image_created_at_datetime == now


@pytest.mark.asyncio
async def test_doorbell_detail_async_image_raises_on_401() -> None:
    """Async image fetch translates HTTP 401 to ContentTokenExpired."""
    detail = DoorbellDetail(json.loads(load_fixture("get_doorbell.battery_full.json")))
    detail.image_url = "https://example.invalid/img.jpg"
    detail.content_token = ""  # exercise the ``or ""`` fallback branch

    response = MagicMock()
    response.status = 401
    response.read = AsyncMock(return_value=b"")

    session = MagicMock()
    session.request = AsyncMock(return_value=response)

    with pytest.raises(ContentTokenExpired):
        await detail.async_get_doorbell_image(session)

    session.request.assert_awaited_once()
    _, kwargs = session.request.call_args
    assert kwargs["headers"] == {"Authorization": ""}
