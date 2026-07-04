#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
import undetected_chromedriver as uc
import os
import re
import shutil
import subprocess
import platform
import time

def get_chrome_major_version(chrome_path=None):
    """Return installed Chrome's major version, or None if it can't be determined."""
    candidates = [chrome_path] if chrome_path else []
    candidates += ["google-chrome", "/usr/bin/google-chrome", "chromium", "chromium-browser"]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            output = subprocess.check_output([candidate, "--version"], stderr=subprocess.STDOUT, text=True)
        except Exception:
            continue
        match = re.search(r"(\d+)\.\d+\.\d+\.\d+", output)
        if match:
            return int(match.group(1))
    return None

def find_chrome():
    """Find Chrome executable using known paths and system commands."""
    possiblePaths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\ProgramData\chocolatey\bin\chrome.exe",
        r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe",
        "/usr/bin/google-chrome",
        "/usr/local/bin/google-chrome",
        "/opt/google/chrome/chrome",
        "/snap/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ]
    # Check predefined paths
    for path in possiblePaths:
        if os.path.exists(path):
            return path
    # Use system command to find Chrome
    try:
        if platform.system() == "Windows":
            chrome_path = shutil.which("chrome")
        else:
            chrome_path = shutil.which("google-chrome") or shutil.which("chromium")
        if chrome_path:
            return chrome_path
    except Exception as e:
        print(f"[ChromeDriver] Error while searching system paths: {e}")
    return None

def get_options():
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return chrome_options

def create_driver():
    """Create a Chrome WebDriver with undetected_chromedriver."""
    try:
        # Kill any existing Chrome processes first
        try:
            if platform.system() == "Windows":
                os.system("taskkill /f /im chrome.exe >nul 2>&1")
            else:
                os.system("pkill -f chrome")
            time.sleep(2)  # Wait for processes to close
        except:
            pass
            
        chrome_options = get_options()
        version_main = get_chrome_major_version()
        driver = uc.Chrome(options=chrome_options, version_main=version_main)
        print("[ChromeDriver] Installed and browser started.")
        return driver
    except Exception as e:
        print(f"[ChromeDriver] Default ChromeDriver creation failed: {e}")
        print("[ChromeDriver] Trying alternative paths...")
        chrome_path = find_chrome()
        if chrome_path:
            chrome_options = get_options()
            chrome_options.binary_location = chrome_path
            try:
                version_main = get_chrome_major_version(chrome_path)
                driver = uc.Chrome(options=chrome_options, version_main=version_main)
                print(f"[ChromeDriver] ChromeDriver started using {chrome_path}")
                return driver
            except Exception as e:
                print(f"[ChromeDriver] ChromeDriver failed using path {chrome_path}: {e}")
        else:
            print("[ChromeDriver] No Chrome executable found in known paths.")

        # Final fallback - try headless mode
        print("[ChromeDriver] Trying headless mode as last resort...")
        try:
            chrome_options = get_options()
            chrome_options.add_argument("--headless")
            version_main = get_chrome_major_version(chrome_path)
            driver = uc.Chrome(options=chrome_options, version_main=version_main)
            print("[ChromeDriver] Started in headless mode successfully.")
            return driver
        except Exception as e:
            print(f"[ChromeDriver] Headless mode also failed: {e}")
        
        raise Exception(
            "[ChromeDriver] Failed to install ChromeDriver. A current version of Chrome was not detected on your system.\n"
            "If you know that Chrome is installed, update Chrome to the latest version. If the script is still not working, "
            "set the path to your Chrome executable manually inside the script."
        )

if __name__ == '__main__':
    create_driver()