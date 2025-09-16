import os
from datetime import datetime
from unittest import mock
from unittest.mock import patch

import aiounittest
import dateutil.parser
import pytest
from aiohttp import ClientOSError, ClientResponse, ClientSession
from aiohttp.helpers import TimerNoop
from aioresponses import CallbackResult, aioresponses
from dateutil.tz import tzlocal, tzutc
from yarl import URL

import yalexs.activity
from yalexs import api_async
from yalexs.api_async import ApiAsync, _raise_response_exceptions
from yalexs.api_common import (
    API_GET_CAPABILITIES_URL,
    API_GET_DOORBELL_URL,
    API_GET_DOORBELLS_URL,
    API_GET_HOUSE_ACTIVITIES_URL,
    API_GET_HOUSES_URL,
    API_GET_LOCK_STATUS_URL,
    API_GET_LOCK_URL,
    API_GET_LOCKS_URL,
    API_GET_PINS_URL,
    API_GET_USER_URL,
    API_LOCK_ASYNC_URL,
    API_LOCK_URL,
    API_STATUS_ASYNC_URL,
    API_UNLATCH_ASYNC_URL,
    API_UNLATCH_URL,
    API_UNLOCK_ASYNC_URL,
    API_UNLOCK_URL,
    API_VALIDATE_VERIFICATION_CODE_URLS,
    HYPER_BRIDGE_PARAM,
    ApiCommon,
)
from yalexs.bridge import BridgeDetail, BridgeStatus, BridgeStatusDetail
from yalexs.const import DEFAULT_BRAND, Brand
from yalexs.exceptions import AugustApiAIOHTTPError, ContentTokenExpired
from yalexs.lock import LockDoorStatus, LockStatus

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as fptr:
        return fptr.read()


def utc_of(year, month, day, hour, minute, second, microsecond):
    return datetime(year, month, day, hour, minute, second, microsecond, tzinfo=tzutc())


@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m


class TestApiAsync(aiounittest.AsyncTestCase):
    @aioresponses()
    async def test_async_get_doorbells(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_DOORBELLS_URL),
            body=load_fixture("get_doorbells.json"),
        )

        api = ApiAsync(ClientSession())
        doorbells = sorted(
            await api.async_get_doorbells(ACCESS_TOKEN), key=lambda d: d.device_id
        )

        self.assertEqual(2, len(doorbells))

        first = doorbells[0]
        self.assertEqual("1KDAbJH89XYZ", first.device_id)
        self.assertEqual("aaaaR08888", first.serial_number)
        self.assertEqual("Back Door", first.device_name)
        self.assertEqual("doorbell_call_status_offline", first.status)
        self.assertEqual(False, first.has_subscription)
        self.assertEqual(None, first.image_url)
        self.assertEqual("3dd2accadddd", first.house_id)

        second = doorbells[1]
        self.assertEqual("K98GiDT45GUL", second.device_id)
        self.assertEqual("tBXZR0Z35E", second.serial_number)
        self.assertEqual("Front Door", second.device_name)
        self.assertEqual("doorbell_call_status_online", second.status)
        self.assertEqual(True, second.has_subscription)
        self.assertEqual("https://image.com/vmk16naaaa7ibuey7sar.jpg", second.image_url)
        self.assertEqual("3dd2accaea08", second.house_id)

    @aioresponses()
    async def test_async_get_doorbell_detail(self, mock):
        expected_doorbell_image_url = "https://image.com/vmk16naaaa7ibuey7sar.jpg"
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_DOORBELL_URL)
            .format(doorbell_id="K98GiDT45GUL"),
            body=load_fixture("get_doorbell.json"),
        )
        mock.get(expected_doorbell_image_url, body="doorbell_image_mocked")

        api = ApiAsync(ClientSession())
        doorbell = await api.async_get_doorbell_detail(ACCESS_TOKEN, "K98GiDT45GUL")

        self.assertEqual("K98GiDT45GUL", doorbell.device_id)
        self.assertEqual("Front Door", doorbell.device_name)
        self.assertEqual("3dd2accaea08", doorbell.house_id)
        self.assertEqual("tBXZR0Z35E", doorbell.serial_number)
        self.assertEqual("2.3.0-RC153+201711151527", doorbell.firmware_version)
        self.assertEqual("doorbell_call_status_online", doorbell.status)
        self.assertEqual(96, doorbell.battery_level)
        self.assertEqual("gen1", doorbell.model)
        self.assertEqual(True, doorbell.is_online)
        self.assertEqual(False, doorbell.is_standby)
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T08:01:35Z"),
            doorbell.image_created_at_datetime,
        )
        self.assertEqual(True, doorbell.has_subscription)
        self.assertEqual(expected_doorbell_image_url, doorbell.image_url)
        self.assertEqual(
            await doorbell.async_get_doorbell_image(ClientSession()),
            b"doorbell_image_mocked",
        )

    @aioresponses()
    async def test_async_get_doorbell_image_token_expired(self, mock):
        expected_doorbell_image_url = "https://image.com/vmk16naaaa7ibuey7sar.jpg"

        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_DOORBELL_URL)
            .format(doorbell_id="K98GiDT45GUL"),
            body=load_fixture("get_doorbell.json"),
        )
        mock.get(expected_doorbell_image_url, status=401)

        api = ApiAsync(ClientSession())
        doorbell = await api.async_get_doorbell_detail(ACCESS_TOKEN, "K98GiDT45GUL")

        with self.assertRaises(ContentTokenExpired):
            await doorbell.async_get_doorbell_image(ClientSession())

    @aioresponses()
    async def test_async_get_doorbell_detail_missing_image(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_DOORBELL_URL)
            .format(doorbell_id="K98GiDT45GUL"),
            body=load_fixture("get_doorbell_missing_image.json"),
        )

        api = ApiAsync(ClientSession())
        doorbell = await api.async_get_doorbell_detail(ACCESS_TOKEN, "K98GiDT45GUL")

        self.assertEqual("K98GiDT45GUL", doorbell.device_id)
        self.assertEqual("Front Door", doorbell.device_name)
        self.assertEqual("3dd2accaea08", doorbell.house_id)
        self.assertEqual("tBXZR0Z35E", doorbell.serial_number)
        self.assertEqual("2.3.0-RC153+201711151527", doorbell.firmware_version)
        self.assertEqual("doorbell_call_status_online", doorbell.status)
        self.assertEqual(96, doorbell.battery_level)
        self.assertEqual(True, doorbell.is_online)
        self.assertEqual(False, doorbell.is_standby)
        self.assertEqual(None, doorbell.image_created_at_datetime)
        self.assertEqual(True, doorbell.has_subscription)
        self.assertEqual(None, doorbell.image_url)

    @aioresponses()
    async def test_async_get_doorbell_offline(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_DOORBELL_URL)
            .format(doorbell_id="231ee2168dd0"),
            body=load_fixture("get_doorbell.offline.json"),
        )

        api = ApiAsync(ClientSession())
        doorbell = await api.async_get_doorbell_detail(ACCESS_TOKEN, "231ee2168dd0")

        self.assertEqual("231ee2168dd0", doorbell.device_id)
        self.assertEqual("My Door", doorbell.device_name)
        self.assertEqual("houseid", doorbell.house_id)
        self.assertEqual("abcd", doorbell.serial_number)
        self.assertEqual("3.1.0-HYDRC75+201909251139", doorbell.firmware_version)
        self.assertEqual("doorbell_offline", doorbell.status)
        self.assertEqual(81, doorbell.battery_level)
        self.assertEqual(False, doorbell.is_online)
        self.assertEqual(False, doorbell.is_standby)
        self.assertEqual(
            dateutil.parser.parse("2019-02-20T23:52:46Z"),
            doorbell.image_created_at_datetime,
        )
        self.assertEqual(True, doorbell.has_subscription)
        self.assertEqual("https://res.cloudinary.com/x.jpg", doorbell.image_url)
        self.assertEqual("hydra1", doorbell.model)

    @aioresponses()
    async def test_async_get_doorbell_gen2_full_battery_detail(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_DOORBELL_URL)
            .format(doorbell_id="did"),
            body=load_fixture("get_doorbell.battery_full.json"),
        )

        api = ApiAsync(ClientSession())
        doorbell = await api.async_get_doorbell_detail(ACCESS_TOKEN, "did")

        self.assertEqual(100, doorbell.battery_level)

    @aioresponses()
    async def test_async_get_doorbell_gen2_medium_battery_detail(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_DOORBELL_URL)
            .format(doorbell_id="did"),
            body=load_fixture("get_doorbell.battery_medium.json"),
        )

        api = ApiAsync(ClientSession())
        doorbell = await api.async_get_doorbell_detail(ACCESS_TOKEN, "did")

        self.assertEqual(75, doorbell.battery_level)

    @aioresponses()
    async def test_async_get_doorbell_gen2_low_battery_detail(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_DOORBELL_URL)
            .format(doorbell_id="did"),
            body=load_fixture("get_doorbell.battery_low.json"),
        )

        api = ApiAsync(ClientSession())
        doorbell = await api.async_get_doorbell_detail(ACCESS_TOKEN, "did")

        self.assertEqual(10, doorbell.battery_level)

    @aioresponses()
    async def test_async_get_locks(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_LOCKS_URL),
            body=load_fixture("get_locks.json"),
        )

        api = ApiAsync(ClientSession())
        locks = sorted(
            await api.async_get_locks(ACCESS_TOKEN), key=lambda d: d.device_id
        )

        self.assertEqual(2, len(locks))

        first = locks[0]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.device_id)
        self.assertEqual("Front Door Lock", first.device_name)
        self.assertEqual("000000000000", first.house_id)
        self.assertEqual(True, first.is_operable)

        second = locks[1]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF9999", second.device_id)
        self.assertEqual("Back Door Lock", second.device_name)
        self.assertEqual("000000000011", second.house_id)
        self.assertEqual(False, second.is_operable)

    @aioresponses()
    async def test_async_get_locks_yale_home_brand(self, mock):
        mock.get(
            ApiCommon(Brand.YALE_HOME).get_brand_url(API_GET_LOCKS_URL),
            body=load_fixture("get_locks.json"),
        )

        api = ApiAsync(ClientSession(), brand=Brand.YALE_HOME)
        locks = sorted(
            await api.async_get_locks(ACCESS_TOKEN), key=lambda d: d.device_id
        )

        self.assertEqual(2, len(locks))

        first = locks[0]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.device_id)
        self.assertEqual("Front Door Lock", first.device_name)
        self.assertEqual("000000000000", first.house_id)
        self.assertEqual(True, first.is_operable)

        second = locks[1]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF9999", second.device_id)
        self.assertEqual("Back Door Lock", second.device_name)
        self.assertEqual("000000000011", second.house_id)
        self.assertEqual(False, second.is_operable)

    @aioresponses()
    async def test_async_get_operable_locks(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_LOCKS_URL),
            body=load_fixture("get_locks.json"),
        )

        api = ApiAsync(ClientSession())
        locks = await api.async_get_operable_locks(ACCESS_TOKEN)

        self.assertEqual(1, len(locks))

        first = locks[0]
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.device_id)
        self.assertEqual("Front Door Lock", first.device_name)
        self.assertEqual("000000000000", first.house_id)
        self.assertEqual(True, first.is_operable)

    @aioresponses()
    async def test_async_get_lock_detail_with_doorsense_bridge_online(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_URL)
            .format(lock_id="ABC"),
            body=load_fixture("get_lock.online_with_doorsense.json"),
        )

        api = ApiAsync(ClientSession())
        lock = await api.async_get_lock_detail(ACCESS_TOKEN, "ABC")

        self.assertEqual("ABC", lock.device_id)
        self.assertEqual("Online door with doorsense", lock.device_name)
        self.assertEqual("123", lock.house_id)
        self.assertEqual("XY", lock.serial_number)
        self.assertEqual("undefined-4.3.0-1.8.14", lock.firmware_version)
        self.assertEqual(92, lock.battery_level)
        self.assertEqual("AUG-MD01", lock.model)
        self.assertEqual(None, lock.keypad)
        self.assertIsInstance(lock.bridge, BridgeDetail)
        self.assertIsInstance(lock.bridge.status, BridgeStatusDetail)
        self.assertEqual(BridgeStatus.ONLINE, lock.bridge.status.current)
        self.assertEqual(True, lock.bridge_is_online)
        self.assertEqual(True, lock.bridge.operative)
        self.assertEqual(True, lock.doorsense)

        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(LockDoorStatus.OPEN, lock.door_state)
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.lock_status_datetime
        )
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.door_state_datetime
        )

    @aioresponses()
    async def test_async_get_lock_detail_with_doorsense_disabled_bridge_online(
        self, mock
    ):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_URL)
            .format(lock_id="ABC"),
            body=load_fixture("get_lock.online_with_doorsense_disabled.json"),
        )

        api = ApiAsync(ClientSession())
        lock = await api.async_get_lock_detail(ACCESS_TOKEN, "ABC")

        self.assertEqual("ABC", lock.device_id)
        self.assertEqual("Online door with doorsense disabled", lock.device_name)
        self.assertEqual("123", lock.house_id)
        self.assertEqual("XY", lock.serial_number)
        self.assertEqual("undefined-4.3.0-1.8.14", lock.firmware_version)
        self.assertEqual(92, lock.battery_level)
        self.assertEqual("AUG-MD01", lock.model)
        self.assertEqual(lock.bridge.hyper_bridge, True)
        self.assertEqual(None, lock.keypad)
        self.assertIsInstance(lock.bridge, BridgeDetail)
        self.assertIsInstance(lock.bridge.status, BridgeStatusDetail)
        self.assertEqual(BridgeStatus.ONLINE, lock.bridge.status.current)
        self.assertEqual(True, lock.bridge_is_online)
        self.assertEqual(True, lock.bridge.operative)
        self.assertEqual(False, lock.doorsense)

        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(LockDoorStatus.DISABLED, lock.door_state)
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.lock_status_datetime
        )
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.door_state_datetime
        )

    @aioresponses()
    async def test_async_get_lock_detail_bridge_online(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_URL)
            .format(lock_id="A6697750D607098BAE8D6BAA11EF8063"),
            body=load_fixture("get_lock.online.json"),
        )

        api = ApiAsync(ClientSession())
        lock = await api.async_get_lock_detail(
            ACCESS_TOKEN, "A6697750D607098BAE8D6BAA11EF8063"
        )

        assert lock.doorbell is False
        assert lock.unlatch_supported is False
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", lock.device_id)
        self.assertEqual("Front Door Lock", lock.device_name)
        self.assertEqual("000000000000", lock.house_id)
        self.assertEqual("X2FSW05DGA", lock.serial_number)
        self.assertEqual("109717e9-3.0.44-3.0.30", lock.firmware_version)
        self.assertEqual(88, lock.battery_level)
        self.assertEqual("AUG-SL02-M02-S02", lock.model)
        self.assertEqual("Medium", lock.keypad.battery_level)
        self.assertEqual(62, lock.keypad.battery_percentage)
        self.assertEqual("5bc65c24e6ef2a263e1450a8", lock.keypad.device_id)
        self.assertIsInstance(lock.bridge, BridgeDetail)
        self.assertEqual(True, lock.bridge_is_online)
        self.assertEqual(True, lock.bridge.operative)
        self.assertEqual(True, lock.doorsense)
        self.assertEqual(lock.bridge.hyper_bridge, False)

        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(LockDoorStatus.CLOSED, lock.door_state)
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.lock_status_datetime
        )
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.door_state_datetime
        )

    @aioresponses()
    async def test_async_get_lock_with_doorbell(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_URL)
            .format(lock_id="A6697750D607098BAE8D6BAA11EF8063"),
            body=load_fixture("lock_with_doorbell.online.json"),
        )

        api = ApiAsync(ClientSession())
        lock = await api.async_get_lock_detail(
            ACCESS_TOKEN, "A6697750D607098BAE8D6BAA11EF8063"
        )
        self.assertEqual(62, lock.keypad.battery_percentage)

        assert lock.doorbell is True

    @aioresponses()
    async def test_async_get_lock_with_unlatch(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_URL)
            .format(lock_id="68895DD075A1444FAD4C00B273EEEF28"),
            body=load_fixture("lock_with_unlatch.online.json"),
        )

        api = ApiAsync(ClientSession())
        lock = await api.async_get_lock_detail(
            ACCESS_TOKEN, "68895DD075A1444FAD4C00B273EEEF28"
        )

        assert lock.unlatch_supported is True

    @aioresponses()
    async def test_async_get_lock_capabilities(self, mock):
        capabilities_response = {
            "lock": {
                "concurrentBLE": 2,
                "batteryType": "AA",
                "doorSense": True,
                "hasMagnetometer": False,
                "hasIntegratedWiFi": False,
                "scheduledSmartAlerts": True,
                "standalone": False,
                "bluetooth": True,
                "slotRange": None,
                "integratedKeypad": True,
                "entryCodeSlots": True,
                "pinSlotMax": 100,
                "pinSlotMin": 1,
                "supportsRFID": True,
                "supportsRFIDLegacy": False,
                "supportsRFIDCredential": True,
                "supportsRFIDOnlyAccess": True,
                "supportsRFIDWithCode": False,
                "supportsSecureMode": False,
                "supportsSecureModeCodeDisable": False,
                "supportsSecureModeMobileControl": False,
                "supportsFingerprintCredential": True,
                "supportsDeliveryMode": False,
                "supportsSchedulePerUser": True,
                "supportsFingerprintOnlyAccess": True,
                "batteryLifeMS": 21513600000,
                "supportedPartners": [],
                "unlatch": True,
            }
        }

        serial_number = "TEST123"
        mock.get(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_CAPABILITIES_URL)
            + f"?serialNumber={serial_number}&topLevelHost=true",
            payload=capabilities_response,
        )

        api = ApiAsync(ClientSession())
        capabilities = await api.async_get_lock_capabilities(
            ACCESS_TOKEN, serial_number
        )

        self.assertEqual(capabilities, capabilities_response)
        self.assertTrue(capabilities["lock"]["unlatch"])

    @aioresponses()
    async def test_async_get_v2_lock_detail_bridge_online(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_URL)
            .format(lock_id="snip"),
            body=load_fixture("get_lock_v2.online.json"),
        )

        api = ApiAsync(ClientSession())
        lock = await api.async_get_lock_detail(ACCESS_TOKEN, "snip")

        self.assertEqual("snip", lock.device_id)
        self.assertEqual("Front Door", lock.device_name)
        self.assertEqual("snip", lock.house_id)
        self.assertEqual("snip", lock.serial_number)
        self.assertEqual("3.0.44-3.0.29", lock.firmware_version)
        self.assertEqual(96, lock.battery_level)
        self.assertEqual("AUG-SL02-M02-S02", lock.model)
        self.assertIsInstance(lock.bridge, BridgeDetail)
        self.assertEqual(True, lock.bridge_is_online)
        self.assertEqual(True, lock.bridge.operative)
        self.assertEqual(False, lock.doorsense)
        self.assertEqual(lock.bridge.hyper_bridge, False)

        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(LockDoorStatus.DISABLED, lock.door_state)
        self.assertEqual(
            lock.offline_keys,
            {
                "created": [],
                "createdhk": [],
                "deleted": [],
                "loaded": [
                    {
                        "UserID": "XXXXXX",
                        "created": "2022-01-14T21:14:50.153Z",
                        "key": "XXXXXX",
                        "loaded": "2022-01-14T21:14:54.568Z",
                        "slot": 1,
                    }
                ],
            },
        )
        self.assertEqual(
            lock.loaded_offline_keys,
            [
                {
                    "UserID": "XXXXXX",
                    "created": "2022-01-14T21:14:50.153Z",
                    "key": "XXXXXX",
                    "loaded": "2022-01-14T21:14:54.568Z",
                    "slot": 1,
                }
            ],
        )
        self.assertEqual(lock.offline_key, "XXXXXX")
        self.assertEqual(lock.offline_slot, 1)
        self.assertEqual(lock.mac_address, "SNIP")

    @aioresponses()
    async def test_async_get_lock_detail_bridge_offline(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_URL)
            .format(lock_id="ABC"),
            body=load_fixture("get_lock.offline.json"),
        )

        api = ApiAsync(ClientSession())
        lock = await api.async_get_lock_detail(ACCESS_TOKEN, "ABC")

        self.assertEqual("ABC", lock.device_id)
        self.assertEqual("Test", lock.device_name)
        self.assertEqual("houseid", lock.house_id)
        self.assertEqual("ABC", lock.serial_number)
        self.assertEqual("undefined-1.59.0-1.13.2", lock.firmware_version)
        self.assertEqual(-100, lock.battery_level)
        self.assertEqual("AUG-X", lock.model)
        self.assertEqual(False, lock.bridge_is_online)
        self.assertEqual(None, lock.keypad)
        self.assertEqual(None, lock.bridge)
        self.assertEqual(False, lock.doorsense)

        self.assertEqual(LockStatus.UNKNOWN, lock.lock_status)
        self.assertEqual(LockDoorStatus.DISABLED, lock.door_state)
        self.assertEqual(None, lock.lock_status_datetime)
        self.assertEqual(None, lock.door_state_datetime)

    @aioresponses()
    async def test_async_get_lock_detail_doorsense_init_state(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_URL)
            .format(lock_id="A6697750D607098BAE8D6BAA11EF8063"),
            body=load_fixture("get_lock.doorsense_init.json"),
        )

        api = ApiAsync(ClientSession())
        lock = await api.async_get_lock_detail(
            ACCESS_TOKEN, "A6697750D607098BAE8D6BAA11EF8063"
        )

        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", lock.device_id)
        self.assertEqual("Front Door Lock", lock.device_name)
        self.assertEqual("000000000000", lock.house_id)
        self.assertEqual("X2FSW05DGA", lock.serial_number)
        self.assertEqual("109717e9-3.0.44-3.0.30", lock.firmware_version)
        self.assertEqual(88, lock.battery_level)
        self.assertEqual("Medium", lock.keypad.battery_level)
        self.assertEqual("5bc65c24e6ef2a263e1450a8", lock.keypad.device_id)
        self.assertEqual("AK-R1", lock.keypad.model)
        self.assertEqual("Front Door Lock Keypad", lock.keypad.device_name)
        self.assertIsInstance(lock.bridge, BridgeDetail)
        self.assertEqual(True, lock.bridge_is_online)
        self.assertEqual(True, lock.bridge.operative)
        self.assertEqual(False, lock.doorsense)

        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(LockDoorStatus.DISABLED, lock.door_state)
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.lock_status_datetime
        )
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.door_state_datetime
        )

        lock.lock_status = LockStatus.UNLATCHED
        self.assertEqual(LockStatus.UNLATCHED, lock.lock_status)

        lock.lock_status = LockStatus.UNLOCKED
        self.assertEqual(LockStatus.UNLOCKED, lock.lock_status)

        lock.door_state = LockDoorStatus.OPEN
        self.assertEqual(LockDoorStatus.OPEN, lock.door_state)

        lock.lock_status_datetime = dateutil.parser.parse("2020-12-10T04:48:30.272Z")
        self.assertEqual(
            dateutil.parser.parse("2020-12-10T04:48:30.272Z"), lock.lock_status_datetime
        )
        lock.door_state_datetime = dateutil.parser.parse("2019-12-10T04:48:30.272Z")
        self.assertEqual(
            dateutil.parser.parse("2019-12-10T04:48:30.272Z"), lock.door_state_datetime
        )
        assert isinstance(lock.raw, dict)

    @aioresponses()
    async def test_async_get_lock_status_with_locked_response(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_STATUS_URL)
            .format(lock_id=lock_id),
            body='{"status": "kAugLockState_Locked"}',
        )

        api = ApiAsync(ClientSession())
        status = await api.async_get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.LOCKED, status)

    @aioresponses()
    async def test_async_get_lock_and_door_status_with_locked_response(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_STATUS_URL)
            .format(lock_id=lock_id),
            body='{"status": "kAugLockState_Locked"'
            ',"doorState": "kAugLockDoorState_Closed"}',
        )

        api = ApiAsync(ClientSession())
        status, door_status = await api.async_get_lock_status(
            ACCESS_TOKEN, lock_id, True
        )

        self.assertEqual(LockStatus.LOCKED, status)
        self.assertEqual(LockDoorStatus.CLOSED, door_status)

    @aioresponses()
    async def test_async_get_lock_status_with_unlocked_response(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_STATUS_URL)
            .format(lock_id=lock_id),
            body='{"status": "kAugLockState_Unlocked"}',
        )

        api = ApiAsync(ClientSession())
        status = await api.async_get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNLOCKED, status)

    @aioresponses()
    async def test_async_get_lock_status_with_unknown_status_response(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_STATUS_URL)
            .format(lock_id=lock_id),
            body='{"status": "not_advertising"}',
        )

        api = ApiAsync(ClientSession())
        status = await api.async_get_lock_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNKNOWN, status)

    @aioresponses()
    async def test_async_get_lock_door_status_with_closed_response(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_STATUS_URL)
            .format(lock_id=lock_id),
            body='{"doorState": "kAugLockDoorState_Closed"}',
        )

        api = ApiAsync(ClientSession())
        door_status = await api.async_get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.CLOSED, door_status)

    @aioresponses()
    async def test_async_get_lock_door_status_with_open_response(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_STATUS_URL)
            .format(lock_id=lock_id),
            body='{"doorState": "kAugLockDoorState_Open"}',
        )

        api = ApiAsync(ClientSession())
        door_status = await api.async_get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.OPEN, door_status)

    @aioresponses()
    async def test_async_get_lock_and_door_status_with_open_response(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_STATUS_URL)
            .format(lock_id=lock_id),
            body='{"status": "kAugLockState_Unlocked"'
            ',"doorState": "kAugLockDoorState_Open"}',
        )

        api = ApiAsync(ClientSession())
        door_status, status = await api.async_get_lock_door_status(
            ACCESS_TOKEN, lock_id, True
        )

        self.assertEqual(LockDoorStatus.OPEN, door_status)
        self.assertEqual(LockStatus.UNLOCKED, status)

    @aioresponses()
    async def test_async_get_lock_door_status_with_unknown_response(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_LOCK_STATUS_URL)
            .format(lock_id=lock_id),
            body='{"doorState": "not_advertising"}',
        )

        api = ApiAsync(ClientSession())
        door_status = await api.async_get_lock_door_status(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockDoorStatus.UNKNOWN, door_status)

    @aioresponses()
    async def test_async_lock_from_fixture(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_LOCK_URL)
            .format(lock_id=lock_id),
            body=load_fixture("lock.json"),
        )

        api = ApiAsync(ClientSession())
        status = await api.async_lock(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.LOCKED, status)

    @aioresponses()
    async def test_async_unlock_from_fixture(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLOCK_URL)
            .format(lock_id=lock_id),
            body=load_fixture("unlock.json"),
        )

        api = ApiAsync(ClientSession())
        status = await api.async_unlock(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNLOCKED, status)

    @aioresponses()
    async def test_async_lock_return_activities_from_fixture(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_LOCK_URL)
            .format(lock_id=lock_id),
            body=load_fixture("lock.json"),
        )

        api = ApiAsync(ClientSession())
        activities = await api.async_lock_return_activities(ACCESS_TOKEN, lock_id)
        expected_lock_dt = (
            dateutil.parser.parse("2020-02-19T19:44:54.371Z")
            .astimezone(tz=tzlocal())
            .replace(tzinfo=None)
        )

        self.assertEqual(len(activities), 2)
        self.assertIsInstance(activities[0], yalexs.activity.LockOperationActivity)
        self.assertEqual(activities[0].device_id, "ABC123")
        self.assertEqual(activities[0].device_type, "lock")
        self.assertEqual(activities[0].action, "lock")
        self.assertEqual(activities[0].activity_start_time, expected_lock_dt)
        self.assertEqual(activities[0].activity_end_time, expected_lock_dt)
        self.assertIsInstance(activities[1], yalexs.activity.DoorOperationActivity)
        self.assertEqual(activities[1].device_id, "ABC123")
        self.assertEqual(activities[1].device_type, "lock")
        self.assertEqual(activities[1].action, "doorclosed")
        self.assertEqual(activities[0].activity_start_time, expected_lock_dt)
        self.assertEqual(activities[0].activity_end_time, expected_lock_dt)

    @aioresponses()
    async def test_async_unlatch_return_activities_from_fixture(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLATCH_URL)
            .format(lock_id=lock_id),
            body=load_fixture("unlatch.json"),
        )

        api = ApiAsync(ClientSession())
        activities = await api.async_unlatch_return_activities(ACCESS_TOKEN, lock_id)
        expected_unlatch_dt = (
            dateutil.parser.parse("2024-03-20T06:39:42.192Z")
            .astimezone(tz=tzlocal())
            .replace(tzinfo=None)
        )

        self.assertEqual(len(activities), 2)
        self.assertIsInstance(activities[0], yalexs.activity.LockOperationActivity)
        self.assertEqual(activities[0].device_id, "ABC123")
        self.assertEqual(activities[0].device_type, "lock")
        self.assertEqual(activities[0].action, "unlatch")
        self.assertEqual(activities[0].activity_start_time, expected_unlatch_dt)
        self.assertEqual(activities[0].activity_end_time, expected_unlatch_dt)
        self.assertIsInstance(activities[1], yalexs.activity.DoorOperationActivity)
        self.assertEqual(activities[1].device_id, "ABC123")
        self.assertEqual(activities[1].device_type, "lock")
        self.assertEqual(activities[1].action, "dooropen")
        self.assertEqual(activities[1].activity_start_time, expected_unlatch_dt)
        self.assertEqual(activities[1].activity_end_time, expected_unlatch_dt)

    @aioresponses()
    async def test_async_unlock_return_activities_from_fixture(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLOCK_URL)
            .format(lock_id=lock_id),
            body=load_fixture("unlock.json"),
        )

        api = ApiAsync(ClientSession())
        activities = await api.async_unlock_return_activities(ACCESS_TOKEN, lock_id)
        expected_unlock_dt = (
            dateutil.parser.parse("2020-02-19T19:44:26.745Z")
            .astimezone(tz=tzlocal())
            .replace(tzinfo=None)
        )

        self.assertEqual(len(activities), 2)
        self.assertIsInstance(activities[0], yalexs.activity.LockOperationActivity)
        self.assertEqual(activities[0].device_id, "ABC")
        self.assertEqual(activities[0].device_type, "lock")
        self.assertEqual(activities[0].action, "unlock")
        self.assertEqual(activities[0].activity_start_time, expected_unlock_dt)
        self.assertEqual(activities[0].activity_end_time, expected_unlock_dt)
        self.assertIsInstance(activities[1], yalexs.activity.DoorOperationActivity)
        self.assertEqual(activities[1].device_id, "ABC")
        self.assertEqual(activities[1].device_type, "lock")
        self.assertEqual(activities[1].action, "doorclosed")
        self.assertEqual(activities[1].activity_start_time, expected_unlock_dt)
        self.assertEqual(activities[1].activity_end_time, expected_unlock_dt)

    @aioresponses()
    async def test_async_lock_return_activities_from_fixture_with_no_doorstate(
        self, mock
    ):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_LOCK_URL)
            .format(lock_id=lock_id),
            body=load_fixture("lock_without_doorstate.json"),
        )

        api = ApiAsync(ClientSession())
        activities = await api.async_lock_return_activities(ACCESS_TOKEN, lock_id)
        expected_lock_dt = (
            dateutil.parser.parse("2020-02-19T19:44:54.371Z")
            .astimezone(tz=tzlocal())
            .replace(tzinfo=None)
        )

        self.assertEqual(len(activities), 1)
        self.assertIsInstance(activities[0], yalexs.activity.LockOperationActivity)
        self.assertEqual(activities[0].device_id, "ABC123")
        self.assertEqual(activities[0].device_type, "lock")
        self.assertEqual(activities[0].action, "lock")
        self.assertEqual(activities[0].activity_start_time, expected_lock_dt)
        self.assertEqual(activities[0].activity_end_time, expected_lock_dt)

    @aioresponses()
    async def test_async_unlatch_return_activities_from_fixture_with_no_doorstate(
        self, mock
    ):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLATCH_URL)
            .format(lock_id=lock_id),
            body=load_fixture("unlatch_without_doorstate.json"),
        )

        api = ApiAsync(ClientSession())
        activities = await api.async_unlatch_return_activities(ACCESS_TOKEN, lock_id)
        expected_unlatch_dt = (
            dateutil.parser.parse("2024-03-20T06:39:42.192Z")
            .astimezone(tz=tzlocal())
            .replace(tzinfo=None)
        )

        self.assertEqual(len(activities), 1)
        self.assertIsInstance(activities[0], yalexs.activity.LockOperationActivity)
        self.assertEqual(activities[0].device_id, "ABC123")
        self.assertEqual(activities[0].device_type, "lock")
        self.assertEqual(activities[0].action, "unlatch")
        self.assertEqual(activities[0].activity_start_time, expected_unlatch_dt)
        self.assertEqual(activities[0].activity_end_time, expected_unlatch_dt)

    @aioresponses()
    async def test_async_unlock_return_activities_from_fixture_with_no_doorstate(
        self, mock
    ):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLOCK_URL)
            .format(lock_id=lock_id),
            body=load_fixture("unlock_without_doorstate.json"),
        )

        api = ApiAsync(ClientSession())
        activities = await api.async_unlock_return_activities(ACCESS_TOKEN, lock_id)
        expected_unlock_dt = (
            dateutil.parser.parse("2020-02-19T19:44:26.745Z")
            .astimezone(tz=tzlocal())
            .replace(tzinfo=None)
        )

        self.assertEqual(len(activities), 1)
        self.assertIsInstance(activities[0], yalexs.activity.LockOperationActivity)
        self.assertEqual(activities[0].device_id, "ABC123")
        self.assertEqual(activities[0].device_type, "lock")
        self.assertEqual(activities[0].action, "unlock")
        self.assertEqual(activities[0].activity_start_time, expected_unlock_dt)
        self.assertEqual(activities[0].activity_end_time, expected_unlock_dt)

    @aioresponses()
    async def test_async_lock(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_LOCK_URL)
            .format(lock_id=lock_id),
            body='{"status":"locked",'
            '"dateTime":"2017-12-10T07:43:39.056Z",'
            '"isLockStatusChanged":false,'
            '"valid":true}',
        )

        api = ApiAsync(ClientSession())
        status = await api.async_lock(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.LOCKED, status)

    @aioresponses()
    async def test_async_lock_async_old_bridge(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_LOCK_ASYNC_URL)
            .format(lock_id=lock_id),
        )

        api = ApiAsync(ClientSession())
        await api.async_lock_async(ACCESS_TOKEN, lock_id, hyper_bridge=False)

    @aioresponses()
    async def test_async_lock_async_new_bridge(self, mock):
        lock_id = 1234
        base_url = ApiCommon(DEFAULT_BRAND).get_brand_url(API_LOCK_ASYNC_URL)
        mock.put(f"{base_url}{HYPER_BRIDGE_PARAM}".format(lock_id=lock_id))

        api = ApiAsync(ClientSession())
        await api.async_lock_async(ACCESS_TOKEN, lock_id)

    @aioresponses()
    async def test_async_unlatch(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLATCH_URL)
            .format(lock_id=lock_id),
            body='{"status": "unlatched"}',
        )

        api = ApiAsync(ClientSession())
        status = await api.async_unlatch(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNLATCHED, status)

    @aioresponses()
    async def test_async_unlatch_async_old_bridge(self, mock):
        lock_id = 1234

        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLATCH_ASYNC_URL)
            .format(lock_id=lock_id)
        )

        api = ApiAsync(ClientSession())
        await api.async_unlatch_async(ACCESS_TOKEN, lock_id, hyper_bridge=False)

    @aioresponses()
    async def test_async_unlatch_async_new_bridge(self, mock):
        lock_id = 1234
        base_url = ApiCommon(DEFAULT_BRAND).get_brand_url(API_UNLATCH_ASYNC_URL)
        mock.put(f"{base_url}{HYPER_BRIDGE_PARAM}".format(lock_id=lock_id))

        api = ApiAsync(ClientSession())
        await api.async_unlatch_async(ACCESS_TOKEN, lock_id, hyper_bridge=True)

    @aioresponses()
    async def test_async_unlock(self, mock):
        lock_id = 1234
        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLOCK_URL)
            .format(lock_id=lock_id),
            body='{"status": "unlocked"}',
        )

        api = ApiAsync(ClientSession())
        status = await api.async_unlock(ACCESS_TOKEN, lock_id)

        self.assertEqual(LockStatus.UNLOCKED, status)

    @aioresponses()
    async def test_async_unlock_async_old_bridge(self, mock):
        lock_id = 1234

        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_UNLOCK_ASYNC_URL)
            .format(lock_id=lock_id)
        )

        api = ApiAsync(ClientSession())
        await api.async_unlock_async(ACCESS_TOKEN, lock_id, hyper_bridge=False)

    @aioresponses()
    async def test_async_unlock_async_new_bridge(self, mock):
        lock_id = 1234
        base_url = ApiCommon(DEFAULT_BRAND).get_brand_url(API_UNLOCK_ASYNC_URL)
        mock.put(f"{base_url}{HYPER_BRIDGE_PARAM}".format(lock_id=lock_id))

        api = ApiAsync(ClientSession())
        await api.async_unlock_async(ACCESS_TOKEN, lock_id, hyper_bridge=True)

    @aioresponses()
    async def test_async_status_async_old_bridge(self, mock):
        lock_id = 1234

        mock.put(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_STATUS_ASYNC_URL)
            .format(lock_id=lock_id)
        )

        api = ApiAsync(ClientSession())
        await api.async_status_async(ACCESS_TOKEN, lock_id, hyper_bridge=False)

    @aioresponses()
    async def test_async_status_async_new_bridge(self, mock):
        lock_id = 1234
        base_url = ApiCommon(DEFAULT_BRAND).get_brand_url(API_STATUS_ASYNC_URL)
        mock.put(f"{base_url}{HYPER_BRIDGE_PARAM}".format(lock_id=lock_id))

        api = ApiAsync(ClientSession())
        await api.async_status_async(ACCESS_TOKEN, lock_id)

    @aioresponses()
    async def test_async_get_pins(self, mock):
        lock_id = 1234
        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_PINS_URL)
            .format(lock_id=lock_id),
            body=load_fixture("get_pins.json"),
        )

        api = ApiAsync(ClientSession())
        pins = await api.async_get_pins(ACCESS_TOKEN, lock_id)

        self.assertEqual(1, len(pins))

        first = pins[0]
        self.assertEqual("epoZ87XSPqxlFdsaYyJiRRVR", first.pin_id)
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", first.lock_id)
        self.assertEqual("c3b3a94f-473z-61a3-a8d1-a6e99482787a", first.user_id)
        self.assertEqual("in-use", first.state)
        self.assertEqual("123456", first.pin)
        self.assertEqual(646545456465161, first.slot)
        self.assertEqual("one-time", first.access_type)
        self.assertEqual("John", first.first_name)
        self.assertEqual("Doe", first.last_name)
        self.assertEqual(True, first.unverified)
        self.assertEqual(utc_of(2016, 11, 26, 22, 27, 11, 176000), first.created_at)
        self.assertEqual(utc_of(2017, 11, 23, 00, 42, 19, 470000), first.updated_at)
        self.assertEqual(utc_of(2017, 12, 10, 3, 12, 55, 563000), first.loaded_date)
        self.assertEqual(utc_of(2018, 1, 1, 1, 1, 1, 563000), first.access_start_time)
        self.assertEqual(utc_of(2018, 12, 1, 1, 1, 1, 563000), first.access_end_time)
        self.assertEqual(utc_of(2018, 11, 5, 10, 2, 41, 684000), first.access_times)

    @aioresponses()
    async def test_async_get_house_activities(self, mock):
        house_id = 1234

        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_HOUSE_ACTIVITIES_URL)
            .format(house_id=house_id)
            + "?limit=8",
            body=load_fixture("get_house_activities.json"),
        )

        api = ApiAsync(ClientSession())
        activities = await api.async_get_house_activities(ACCESS_TOKEN, house_id)

        self.assertEqual(10, len(activities))

        self.assertIsInstance(activities[0], yalexs.activity.LockOperationActivity)
        self.assertIsInstance(activities[1], yalexs.activity.LockOperationActivity)
        self.assertIsInstance(activities[2], yalexs.activity.LockOperationActivity)
        self.assertIsInstance(activities[3], yalexs.activity.LockOperationActivity)
        self.assertIsInstance(activities[4], yalexs.activity.LockOperationActivity)
        self.assertIsInstance(activities[5], yalexs.activity.DoorOperationActivity)
        self.assertIsInstance(activities[6], yalexs.activity.DoorOperationActivity)
        self.assertIsInstance(activities[7], yalexs.activity.DoorOperationActivity)
        self.assertIsInstance(activities[8], yalexs.activity.LockOperationActivity)
        self.assertIsInstance(activities[9], yalexs.activity.LockOperationActivity)

    @aioresponses()
    async def test_async_get_retry_raises_our_exception_class(self, mock):
        house_id = 1234

        mock.get(
            ApiCommon(DEFAULT_BRAND)
            .get_brand_url(API_GET_HOUSE_ACTIVITIES_URL)
            .format(house_id=house_id)
            + "?limit=8",
            exception=ClientOSError("any"),
        )

        api = ApiAsync(ClientSession())
        with (
            patch.object(api_async, "API_EXCEPTION_RETRY_TIME", 0),
            pytest.raises(AugustApiAIOHTTPError),
        ):
            await api.async_get_house_activities(ACCESS_TOKEN, house_id)

    @aioresponses()
    async def test_async_refresh_access_token(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_HOUSES_URL),
            body="{}",
            headers={"x-august-access-token": "xyz"},
        )

        api = ApiAsync(ClientSession())
        new_token = await api.async_refresh_access_token("token")
        assert new_token == "xyz"

    @aioresponses()
    async def test_async_validate_verification_code(self, mock):
        last_args = {}

        def response_callback(url, **kwargs):
            last_args.update(kwargs)
            return CallbackResult(status=200, body="{}")

        mock.post(
            ApiCommon(DEFAULT_BRAND).get_brand_url(
                API_VALIDATE_VERIFICATION_CODE_URLS["email"]
            ),
            callback=response_callback,
        )

        api = ApiAsync(ClientSession())
        await api.async_validate_verification_code(
            ACCESS_TOKEN, "email", "emailaddress", 123456
        )
        assert last_args["json"] == {"code": "123456", "email": "emailaddress"}

    async def test__raise_response_exceptions(self):
        loop = mock.Mock()
        request_info = mock.Mock()
        request_info.status.return_value = 428
        session = ClientSession()
        four_two_eight = MockedResponse(
            "get",
            URL("http://code404.tld"),
            request_info=request_info,
            writer=mock.Mock(),
            continue100=None,
            timer=TimerNoop(),
            traces=[],
            status=404,
            loop=loop,
            session=session,
        )

        try:
            _raise_response_exceptions(four_two_eight)
        except Exception as err:  # noqa: BLE001
            self.assertIsInstance(err, AugustApiAIOHTTPError)

        ERROR_MAP = {
            560: "The operation failed with error code 560: 560.",
            422: "The operation failed because the bridge (connect) is offline: 422",
            423: "The operation failed because the bridge (connect) is in use: 423",
            408: "The operation timed out because the bridge (connect) failed to respond: 408",
        }

        for status_code in ERROR_MAP:
            mocked_response = MockedResponse(
                "get",
                URL("http://code.any.tld"),
                request_info=request_info,
                writer=mock.Mock(),
                continue100=None,
                timer=TimerNoop(),
                traces=[],
                status=status_code,
                loop=loop,
                session=session,
            )

            try:
                _raise_response_exceptions(mocked_response)
            except AugustApiAIOHTTPError as err:
                self.assertEqual(str(err), ERROR_MAP[status_code])

    @aioresponses()
    async def test_async_get_usern(self, mock):
        mock.get(
            ApiCommon(DEFAULT_BRAND).get_brand_url(API_GET_USER_URL),
            body='{"UserID": "abc"}',
        )

        api = ApiAsync(ClientSession())
        user_details = await api.async_get_user("token")
        assert user_details == {"UserID": "abc"}


class MockedResponse(ClientResponse):
    def __init__(self, *args, **kwargs):
        content = kwargs.pop("content", None)
        status = kwargs.pop("status", None)
        super().__init__(*args, **kwargs)
        self._mocked_content = content
        self._mocked_status = status

    @property
    def content(self):
        return self._mocked_content

    @property
    def reason(self):
        return self._mocked_status

    @property
    def status(self):
        return self._mocked_status


@pytest.mark.parametrize(
    "status_code",
    [502, 429],
)
@pytest.mark.asyncio
async def test_retry_502_429(status_code: int, mock_aioresponse: aioresponses) -> None:
    last_args = {}
    attempt = 0

    def response_callback(url, **kwargs):
        nonlocal attempt
        attempt += 1
        last_args.update(kwargs)
        if attempt == 1:
            return CallbackResult(status=status_code, body="{}")
        return CallbackResult(status=200, body="{}")

    for _ in range(2):
        mock_aioresponse.post(
            ApiCommon(DEFAULT_BRAND).get_brand_url(
                API_VALIDATE_VERIFICATION_CODE_URLS["email"]
            ),
            callback=response_callback,
        )

    api = ApiAsync(ClientSession())
    with (
        patch("yalexs.api_async.API_EXCEPTION_RETRY_TIME", 0),
        patch("yalexs.api_async.API_RETRY_ATTEMPTS", 2),
        patch("yalexs.api_async.asyncio.sleep"),
    ):
        await api.async_validate_verification_code(
            ACCESS_TOKEN, "email", "emailaddress", 123456
        )
    assert last_args["json"] == {"code": "123456", "email": "emailaddress"}
    assert attempt == 2
