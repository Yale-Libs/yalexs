import datetime
import json
import os
import unittest

import dateutil.parser
import pytest

from yalexs.activity import (
    SOURCE_LOG,
    SOURCE_PUBNUB,
    BridgeOperationActivity,
    DoorbellMotionActivity,
    DoorOperationActivity,
    LockOperationActivity,
)
from yalexs.api_common import _convert_lock_result_to_activities
from yalexs.const import Brand
from yalexs.doorbell import DoorbellDetail
from yalexs.lock import LockDetail, LockDoorStatus, LockStatus
from yalexs.pubnub_activity import activities_from_pubnub_message
from yalexs.util import (
    as_utc_from_local,
    get_configuration_url,
    get_latest_activity,
    get_ssl_context,
    update_doorbell_image_from_activity,
    update_lock_detail_from_activity,
)


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as fptr:
        return fptr.read()


def test_get_latest_activity():
    """Test when two activities happen at the same time we prefer the one that is not moving."""
    lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))
    unlocking_activities = activities_from_pubnub_message(
        lock,
        dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
        {
            "remoteEvent": 1,
            "status": "kAugLockState_Unlocking",
            "info": {
                "action": "unlock",
                "startTime": "2021-03-20T18:19:05.373Z",
                "context": {
                    "transactionID": "_oJRZKJsx",
                    "startDate": "2021-03-20T18:19:05.371Z",
                    "retryCount": 1,
                },
                "lockType": "lock_version_1001",
                "serialNumber": "M1FBA029QJ",
                "rssi": -53,
                "wlanRSSI": -55,
                "wlanSNR": 44,
                "duration": 2534,
            },
        },
    )
    unlocked_activities = activities_from_pubnub_message(
        lock,
        dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
        {
            "remoteEvent": 1,
            "status": "kAugLockState_Unlocked",
            "info": {
                "action": "unlock",
                "startTime": "2021-03-20T18:19:05.373Z",
                "context": {
                    "transactionID": "_oJRZKJsx",
                    "startDate": "2021-03-20T18:19:05.371Z",
                    "retryCount": 1,
                },
                "lockType": "lock_version_1001",
                "serialNumber": "M1FBA029QJ",
                "rssi": -53,
                "wlanRSSI": -55,
                "wlanSNR": 44,
                "duration": 2534,
            },
        },
    )
    assert get_latest_activity(unlocking_activities[0], None) == unlocking_activities[0]
    assert get_latest_activity(None, unlocked_activities[0]) == unlocked_activities[0]
    assert (
        get_latest_activity(unlocking_activities[0], unlocked_activities[0])
        == unlocked_activities[0]
    )
    assert (
        get_latest_activity(unlocked_activities[0], unlocking_activities[0])
        == unlocked_activities[0]
    )


def test_update_lock_detail_from_activity():
    """Test when two activities happen at the same time we prefer the one that is not moving."""
    lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))
    unlocking_activities = activities_from_pubnub_message(
        lock,
        dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
        {
            "remoteEvent": 1,
            "status": "kAugLockState_Unlocking",
            "info": {
                "action": "unlock",
                "startTime": "2021-03-20T18:19:05.373Z",
                "context": {
                    "transactionID": "_oJRZKJsx",
                    "startDate": "2021-03-20T18:19:05.371Z",
                    "retryCount": 1,
                },
                "lockType": "lock_version_1001",
                "serialNumber": "M1FBA029QJ",
                "rssi": -53,
                "wlanRSSI": -55,
                "wlanSNR": 44,
                "duration": 2534,
            },
        },
    )
    unlocked_activities = activities_from_pubnub_message(
        lock,
        dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
        {
            "remoteEvent": 1,
            "status": "kAugLockState_Unlocked",
            "info": {
                "action": "unlock",
                "startTime": "2021-03-20T18:19:05.373Z",
                "context": {
                    "transactionID": "_oJRZKJsx",
                    "startDate": "2021-03-20T18:19:05.371Z",
                    "retryCount": 1,
                },
                "lockType": "lock_version_1001",
                "serialNumber": "M1FBA029QJ",
                "rssi": -53,
                "wlanRSSI": -55,
                "wlanSNR": 44,
                "duration": 2534,
            },
        },
    )
    update_lock_detail_from_activity(lock, unlocking_activities[0])
    assert lock.lock_status == LockStatus.UNLOCKING
    update_lock_detail_from_activity(lock, unlocked_activities[0])
    assert lock.lock_status == LockStatus.UNLOCKED
    update_lock_detail_from_activity(lock, unlocking_activities[0])
    assert lock.lock_status == LockStatus.UNLOCKED


class TestLockDetail(unittest.TestCase):
    def test_update_lock_with_activity_has_no_status(self):
        lock = LockDetail(
            json.loads(load_fixture("get_lock.nostatus_with_doorsense.json"))
        )
        self.assertEqual("ABC", lock.device_id)
        self.assertEqual(LockStatus.UNKNOWN, lock.lock_status)
        self.assertEqual(LockDoorStatus.UNKNOWN, lock.door_state)
        self.assertEqual(None, lock.lock_status_datetime)
        self.assertEqual(None, lock.door_state_datetime)

        unlock_operation_activity = LockOperationActivity(
            SOURCE_LOG, json.loads(load_fixture("unlock_activity.json"))
        )

        self.assertTrue(
            update_lock_detail_from_activity(lock, unlock_operation_activity)
        )
        self.assertEqual(LockStatus.UNLOCKED, lock.lock_status)

    def test_update_lock_with_activity(self):
        lock = LockDetail(
            json.loads(load_fixture("get_lock.online_with_doorsense.json"))
        )
        self.assertEqual("ABC", lock.device_id)
        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(LockDoorStatus.OPEN, lock.door_state)
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.lock_status_datetime
        )
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T04:48:30.272Z"), lock.door_state_datetime
        )

        lock_operation_activity = LockOperationActivity(
            SOURCE_LOG, json.loads(load_fixture("lock_activity.json"))
        )
        unlock_operation_activity = LockOperationActivity(
            SOURCE_LOG, json.loads(load_fixture("unlock_activity.json"))
        )
        open_operation_activity = DoorOperationActivity(
            SOURCE_LOG, json.loads(load_fixture("door_open_activity.json"))
        )
        closed_operation_activity = DoorOperationActivity(
            SOURCE_LOG, json.loads(load_fixture("door_closed_activity.json"))
        )
        closed_operation_wrong_deviceid_activity = DoorOperationActivity(
            SOURCE_LOG,
            json.loads(load_fixture("door_closed_activity_wrong_deviceid.json")),
        )
        closed_operation_wrong_houseid_activity = DoorOperationActivity(
            SOURCE_LOG,
            json.loads(load_fixture("door_closed_activity_wrong_houseid.json")),
        )

        self.assertTrue(
            update_lock_detail_from_activity(lock, unlock_operation_activity)
        )
        self.assertEqual(LockStatus.UNLOCKED, lock.lock_status)
        self.assertEqual(
            as_utc_from_local(datetime.datetime.fromtimestamp(1582007217000 / 1000)),  # noqa: DTZ006
            lock.lock_status_datetime,
        )

        self.assertTrue(update_lock_detail_from_activity(lock, lock_operation_activity))
        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(
            as_utc_from_local(datetime.datetime.fromtimestamp(1582007218000 / 1000)),  # noqa: DTZ006
            lock.lock_status_datetime,
        )

        # returns false we send an older activity
        self.assertFalse(
            update_lock_detail_from_activity(lock, unlock_operation_activity)
        )

        self.assertTrue(
            update_lock_detail_from_activity(lock, closed_operation_activity)
        )
        self.assertEqual(LockDoorStatus.CLOSED, lock.door_state)
        self.assertEqual(
            as_utc_from_local(datetime.datetime.fromtimestamp(1582007217000 / 1000)),  # noqa: DTZ006
            lock.door_state_datetime,
        )

        self.assertTrue(update_lock_detail_from_activity(lock, open_operation_activity))
        self.assertEqual(LockDoorStatus.OPEN, lock.door_state)
        self.assertEqual(
            as_utc_from_local(datetime.datetime.fromtimestamp(1582007219000 / 1000)),  # noqa: DTZ006
            lock.door_state_datetime,
        )

        # returns false we send an older activity
        self.assertFalse(
            update_lock_detail_from_activity(lock, closed_operation_activity)
        )

        with self.assertRaises(ValueError):
            update_lock_detail_from_activity(
                lock, closed_operation_wrong_deviceid_activity
            )

        # We do not always have the houseid so we do not throw
        # as long as the deviceid is correct since they are unique
        self.assertFalse(
            update_lock_detail_from_activity(
                lock, closed_operation_wrong_houseid_activity
            )
        )

        self.assertEqual(LockDoorStatus.OPEN, lock.door_state)
        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        activities = _convert_lock_result_to_activities(
            json.loads(load_fixture("unlock.json"))
        )
        for activity in activities:
            self.assertTrue(update_lock_detail_from_activity(lock, activity))
        self.assertEqual(LockDoorStatus.CLOSED, lock.door_state)
        self.assertEqual(LockStatus.UNLOCKED, lock.lock_status)

        bridge_offline_activity = BridgeOperationActivity(
            SOURCE_PUBNUB,
            {
                "action": "associated_bridge_offline",
                "callingUser": {"UserID": None},
                "dateTime": 1512906510272.0,
                "deviceName": "Front Door Lock",
                "deviceType": "lock",
                "deviceID": lock.device_id,
                "house": "000000000000",
                "info": {},
            },
        )
        assert bridge_offline_activity.source == SOURCE_PUBNUB
        self.assertTrue(update_lock_detail_from_activity(lock, bridge_offline_activity))
        assert lock.bridge_is_online is False
        bridge_online_activity = BridgeOperationActivity(
            SOURCE_PUBNUB,
            {
                "action": "associated_bridge_online",
                "callingUser": {"UserID": None},
                "dateTime": 1512906510272.0,
                "deviceName": "Front Door Lock",
                "deviceType": "lock",
                "deviceID": lock.device_id,
                "house": "000000000000",
                "info": {},
            },
        )
        self.assertTrue(update_lock_detail_from_activity(lock, bridge_online_activity))
        assert lock.bridge_is_online is True
        assert bridge_online_activity.source == SOURCE_PUBNUB


class TestDetail(unittest.TestCase):
    def test_update_doorbell_image_from_activity(self):
        doorbell = DoorbellDetail(json.loads(load_fixture("get_doorbell.json")))
        self.assertEqual("K98GiDT45GUL", doorbell.device_id)
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T08:01:35Z"),
            doorbell.image_created_at_datetime,
        )
        self.assertEqual(
            "https://image.com/vmk16naaaa7ibuey7sar.jpg", doorbell.image_url
        )
        doorbell_motion_activity_no_image = DoorbellMotionActivity(
            SOURCE_LOG,
            json.loads(load_fixture("doorbell_motion_activity_no_image.json")),
        )
        self.assertFalse(
            update_doorbell_image_from_activity(
                doorbell, doorbell_motion_activity_no_image
            )
        )
        doorbell_motion_activity = DoorbellMotionActivity(
            SOURCE_LOG, json.loads(load_fixture("doorbell_motion_activity.json"))
        )
        self.assertTrue(
            update_doorbell_image_from_activity(doorbell, doorbell_motion_activity)
        )
        self.assertEqual(
            dateutil.parser.parse("2020-02-20T17:44:45Z"),
            doorbell.image_created_at_datetime,
        )
        self.assertEqual("https://my.updated.image/image.jpg", doorbell.image_url)
        old_doorbell_motion_activity = DoorbellMotionActivity(
            SOURCE_LOG, json.loads(load_fixture("doorbell_motion_activity_old.json"))
        )
        # returns false we send an older activity
        self.assertFalse(
            update_doorbell_image_from_activity(doorbell, old_doorbell_motion_activity)
        )
        self.assertEqual(
            dateutil.parser.parse("2020-02-20T17:44:45Z"),
            doorbell.image_created_at_datetime,
        )
        self.assertEqual("https://my.updated.image/image.jpg", doorbell.image_url)
        wrong_doorbell_motion_activity = DoorbellMotionActivity(
            SOURCE_LOG, json.loads(load_fixture("doorbell_motion_activity_wrong.json"))
        )

        with self.assertRaises(ValueError):
            update_doorbell_image_from_activity(
                doorbell, wrong_doorbell_motion_activity
            )

    def test_update_doorbell_image_from_activity_missing_image_at_start(self):
        doorbell = DoorbellDetail(
            json.loads(load_fixture("get_doorbell_missing_image.json"))
        )
        self.assertEqual("K98GiDT45GUL", doorbell.device_id)
        self.assertEqual(
            None,
            doorbell.image_created_at_datetime,
        )
        self.assertEqual(None, doorbell.image_url)
        doorbell_motion_activity_no_image = DoorbellMotionActivity(
            SOURCE_LOG,
            json.loads(load_fixture("doorbell_motion_activity_no_image.json")),
        )
        self.assertFalse(
            update_doorbell_image_from_activity(
                doorbell, doorbell_motion_activity_no_image
            )
        )
        doorbell_motion_activity = DoorbellMotionActivity(
            SOURCE_LOG, json.loads(load_fixture("doorbell_motion_activity.json"))
        )
        self.assertTrue(
            update_doorbell_image_from_activity(doorbell, doorbell_motion_activity)
        )
        self.assertEqual(
            dateutil.parser.parse("2020-02-20T17:44:45Z"),
            doorbell.image_created_at_datetime,
        )
        self.assertEqual("https://my.updated.image/image.jpg", doorbell.image_url)


def test_get_configuration_url():
    """Test that we get the correct configuration url for the brand."""
    assert get_configuration_url("august") == "https://account.august.com"
    assert get_configuration_url("yale_access") == "https://account.august.com"
    assert get_configuration_url("yale_home") == "https://account.aaecosystem.com"
    assert get_configuration_url(Brand.AUGUST) == "https://account.august.com"
    assert get_configuration_url(Brand.YALE_ACCESS) == "https://account.august.com"
    assert get_configuration_url(Brand.YALE_HOME) == "https://account.aaecosystem.com"


def test_get_ssl_context():
    """Test getting the ssl context is cached."""
    assert get_ssl_context() is get_ssl_context()


def test_update_lock_detail_with_unhandled_activity_type_raises():
    """A non Lock/Door/Bridge activity must fall through the chain and raise."""
    lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))
    bogus_activity = DoorbellMotionActivity(
        SOURCE_PUBNUB,
        {
            "action": "doorbell_motion_detected",
            "dateTime": 1582220686158,
            "deviceID": lock.device_id,
            "deviceName": lock.device_name,
            "deviceType": "doorbell",
            "house": "abc",
            "info": {},
        },
    )
    with pytest.raises(ValueError):
        update_lock_detail_from_activity(lock, bogus_activity)


def test_update_lock_detail_with_unknown_bridge_action_returns_true():
    """BridgeOp with an unknown action (not online/offline) still returns True."""
    lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))
    bridge_unknown = BridgeOperationActivity(
        SOURCE_PUBNUB,
        {
            "action": "associated_bridge_unknown",
            "callingUser": {"UserID": None},
            "dateTime": 1512906510272.0,
            "deviceName": lock.device_name,
            "deviceType": "lock",
            "deviceID": lock.device_id,
            "house": "000000000000",
            "info": {},
        },
    )
    assert update_lock_detail_from_activity(lock, bridge_unknown) is True


def test_update_doorbell_image_with_bridge_activity_raises():
    """BridgeOp is in DoorbellActivityTypes but not handled — must raise."""
    doorbell = DoorbellDetail(json.loads(load_fixture("get_doorbell.json")))
    bridge_activity = BridgeOperationActivity(
        SOURCE_PUBNUB,
        {
            "action": "associated_bridge_online",
            "callingUser": {"UserID": None},
            "dateTime": 1582220686158,
            "deviceName": doorbell.device_name,
            "deviceType": "doorbell",
            "deviceID": doorbell.device_id,
            "house": "abc",
            "info": {},
        },
    )
    with pytest.raises(ValueError):
        update_doorbell_image_from_activity(doorbell, bridge_activity)
