import asyncio
import base64
import binascii
import threading

from Auth.firebase_messaging import FcmRegisterConfig, FcmPushClient
from Auth.token_cache import set_cached_value, get_cached_value

class FcmReceiver:

    _instance = None
    _listening = False
    _loop = None
    _loop_thread = None

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
            android_cert_sha1="38918a453d07199354f8b19af05ec6562ced5788",
        )

        self.credentials = get_cached_value('fcm_credentials')
        self.location_update_callbacks = []
        self.pc = FcmPushClient(self._on_notification, fcm_config, self.credentials, self._on_credentials_updated)


    def register_for_location_updates(self, callback):

        if not self._listening:
            self._start_listener_in_background()

        self.location_update_callbacks.append(callback)

        return self.credentials['fcm']['registration']['token']


    def stop_listening(self):
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.pc.stop(), self._loop)
        self._listening = False


    def get_android_id(self):

        if self.credentials is None:
            return self._start_listener_in_background()

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
        # Start the FCM listener
        await self.pc.start()

    def _run_event_loop_in_thread(self):
        """Run the event loop in a background thread"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _start_listener_in_background(self):
        """Start FCM listener in a background thread with its own event loop"""
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_event_loop_in_thread, daemon=True)
        self._loop_thread.start()

        # Register for FCM first (blocking)
        temp_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(temp_loop)
        temp_loop.run_until_complete(self._register_for_fcm())
        temp_loop.close()

        # Now start the listener in the background loop
        asyncio.run_coroutine_threadsafe(self.pc.start(), self._loop)
        self._listening = True
        print("[FCMReceiver] Listening for notifications. This can take a few seconds...")

        return self.credentials['gcm']['android_id']


if __name__ == "__main__":
    receiver = FcmReceiver()
    print(receiver.get_android_id())
