"""Tests for yalexs.api_common.

Coverage sweep targeting untested request builders, alarm processors,
debug branches, and brand-config gated cached properties.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from yalexs.alarm import Alarm, AlarmDevice, ArmState
from yalexs.api_common import (
    API_GET_ALARM_DEVICES_URL,
    API_GET_ALARMS_URL,
    API_GET_HOUSE_URL,
    API_GET_HOUSES_URL,
    API_PUT_ALARM_URL,
    API_SEND_VERIFICATION_CODE_URLS,
    API_WAKEUP_DOORBELL_URL,
    API_WEBSOCKET_SUBSCRIBERS,
    API_WEBSOCKET_SUBSCRIBERS_WITH_SUBSCRIBER_ID,
    ApiCommon,
    _activity_from_dict,
    _process_activity_json,
    _process_alarm_devices_json,
    _process_alarms_json,
)
from yalexs.const import BASE_URLS, Brand


def _alarm_data(**overrides: Any) -> dict[str, Any]:
    data = {
        "location": "Main House",
        "houseID": "house-1",
        "pubsubChannel": "chan-abc",
        "serialNumber": "SN12345",
        "status": "ARMED",
        "areaIDs": ["area-1", "area-2"],
    }
    data.update(overrides)
    return data


def _alarm_device_data(**overrides: Any) -> dict[str, Any]:
    data = {
        "_id": "dev-1",
        "name": "Front Sensor",
        "alarmID": "alarm-1",
        "serialNumber": "DEV-SN",
        "type": "ContactSensor",
        "pubsubChannel": "chan-dev",
        "status": {
            "firmwareVersion": "1.2.3",
            "online": True,
            "contactOpen": False,
            "fault": False,
            "tamperOpen": False,
            "lowBattery": False,
        },
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def test_activity_from_dict_unknown_action_with_debug(caplog):
    """Unknown action should log 'Unknown activity' when debug=True."""
    caplog.set_level(logging.DEBUG)
    result = _activity_from_dict("source", {"action": "totally_made_up"}, debug=True)
    assert result is None
    assert any("Unknown activity" in r.message for r in caplog.records)


def test_activity_from_dict_known_action_with_debug(caplog):
    """Known action should log 'Processing activity' and return an instance."""
    caplog.set_level(logging.DEBUG)
    # `lock` is a known action mapped to LockOperationActivity
    activity_dict = {
        "action": "lock",
        "dateTime": 1700000000000,
        "deviceID": "lock-1",
        "deviceType": "lock",
        "info": {},
    }
    result = _activity_from_dict("source-x", activity_dict, debug=True)
    assert result is not None
    assert any("Processing activity" in r.message for r in caplog.records)


def test_activity_from_dict_unknown_action_no_debug(caplog):
    """When debug=False the debug-branch logging must NOT fire."""
    caplog.set_level(logging.DEBUG)
    result = _activity_from_dict("source", {"action": "still_made_up"}, debug=False)
    assert result is None
    # Neither "Processing activity" nor "Unknown activity" logged
    assert not any(
        "Processing activity" in r.message or "Unknown activity" in r.message
        for r in caplog.records
    )


def test_process_activity_json_events_key_unwrap():
    """Payloads with an 'events' key should be unwrapped before processing."""
    payload = {
        "events": [
            {
                "action": "lock",
                "dateTime": 1700000000000,
                "deviceID": "lock-1",
                "deviceType": "lock",
                "info": {},
            },
            {"action": "unknown_action_skip_me"},
        ]
    }
    activities = _process_activity_json(payload)
    # Only the known activity is returned, the unknown one is filtered out
    assert len(activities) == 1


def test_process_activity_json_plain_list():
    """Payloads without 'events' should be iterated directly."""
    payload = [
        {
            "action": "unlock",
            "dateTime": 1700000000000,
            "deviceID": "lock-1",
            "deviceType": "lock",
            "info": {},
        }
    ]
    activities = _process_activity_json(payload)
    assert len(activities) == 1


def test_process_alarms_json():
    raw = [_alarm_data(houseID="house-A"), _alarm_data(location="Cottage")]
    raw[0]["alarmID"] = "alarm-A"
    raw[1]["alarmID"] = "alarm-B"
    alarms = _process_alarms_json(raw)
    assert len(alarms) == 2
    assert all(isinstance(a, Alarm) for a in alarms)
    assert alarms[0].device_id == "alarm-A"
    assert alarms[1].device_id == "alarm-B"


def test_process_alarm_devices_json():
    raw = [_alarm_device_data(), _alarm_device_data(_id="dev-2", name="Back Sensor")]
    devices = _process_alarm_devices_json(raw)
    assert len(devices) == 2
    assert all(isinstance(d, AlarmDevice) for d in devices)
    assert devices[0].device_id == "dev-1"
    assert devices[1].device_id == "dev-2"


# ---------------------------------------------------------------------------
# ApiCommon — brand-gated cached properties
# ---------------------------------------------------------------------------


@pytest.fixture
def api_global() -> ApiCommon:
    """OAuth+alarm-enabled brand (per project learnings, the canonical fixture)."""
    return ApiCommon(Brand.YALE_GLOBAL)


@pytest.fixture
def api_august() -> ApiCommon:
    return ApiCommon(Brand.AUGUST)


def test_brand_supports_alarms_true(api_global: ApiCommon) -> None:
    assert api_global.brand_supports_alarms is True


def test_brand_supports_alarms_false(api_august: ApiCommon) -> None:
    assert api_august.brand_supports_alarms is False


def test_brand_supports_doorbells(api_august: ApiCommon, api_global: ApiCommon) -> None:
    # Sanity: both AUGUST and YALE_GLOBAL support doorbells
    assert api_august.brand_supports_doorbells is True
    assert api_global.brand_supports_doorbells is True


# ---------------------------------------------------------------------------
# ApiCommon — request builders
# ---------------------------------------------------------------------------


def test_build_send_verification_code_request_email(api_global: ApiCommon) -> None:
    req = api_global._build_send_verification_code_request(
        "token", "email", "user@example.com"
    )
    assert req["method"] == "post"
    assert req["url"].endswith(API_SEND_VERIFICATION_CODE_URLS["email"])
    assert req["json"] == {"value": "user@example.com"}
    # Email branch does NOT add smsHashString
    assert "smsHashString" not in req["json"]


def test_build_send_verification_code_request_phone(api_global: ApiCommon) -> None:
    req = api_global._build_send_verification_code_request(
        "token", "phone", "+15555550100"
    )
    assert req["json"]["value"] == "+15555550100"
    assert req["json"]["smsHashString"] == "anY0ZsRmXw+"


def test_build_wakeup_doorbell_request(api_global: ApiCommon) -> None:
    req = api_global._build_wakeup_doorbell_request("token", "doorbell-99")
    assert req["method"] == "get"
    assert req["access_token"] == "token"
    assert req["url"] == api_global.get_brand_url(
        API_WAKEUP_DOORBELL_URL.format(doorbell_id="doorbell-99")
    )


def test_build_get_houses_request(api_global: ApiCommon) -> None:
    req = api_global._build_get_houses_request("token")
    assert req["method"] == "get"
    assert req["access_token"] == "token"
    assert req["url"].endswith(API_GET_HOUSES_URL)


def test_build_get_house_request(api_global: ApiCommon) -> None:
    req = api_global._build_get_house_request("token", "house-42")
    assert req["method"] == "get"
    assert req["url"] == api_global.get_brand_url(
        API_GET_HOUSE_URL.format(house_id="house-42")
    )


def test_build_websocket_subscribe_request(api_global: ApiCommon) -> None:
    req = api_global._build_websocket_subscribe_request("token")
    assert req["method"] == "post"
    assert req["access_token"] == "token"
    assert req["url"].endswith(API_WEBSOCKET_SUBSCRIBERS)
    assert req["json"] == {"scopes": ["lock"]}


def test_build_websocket_get_request(api_global: ApiCommon) -> None:
    req = api_global._build_websocket_get_request("token", "sub-id-1")
    assert req["method"] == "get"
    assert req["access_token"] == "token"
    assert req["url"] == api_global.get_brand_url(
        API_WEBSOCKET_SUBSCRIBERS_WITH_SUBSCRIBER_ID.format(subscriber_id="sub-id-1")
    )


def test_build_websocket_delete_request(api_global: ApiCommon) -> None:
    req = api_global._build_websocket_delete_request("token", "sub-id-2")
    assert req["method"] == "delete"
    assert req["access_token"] == "token"
    assert req["url"].endswith("/websocket/subscribers/sub-id-2")


def test_build_get_alarms_request(api_global: ApiCommon) -> None:
    req = api_global._build_get_alarms_request("token")
    assert req["method"] == "get"
    assert req["access_token"] == "token"
    assert req["url"].endswith(API_GET_ALARMS_URL)


def test_build_get_alarm_devices_request(api_global: ApiCommon) -> None:
    req = api_global._build_get_alarm_devices_request("token", "alarm-77")
    assert req["method"] == "get"
    assert req["url"] == api_global.get_brand_url(
        API_GET_ALARM_DEVICES_URL.format(alarm_id="alarm-77")
    )


def test_build_call_alarm_state_request(api_global: ApiCommon) -> None:
    alarm = Alarm("alarm-77", _alarm_data(areaIDs=["a", "b"]))
    req = api_global._build_call_alarm_state_request("token", alarm, ArmState.Away)
    assert req["method"] == "PUT"
    assert req["access_token"] == "token"
    assert req["url"] == api_global.get_brand_url(
        API_PUT_ALARM_URL.format(alarm_id="alarm-77", arm_state=ArmState.Away)
    )
    assert req["json"] == {"areaIDs": ["a", "b"]}


def test_get_brand_url_uses_brand_base_url(api_global: ApiCommon) -> None:
    assert api_global.get_brand_url("/x") == f"{BASE_URLS[Brand.YALE_GLOBAL]}/x"
