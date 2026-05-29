"""Tests for yalexs.users module."""

from yalexs.users import USER_CACHE, YaleUser, cache_user_info, get_user_info


def test_yale_user_all_accessors():
    user = YaleUser(
        "uuid-1",
        {
            "FirstName": "Ada",
            "LastName": "Lovelace",
            "UserType": "owner",
            "imageInfo": {
                "thumbnail": {"secure_url": "https://example.com/thumb.jpg"},
                "original": {"secure_url": "https://example.com/full.jpg"},
            },
        },
    )
    assert user.first_name == "Ada"
    assert user.last_name == "Lovelace"
    assert user.user_type == "owner"
    assert user.thumbnail_url == "https://example.com/thumb.jpg"
    assert user.image_url == "https://example.com/full.jpg"


def test_yale_user_missing_fields_returns_none():
    user = YaleUser("uuid-2", {})
    assert user.first_name is None
    assert user.last_name is None
    assert user.user_type is None
    assert user.thumbnail_url is None
    assert user.image_url is None


def test_cache_user_info_dedupes():
    USER_CACHE.clear()
    cache_user_info("uuid-3", {"FirstName": "Grace"})
    first = get_user_info("uuid-3")
    cache_user_info("uuid-3", {"FirstName": "Different"})
    second = get_user_info("uuid-3")
    assert first is second
    assert second.first_name == "Grace"


def test_get_user_info_missing_returns_none():
    USER_CACHE.clear()
    assert get_user_info("not-cached") is None
