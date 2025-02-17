import asyncio
import base64
import binascii

from Auth.firebase_messaging import FcmRegisterConfig, FcmPushClient
from Auth.token_cache import set_cached_value, get_cached_value

class FcmReceiver:

    _instance = None
    _listening = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FcmReceiver, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        # Define Firebase project configuration
        project_id = "google.com:api-project-289722593072"
        app_id = "1:289722593072:android:3cfcf5bc359f0308"
        api_key = "AIzaSyD_gko3P392v6how2H7UpdeXQ0v2HLettc"
        message_sender_id = "289722593072"

        fcm_config = FcmRegisterConfig(
            project_id=project_id,
            app_id=app_id,
            api_key=api_key,
            messaging_sender_id=message_sender_id,
            bundle_id="com.google.android.apps.adm",
        )

        self.credentials = get_cached_value('fcm_credentials')
        self.location_update_callbacks = []
        self.pc = FcmPushClient(self._on_notification, fcm_config, self.credentials, self._on_credentials_updated)


    def register_for_location_updates(self, callback):

        if not self._listening:
            asyncio.get_event_loop().run_until_complete(self._register_for_fcm_and_listen())

        self.location_update_callbacks.append(callback)

        return self.credentials['fcm']['registration']['token']


    def stop_listening(self):
        asyncio.get_event_loop().run_until_complete(self.pc.stop())
        self._listening = False


    def get_android_id(self):

        if self.credentials is None:
            return asyncio.get_event_loop().run_until_complete(self._register_for_fcm_and_listen())

        return self.credentials['gcm']['android_id']


    # Define a callback function for handling notifications
    def _on_notification(self, obj, notification, data_message):

        # Check if the payload is present
        if 'data' in obj and 'com.google.android.apps.adm.FCM_PAYLOAD' in obj['data']:

            # Decode the base64 string
            base64_string = obj['data']['com.google.android.apps.adm.FCM_PAYLOAD']
            decoded_bytes = base64.b64decode(base64_string)

            # print("[FCMReceiver] Decoded FMDN Message:", decoded_bytes.hex())

            # Convert to hex string
            hex_string = binascii.hexlify(decoded_bytes).decode('utf-8')

            for callback in self.location_update_callbacks:
                callback(hex_string)
        else:
            print("[FCMReceiver] Payload not found in the notification.")


    def _on_credentials_updated(self, creds):
        self.credentials = creds

        # Also store to disk
        set_cached_value('fcm_credentials', self.credentials)
        print("[FCMReceiver] Credentials updated.")


    async def _register_for_fcm(self):
        fcm_token = None

        # Register or check in with FCM and get the FCM token
        while fcm_token is None:
            try:
                fcm_token = await self.pc.checkin_or_register()
            except Exception as e:
                await self.pc.stop()
                print("[FCMReceiver] Failed to register with FCM. Retrying...")
                await asyncio.sleep(5)


    async def _register_for_fcm_and_listen(self):
        await self._register_for_fcm()
        await self.pc.start()
        self._listening = True
        print("[FCMReceiver] Listening for notifications.")


if __name__ == "__main__":
    receiver = FcmReceiver()
    print(receiver.get_android_id())