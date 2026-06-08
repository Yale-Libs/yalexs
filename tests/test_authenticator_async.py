import asyncio
import json
import logging
import os
import pathlib
import unittest
from datetime import datetime, timedelta, timezone

import aiofiles
import pytest
import pytest_asyncio
from aiohttp import ClientError, ClientSession
from dateutil.tz import tzutc

from yalexs.api_async import ApiAsync
from yalexs.api_common import (
    API_GET_HOUSES_URL,
    API_GET_SESSION_URL,
    API_SEND_VERIFICATION_CODE_URLS,
    API_VALIDATE_VERIFICATION_CODE_URLS,
    ApiCommon,
)
from yalexs.authenticator_async import (
    AuthenticationState,
    AuthenticatorAsync,
    ValidationResult,
)
from yalexs.const import DEFAULT_BRAND, HEADER_AUGUST_ACCESS_TOKEN, Brand

from .common import aiointercept


def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"


class TestAuthenticatorAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Setup things to be run when tests are started."""

    def _new_session(self) -> ClientSession:
        """Create a ClientSession that is closed during test cleanup."""
        session = ClientSession()
        self.addAsyncCleanup(session.close)
        return session

    async def _async_create_authenticator_async(self, mock_aioresponses):
        authenticator = AuthenticatorAsync(
            ApiAsync(self._new_session()),
            "phone",
            "user",
            "pass",
            install_id="install_id",
        )
        await authenticator.async_setup_authentication()
        return authenticator

    def _setup_session_response(
        self,
        mock_aioresponses,
        v_password,
        v_install_id,
        expires_at=None,
    ):
        if expires_at is None:
            expires_at = format_datetime(datetime.now(timezone.utc))
        mock_aioresponses.post(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_SESSION_URL),
            headers={"x-august-access-token": "access_token"},
            body=json.dumps(
                {
                    "expiresAt": expires_at,
                    "vPassword": v_password,
                    "vInstallId": v_install_id,
                }
            ),
        )

    @aiointercept()
    async def test_async_should_refresh_when_token_expiry_is_after_renewal_threshold(
        self, mock_aioresponses
    ):
        expired_expires_at = format_datetime(
            datetime.now(timezone.utc) + timedelta(days=6)
        )
        self._setup_session_response(
            mock_aioresponses, True, True, expires_at=expired_expires_at
        )

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        await authenticator.async_authenticate()

        should_refresh = authenticator.should_refresh()

        self.assertEqual(True, should_refresh)

    @aiointercept()
    async def test_async_should_refresh_when_token_expiry_is_before_renewal_threshold(
        self, mock_aioresponses
    ):
        not_expired_expires_at = format_datetime(
            datetime.now(timezone.utc) + timedelta(days=8)
        )
        self._setup_session_response(
            mock_aioresponses, True, True, expires_at=not_expired_expires_at
        )

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        await authenticator.async_authenticate()

        should_refresh = authenticator.should_refresh()

        self.assertEqual(False, should_refresh)

    @aiointercept()
    async def test_async_refresh_token(self, mock_aioresponses):
        self._setup_session_response(mock_aioresponses, True, True)

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        await authenticator.async_authenticate()

        token = "e30=.eyJleHAiOjEzMzd9.e30="
        mock_aioresponses.get(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_HOUSES_URL),
            body=token,
            headers={HEADER_AUGUST_ACCESS_TOKEN: token},
        )

        access_token = await authenticator.async_refresh_access_token(force=False)

        self.assertEqual(token, access_token.access_token)
        self.assertEqual(
            datetime.fromtimestamp(1337, tz=tzutc()),
            access_token.parsed_expiration_time(),
        )

    @aiointercept()
    async def test_async_get_session_with_authenticated_response(
        self, mock_aioresponses
    ):
        self._setup_session_response(mock_aioresponses, True, True)

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        authentication = await authenticator.async_authenticate()

        self.assertEqual("access_token", authentication.access_token)
        self.assertEqual("install_id", authentication.install_id)
        self.assertEqual(AuthenticationState.AUTHENTICATED, authentication.state)

    @aiointercept()
    async def test_async_get_session_with_bad_password_response(
        self, mock_aioresponses
    ):
        self._setup_session_response(mock_aioresponses, False, True)

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        authentication = await authenticator.async_authenticate()

        self.assertEqual("access_token", authentication.access_token)
        self.assertEqual("install_id", authentication.install_id)
        self.assertEqual(AuthenticationState.BAD_PASSWORD, authentication.state)

    @aiointercept()
    async def test_async_get_session_with_requires_validation_response(
        self, mock_aioresponses
    ):
        self._setup_session_response(mock_aioresponses, True, False)

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        authentication = await authenticator.async_authenticate()

        self.assertEqual("access_token", authentication.access_token)
        self.assertEqual("install_id", authentication.install_id)
        self.assertEqual(AuthenticationState.REQUIRES_VALIDATION, authentication.state)

    @aiointercept()
    async def test_async_get_session_with_already_authenticated_state(
        self, mock_aioresponses
    ):
        self._setup_session_response(mock_aioresponses, True, True)

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        # this will set authentication state to AUTHENTICATED
        await authenticator.async_authenticate()
        # call authenticate() again
        authentication = await authenticator.async_authenticate()

        self.assertEqual("access_token", authentication.access_token)
        self.assertEqual("install_id", authentication.install_id)
        self.assertEqual(AuthenticationState.AUTHENTICATED, authentication.state)

    @aiointercept()
    async def test_async_send_verification_code(self, mock_aioresponses):
        self._setup_session_response(mock_aioresponses, True, False)

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        mock_aioresponses.post(
            ApiCommon(DEFAULT_BRAND).get_brand_url(
                API_SEND_VERIFICATION_CODE_URLS["phone"]
            ),
            body="{}",
        )
        await authenticator.async_authenticate()
        result = await authenticator.async_send_verification_code()

        self.assertEqual(True, result)

    @aiointercept()
    async def test_async_validate_verification_code_with_no_code(
        self, mock_aioresponses
    ):
        self._setup_session_response(mock_aioresponses, True, False)

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        await authenticator.async_authenticate()

        mock_aioresponses.post(
            ApiCommon(DEFAULT_BRAND).get_brand_url(
                API_VALIDATE_VERIFICATION_CODE_URLS["phone"]
            ),
            body="{}",
        )
        result = await authenticator.async_validate_verification_code("")

        self.assertEqual(ValidationResult.INVALID_VERIFICATION_CODE, result)

    @aiointercept()
    async def test_async_validate_verification_code_with_validated_response(
        self, mock_aioresponses
    ):
        self._setup_session_response(mock_aioresponses, True, False)

        mock_aioresponses.post(
            ApiCommon(DEFAULT_BRAND).get_brand_url(
                API_VALIDATE_VERIFICATION_CODE_URLS["phone"]
            ),
            body="{}",
        )

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        await authenticator.async_authenticate()
        result = await authenticator.async_validate_verification_code("123456")

        self.assertEqual(ValidationResult.VALIDATED, result)

    @aiointercept()
    async def test_async_validate_verification_code_with_invalid_code_response(
        self, mock_aioresponses
    ):
        self._setup_session_response(mock_aioresponses, True, False)

        mock_aioresponses.post(
            ApiCommon(DEFAULT_BRAND).get_brand_url(
                API_VALIDATE_VERIFICATION_CODE_URLS["phone"]
            ),
            exception=ClientError(),
        )

        authenticator = await self._async_create_authenticator_async(mock_aioresponses)
        await authenticator.async_authenticate()
        result = await authenticator.async_validate_verification_code("123456")

        self.assertEqual(ValidationResult.INVALID_VERIFICATION_CODE, result)


# ---------------------------------------------------------------------------
# Coverage for cache-file paths, oauth gating, and refresh short-circuits.
# Bare pytest, fully typed — no classes.
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_aioresponse() -> aiointercept:
    async with aiointercept() as m:
        yield m


@pytest.fixture
def cache_path(tmp_path: pathlib.Path) -> str:
    # Hand out a path that does not exist yet; tests that want a populated
    # cache write into it explicitly.
    return str(tmp_path / "auth-cache.json")


def _make_authenticator(
    session: ClientSession,
    cache_path: str,
    brand: Brand = DEFAULT_BRAND,
) -> AuthenticatorAsync:
    return AuthenticatorAsync(
        ApiAsync(session, brand=brand),
        "phone",
        "user",
        "pass",
        install_id="install_id",
        access_token_cache_file=cache_path,
    )


async def _write_cache(cache_path: str, expires_at: datetime) -> None:
    payload = {
        "install_id": "cached_install",
        "access_token": "cached_token",
        "access_token_expires": expires_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "state": AuthenticationState.AUTHENTICATED.value,
    }
    async with aiofiles.open(cache_path, "w") as f:
        await f.write(json.dumps(payload))


@pytest.mark.asyncio
async def test_setup_authentication_with_missing_cache_file(
    cache_path: str,
) -> None:
    async with ClientSession() as session:
        authenticator = _make_authenticator(session, cache_path)
        await authenticator.async_setup_authentication()
        # Falls through to fresh REQUIRES_AUTHENTICATION state.
        assert (
            authenticator._authentication.state
            == AuthenticationState.REQUIRES_AUTHENTICATION
        )
        assert authenticator._authentication.install_id == "install_id"


@pytest.mark.asyncio
async def test_setup_authentication_with_invalid_json(cache_path: str) -> None:
    async with aiofiles.open(cache_path, "w") as f:
        await f.write("not-json{")
    async with ClientSession() as session:
        authenticator = _make_authenticator(session, cache_path)
        await authenticator.async_setup_authentication()
        assert (
            authenticator._authentication.state
            == AuthenticationState.REQUIRES_AUTHENTICATION
        )


@pytest.mark.asyncio
async def test_setup_authentication_loads_valid_cache(cache_path: str) -> None:
    # Far-future expiration → no warning, loaded as-is.
    await _write_cache(cache_path, datetime.now(timezone.utc) + timedelta(days=30))
    async with ClientSession() as session:
        authenticator = _make_authenticator(session, cache_path)
        await authenticator.async_setup_authentication()
        assert authenticator._authentication.state == AuthenticationState.AUTHENTICATED
        assert authenticator._authentication.access_token == "cached_token"
        assert authenticator._authentication.install_id == "cached_install"


@pytest.mark.asyncio
async def test_setup_authentication_with_expired_cache(cache_path: str) -> None:
    await _write_cache(cache_path, datetime.now(timezone.utc) - timedelta(days=1))
    async with ClientSession() as session:
        authenticator = _make_authenticator(session, cache_path)
        await authenticator.async_setup_authentication()
        # Expired tokens reset state to REQUIRES_AUTHENTICATION.
        assert (
            authenticator._authentication.state
            == AuthenticationState.REQUIRES_AUTHENTICATION
        )
        # install_id from the configured authenticator, not the cached one.
        assert authenticator._authentication.install_id == "install_id"


@pytest.mark.asyncio
async def test_setup_authentication_with_soon_expiring_cache_warns(
    cache_path: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Within the 7-day renewal threshold → logs a warning but keeps the token.
    await _write_cache(cache_path, datetime.now(timezone.utc) + timedelta(days=2))
    caplog.set_level(logging.WARNING, logger="yalexs.authenticator_async")
    async with ClientSession() as session:
        authenticator = _make_authenticator(session, cache_path)
        await authenticator.async_setup_authentication()
        assert any(
            r.name == "yalexs.authenticator_async"
            and r.levelno == logging.WARNING
            and "going to expire" in r.getMessage()
            for r in caplog.records
        ), f"expected expiry warning, got: {caplog.records}"
        assert authenticator._authentication.state == AuthenticationState.AUTHENTICATED


@pytest.mark.asyncio
async def test_authenticate_writes_cache_file(
    cache_path: str,
    mock_aioresponse: aiointercept,
) -> None:
    # Round-trip: a successful authenticate() should persist to disk.
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )[:-3] + "Z"
    mock_aioresponse.post(
        ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_SESSION_URL),
        headers={"x-august-access-token": "fresh_token"},
        body=json.dumps(
            {"expiresAt": expires_at, "vPassword": True, "vInstallId": True}
        ),
    )
    async with ClientSession() as session:
        authenticator = _make_authenticator(session, cache_path)
        await authenticator.async_setup_authentication()
        await authenticator.async_authenticate()

        exists = await asyncio.to_thread(os.path.exists, cache_path)
        assert exists
        async with aiofiles.open(cache_path) as f:
            stored = json.loads(await f.read())
        assert stored["access_token"] == "fresh_token"
        assert stored["state"] == AuthenticationState.AUTHENTICATED.value


@pytest.mark.asyncio
async def test_authenticate_raises_for_oauth_required_brand() -> None:
    async with ClientSession() as session:
        authenticator = AuthenticatorAsync(
            ApiAsync(session, brand=Brand.YALE_GLOBAL),
            "phone",
            "user",
            "pass",
            install_id="install_id",
        )
        await authenticator.async_setup_authentication()
        with pytest.raises(RuntimeError):
            await authenticator.async_authenticate()


@pytest.mark.asyncio
async def test_refresh_short_circuits_when_not_authenticated(
    cache_path: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING, logger="yalexs.authenticator_async")
    async with ClientSession() as session:
        authenticator = _make_authenticator(session, cache_path)
        await authenticator.async_setup_authentication()
        # State is REQUIRES_AUTHENTICATION → refresh logs warning and returns
        # current authentication without hitting the API.
        result = await authenticator.async_refresh_access_token(force=True)
        assert any(
            r.name == "yalexs.authenticator_async"
            and r.levelno == logging.WARNING
            and "not authenticated" in r.getMessage()
            for r in caplog.records
        ), f"expected not-authenticated warning, got: {caplog.records}"
        assert result is authenticator._authentication


@pytest.mark.asyncio
async def test_refresh_no_op_when_refresh_not_needed(
    cache_path: str,
    mock_aioresponse: aiointercept,
) -> None:
    # Authenticate with a far-future expiration, then refresh(force=False)
    # should short-circuit without calling the API.
    far_future = (datetime.now(timezone.utc) + timedelta(days=30)).strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )[:-3] + "Z"
    mock_aioresponse.post(
        ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_SESSION_URL),
        headers={"x-august-access-token": "fresh_token"},
        body=json.dumps(
            {"expiresAt": far_future, "vPassword": True, "vInstallId": True}
        ),
    )
    async with ClientSession() as session:
        authenticator = _make_authenticator(session, cache_path)
        await authenticator.async_setup_authentication()
        await authenticator.async_authenticate()

        # No refresh endpoint registered — would 404 if called.
        result = await authenticator.async_refresh_access_token(force=False)
        assert result.access_token == "fresh_token"
