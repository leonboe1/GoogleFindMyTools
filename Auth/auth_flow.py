#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import threading

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from chrome_driver import create_driver

SIGN_IN_WAIT_S = 300

# create_driver() unconditionally pkills any running "chrome" process before
# launching a new one, so two overlapping calls would kill each other's
# browser. This serializes them process-wide instead of racing.
_flow_lock = threading.Lock()

def request_oauth_account_token_flow():
    with _flow_lock:
        return _request_oauth_account_token_flow()


def _request_oauth_account_token_flow():

    print("""[AuthFlow] This script will now open Google Chrome on your device to login to your Google account.
> Please make sure that Chrome is installed on your system.
> For macOS users only: Make that you allow Python (or PyCharm) to control Chrome if prompted.
    """)

    # Press enter to continue
    input("[AuthFlow] Press Enter to continue...")

    # Automatically install and set up the Chrome driver
    print("[AuthFlow] Installing ChromeDriver...")

    driver = create_driver()

    try:
        # Open the browser and navigate to the URL
        driver.get("https://accounts.google.com/EmbeddedSetup")

        # Wait until the "oauth_token" cookie is set
        print(f"[AuthFlow] Waiting up to {SIGN_IN_WAIT_S}s for you to finish signing in "
              f"('oauth_token' cookie not set yet)...")
        try:
            WebDriverWait(driver, SIGN_IN_WAIT_S).until(
                lambda d: d.get_cookie("oauth_token") is not None
            )
        except TimeoutException:
            # Selenium's own TimeoutException carries no message, so this
            # would otherwise surface as a blank "Message: " error with no
            # indication of what actually happened or how long it waited.
            raise TimeoutError(
                f"Timed out after {SIGN_IN_WAIT_S}s waiting for you to complete the Google "
                f"sign-in in the browser. Run this again to retry."
            ) from None

        # Get the value of the "oauth_token" cookie
        oauth_token_cookie = driver.get_cookie("oauth_token")
        oauth_token_value = oauth_token_cookie['value']

        # Print the value of the "oauth_token" cookie
        print("[AuthFlow] Retrieved Account Token successfully.")

        return oauth_token_value

    finally:
        # Close the browser
        driver.quit()

if __name__ == '__main__':
    request_oauth_account_token_flow()