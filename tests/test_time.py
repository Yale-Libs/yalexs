"""Tests for yalexs.time."""

import datetime

import pytest

from yalexs.time import epoch_to_datetime, parse_datetime


def test_epoch_to_datetime_returns_naive_local_datetime():
    result = epoch_to_datetime(0)
    assert isinstance(result, datetime.datetime)
    assert result.tzinfo is None


def test_parse_datetime_iso_uses_ciso8601():
    result = parse_datetime("2024-01-15T12:34:56Z")
    assert isinstance(result, datetime.datetime)
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


def test_parse_datetime_non_iso_falls_back_to_dateutil():
    # ciso8601 raises ValueError on non-ISO formats; dateutil handles them.
    result = parse_datetime("January 15, 2024 12:34:56")
    assert isinstance(result, datetime.datetime)
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


def test_parse_datetime_invalid_raises():
    # Both parsers should fail on garbage input.
    with pytest.raises((ValueError, TypeError)):
        parse_datetime("not a date at all xyz")
