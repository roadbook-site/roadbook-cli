import os
import sys
import shutil
from pathlib import Path

def find_all_browsers() -> list:
    """Finds all supported Chrome/Edge based browsers on the system."""
    browsers = []
    
    # Check environment variable first
    if "ROADBOOK_BROWSER_PATH" in os.environ:
        path = os.environ["ROADBOOK_BROWSER_PATH"]
        if os.path.exists(path):
            browsers.append({"name": "Custom (ROADBOOK_BROWSER_PATH)", "path": path})

    system = sys.platform

    def add_if_exists(name, paths):
        for p in paths:
            if os.path.exists(p):
                # avoid duplicates if path already added
                if not any(b["path"] == p for b in browsers):
                    browsers.append({"name": name, "path": p})
                break # Only add one instance per browser name

    if system == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        
        # Google Chrome
        add_if_exists("Google Chrome", [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.join(local_app_data, r"Google\Chrome\Application\chrome.exe")
        ])
        
        # Microsoft Edge
        add_if_exists("Microsoft Edge", [
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        ])
        
        # 360 Chrome (360极速浏览器)
        add_if_exists("360 Chrome (极速浏览器)", [
            r"C:\Program Files (x86)\360\360Chrome\Chrome\Application\360chrome.exe",
            r"C:\Program Files\360\360Chrome\Chrome\Application\360chrome.exe",
            os.path.join(local_app_data, r"360Chrome\Chrome\Application\360chrome.exe")
        ])

        # 360 Secure Browser (360安全浏览器)
        add_if_exists("360 Secure Browser (安全浏览器)", [
            r"C:\Program Files (x86)\360\360se6\Application\360se.exe",
            r"C:\Program Files\360\360se6\Application\360se.exe",
            os.path.join(local_app_data, r"360se6\Application\360se.exe")
        ])
        
        # Brave
        add_if_exists("Brave Browser", [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
        ])

    elif system == "darwin":  # macOS
        add_if_exists("Google Chrome", [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ])
        add_if_exists("Microsoft Edge", [
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        ])
        add_if_exists("Brave Browser", [
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
        ])

    else:  # Linux
        def add_linux_cmd(name, commands):
            for cmd in commands:
                path = shutil.which(cmd)
                if path and not any(b["path"] == path for b in browsers):
                    browsers.append({"name": name, "path": path})
                    break

        add_linux_cmd("Google Chrome", ["google-chrome", "google-chrome-stable"])
        add_linux_cmd("Chromium", ["chromium-browser", "chromium"])
        add_linux_cmd("Microsoft Edge", ["microsoft-edge"])
        add_linux_cmd("Brave Browser", ["brave-browser", "brave"])

    # Attempt to add Playwright's Chromium as a fallback
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            playwright_chrome_path = p.chromium.executable_path
            if os.path.exists(playwright_chrome_path):
                # avoid duplicates if path already added
                if not any(b["path"] == playwright_chrome_path for b in browsers):
                    browsers.append({"name": "Playwright Chromium (Fallback)", "path": playwright_chrome_path})
    except Exception:
        pass

    return browsers

def find_chrome_executable() -> str:
    """Finds the default Chrome or Edge executable on the system."""
    browsers = find_all_browsers()
    if browsers:
        return browsers[0]["path"]
    return None
