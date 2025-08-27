import datetime
import json
import os
import unittest

import dateutil.parser
from dateutil.tz import tzlocal

from yalexs.activity import (
    SOURCE_PUBNUB,
    SOURCE_WEBSOCKET,
    ActivityType,
    BridgeOperationActivity,
    DoorbellDingActivity,
    DoorbellImageCaptureActivity,
    DoorbellMotionActivity,
    DoorOperationActivity,
    LockOperationActivity,
)
from yalexs.doorbell import DoorbellDetail
from yalexs.lock import (
    DOOR_STATE_KEY,
    LOCK_STATUS_KEY,
    LockDetail,
    LockDoorStatus,
    LockStatus,
)
from yalexs.pubnub_activity import activities_from_pubnub_message
from yalexs.users import cache_user_info, get_user_info


def load_fixture(filename):
    """Load a fixture."""
    path = os.path.join(os.path.dirname(__file__), "fixtures", filename)
    with open(path) as fptr:
        return fptr.read()


class TestLockDetail(unittest.TestCase):
    def test_update_lock_details_from_pubnub_message(self):
        lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", lock.device_id)
        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(LockDoorStatus.DISABLED, lock.door_state)

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "remoteEvent": 1,
                "status": "kAugLockState_Unlatching",
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
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "unlatching"

        activities = activities_from_pubnub_message(
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
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "unlocking"

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:31.273Z"),
            {
                "remoteEvent": 1,
                "status": "kAugLockState_Locking",
                "info": {
                    "action": "unlock",
                    "startTime": "2021-03-20T18:19:06.374Z",
                    "context": {
                        "transactionID": "_oJRZKJsx",
                        "startDate": "2021-03-20T18:19:06.372Z",
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
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "locking"

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:31.273Z"),
            {
                "remoteEvent": 1,
                "status": "FAILED_BRIDGE_ERROR_LOCK_JAMMED",
                "info": {
                    "action": "unlock",
                    "startTime": "2021-03-20T18:19:06.374Z",
                    "context": {
                        "transactionID": "_oJRZKJsx",
                        "startDate": "2021-03-20T18:19:06.372Z",
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
        assert isinstance(activities[0], LockOperationActivity)
        assert activities[0].activity_start_time == dateutil.parser.parse(
            "2021-03-20T18:19:06.374Z"
        ).astimezone(tz=tzlocal()).replace(tzinfo=None)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "jammed"

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:31.273Z"),
            {
                "remoteEvent": 1,
                "status": "kAugLockState_Unlocked",
                "info": {
                    "action": "unlock",
                    "startTime": "2021-03-20T18:19:06.374Z",
                    "context": {
                        "transactionID": "_oJRZKJsx",
                        "startDate": "2021-03-20T18:19:06.372Z",
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
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].activity_start_time == dateutil.parser.parse(
            "2021-03-20T18:19:06.374Z"
        ).astimezone(tz=tzlocal()).replace(tzinfo=None)
        assert activities[0].action == "unlock"

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "status": "locked",
                "callingUserID": "8918341e-7e68-4079-ad0a-1fa8a45d855b",
                "doorState": "closed",
            },
        )
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "lock"
        assert activities[0].operated_by is None
        assert isinstance(activities[1], DoorOperationActivity)
        assert "DoorOperationActivity" in str(activities[1])
        assert activities[1].action == "doorclosed"

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "status": "locked",
                "callingUserID": "8918341e-7e68-4079-ad0a-1fa8a45d855b",
                "doorState": "open",
            },
        )
        assert isinstance(activities[0], LockOperationActivity)
        assert activities[0].action == "lock"
        assert activities[0].operated_by is None
        assert (
            activities[0].activity_type == ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR
        )
        assert isinstance(activities[1], DoorOperationActivity)
        assert activities[1].action == "dooropen"

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "status": "locked",
                "callingUserID": "cccca94e-373e-aaaa-bbbb-333396827777",
                "doorState": "closed",
            },
        )
        assert isinstance(activities[0], LockOperationActivity)
        assert activities[0].action == "lock"
        assert activities[0].operated_by is None
        assert (
            activities[0].activity_type == ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR
        )
        assert isinstance(activities[1], DoorOperationActivity)
        assert activities[1].action == "doorclosed"

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T11:48:30.272Z"),
            {
                LOCK_STATUS_KEY: "DoorStateChanged",
                "lockID": "xxx",
                "timeStamp": 1615087688187,
            },
        )
        assert not activities
        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T12:48:30.272Z"),
            {
                DOOR_STATE_KEY: "init",
                "lockID": "xxx",
                "timeStamp": 1615087688187,
            },
        )
        assert not activities

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T11:48:30.272Z"),
            {
                LOCK_STATUS_KEY: "associated_bridge_offline",
                "lockID": "xxx",
                "timeStamp": 1615087688187,
            },
        )
        assert isinstance(activities[0], BridgeOperationActivity)
        assert activities[0].action == "associated_bridge_offline"

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T11:48:30.272Z"),
            {
                LOCK_STATUS_KEY: "associated_bridge_online",
                "lockID": "xxx",
                "timeStamp": 1615087688187,
            },
        )
        assert isinstance(activities[0], BridgeOperationActivity)
        assert activities[0].action == "associated_bridge_online"

        cache_user_info(
            "5309b78d-de0c-4ec5-b878-02784c3b598a",
            {"FirstName": "bob", "LastName": "smith"},
        )
        assert get_user_info("5309b78d-de0c-4ec5-b878-02784c3b598a") is not None

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "status": "unlocked",
                "callingUserID": "5309b78d-de0c-4ec5-b878-02784c3b598a",
                "doorState": "closed",
                "info": {
                    "action": "unlock",
                    "startTime": "2017-12-10T05:48:30.272Z",
                    "context": {
                        "transactionID": "_oJRZKJsx",
                        "startDate": "2017-12-10T05:48:30.272Z",
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
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "unlock"
        assert activities[0].operated_by == "bob smith"

        activities = activities_from_pubnub_message(
            lock,
            datetime.datetime.fromtimestamp(16844292526891571 / 10_000_000),
            {
                "status": "unlatched",
                "callingUserID": "manualunlatch",
                "doorState": "open",
            },
        )
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "unlatch"
        assert (
            activities[0].activity_type is ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR
        )
        assert activities[0].operated_by is None

        activities = activities_from_pubnub_message(
            lock,
            datetime.datetime.fromtimestamp(16844292526891571 / 10_000_000),
            {
                "status": "unlocked",
                "callingUserID": "manualunlock",
                "doorState": "open",
            },
        )
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "unlock"
        assert (
            activities[0].activity_type is ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR
        )
        assert activities[0].operated_by is None

        activities = activities_from_pubnub_message(
            lock,
            datetime.datetime.fromtimestamp(16844299539729015 / 10_000_000),
            {
                "status": "locked",
                "callingUserID": "manuallock",
                "doorState": "open",
            },
        )
        assert isinstance(activities[0], LockOperationActivity)
        assert "LockOperationActivity" in str(activities[0])
        assert activities[0].action == "lock"
        assert (
            activities[0].activity_type is ActivityType.LOCK_OPERATION_WITHOUT_OPERATOR
        )
        assert activities[0].operated_by is None

        # status polls should not create activities
        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "remoteEvent": 1,
                "status": "kAugLockState_Locked",
                "info": {
                    "action": "status",
                    "startTime": "2024-02-15T07:33:50.804Z",
                    "context": {
                        "transactionID": "RP99lHGUIx",
                        "startDate": "2024-02-15T07:33:50.793Z",
                        "retryCount": 1,
                    },
                    "lockType": "lock_version_17",
                    "serialNumber": "L.....",
                    "rssi": 0,
                    "wlanRSSI": -35,
                    "wlanSNR": -1,
                    "duration": 991,
                    "lockID": "AF5EFD84.....",
                    "bridgeID": "652e35ba7e.....",
                    "serial": "L.....",
                },
                "doorState": "kAugDoorState_Closed",
                "retryCount": 1,
                "totalTime": 1028,
                "resultsFromOperationCache": False,
            },
        )

        assert len(activities) == 0


class TestDetail(unittest.TestCase):
    def test_update_doorbell_details_from_pubnub_message(self):
        doorbell = DoorbellDetail(json.loads(load_fixture("get_doorbell.json")))
        self.assertEqual("K98GiDT45GUL", doorbell.device_id)
        self.assertEqual(
            dateutil.parser.parse("2017-12-10T08:01:35Z"),
            doorbell.image_created_at_datetime,
        )
        self.assertEqual(
            "https://image.com/vmk16naaaa7ibuey7sar.jpg", doorbell.image_url
        )
        activities = activities_from_pubnub_message(
            doorbell,
            dateutil.parser.parse("2021-03-16T01:07:08.817Z"),
            {
                "status": "imagecapture",
                "data": {
                    "event": "imagecapture",
                    "result": {
                        "created_at": "2021-03-16T01:07:08.817Z",
                        "secure_url": "https://dyu7azbnaoi74.cloudfront.net/zip/images/zip.jpeg",
                    },
                },
            },
        )
        assert isinstance(activities[0], DoorbellImageCaptureActivity)
        assert "DoorbellImageCaptureActivity" in str(activities[0])

        assert (
            activities[0].image_url
            == "https://dyu7azbnaoi74.cloudfront.net/zip/images/zip.jpeg"
        )
        assert activities[0].image_created_at_datetime == dateutil.parser.parse(
            "2021-03-16T01:07:08.817Z"
        )

        activities = activities_from_pubnub_message(
            doorbell,
            dateutil.parser.parse("2021-03-16T01:07:08.817Z"),
            {
                "status": "imagecapture",
                "data": {
                    "event": "imagecapture",
                    "result": {
                        "created_at": "2021-03-16T01:07:08.817Z",
                        "secure_url": "https://dyu7azbnaoi74.cloudfront.net/zip/images/zip.jpeg",
                    },
                },
            },
        )
        assert isinstance(activities[0], DoorbellImageCaptureActivity)
        assert (
            activities[0].image_url
            == "https://dyu7azbnaoi74.cloudfront.net/zip/images/zip.jpeg"
        )
        assert activities[0].image_created_at_datetime == dateutil.parser.parse(
            "2021-03-16T01:07:08.817Z"
        )

        activities = activities_from_pubnub_message(
            doorbell,
            dateutil.parser.parse("2021-03-16T01:07:08.817Z"),
            {
                "status": "doorbell_motion_detected",
                "callID": None,
                "origin": "mars-api",
                "data": {
                    "event": "doorbell_motion_detected",
                    "image": {
                        "height": 640,
                        "width": 480,
                        "format": "jpg",
                        "created_at": "2021-03-16T02:36:26.886Z",
                        "bytes": 14061,
                        "secure_url": "https://dyu7azbnaoi74.cloudfront.net/images/1f8.jpeg",
                        "url": "https://dyu7azbnaoi74.cloudfront.net/images/1f8.jpeg",
                        "etag": "09e839331c4ea59eef28081f2caa0e90",
                    },
                    "doorbellName": "Front Door",
                    "callID": None,
                    "origin": "mars-api",
                    "mutableContent": True,
                },
            },
        )
        assert isinstance(activities[0], DoorbellMotionActivity)
        assert (
            activities[0].image_url
            == "https://dyu7azbnaoi74.cloudfront.net/images/1f8.jpeg"
        )
        assert activities[0].image_created_at_datetime == dateutil.parser.parse(
            "2021-03-16T02:36:26.886Z"
        )

        activities = activities_from_pubnub_message(
            doorbell,
            dateutil.parser.parse("2021-03-16T01:07:08.817Z"),
            {
                "status": "buttonpush",
                "origin": "mars-api",
                "data": {
                    "doorbellID": "26593a60f5d6",
                    "event": "buttonpush",
                    "doorbellName": "Front Door",
                    "origin": "mars-api",
                },
            },
        )
        assert isinstance(activities[0], DoorbellDingActivity)
        assert "DoorbellDingActivity" in str(activities[0])


class TestBridge(unittest.TestCase):
    def test_update_bridge_details_from_pubnub_message(self):
        lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))
        self.assertEqual("A6697750D607098BAE8D6BAA11EF8063", lock.device_id)
        self.assertEqual(LockStatus.LOCKED, lock.lock_status)
        self.assertEqual(LockDoorStatus.DISABLED, lock.door_state)

        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "remoteEvent": 1,
                "status": "unknown",
                "result": "failed",
                "error": {
                    "jse_shortmsg": "",
                    "jse_info": {},
                    "message": "Bridge is offline",
                    "statusCode": 422,
                    "body": {"code": 98, "message": "Bridge is offline"},
                    "restCode": 98,
                    "name": "ERRNO_BRIDGE_OFFLINE",
                    "code": "Error",
                },
                "info": {
                    "lockID": "45E3635D35B9471FAF1218885816E90D",
                    "action": "status",
                },
            },
        )
        assert isinstance(activities[0], BridgeOperationActivity)
        assert "BridgeOperationActivity" in str(activities[0])
        assert activities[0].action == "associated_bridge_offline"

    def test_websocket_source_handling(self):
        lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))
        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {"status": "kAugLockState_Locked"},
            source=SOURCE_WEBSOCKET,
        )
        assert len(activities) == 1
        assert activities[0].source == SOURCE_WEBSOCKET

    def test_pubnub_source_default(self):
        lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))
        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {"status": "kAugLockState_Locked"},
        )
        assert len(activities) == 1
        assert activities[0].source == SOURCE_PUBNUB

    def test_is_status_property(self):
        """Test is_status property correctly identifies status updates."""
        lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))

        # Test normal lock operation is not a status
        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "status": "kAugLockState_Locked",
                "info": {"action": "lock", "startTime": "2017-12-10T05:48:30.272Z"},
                "callingUserID": "user123",
            },
        )
        assert len(activities) == 1
        assert activities[0].is_status is False

        # Test status update with no info and no user
        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {"status": "kAugLockState_Locked"},
        )
        assert len(activities) == 1
        assert activities[0].is_status is True

        # Test manual operation is not a status
        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "status": "kAugLockState_Locked",
                "callingUserID": "manuallock",
            },
        )
        assert len(activities) == 1
        assert activities[0].is_status is False
        # Manual operations without timestamps don't store the user ID but mark as manual
        assert activities[0].operated_manual is True

        # Test WebSocket messages with empty info are not status
        activities = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {"status": "kAugLockState_Locked"},
            source=SOURCE_WEBSOCKET,
        )
        assert len(activities) == 1
        assert activities[0].is_status is False

    def test_pubnub_duplicate_state_detection(self):
        """Test that duplicate PubNub messages with same state are detected."""
        lock = LockDetail(json.loads(load_fixture("get_lock.doorsense_init.json")))

        # First message - manual lock when already locked
        activities1 = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:30.272Z"),
            {
                "status": "locked",
                "callingUserID": "manuallock",
                "doorState": "closed",
            },
            source=SOURCE_PUBNUB,
        )
        assert len(activities1) == 2  # lock and door activities
        assert activities1[0].action == "lock"
        assert activities1[1].action == "doorclosed"

        # Second identical message should still create activities
        # (state tracking happens at the manager level, not here)
        activities2 = activities_from_pubnub_message(
            lock,
            dateutil.parser.parse("2017-12-10T05:48:31.272Z"),
            {
                "status": "locked",
                "callingUserID": "manuallock",
                "doorState": "closed",
            },
            source=SOURCE_PUBNUB,
        )
        assert len(activities2) == 2
        assert activities2[0].action == "lock"
        assert activities2[1].action == "doorclosed"
        # Both should NOT be marked as status since they have manual flag
        assert (
            activities2[0].is_status is False
        )  # manual lock operations are not status
        assert (
            activities2[1].is_status is False
        )  # door activity with manual flag is not status
