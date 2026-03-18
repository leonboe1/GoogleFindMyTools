#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#
import undetected_chromedriver as uc
import os
import shutil
import platform
import time
import subprocess
import re

def get_chrome_version(chrome_path):
    """Get Chrome version from executable."""
    try:
        if platform.system() == "Windows":
            # Try to get version from registry first
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                winreg.CloseKey(key)
                return int(version.split('.')[0])
            except:
                pass
            # Fallback: run chrome with --version
            result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=10)
            version_match = re.search(r'(\d+)\.\d+\.\d+\.\d+', result.stdout)
            if version_match:
                return int(version_match.group(1))
        else:
            result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True, timeout=10)
            version_match = re.search(r'(\d+)\.\d+\.\d+\.\d+', result.stdout)
            if version_match:
                return int(version_match.group(1))
    except Exception as e:
        print(f"[ChromeDriver] Could not determine Chrome version: {e}")
    return None

def find_chrome():
    """Find Chrome executable using known paths and system commands."""
    # Expand %USERNAME% for Windows paths
    username = os.environ.get('USERNAME', os.environ.get('USER', ''))

    possiblePaths = [
        # Windows paths
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\ProgramData\chocolatey\bin\chrome.exe",
        os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe"),
        f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
        # Additional Windows paths for Chrome installed per-user
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        # Linux paths
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/local/bin/google-chrome",
        "/opt/google/chrome/chrome",
        "/snap/bin/chromium",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        # macOS paths
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ]

    # Filter out empty paths and check for existence
    for path in possiblePaths:
        if path and os.path.exists(path):
            print(f"[ChromeDriver] Found Chrome at: {path}")
            return path

    # Use system command to find Chrome
    try:
        if platform.system() == "Windows":
            # Try multiple executable names on Windows
            for name in ["chrome", "google-chrome", "chromium"]:
                chrome_path = shutil.which(name)
                if chrome_path:
                    return chrome_path
            # Try using 'where' command on Windows
            try:
                result = subprocess.run(["where", "chrome.exe"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip().split('\n')[0]
            except:
                pass
        else:
            for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
                chrome_path = shutil.which(name)
                if chrome_path:
                    return chrome_path
    except Exception as e:
        print(f"[ChromeDriver] Error while searching system paths: {e}")
    return None

def get_options(headless=False):
    """Configure Chrome options for undetected-chromedriver."""
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--ignore-certificate-errors")

    if headless:
        chrome_options.add_argument("--headless=new")

    return chrome_options


def _try_create_uc_driver(chrome_options, version_main=None, browser_executable_path=None):
    """Helper to create undetected-chromedriver with proper error handling."""
    kwargs = {"options": chrome_options}

    if version_main is not None:
        kwargs["version_main"] = version_main

    if browser_executable_path is not None:
        kwargs["browser_executable_path"] = browser_executable_path

    return uc.Chrome(**kwargs)


def _try_webdriver_manager_fallback():
    """Try to use webdriver-manager as a fallback for standard Selenium."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        print("[ChromeDriver] Attempting webdriver-manager fallback...")
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=service, options=options)
        print("[ChromeDriver] Started using webdriver-manager (standard Selenium).")
        print("[ChromeDriver] WARNING: This uses standard Selenium without bot detection bypass!")
        return driver
    except Exception as e:
        print(f"[ChromeDriver] webdriver-manager fallback failed: {e}")
        return None


def safe_quit_driver(driver):
    """Safely quit the Chrome driver, handling WinError 6 and other errors."""
    if driver is None:
        return

    try:
        # Try normal quit first
        driver.quit()
    except OSError as e:
        # Handle "WinError 6: The handle is invalid" and similar errors
        print(f"[ChromeDriver] OSError during quit (usually harmless): {e}")
    except Exception as e:
        print(f"[ChromeDriver] Error during quit: {e}")
    finally:
        # Force kill any remaining processes
        try:
            if platform.system() == "Windows":
                os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
            else:
                os.system("pkill -f chromedriver >/dev/null 2>&1")
        except:
            pass


def create_driver():
    """Create a Chrome WebDriver with undetected_chromedriver.

    Attempts multiple strategies:
    1. Default undetected-chromedriver with auto-detection
    2. Specify Chrome path explicitly
    3. Specify Chrome version explicitly
    4. Try headless mode
    5. Fall back to webdriver-manager (standard Selenium)
    """
    # Kill any existing Chrome processes first
    try:
        if platform.system() == "Windows":
            os.system("taskkill /f /im chrome.exe >nul 2>&1")
            os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
        else:
            os.system("pkill -f chrome >/dev/null 2>&1")
            os.system("pkill -f chromedriver >/dev/null 2>&1")
        time.sleep(1)
    except:
        pass

    chrome_path = find_chrome()
    version_main = None

    if chrome_path:
        version_main = get_chrome_version(chrome_path)
        if version_main:
            print(f"[ChromeDriver] Detected Chrome version: {version_main}")

    # Strategy 1: Default with version_main if detected
    try:
        chrome_options = get_options()
        if chrome_path:
            chrome_options.binary_location = chrome_path
        driver = _try_create_uc_driver(chrome_options, version_main=version_main)
        print("[ChromeDriver] Installed and browser started.")
        return driver
    except Exception as e:
        print(f"[ChromeDriver] Strategy 1 (default) failed: {e}")

    # Strategy 2: Use browser_executable_path parameter
    if chrome_path:
        try:
            chrome_options = get_options()
            driver = _try_create_uc_driver(
                chrome_options,
                version_main=version_main,
                browser_executable_path=chrome_path
            )
            print(f"[ChromeDriver] Started using browser_executable_path: {chrome_path}")
            return driver
        except Exception as e:
            print(f"[ChromeDriver] Strategy 2 (explicit path) failed: {e}")

    # Strategy 3: Try without specifying version
    try:
        chrome_options = get_options()
        if chrome_path:
            chrome_options.binary_location = chrome_path
        driver = _try_create_uc_driver(chrome_options, version_main=None)
        print("[ChromeDriver] Started without explicit version.")
        return driver
    except Exception as e:
        print(f"[ChromeDriver] Strategy 3 (no version) failed: {e}")

    # Strategy 4: Try headless mode
    print("[ChromeDriver] Trying headless mode...")
    try:
        chrome_options = get_options(headless=True)
        if chrome_path:
            chrome_options.binary_location = chrome_path
        driver = _try_create_uc_driver(chrome_options, version_main=version_main)
        print("[ChromeDriver] Started in headless mode successfully.")
        return driver
    except Exception as e:
        print(f"[ChromeDriver] Strategy 4 (headless) failed: {e}")

    # Strategy 5: webdriver-manager fallback
    driver = _try_webdriver_manager_fallback()
    if driver:
        return driver

    # All strategies failed
    raise Exception(
        "[ChromeDriver] Failed to start ChromeDriver after all attempts.\n"
        "Possible solutions:\n"
        "1. Make sure Google Chrome is installed and up-to-date\n"
        "2. Try: pip install --upgrade undetected-chromedriver selenium webdriver-manager\n"
        "3. If Chrome is installed but not detected, set the path manually:\n"
        f"   Current detected path: {chrome_path or 'None'}\n"
        f"   Current detected version: {version_main or 'Unknown'}\n"
        "4. Check if Chrome is blocked by antivirus or firewall"
    )


if __name__ == '__main__':
    driver = create_driver()
    print("Driver created successfully!")
    driver.quit()