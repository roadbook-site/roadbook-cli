import os
import sys
import shutil
from pathlib import Path

def find_chrome_executable() -> str:
    """Finds the default Chrome or Edge executable on the system."""
    
    # Check environment variable first
    if "ROADBOOK_BROWSER_PATH" in os.environ:
        return os.environ["ROADBOOK_BROWSER_PATH"]
        
    system = sys.platform
    
    if system == "win32":
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe")
        ]
        for path in paths:
            if os.path.exists(path):
                return path
                
    elif system == "darwin": # macOS
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        ]
        for path in paths:
            if os.path.exists(path):
                return path
                
    else: # linux
        commands = ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium", "microsoft-edge"]
        for cmd in commands:
            path = shutil.which(cmd)
            if path:
                return path
                
    return None
