#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import json
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

from Auth.token_cache import set_cached_value
from chrome_driver import create_driver
from KeyBackup.response_parser import get_fmdn_shared_key
from KeyBackup.shared_key_request import get_security_domain_request_url
from KeyBackup.vault_web_api import fetch_vault_keys_via_web_app

SIGN_IN_WAIT_S = 300

def request_shared_key_flow():
    driver = create_driver()
    try:
        # Open Google accounts sign-in page
        driver.get("https://accounts.google.com/")

        # Wait for user to sign in and redirect to https://myaccount.google.com
        print(f"[SharedKeyFlow] Waiting up to {SIGN_IN_WAIT_S}s for you to sign in...")
        try:
            WebDriverWait(driver, SIGN_IN_WAIT_S).until(
                ec.url_contains("https://myaccount.google.com")
            )
        except TimeoutException:
            # Selenium's own TimeoutException carries no message - give this
            # a clear one instead, same as Auth/auth_flow.py's sign-in wait.
            raise TimeoutError(
                f"Timed out after {SIGN_IN_WAIT_S}s waiting for you to sign in to your "
                f"Google account for the encryption confirmation step. Run this again "
                f"to retry."
            ) from None
        print("[SharedKeyFlow] Signed in successfully.")

        # Best-effort: also pull every owner key version via the same internal
        # RPC the real Find My Device web app uses (see KeyBackup/vault_web_api.py).
        # GetEidInfoForE2eeDevices (the endpoint the rest of this codebase uses)
        # always hands back only its own idea of "current", regardless of what
        # version is requested - this is the only way found so far to reach
        # the others. Each entry is itself still encrypted with the account's
        # one stable shared key (confirmed empirically: decrypting one with
        # get_shared_key() reproduces the exact owner key already cached from
        # the normal flow), so cache the raw blobs now and unwrap them lazily
        # wherever get_shared_key() is actually available - see
        # SpotApi/GetEidInfoForE2eeDevices/get_owner_key.py's
        # get_owner_key_from_wrapped_blob(). Any failure here is non-fatal to
        # sign-in; the unlock-page flow below is still the primary path.
        for entry in fetch_vault_keys_via_web_app(driver):
            if entry["domain"] == "finder_hw":
                set_cached_value(f"encrypted_owner_key_v{entry['version']}", entry["key"].hex())

        # Open the security domain request URL
        security_url = get_security_domain_request_url()
        driver.get(security_url)

        # Inject JavaScript interface
        script = """
        window.mm = {
            setVaultSharedKeys: function(str, vaultKeys) {
                console.log('setVaultSharedKeys called with:', str, vaultKeys);
                alert(JSON.stringify({ method: 'setVaultSharedKeys', str: str, vaultKeys: vaultKeys }));
            },
            closeView: function() {
                console.log('closeView called');
                alert(JSON.stringify({ method: 'closeView' }));
            }
        };
        """
        driver.execute_script(script)

        # This used to be an unconditional "while True" whose except-block
        # swallowed every exception (not just "no alert yet"), so if
        # neither JS callback ever fired it hung forever with no way out
        # short of killing the process by hand. Bound it to the same
        # sign-in timeout used above instead.
        print(f"[SharedKeyFlow] Waiting up to {SIGN_IN_WAIT_S}s for the encryption confirmation...")
        deadline = time.monotonic() + SIGN_IN_WAIT_S
        while time.monotonic() < deadline:
            # Check for alerts indicating JavaScript calls
            try:
                WebDriverWait(driver, 0.5).until(ec.alert_is_present())
            except TimeoutException:
                continue  # no alert yet - keep polling until the deadline

            alert = driver.switch_to.alert
            message = alert.text
            alert.accept()

            try:
                data = json.loads(message)
            except ValueError:
                print(f"[SharedKeyFlow] Ignoring unparseable alert: {message!r}")
                continue

            if data.get('method') == 'setVaultSharedKeys':
                shared_key = get_fmdn_shared_key(data['vaultKeys'])
                print("[SharedKeyFlow] Received Shared Key.")
                return shared_key.hex()
            elif data.get('method') == 'closeView':
                raise RuntimeError(
                    "Google closed the encryption confirmation without providing a key "
                    "(it may have been cancelled, or failed on Google's side). Run this "
                    "again to retry."
                )

        raise TimeoutError(
            f"Timed out after {SIGN_IN_WAIT_S}s waiting for the encryption confirmation "
            f"step to complete. Run this again to retry."
        )
    finally:
        driver.quit()


if __name__ == "__main__":
   request_shared_key_flow()
