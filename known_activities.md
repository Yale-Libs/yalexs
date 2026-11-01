# Known Activity Actions

## doorclosed

```
{
  "entities": {
    "device": "<deviceId>",
    "callingUser": "deleted",
    "otherUser": "deleted",
    "house": "<houseId>",
    "activity": "<activityId>"
  },
  "house": {
    "houseID": "<houseId>",
    "houseName": "<houseName>"
  },
  "dateTime": <epochTimestamp>,
  "action": "doorclosed",
  "deviceName": "<deviceName>",
  "deviceID": "<deviceId>",
  "deviceType": "lock",
  "callingUser": {
    "UserID": "deleted",
    "FirstName": "Unknown",
    "LastName": "User",
    "UserName": "deleteduser",
    "PhoneNo": "deleted"
  },
  "otherUser": {
    "UserID": "deleted",
    "FirstName": "Unknown",
    "LastName": "User",
    "UserName": "deleteduser",
    "PhoneNo": "deleted"
  },
  "info": {
    "DateLogActionID": "<uniqueId>"
  }
}
```

## dooropen

```
{
  "entities": {
    "device": "<deviceId>",
    "callingUser": "deleted",
    "otherUser": "deleted",
    "house": "<houseId>",
    "activity": "<activityId>"
  },
  "house": {
    "houseID": "<houseId>",
    "houseName": <houseName>
  },
  "dateTime": <epochTimestamp>,
  "action": "dooropen",
  "deviceName": <deviceName>,
  "deviceID": "<deviceId>",
  "deviceType": "lock",
  "callingUser": {
    "UserID": "deleted",
    "FirstName": "Unknown",
    "LastName": "User",
    "UserName": "deleteduser",
    "PhoneNo": "deleted"
  },
  "otherUser": {
    "UserID": "deleted",
    "FirstName": "Unknown",
    "LastName": "User",
    "UserName": "deleteduser",
    "PhoneNo": "deleted"
  },
  "info": {
    "DateLogActionID": "<uniqueId>"
  }
}
```

## unlock

```
{
  "entities": {
    "device": "<deviceId>",
    "callingUser": "<userId>",
    "otherUser": "deleted",
    "house": "<houseId>",
    "activity": "<activityId>"
  },
  "house": {
    "houseID": "<houseId>",
    "houseName": <houseName>
  },
  "source": {
    "sourceType": "mercury"
  },
  "dateTime": <epochTimestamp>,
  "action": "unlock",
  "deviceName": <deviceName>,
  "deviceID": "<deviceId>",
  "deviceType": "lock",
  "callingUser": {
    "UserID": "<userId>",
    "FirstName": "<firstName>",
    "LastName": "<lastName>",
    "imageInfo": {
      "original": {
        "width": <imageWidth>,
        "height": <imageHeight>,
        "format": "<imageFormat>",
        "url": "<imageUrl>",
        "secure_url": "<imageSecureUrl>"
      },
      "thumbnail": {
        "width": <thumbnailWidth>,
        "height": <thumbnailHeight>,
        "format": "<imageFormat>",
        "url": "<thumbnailUrl>",
        "secure_url": "<thumbnailSecureUrl>"
      }
    }
  },
  "otherUser": {
    "UserID": "deleted",
    "FirstName": "Unknown",
    "LastName": "User",
    "UserName": "deleteduser",
    "PhoneNo": "deleted"
  },
  "info": {
    "agent": "mercury",
    "keypad": true
  }
}
```

## lock

```
{
  "entities": {
    "device": "<deviceId>",
    "callingUser": "<userId>",
    "otherUser": "deleted",
    "house": "<houseId>",
    "activity": "<activityId>"
  },
  "house": {
    "houseID": "<houseId>",
    "houseName": <houseName>
  },
  "dateTime": <epochTimestamp>,
  "action": "lock",
  "deviceName": <deviceName>,
  "deviceID": "<deviceId>",
  "deviceType": "lock",
  "callingUser": {
    "UserID": "<userId>",
    "FirstName": "<firstName>",
    "LastName": "<lastName>"
  },
  "otherUser": {
    "UserID": "deleted",
    "FirstName": "Unknown",
    "LastName": "User",
    "UserName": "deleteduser",
    "PhoneNo": "deleted"
  },
  "info": {
    "remote": true,
    "DateLogActionID": "<uniqueId>"
  }
}
```

## onetouchlock

```
{
  "entities": {
    "device": "<deviceId>",
    "callingUser": "deleted",
    "otherUser": "deleted",
    "house": "<houseId>",
    "activity": "<activityId>"
  },
  "house": {
    "houseID": "<houseId>",
    "houseName": <houseName>
  },
  "dateTime": <epochTimestamp>,
  "action": "onetouchlock",
  "deviceName": <deviceName>,
  "deviceID": "<deviceId>",
  "deviceType": "lock",
  "callingUser": {
    "UserID": "deleted",
    "FirstName": "Unknown",
    "LastName": "User",
    "UserName": "deleteduser",
    "PhoneNo": "deleted"
  },
  "otherUser": {
    "UserID": "deleted",
    "FirstName": "Unknown",
    "LastName": "User",
    "UserName": "deleteduser",
    "PhoneNo": "deleted"
  },
  "info": {
    "DateLogActionID": "<uniqueId>"
  }
}
```

## doorbell_call_button_press

Button press on a Yale Smart Video Doorbell (`eagle_doorbell`, Yale "aa"
platform). These doorbells do not push over PubNub/websocket; the press only
appears in the house activity feed (`/houses/<houseId>/activities`).

```
{
  "id": "<activityId>",
  "timestamp": <epochTimestampMs>,
  "icon": "https://activity-icon.aaecosystem.com/app/ActivityFeedIcons/doorbell_detected_doorbell_ring@3x.png",
  "action": "doorbell_call_button_press",
  "deviceID": "<doorbellId>",
  "deviceType": "doorbell",
  "attachment": "https://videocontent.aaecosystem.com/<houseId>/<doorbellId>/images/<activityId>.jpeg",
  "attachmentWidth": 1920,
  "attachmentHeight": 1080,
  "doorbell": {
    "contentToken": "<jwt>",
    "dvrID": "<activityId>",
    "videoUploadProgress": "not_started",
    "videoAvailable": false,
    "videoRecordingState": "recording_ongoing",
    "eventContainsVideoContent": true
  },
  "reason": "DOORBELL_RING",
  "otherReasonIcons": [],
  "userActions": [],
  "title": "<b><deviceName></b> pressed in <b><houseName></b>"
}
```
