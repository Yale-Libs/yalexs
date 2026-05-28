# yalexs [![PyPI version](https://badge.fury.io/py/yalexs.svg)](https://badge.fury.io/py/yalexs) [![Build Status](https://github.com/bdraco/yalexs/workflows/CI/badge.svg)](https://github.com/bdraco/yalexs) [![codecov](https://codecov.io/gh/Yale-Libs/yalexs/branch/main/graph/badge.svg)](https://codecov.io/gh/Yale-Libs/yalexs) [![Python Versions](https://img.shields.io/pypi/pyversions/yalexs.svg)](https://pypi.python.org/pypi/yalexs/)

Python API for Yale Access (formerly August) Smart Lock and Doorbell. This is used in [Home Assistant](https://home-assistant.io) but should be generic enough that can be used elsewhere.

## Yale Access formerly August

This library is a fork of Joe Lu's excellent august library from https://github.com/snjoetw/py-august

## Classes

### Authenticator

Authenticator is responsible for all authentication related logic, this includes authentication and verifying the account belongs to the user by sending a verification code to email or phone.

#### Constructor

| Argument                  | Description                                                                                                                                                                                                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| api                       | See Api class.                                                                                                                                                                                                                              |
| login_method              | Login method, either "phone" or "email".                                                                                                                                                                                                    |
| username                  | If you're login_method is phone, then this is your full phone# including "+" and country code; otherwise enter your email address here.                                                                                                     |
| password                  | Password.                                                                                                                                                                                                                                   |
| install_id\*              | ID that's generated when Yale Access app is installed. If not specified, Authenticator will auto-generate one. If an install_id is provisioned, then it's good to provide the provisioned install_id as you'll bypass verification process. |
| access_token_cache_file\* | Path to access_token cache file. If specified, access_token info will be cached in the file. Subsequent authentication will utilize information in the file to determine correct authentication state.                                      |

\* means optional

#### Methods

##### authenticate

Authenticates using specified login_method, username and password.

Outcome of this method is an Authentication object. Use Authentication.state figure out authentication state. User is authenticated only if Authentication.state = AuthenticationState.AUTHENTICATED.

If an authenticated access_token is already in the access_token_cache_file, this method will return cached authentication.

##### send_verification_code

Sends a 6-digits verification code to phone or email depending on login_method.

##### validate_verification_code

Validates verification code. This method returns ValidationResult. Check the value to see if verification code is valid or not.

## Install

```bash
pip install yalexs
```

## Usage

```python
import asyncio
from aiohttp import ClientSession

from yalexs.api_async import ApiAsync
from yalexs.authenticator_async import AuthenticatorAsync
from yalexs.const import Brand
from yalexs.alarm import ArmState


async def main():
    api = ApiAsync(ClientSession(), timeout=20, brand=Brand.YALE_HOME)
    authenticator = AuthenticatorAsync(api, "email", "EMAIL_ADDRESS", "PASSWORD}",
        access_token_cache_file="auth.txt",install_id="UUID")
    await authenticator.async_setup_authentication()
    authentication = await authenticator.async_authenticate()
    access_token = authentication.access_token

    # if(authentication.state == AuthenticationState.REQUIRES_VALIDATION) :
    #   await authenticator.async_send_verification_code()
    # await authenticator.async_validate_verification_code("12345")

    # DO STUFF HERE LIKE GET THE ALARMS, LOCS, ETC....
    alarms = await api.async_get_alarms(access_token)
    locks = api.get_locks(access_token)

    # OR ARM YOUR ALARM
    await api.async_arm_alarm(access_token, alarms[0], ArmState.Away)



asyncio.run(main())
```
