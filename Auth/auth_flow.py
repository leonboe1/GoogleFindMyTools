#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

from selenium.webdriver.support.ui import WebDriverWait
from chrome_driver import create_driver

def request_oauth_account_token_flow():

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
        print("[AuthFlow] Waiting for 'oauth_token' cookie to be set...")
        WebDriverWait(driver, 300).until(
            lambda d: d.get_cookie("oauth_token") is not None
        )

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