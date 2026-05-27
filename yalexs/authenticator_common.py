from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import jwt

from .api_common import ApiCommon
from .const import HEADER_ACCESS_TOKEN, HEADER_AUGUST_ACCESS_TOKEN
from .time import parse_datetime

# The default time before expiration to refresh a token
DEFAULT_RENEWAL_THRESHOLD = timedelta(days=7)

_LOGGER = logging.getLogger(__name__)


def to_authentication_json(authentication):
    if authentication is None:
        return json.dumps({})

    return json.dumps(
        {
            "install_id": authentication.install_id,
            "access_token": authentication.access_token,
            "access_token_expires": authentication.access_token_expires,
            "state": authentication.state.value,
        }
    )


def from_authentication_json(data):
    if data is None:
        return None

    install_id = data["install_id"]
    access_token = data["access_token"]
    access_token_expires = data["access_token_expires"]
    state = AuthenticationState(data["state"])
    return Authentication(state, install_id, access_token, access_token_expires)


class Authentication:
    def __init__(
        self, state, install_id=None, access_token=None, access_token_expires=None
    ):
        self._state = state
        self._install_id = str(uuid.uuid4()) if install_id is None else install_id
        self._access_token = access_token
        self._access_token_expires = access_token_expires
        self._parsed_expiration_time = None
        if access_token_expires:
            self._parsed_expiration_time = parse_datetime(access_token_expires)

    @property
    def install_id(self):
        return self._install_id

    @property
    def access_token(self):
        return self._access_token

    @property
    def access_token_expires(self):
        return self._access_token_expires

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def parsed_expiration_time(self):
        return self._parsed_expiration_time

    def is_expired(self):
        return self._parsed_expiration_time < datetime.now(timezone.utc)


class AuthenticationState(Enum):
    REQUIRES_AUTHENTICATION = "requires_authentication"
    REQUIRES_VALIDATION = "requires_validation"
    AUTHENTICATED = "authenticated"
    BAD_PASSWORD = "bad_password"  # nosec


class ValidationResult(Enum):
    VALIDATED = "validated"
    INVALID_VERIFICATION_CODE = "invalid_verification_code"


class AuthenticatorCommon:
    def __init__(
        self,
        api: ApiCommon,
        login_method: str | None,
        username: str | None,
        password: str | None,
        install_id: str | None = None,
        access_token_cache_file: str | None = None,
        access_token_renewal_threshold: timedelta = DEFAULT_RENEWAL_THRESHOLD,
    ) -> None:
        self._api = api
        self._login_method = login_method
        self._username = username
        self._password = password
        self._install_id = install_id
        self._access_token_cache_file = access_token_cache_file
        self._access_token_renewal_threshold = access_token_renewal_threshold
        self._authentication = None

    def _authentication_from_session_response(
        self,
        install_id: str,
        response_headers: dict[str, Any],
        json_dict: dict[str, Any],
    ) -> Authentication:
        access_token = (
            response_headers.get(HEADER_ACCESS_TOKEN)
            or response_headers[HEADER_AUGUST_ACCESS_TOKEN]
        )
        access_token_expires = json_dict["expiresAt"]
        v_password = json_dict["vPassword"]
        v_install_id = json_dict["vInstallId"]

        if not v_password:
            state = AuthenticationState.BAD_PASSWORD
        elif not v_install_id:
            state = AuthenticationState.REQUIRES_VALIDATION
        else:
            state = AuthenticationState.AUTHENTICATED

        self._authentication = Authentication(
            state, install_id, access_token, access_token_expires
        )

        return self._authentication

    def should_refresh(self):
        return self._authentication.state == AuthenticationState.AUTHENTICATED and (
            (self._authentication.parsed_expiration_time() - datetime.now(timezone.utc))
            < self._access_token_renewal_threshold
        )

    def _process_refreshed_access_token(self, refreshed_token):
        jwt_claims = jwt.decode(refreshed_token, options={"verify_signature": False})

        if "exp" not in jwt_claims:
            _LOGGER.warning("Did not find expected `exp' claim in JWT")
            return self._authentication

        new_expiration = datetime.fromtimestamp(jwt_claims["exp"], tz=timezone.utc)
        # The yale access api always returns expiresAt formatted as
        # ``%Y-%m-%dT%H:%M:%S.%fZ`` from the get_session api call, so we
        # store access_token_expires the same way for compatibility.
        self._authentication = Authentication(
            self._authentication.state,
            install_id=self._authentication.install_id,
            access_token=refreshed_token,
            access_token_expires=new_expiration.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )

        _LOGGER.info("Successfully refreshed access token")
        return self._authentication
