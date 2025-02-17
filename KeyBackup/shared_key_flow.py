#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import undetected_chromedriver as uc

from KeyBackup.response_parser import get_fmdn_shared_key
from KeyBackup.shared_key_request import get_security_domain_request_url


# Initialize undetected Chrome WebDriver
def create_driver():
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--start-maximized")

    # For Windows users only: set binary location to "C:\ProgramData\chocolatey\bin\chrome.exe" or similar
    # chrome_options.binary_location = r"INSERT_PATH_TO_CHROME_BINARY_HERE"

    try:
        driver = uc.Chrome(options=chrome_options)
        print("[SharedKeyFlow] ChromeDriver installed and browser started.")
        return driver
    except Exception as e:
        raise Exception("[SharedKeyFlow] Failed to install ChromeDriver. A current version of Chrome was not detected on your system.\n\nIf you know that Chrome is installed, first try to update Chrome to the latest version. If the script is still not working afterward, open the file 'KeyBackup/shared_key_flow.py' and set the path to your Chrome executable in line 20.")


def request_shared_key_flow():
    driver = create_driver()
    try:
        # Open Google accounts sign-in page
        driver.get("https://accounts.google.com/")

        # Wait for user to sign in and redirect to https://myaccount.google.com
        WebDriverWait(driver, 300).until(
            ec.url_contains("https://myaccount.google.com")
        )
        print("[SharedKeyFlow] Signed in successfully.")

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

        while True:
            # Check for alerts indicating JavaScript calls
            try:
                WebDriverWait(driver, 0.5).until(ec.alert_is_present())
                alert = driver.switch_to.alert
                message = alert.text
                alert.accept()

                # Parse the alert message
                import json
                data = json.loads(message)

                if data['method'] == 'setVaultSharedKeys':
                    shared_key = get_fmdn_shared_key(data['vaultKeys'])
                    print("[SharedKeyFlow] Received Shared Key.")
                    driver.quit()
                    return shared_key.hex()
                elif data['method'] == 'closeView':
                    print("[SharedKeyFlow] closeView() called. Closing browser.")
                    driver.quit()
                    break

            except Exception:
                pass

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
   request_shared_key_flow()
