"""Tests for ``yalexs.pin`` covering accessor branches and repr."""

from __future__ import annotations

import datetime

from yalexs.pin import Pin


def _pin_data(**overrides):
    data = {
        "_id": "pin-1",
        "lockID": "lock-1",
        "userID": "user-1",
        "state": "in-use",
        "pin": "123456",
        "slot": 1,
        "accessType": "always",
        "firstName": "John",
        "lastName": "Doe",
        "unverified": False,
        "createdAt": "2018-01-01T01:02:03.000Z",
        "updatedAt": "2018-02-01T01:02:03.000Z",
        "loadedDate": "2018-03-01T01:02:03.000Z",
    }
    data.update(overrides)
    return data


def test_pin_basic_properties_and_optional_times_absent() -> None:
    """Without temporary-access fields, time accessors return None."""
    pin = Pin(_pin_data())

    assert pin.pin_id == "pin-1"
    assert pin.lock_id == "lock-1"
    assert pin.user_id == "user-1"
    assert pin.state == "in-use"
    assert pin.pin == "123456"
    assert pin.slot == 1
    assert pin.access_type == "always"
    assert pin.first_name == "John"
    assert pin.last_name == "Doe"
    assert pin.unverified is False

    assert pin.created_at == datetime.datetime(
        2018, 1, 1, 1, 2, 3, tzinfo=datetime.timezone.utc
    )
    assert pin.updated_at == datetime.datetime(
        2018, 2, 1, 1, 2, 3, tzinfo=datetime.timezone.utc
    )
    assert pin.loaded_date == datetime.datetime(
        2018, 3, 1, 1, 2, 3, tzinfo=datetime.timezone.utc
    )

    # Missing temporary-access fields take the falsy short-circuit branch.
    assert pin.access_start_time is None
    assert pin.access_end_time is None
    assert pin.access_times is None


def test_pin_temporary_access_times_parse_when_present() -> None:
    """When the optional access-time fields are set, they parse to datetimes."""
    pin = Pin(
        _pin_data(
            accessStartTime="2018-01-01T01:01:01.563Z",
            accessEndTime="2018-12-01T01:01:01.563Z",
            accessTimes="2018-11-05T10:02:41.684Z",
        )
    )

    assert pin.access_start_time == datetime.datetime(
        2018, 1, 1, 1, 1, 1, 563000, tzinfo=datetime.timezone.utc
    )
    assert pin.access_end_time == datetime.datetime(
        2018, 12, 1, 1, 1, 1, 563000, tzinfo=datetime.timezone.utc
    )
    assert pin.access_times == datetime.datetime(
        2018, 11, 5, 10, 2, 41, 684000, tzinfo=datetime.timezone.utc
    )


def test_pin_repr_includes_id_and_names() -> None:
    """__repr__ surfaces the identifying fields used in debug logs."""
    pin = Pin(_pin_data(firstName="Alice", lastName="Smith"))

    rep = repr(pin)
    assert rep == "Pin(id=pin-1 firstName=Alice, lastName=Smith)"
