# yalexs [![PyPI version](https://badge.fury.io/py/yalexs.svg)](https://badge.fury.io/py/yalexs) [![Build Status](https://github.com/Yale-Libs/yalexs/workflows/CI/badge.svg)](https://github.com/Yale-Libs/yalexs) [![codecov](https://codecov.io/gh/Yale-Libs/yalexs/branch/main/graph/badge.svg)](https://codecov.io/gh/Yale-Libs/yalexs) [![Python Versions](https://img.shields.io/pypi/pyversions/yalexs.svg)](https://pypi.python.org/pypi/yalexs/)

Python API for Yale Access (formerly August) Smart Lock and Doorbell. This is used in [Home Assistant](https://home-assistant.io) but should be generic enough that can be used elsewhere.

## Yale Access formerly August

This library is a fork of Joe Lu's excellent august library from https://github.com/snjoetw/py-august

## API status

This is an unofficial library. As of v9, only the **async** API (`yalexs.api_async.ApiAsync`, `yalexs.authenticator_async.AuthenticatorAsync`) is supported — the synchronous `Api` / `Authenticator` classes were removed in v8 (see [#141](https://github.com/Yale-Libs/yalexs/pull/141)).

The public API key historically embedded in this library is no longer accepted by either backend. `Brand.AUGUST` (Fortune Brands / Yale Access) now requires an official partner key issued by the vendor. See [#167](https://github.com/Yale-Libs/yalexs/issues/167) for context. The `Brand.YALE_HOME` (Assa Abloy) config was removed in [#409](https://github.com/Yale-Libs/yalexs/issues/409) because its key stopped working; Yale Home accounts now authenticate through `Brand.YALE_GLOBAL`, which requires OAuth via Home Assistant. The usage example below is illustrative — you will need to supply a working key via the brand/API plumbing for it to authenticate against the live service.

### Vendor-gated and unsupported endpoints

Several capabilities that exist in the official Yale Access / August apps are **not** available through this library, because the vendor either blocks them for third-party API keys or has never published a write contract. These recur in the issue tracker; the short answer is that they cannot be implemented blind:

| Capability                                                                               | Status                                                                                                                         | Reference                                              |
| ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| Doorbell video / camera (`/doorbells/{id}/videoevent`, `/doorbells/{id}/kvscredentials`) | Returns `NotAuthorized` — _"endpoint not allowed for API key"_ on the global Yale branding.                                    | [#293](https://github.com/Yale-Libs/yalexs/issues/293) |
| Privacy-mode toggle                                                                      | No documented API endpoint; not exposed by the app's public surface.                                                           | [#290](https://github.com/Yale-Libs/yalexs/issues/290) |
| Add / remove user PIN codes                                                              | Read-only here: only `async_get_pins` (`GET /locks/{id}/pins`) exists. No documented POST/PUT/DELETE contract for slot writes. | [#78](https://github.com/Yale-Libs/yalexs/issues/78)   |

If Yale publishes (or you can reverse-engineer with a valid partner key) the request shape for any of these, contributions are welcome.

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
