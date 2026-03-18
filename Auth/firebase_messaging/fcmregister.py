#
# firebase-messaging
# https://github.com/sdb9696/firebase-messaging
#
# MIT License
#
# Copyright (c) 2017 Matthieu Lemoine
# Copyright (c) 2023 Steven Beth
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import asyncio
import json
import logging
import os
import secrets
import time
import uuid
from base64 import b64encode, urlsafe_b64encode
from dataclasses import dataclass
from typing import Any, Callable

from aiohttp import ClientSession, ClientTimeout
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from google.protobuf.json_format import MessageToDict, MessageToJson

from .const import (
    AUTH_VERSION,
    FCM_INSTALLATION,
    FCM_REGISTRATION,
    FCM_SEND_URL,
    GCM_CHECKIN_URL,
    GCM_REGISTER_URL,
    GCM_SERVER_KEY_B64,
    SDK_VERSION,
)
from .proto.android_checkin_pb2 import (
    DEVICE_CHROME_BROWSER,
    AndroidCheckinProto,
    ChromeBuildProto,
)
from .proto.checkin_pb2 import (
    AndroidCheckinRequest,
    AndroidCheckinResponse,
)

_logger = logging.getLogger(__name__)


def _normalize_sha1_fingerprint(v: str) -> str:
    """Strip colons/spaces and validate a SHA-1 hex fingerprint."""
    v = v.replace(":", "").replace(" ", "").strip().lower()
    if len(v) != 40 or not all(c in "0123456789abcdef" for c in v):
        raise ValueError(f"Invalid SHA-1 fingerprint: {v!r}")
    return v


@dataclass
class FcmRegisterConfig:
    project_id: str
    app_id: str
    api_key: str
    messaging_sender_id: str
    bundle_id: str = "receiver.push.com"
    chrome_id: str = "org.chromium.linux"
    chrome_version: str = "94.0.4606.51"
    vapid_key: str | None = GCM_SERVER_KEY_B64
    persistend_ids: list[str] | None = None
    heartbeat_interval_ms: int = 5 * 60 * 1000  # 5 mins
    android_cert_sha1: str | None = None

    def __postinit__(self) -> None:
        if self.persistend_ids is None:
            self.persistend_ids = []
        if self.android_cert_sha1 is not None:
            self.android_cert_sha1 = _normalize_sha1_fingerprint(
                self.android_cert_sha1
            )


class FcmRegister:
    CLIENT_TIMEOUT = ClientTimeout(total=100)

    def __init__(
        self,
        config: FcmRegisterConfig,
        credentials: dict | None = None,
        credentials_updated_callback: Callable[[dict[str, Any]], None] | None = None,
        *,
        http_client_session: ClientSession | None = None,
        log_debug_verbose: bool = False,
    ):
        self.config = config
        self.credentials = credentials
        self.credentials_updated_callback = credentials_updated_callback

        self._log_debug_verbose = log_debug_verbose

        self._http_client_session = http_client_session
        self._local_session: ClientSession | None = None

    def _add_android_restriction_headers(self, headers: dict[str, str]) -> None:
        """Add X-Android-Package/Cert headers when configured."""
        if self.config.bundle_id:
            headers["X-Android-Package"] = self.config.bundle_id
        if self.config.android_cert_sha1:
            headers["X-Android-Cert"] = self.config.android_cert_sha1

    def _get_checkin_payload(
        self, android_id: int | None = None, security_token: int | None = None
    ) -> AndroidCheckinRequest:
        chrome = ChromeBuildProto()
        chrome.platform = ChromeBuildProto.Platform.PLATFORM_LINUX  # 3
        chrome.chrome_version = self.config.chrome_version
        chrome.channel = ChromeBuildProto.Channel.CHANNEL_STABLE  # 1

        checkin = AndroidCheckinProto()
        checkin.type = DEVICE_CHROME_BROWSER  # 3
        checkin.chrome_build.CopyFrom(chrome)

        payload = AndroidCheckinRequest()
        payload.user_serial_number = 0
        payload.checkin.CopyFrom(checkin)
        payload.version = 3
        if android_id and security_token:
            payload.id = int(android_id)
            payload.security_token = int(security_token)

        return payload

    async def gcm_check_in_and_register(
        self,
    ) -> dict[str, Any] | None:
        options = await self.gcm_check_in()
        if not options:
            raise RuntimeError("Unable to register and check in to gcm")
        gcm_credentials = await self.gcm_register(options)
        return gcm_credentials

    async def gcm_check_in(
        self,
        android_id: int | None = None,
        security_token: int | None = None,
    ) -> dict[str, Any] | None:
        """
        perform check-in request

        android_id, security_token can be provided if we already did the initial
        check-in

        returns dict with android_id, security_token and more
        """

        payload = self._get_checkin_payload(android_id, security_token)

        if self._log_debug_verbose:
            _logger.debug("GCM check in payload:\n%s", payload)

        retries = 100
        acir = None
        content = None
        for try_num in range(retries):
            try:
                async with self._session.post(
                    url=GCM_CHECKIN_URL,
                    headers={"Content-Type": "application/x-protobuf"},
                    data=payload.SerializeToString(),
                    timeout=self.CLIENT_TIMEOUT,
                ) as resp:
                    if resp.status == 200:
                        acir = AndroidCheckinResponse()
                        content = await resp.read()
                        break
                    else:
                        text = await resp.text()
                if acir and content:
                    break
                else:
                    _logger.warning(
                        "GCM checkin failed on attempt %s out "
                        + "of %s with status: %s, %s",
                        try_num + 1,
                        retries,
                        resp.status,
                        text,
                    )
                # retry without android id and security_token
                payload = self._get_checkin_payload()
                await asyncio.sleep(1)
            except Exception as e:
                _logger.warning(
                    "Error during gcm checkin post attempt %s out of %s",
                    try_num + 1,
                    retries,
                    exc_info=e,
                )
                await asyncio.sleep(1)

        if not acir or not content:
            _logger.error("Unable to checkin to gcm after %s retries", retries)
            return None
        acir.ParseFromString(content)

        if self._log_debug_verbose:
            msg = MessageToJson(acir, indent=4)
            _logger.debug("GCM check in response (raw):\n%s", msg)

        return MessageToDict(acir)

    async def gcm_register(
        self,
        options: dict[str, Any],
        retries: int = 100,
    ) -> dict[str, str] | None:
        """
        obtains a gcm token

        app_id: app id as an integer
        retries: number of failed requests before giving up

        returns {"token": "...", "gcm_app_id": 123123, "androidId":123123,
                        "securityToken": 123123}
        """
        # contains android_id, security_token and more
        gcm_app_id = f"wp:{self.config.bundle_id}#{uuid.uuid4()}"
        android_id = options["androidId"]
        security_token = options["securityToken"]

        headers = {
            "Authorization": f"AidLogin {android_id}:{security_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = {
            "app": "org.chromium.linux",
            "X-subtype": gcm_app_id,
            "device": android_id,
            "sender": GCM_SERVER_KEY_B64,
        }
        if self._log_debug_verbose:
            _logger.debug("GCM Registration request: %s", body)

        last_error: str | Exception | None = None
        for try_num in range(retries):
            try:
                async with self._session.post(
                    url=GCM_REGISTER_URL,
                    headers=headers,
                    data=body,
                    timeout=self.CLIENT_TIMEOUT,
                ) as resp:
                    response_text = await resp.text()
                if "Error" in response_text:
                    _logger.warning(
                        "GCM register request attempt %s out of %s has failed with %s",
                        try_num + 1,
                        retries,
                        response_text,
                    )
                    last_error = response_text
                    await asyncio.sleep(1)
                    continue
                token = response_text.split("=")[1]

                return {
                    "token": token,
                    "app_id": gcm_app_id,
                    "android_id": android_id,
                    "security_token": security_token,
                }

            except Exception as e:
                last_error = e
                _logger.warning(
                    "Error during gcm auth request attempt %s out of %s",
                    try_num + 1,
                    retries,
                    exc_info=e,
                )
                await asyncio.sleep(1)

        errorstr = f"Unable to complete gcm auth request after {retries} tries"
        if isinstance(last_error, Exception):
            _logger.error(errorstr, exc_info=last_error)
        else:
            errorstr += f", last error was {last_error}"
            _logger.error(errorstr)
        return None

    async def fcm_install_and_register(
        self, gcm_data: dict[str, Any], keys: dict[str, Any]
    ) -> dict[str, Any] | None:
        if installation := await self.fcm_install():
            registration = await self.fcm_register(gcm_data, installation, keys)
            return {
                "registration": registration,
                "installation": installation,
            }
        return None

    async def fcm_install(self) -> dict | None:
        fid = bytearray(secrets.token_bytes(17))
        # Replace the first 4 bits with the FID header 0b0111.
        fid[0] = 0b01110000 + (fid[0] % 0b00010000)
        fid64 = b64encode(fid).decode()

        hb_header = b64encode(
            json.dumps({"heartbeats": [], "version": 2}).encode()
        ).decode()
        headers = {
            "x-firebase-client": hb_header,
            "x-goog-api-key": self.config.api_key,
        }
        self._add_android_restriction_headers(headers)
        payload = {
            "appId": self.config.app_id,
            "authVersion": AUTH_VERSION,
            "fid": fid64,
            "sdkVersion": SDK_VERSION,
        }
        url = FCM_INSTALLATION + f"projects/{self.config.project_id}/installations"
        async with self._session.post(
            url=url,
            headers=headers,
            data=json.dumps(payload),
            timeout=self.CLIENT_TIMEOUT,
        ) as resp:
            if resp.status == 200:
                fcm_install = await resp.json()

                return {
                    "token": fcm_install["authToken"]["token"],
                    "expires_in": int(fcm_install["authToken"]["expiresIn"][:-1:]),
                    "refresh_token": fcm_install["refreshToken"],
                    "fid": fcm_install["fid"],
                    "created_at": time.monotonic(),
                }
            else:
                text = await resp.text()
                _logger.error(
                    "Error during fcm_install: %s ",
                    text,
                )
                return None

    async def fcm_refresh_install_token(self) -> dict | None:
        hb_header = b64encode(
            json.dumps({"heartbeats": [], "version": 2}).encode()
        ).decode()
        if not self.credentials:
            raise RuntimeError("Credentials must be set to refresh install token")
        fcm_refresh_token = self.credentials["fcm"]["installation"]["refresh_token"]

        headers = {
            "Authorization": f"{AUTH_VERSION} {fcm_refresh_token}",
            "x-firebase-client": hb_header,
            "x-goog-api-key": self.config.api_key,
        }
        self._add_android_restriction_headers(headers)
        payload = {
            "installation": {
                "sdkVersion": SDK_VERSION,
                "appId": self.config.app_id,
            }
        }
        url = (
            FCM_INSTALLATION + f"projects/{self.config.project_id}/"
            "installations/{fid}/authTokens:generate"
        )
        async with self._session.post(
            url=url,
            headers=headers,
            data=json.dumps(payload),
            timeout=self.CLIENT_TIMEOUT,
        ) as resp:
            if resp.status == 200:
                fcm_refresh = await resp.json()
                return {
                    "token": fcm_refresh["token"],
                    "expires_in": int(fcm_refresh["expiresIn"][:-1:]),
                    "created_at": time.monotonic(),
                }
            else:
                text = await resp.text()
                _logger.error(
                    "Error during fcm_refresh_install_token: %s ",
                    text,
                )
                return None

    def generate_keys(self) -> dict:
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        serialized_private = private_key.private_bytes(
            encoding=serialization.Encoding.DER,  # asn1
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        serialized_public = public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return {
            "public": urlsafe_b64encode(serialized_public[26:]).decode(
                "ascii"
            ),  # urlsafe_base64(serialized_public[26:]),
            "private": urlsafe_b64encode(serialized_private).decode("ascii"),
            "secret": urlsafe_b64encode(os.urandom(16)).decode("ascii"),
        }

    async def fcm_register(
        self,
        gcm_data: dict,
        installation: dict,
        keys: dict,
        retries: int = 2,
    ) -> dict[str, Any] | None:
        headers = {
            "x-goog-api-key": self.config.api_key,
            "x-goog-firebase-installations-auth": installation["token"],
        }
        self._add_android_restriction_headers(headers)
        # If vapid_key is the default do not send it here or it will error
        vapid_key = (
            self.config.vapid_key
            if self.config.vapid_key != GCM_SERVER_KEY_B64
            else None
        )
        payload = {
            "web": {
                "applicationPubKey": vapid_key,
                "auth": keys["secret"],
                "endpoint": FCM_SEND_URL + gcm_data["token"],
                "p256dh": keys["public"],
            }
        }
        url = FCM_REGISTRATION + f"projects/{self.config.project_id}/registrations"
        if self._log_debug_verbose:
            _logger.debug("FCM registration data: %s", payload)

        for try_num in range(retries):
            try:
                async with self._session.post(
                    url=url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=self.CLIENT_TIMEOUT,
                ) as resp:
                    if resp.status == 200:
                        fcm = await resp.json()
                        return fcm
                    else:
                        text = await resp.text()
                        _logger.error(  # pylint: disable=duplicate-code
                            "Error during fmc register request "
                            "attempt %s out of %s: %s",
                            try_num + 1,
                            retries,
                            text,
                        )

            except Exception as e:
                _logger.error(  # pylint: disable=duplicate-code
                    "Error during fmc register request attempt %s out of %s",
                    try_num + 1,
                    retries,
                    exc_info=e,
                )
                await asyncio.sleep(1)
        return None

    async def checkin_or_register(self) -> dict[str, Any]:
        """Check in if you have credentials otherwise register as a new client.

        :param sender_id: sender id identifying push service you are connecting to.
        :param app_id: identifier for your application.
        :return: The FCM token which is used to identify you with the push end
            point application.
        """
        if self.credentials:
            gcm_response = await self.gcm_check_in(
                self.credentials["gcm"]["android_id"],
                self.credentials["gcm"]["security_token"],
            )
            if gcm_response:
                return self.credentials

        self.credentials = await self.register()
        if self.credentials_updated_callback:
            self.credentials_updated_callback(self.credentials)

        return self.credentials

    async def register(self) -> dict:
        """Register gcm and fcm tokens for sender_id.
            Typically you would
            call checkin instead of register which does not do a full registration
            if credentials are present

        :param sender_id: sender id identifying push service you are connecting to.
        :param app_id: identifier for your application.
        :return: The dict containing all credentials.
        """

        keys = self.generate_keys()

        gcm_data = await self.gcm_check_in_and_register()
        if gcm_data is None:
            raise RuntimeError(
                "Unable to establish subscription with Google Cloud Messaging."
            )
        self._log_verbose("GCM subscription: %s", gcm_data)

        fcm_data = await self.fcm_install_and_register(gcm_data, keys)
        if not fcm_data:
            raise RuntimeError("Unable to register with fcm")
        self._log_verbose("FCM registration: %s", fcm_data)
        res: dict[str, Any] = {
            "keys": keys,
            "gcm": gcm_data,
            "fcm": fcm_data,
            "config": {
                "bundle_id": self.config.bundle_id,
                "project_id": self.config.project_id,
                "vapid_key": self.config.vapid_key,
            },
        }
        self._log_verbose("Credential: %s", res)
        _logger.info("Registered with FCM")
        return res

    def _log_verbose(self, msg: str, *args: object) -> None:
        if self._log_debug_verbose:
            _logger.debug(msg, *args)

    @property
    def _session(self) -> ClientSession:
        if self._http_client_session:
            return self._http_client_session
        if self._local_session is None:
            self._local_session = ClientSession()
        return self._local_session

    async def close(self) -> None:
        """Close aiohttp session."""
        session = self._local_session
        self._local_session = None
        if session:
            await session.close()
