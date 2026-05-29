"""Tests for yalexs.backports.enum.StrEnum."""

from enum import auto

import pytest

from yalexs.backports.enum import StrEnum


class _Color(StrEnum):
    RED = "red"
    BLUE = "blue"


def test_strenum_stores_string_value():
    assert _Color.RED.value == "red"
    assert str(_Color.RED) == "red"


def test_strenum_rejects_non_string_value():
    with pytest.raises(TypeError, match="is not a string"):

        class _Bad(StrEnum):
            X = 1  # type: ignore[assignment]


def test_strenum_auto_unsupported():
    with pytest.raises(TypeError, match="auto"):

        class _AutoEnum(StrEnum):
            A = auto()
