# yalexs [![PyPI version](https://badge.fury.io/py/yalexs.svg)](https://badge.fury.io/py/yalexs) [![Build Status](https://github.com/bdraco/yalexs/workflows/CI/badge.svg)](https://github.com/bdraco/yalexs) [![codecov](https://codecov.io/gh/Yale-Libs/yalexs/branch/main/graph/badge.svg)](https://codecov.io/gh/Yale-Libs/yalexs) [![Python Versions](https://img.shields.io/pypi/pyversions/yalexs.svg)](https://pypi.python.org/pypi/yalexs/)

Python API for Yale Access (formerly August) Smart Lock and Doorbell. This is used in [Home Assistant](https://home-assistant.io) but should be generic enough that can be used elsewhere.

## Yale Access formerly August

This library is a fork of Joe Lu's excellent august library from https://github.com/snjoetw/py-august

## API status

This is an unofficial library. As of v9, only the **async** API (`yalexs.api_async.ApiAsync`, `yalexs.authenticator_async.AuthenticatorAsync`) is supported — the synchronous `Api` / `Authenticator` classes were removed in v8 (see [#141](https://github.com/Yale-Libs/yalexs/pull/141)).

The public API key historically embedded in this library is no longer accepted by either backend. Both `Brand.AUGUST` (Fortune Brands / Yale Access) and `Brand.YALE_HOME` (Assa Abloy) now require an official partner key issued by the vendor. See [#167](https://github.com/Yale-Libs/yalexs/issues/167) for context. The usage example below is illustrative — you will need to supply a working key via the brand/API plumbing for it to authenticate against the live service.

## Install

```bash
pip install yalexs
```

## Classes

### AuthenticatorAsync

`AuthenticatorAsync` handles authentication: signing in, sending a verification code to email or phone, and validating the returned code.

#### Constructor

| Argument                  | Description                                                                                                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| api                       | An `ApiAsync` instance.                                                                                                                                                           |
| login_method              | Login method, either `"phone"` or `"email"`.                                                                                                                                      |
| username                  | If `login_method` is `phone`, your full phone number including `+` and country code; otherwise your email address.                                                                |
| password                  | Account password.                                                                                                                                                                 |
| install_id\*              | ID generated when the Yale Access app is installed. If not specified, the authenticator generates one. Providing a previously provisioned install ID skips the verification step. |
| access_token_cache_file\* | Path to a token cache file. If set, authentication state is persisted to disk so subsequent runs can skip the login step until the token expires.                                 |

\* optional

#### Methods

##### `async_setup_authentication()`

Loads cached credentials from `access_token_cache_file` if present. Call once before `async_authenticate()`.

##### `async_authenticate() -> Authentication`

Authenticates with the API. The returned `Authentication.state` is one of:

- `AuthenticationState.AUTHENTICATED` — logged in, `access_token` is valid.
- `AuthenticationState.REQUIRES_VALIDATION` — call `async_send_verification_code()` then `async_validate_verification_code(code)`.
- `AuthenticationState.BAD_PASSWORD` — credentials rejected.
- `AuthenticationState.REQUIRES_AUTHENTICATION` — no cached token; call `async_authenticate()` to obtain one.

If a valid token is already cached, this returns it without contacting the API.

##### `async_send_verification_code() -> bool`

Sends a 6-digit verification code to the phone or email tied to the account.

##### `async_validate_verification_code(code: str) -> ValidationResult`

Validates the code. Returns `ValidationResult.VALIDATED` on success or `ValidationResult.INVALID_VERIFICATION_CODE` otherwise.

##### `async_refresh_access_token(force: bool = False) -> Authentication | None`

Refreshes the access token if it is within the renewal threshold (default 7 days before expiry). Pass `force=True` to refresh unconditionally.

## Usage

```python
import asyncio

from aiohttp import ClientSession

from yalexs.alarm import ArmState
from yalexs.api_async import ApiAsync
from yalexs.authenticator_async import AuthenticationState, AuthenticatorAsync
from yalexs.const import Brand


async def main() -> None:
    async with ClientSession() as session:
        api = ApiAsync(session, timeout=20, brand=Brand.AUGUST)
        authenticator = AuthenticatorAsync(
            api,
            "email",
            "EMAIL_ADDRESS",
            "PASSWORD",
            access_token_cache_file="auth.txt",
        )
        await authenticator.async_setup_authentication()
        authentication = await authenticator.async_authenticate()

        if authentication.state is AuthenticationState.REQUIRES_VALIDATION:
            await authenticator.async_send_verification_code()
            code = input("Verification code: ")
            await authenticator.async_validate_verification_code(code)
            authentication = await authenticator.async_authenticate()

        access_token = authentication.access_token

        locks = await api.async_get_locks(access_token)
        for lock in locks:
            print(lock)

        # Alarms (Yale Home brand only)
        if api.brand_supports_alarms:
            alarms = await api.async_get_alarms(access_token)
            if alarms:
                await api.async_arm_alarm(access_token, alarms[0], ArmState.Away)


asyncio.run(main())
```
