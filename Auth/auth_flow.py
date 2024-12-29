#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import time
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait

def request_oauth_account_token_flow():
    # Set up Chrome options
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Update with your own path if different, probably need to set it as a startup flag in the future.

    print("""[AuthFlow] This script will now open Google Chrome on your device. 
    Make that you allow Python (or PyCharm) to control Chrome (macOS only). 
    Please login with your Google account.""")

    # Press enter to continue
    input("[AuthFlow] Press Enter to continue...")

    # Automatically install and set up the Chrome driver
    print("[AuthFlow] Installing ChromeDriver...")
    driver = uc.Chrome(options=chrome_options)
    print("[AuthFlow] ChromeDriver installed and browser started.")

    try:
        # Open the browser and navigate to the URL
        print("[AuthFlow] Navigating to the URL...")
        start_time = time.time()
        driver.get("https://accounts.google.com/EmbeddedSetup")
        print(f"[AuthFlow] Page loaded in {time.time() - start_time:.2f} seconds.")

        # Wait until the "oauth_token" cookie is set
        print("[AuthFlow] Waiting for 'oauth_token' cookie to be set...")
        WebDriverWait(driver, 300).until(
            lambda d: d.get_cookie("oauth_token") is not None
        )

        # Get the value of the "oauth_token" cookie
        oauth_token_cookie = driver.get_cookie("oauth_token")
        oauth_token_value = oauth_token_cookie['value']

        # Print the value of the "oauth_token" cookie
        print("oauth_token:", oauth_token_value)

        return oauth_token_value

    finally:
        # Close the browser
        print("[AuthFlow] Closing the browser...")
        driver.quit()

if __name__ == '__main__':
    request_oauth_account_token_flow()
