"""
Push delivery via Firebase Cloud Messaging (Section 25).

This is a stub: it logs what *would* be sent rather than calling Firebase,
since real delivery needs a service-account credential (FIREBASE_CONFIG in
.env) and the firebase-admin package, neither of which belong hard-coded
into an MVP scaffold. Swap `FCMClient.send` for a real implementation like:

    import firebase_admin
    from firebase_admin import credentials, messaging

    cred = credentials.Certificate(json.loads(settings.FIREBASE_CONFIG))
    firebase_admin.initialize_app(cred)

    async def send(self, device_token, title, body, data=None):
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=device_token,
        )
        messaging.send(message)

The rest of the app (NotificationService) doesn't need to change when this
swap happens — it only calls `send`, and device-token storage/lookup (per
user, per installed device) is the other piece to add alongside it.
"""
import logging

logger = logging.getLogger("homecare.fcm")


class FCMClient:
    async def send(self, user_id, title: str, body: str, data: dict | None = None) -> None:
        logger.info("[FCM stub] would push to user=%s title=%r body=%r data=%s", user_id, title, body, data)


fcm_client = FCMClient()
