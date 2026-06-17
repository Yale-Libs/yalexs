"""Constants."""

from __future__ import annotations

from dataclasses import dataclass

from .backports.enum import StrEnum


class Brand(StrEnum):
    AUGUST = "august"
    YALE_ACCESS = "yale_access"
    YALE_GLOBAL = "yale_global"  # requires OAuth with Home Assistant
    YALE_AUGUST = "yale_august"  # requires OAuth with Home Assistant


DEFAULT_BRAND = Brand.AUGUST


@dataclass
class BrandConfig:
    """Brand configuration."""

    name: str
    branding: str
    access_token_header: str
    api_key_header: str
    branding_header: str
    api_key: str
    supports_doorbells: bool
    supports_alarms: bool
    require_oauth: bool
    base_url: str
    configuration_url: str
    pubnub_subscribe_token: str | None
    pubnub_publish_token: str | None


HEADER_VALUE_API_KEY_OLD = "7cab4bbd-2693-4fc1-b99b-dec0fb20f9d4"
HEADER_VALUE_API_KEY = "d9984f29-07a6-816e-e1c9-44ec9d1be431"

HEADER_AUGUST_ACCESS_TOKEN = "x-august-access-token"  # nosec
HEADER_AUGUST_API_KEY = "x-august-api-key"  # nosec
HEADER_AUGUST_BRANDING = "x-august-branding"

HEADER_ACCESS_TOKEN = "x-access-token"  # nosec
HEADER_API_KEY = "x-api-key"  # nosec
HEADER_BRANDING = "x-branding"

BRAND_CONFIG: dict[Brand, BrandConfig] = {
    Brand.AUGUST: BrandConfig(
        name="August",
        branding="august",
        access_token_header=HEADER_AUGUST_ACCESS_TOKEN,
        api_key_header=HEADER_AUGUST_API_KEY,
        branding_header=HEADER_AUGUST_BRANDING,
        api_key=HEADER_VALUE_API_KEY,
        supports_doorbells=True,
        supports_alarms=False,
        require_oauth=False,
        base_url="https://api-production.august.com",
        configuration_url="https://account.august.com",
        pubnub_subscribe_token="sub-c-1030e062-0ebe-11e5-a5c2-0619f8945a4f",  # nosec
        pubnub_publish_token="pub-c-567d7f2d-270a-438a-a785-f0af12ad8312",  # nosec
    ),
    Brand.YALE_ACCESS: BrandConfig(
        name="Yale Access",
        branding="yale",
        access_token_header=HEADER_AUGUST_ACCESS_TOKEN,
        api_key_header=HEADER_AUGUST_API_KEY,
        branding_header=HEADER_AUGUST_BRANDING,
        api_key=HEADER_VALUE_API_KEY,
        supports_doorbells=True,
        supports_alarms=False,
        require_oauth=False,
        base_url="https://api-production.august.com",
        configuration_url="https://account.august.com",
        pubnub_subscribe_token="sub-c-1030e062-0ebe-11e5-a5c2-0619f8945a4f",  # nosec
        pubnub_publish_token="pub-c-567d7f2d-270a-438a-a785-f0af12ad8312",  # nosec
    ),
    Brand.YALE_GLOBAL: BrandConfig(
        name="Yale Global",
        branding="yale",
        access_token_header=HEADER_ACCESS_TOKEN,
        api_key_header=HEADER_API_KEY,
        branding_header=HEADER_BRANDING,
        # Sadly we currently do not have a way to avoid
        # having the API key in the code because it must
        # run on the user's device
        api_key="d16a1029-d823-4b55-a4ce-a769a9b56f0e",
        supports_doorbells=True,
        supports_alarms=True,  # ??
        require_oauth=True,
        base_url="https://api.aaecosystem.com",
        configuration_url="https://account.aaecosystem.com",
        # This brand uses WebSockets and has migrated
        # away from PubNub for this purpose which is great
        # because its one less credential we have to expose
        # to the user
        pubnub_publish_token=None,
        pubnub_subscribe_token=None,
    ),
    Brand.YALE_AUGUST: BrandConfig(
        name="Yale August",
        branding="august",
        access_token_header=HEADER_AUGUST_ACCESS_TOKEN,
        api_key_header=HEADER_AUGUST_API_KEY,
        branding_header=HEADER_AUGUST_BRANDING,
        api_key="66814fd9-af2c-426c-9710-b37e7eadfb51",
        supports_doorbells=True,
        supports_alarms=False,
        require_oauth=True,
        base_url="https://api-production.august.com",
        configuration_url="https://account.august.com",
        pubnub_subscribe_token="sub-c-1030e062-0ebe-11e5-a5c2-0619f8945a4f",  # nosec
        pubnub_publish_token="pub-c-567d7f2d-270a-438a-a785-f0af12ad8312",  # nosec
    ),
}

BRANDS = {brand: brand_config.name for brand, brand_config in BRAND_CONFIG.items()}
BRANDS_WITHOUT_OAUTH = {
    brand: brand_config.name
    for brand, brand_config in BRAND_CONFIG.items()
    if not brand_config.require_oauth
}
BRANDING = {
    brand: brand_config.branding for brand, brand_config in BRAND_CONFIG.items()
}
BASE_URLS = {
    brand: brand_config.base_url for brand, brand_config in BRAND_CONFIG.items()
}
CONFIGURATION_URLS = {
    brand: brand_config.configuration_url
    for brand, brand_config in BRAND_CONFIG.items()
}
