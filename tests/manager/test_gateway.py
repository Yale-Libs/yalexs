"""Tests for the manager Gateway."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiohttp import ClientError, ClientResponseError, ClientSession
from aiohttp.client_reqrep import RequestInfo
from yarl import URL

from yalexs.authenticator_common import Authentication, AuthenticationState
from yalexs.exceptions import (
    AugustApiAIOHTTPError,
    InvalidAuth,
    RateLimited,
)
from yalexs.manager.const import (
    CONF_ACCESS_TOKEN_CACHE_FILE,
    CONF_BRAND,
    CONF_INSTALL_ID,
    CONF_LOGIN_METHOD,
    CONF_PASSWORD,
    CONF_TIMEOUT,
    CONF_USERNAME,
    DEFAULT_AUGUST_CONFIG_FILE,
    VERIFICATION_CODE_KEY,
)
from yalexs.manager.exceptions import CannotConnect, RequireValidation
from yalexs.manager.gateway import Gateway


def _make_authentication(state: AuthenticationState) -> Authentication:
    return Authentication(
        state=state,
        install_id="install-id",
        access_token="access-token",
        access_token_expires=None,
    )


def _request_info() -> RequestInfo:
    return RequestInfo(url=URL("https://example/"), method="GET", headers={})


def _response_error(status: int) -> ClientResponseError:
    return ClientResponseError(
        request_info=_request_info(),
        history=(),
        status=status,
        message="boom",
    )


def _august_api_error(status: int | None) -> AugustApiAIOHTTPError:
    client_error = _response_error(status) if status is not None else ClientError("nope")
    return AugustApiAIOHTTPError("msg", aiohttp_client_error=client_error)


@pytest.fixture
def session() -> ClientSession:
    return MagicMock(spec=ClientSession)


@pytest.mark.asyncio
async def test_init_stores_config(tmp_path: Path, session: ClientSession) -> None:
    gw = Gateway(tmp_path, session)
    assert gw._aiohttp_session is session
    assert gw._config_path is tmp_path
    assert gw._config is None


@pytest.mark.asyncio
async def test_async_get_access_token_returns_authentication_token(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    gw.authentication = _make_authentication(AuthenticationState.AUTHENTICATED)

    assert await gw.async_get_access_token() == "access-token"


@pytest.mark.asyncio
async def test_configure_access_token_cache_file_uses_override(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)

    result = gw.async_configure_access_token_cache_file("user@example.com", "custom.cache")

    assert result == tmp_path / "custom.cache"
    assert gw._access_token_cache_file == "custom.cache"


@pytest.mark.asyncio
async def test_configure_access_token_cache_file_falls_back_to_default(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)

    result = gw.async_configure_access_token_cache_file("user@example.com", None)

    expected_name = f".user@example.com{DEFAULT_AUGUST_CONFIG_FILE}"
    assert result == tmp_path / expected_name
    assert gw._access_token_cache_file == expected_name


@pytest.mark.asyncio
async def test_async_setup_returns_early_with_verification_code(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)

    await gw.async_setup({VERIFICATION_CODE_KEY: "123456"})

    assert gw._config is None
    assert not hasattr(gw, "api")
    assert not hasattr(gw, "authenticator")


@pytest.mark.asyncio
async def test_async_setup_builds_api_and_authenticator(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    conf = {
        CONF_USERNAME: "user@example.com",
        CONF_PASSWORD: "pw",
        CONF_LOGIN_METHOD: "email",
        CONF_INSTALL_ID: "install-1",
        CONF_BRAND: "yale_global",
        CONF_TIMEOUT: 10,
    }
    fake_authenticator = Mock()
    fake_authenticator.async_setup_authentication = AsyncMock()
    authenticator_class = Mock(return_value=fake_authenticator)

    with patch("yalexs.manager.gateway.ApiAsync") as api_cls:
        await gw.async_setup(conf, authenticator_class=authenticator_class)

    api_cls.assert_called_once_with(session, timeout=10, brand="yale_global")
    authenticator_class.assert_called_once()
    _, kwargs = authenticator_class.call_args
    # positional args: api, login_method, username, password
    assert authenticator_class.call_args.args[1] == "email"
    assert authenticator_class.call_args.args[2] == "user@example.com"
    assert authenticator_class.call_args.args[3] == "pw"
    assert kwargs["install_id"] == "install-1"
    expected_cache = tmp_path / f".user@example.com{DEFAULT_AUGUST_CONFIG_FILE}"
    assert kwargs["access_token_cache_file"] == expected_cache
    fake_authenticator.async_setup_authentication.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_setup_without_username_skips_cache_file(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    fake_authenticator = Mock()
    fake_authenticator.async_setup_authentication = AsyncMock()
    authenticator_class = Mock(return_value=fake_authenticator)

    with patch("yalexs.manager.gateway.ApiAsync"):
        await gw.async_setup(
            {CONF_LOGIN_METHOD: "email", CONF_PASSWORD: "pw"},
            authenticator_class=authenticator_class,
        )

    _, kwargs = authenticator_class.call_args
    assert kwargs["access_token_cache_file"] is None


@pytest.mark.asyncio
async def test_async_setup_uses_default_authenticator_when_none_supplied(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    fake_authenticator = Mock()
    fake_authenticator.async_setup_authentication = AsyncMock()

    with (
        patch("yalexs.manager.gateway.ApiAsync"),
        patch(
            "yalexs.manager.gateway.AuthenticatorAsync",
            return_value=fake_authenticator,
        ) as default_cls,
    ):
        await gw.async_setup(
            {
                CONF_USERNAME: "user@example.com",
                CONF_PASSWORD: "pw",
                CONF_LOGIN_METHOD: "email",
            }
        )

    default_cls.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_passes_access_token_cache_file_from_conf(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    fake_authenticator = Mock()
    fake_authenticator.async_setup_authentication = AsyncMock()
    authenticator_class = Mock(return_value=fake_authenticator)

    with patch("yalexs.manager.gateway.ApiAsync"):
        await gw.async_setup(
            {
                CONF_USERNAME: "u",
                CONF_PASSWORD: "pw",
                CONF_LOGIN_METHOD: "email",
                CONF_ACCESS_TOKEN_CACHE_FILE: "explicit.cache",
            },
            authenticator_class=authenticator_class,
        )

    _, kwargs = authenticator_class.call_args
    assert kwargs["access_token_cache_file"] == tmp_path / "explicit.cache"


def _gateway_with_authenticator(
    tmp_path: Path, session: ClientSession, auth_state: AuthenticationState
) -> tuple[Gateway, Mock]:
    gw = Gateway(tmp_path, session)
    gw.authenticator = Mock()
    gw.authenticator.async_authenticate = AsyncMock(
        return_value=_make_authentication(auth_state)
    )
    gw.api = Mock()
    gw.api.async_get_operable_locks = AsyncMock()
    return gw, gw.authenticator


@pytest.mark.asyncio
async def test_async_authenticate_success(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.AUTHENTICATED
    )

    with patch(
        "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
        new=AsyncMock(),
    ):
        result = await gw.async_authenticate()

    assert result is gw.authentication
    assert result.state is AuthenticationState.AUTHENTICATED
    gw.api.async_get_operable_locks.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_authenticate_bad_password_raises_invalid_auth(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.BAD_PASSWORD
    )

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(),
        ),
        pytest.raises(InvalidAuth),
    ):
        await gw.async_authenticate()


@pytest.mark.asyncio
async def test_async_authenticate_requires_validation_raises(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.REQUIRES_VALIDATION
    )

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(),
        ),
        pytest.raises(RequireValidation),
    ):
        await gw.async_authenticate()


@pytest.mark.asyncio
async def test_async_authenticate_unknown_state_raises_invalid_auth(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.REQUIRES_AUTHENTICATION
    )

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(),
        ),
        pytest.raises(InvalidAuth),
    ):
        await gw.async_authenticate()


@pytest.mark.asyncio
async def test_async_authenticate_august_auth_failed_maps_to_invalid_auth(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.AUTHENTICATED
    )
    gw.api.async_get_operable_locks = AsyncMock(side_effect=_august_api_error(401))

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(),
        ),
        pytest.raises(InvalidAuth),
    ):
        await gw.async_authenticate()


@pytest.mark.asyncio
async def test_async_authenticate_august_other_status_maps_to_cannot_connect(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.AUTHENTICATED
    )
    gw.api.async_get_operable_locks = AsyncMock(side_effect=_august_api_error(500))

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(),
        ),
        pytest.raises(CannotConnect),
    ):
        await gw.async_authenticate()


@pytest.mark.asyncio
async def test_async_authenticate_client_response_401_maps_to_invalid_auth(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.AUTHENTICATED
    )
    gw.api.async_get_operable_locks = AsyncMock(side_effect=_response_error(401))

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(),
        ),
        pytest.raises(InvalidAuth),
    ):
        await gw.async_authenticate()


@pytest.mark.asyncio
async def test_async_authenticate_client_response_other_maps_to_cannot_connect(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.AUTHENTICATED
    )
    gw.api.async_get_operable_locks = AsyncMock(side_effect=_response_error(503))

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(),
        ),
        pytest.raises(CannotConnect),
    ):
        await gw.async_authenticate()


@pytest.mark.asyncio
async def test_async_authenticate_client_error_maps_to_cannot_connect(
    tmp_path: Path, session: ClientSession, caplog: pytest.LogCaptureFixture
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.AUTHENTICATED
    )
    gw.api.async_get_operable_locks = AsyncMock(
        side_effect=ClientError("connection reset")
    )

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(),
        ),
        caplog.at_level("ERROR"),
        pytest.raises(CannotConnect),
    ):
        await gw.async_authenticate()

    assert "Unable to connect" in caplog.text


@pytest.mark.asyncio
async def test_async_authenticate_rate_limited_reraises(
    tmp_path: Path, session: ClientSession
) -> None:
    gw, _ = _gateway_with_authenticator(
        tmp_path, session, AuthenticationState.AUTHENTICATED
    )

    with (
        patch(
            "yalexs.manager.gateway._RateLimitChecker.check_rate_limit",
            new=AsyncMock(side_effect=RateLimited("slow down", 123.0)),
        ),
        pytest.raises(RateLimited),
    ):
        await gw.async_authenticate()


@pytest.mark.asyncio
async def test_async_reset_authentication_removes_existing_file(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    cache_path = gw.async_configure_access_token_cache_file("user", None)
    cache_path.write_text("{}")
    assert cache_path.exists()

    await gw.async_reset_authentication()

    assert not cache_path.exists()


@pytest.mark.asyncio
async def test_async_reset_authentication_noop_when_missing(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    gw.async_configure_access_token_cache_file("user", None)

    await gw.async_reset_authentication()  # must not raise


@pytest.mark.asyncio
async def test_async_refresh_access_token_skipped_when_not_needed(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    gw.authenticator = Mock()
    gw.authenticator.should_refresh = Mock(return_value=False)
    gw.authenticator.async_refresh_access_token = AsyncMock()

    await gw.async_refresh_access_token_if_needed()

    gw.authenticator.async_refresh_access_token.assert_not_called()


@pytest.mark.asyncio
async def test_async_refresh_access_token_updates_authentication(
    tmp_path: Path, session: ClientSession
) -> None:
    gw = Gateway(tmp_path, session)
    gw.authentication = _make_authentication(AuthenticationState.AUTHENTICATED)
    refreshed = _make_authentication(AuthenticationState.AUTHENTICATED)
    gw.authenticator = Mock()
    gw.authenticator.should_refresh = Mock(return_value=True)
    gw.authenticator.async_refresh_access_token = AsyncMock(return_value=refreshed)

    await gw.async_refresh_access_token_if_needed()

    gw.authenticator.async_refresh_access_token.assert_awaited_once_with(force=False)
    assert gw.authentication is refreshed
