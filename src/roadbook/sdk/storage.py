# src/roadbook/sdk/storage.py
import os
import time
from pathlib import Path
from typing import Union

class StorageManager:
    """Manages unstructured and binary data (like screenshots, html files, downloads)."""
    
    def __init__(self, run_dir: Path, outputs_dir: Path):
        self.run_dir = run_dir
        self.outputs_dir = outputs_dir
        self.screenshots_dir = run_dir / "screenshots"
        # Store kv files (downloads/media) in a dedicated 'downloads' subdirectory
        self.downloads_dir = outputs_dir / "downloads"
        
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    def get_download_path(self, filename: str) -> str:
        """Returns the absolute path to save a downloaded file in the current run's outputs."""
        filepath = self.downloads_dir / filename
        return str(filepath)

    def set_value(self, key: str, value: Union[str, bytes], content_type: str = "text/plain"):
        """Saves a value to the KV store (downloads dir). The key determines the filename."""
        # Simple heuristic to add extension based on content_type if missing
        ext = ""
        if "html" in content_type and not key.endswith(".html"):
            ext = ".html"
        elif "json" in content_type and not key.endswith(".json"):
            ext = ".json"
        elif "png" in content_type and not key.endswith(".png"):
            ext = ".png"
            
        filename = f"{key}{ext}"
        filepath = self.downloads_dir / filename
        
        mode = "wb" if isinstance(value, bytes) else "w"
        encoding = None if isinstance(value, bytes) else "utf-8"
        
        with open(filepath, mode, encoding=encoding) as f:
            f.write(value)
            
        return str(filepath)

    def get_value(self, key: str) -> Union[str, bytes, None]:
        """Reads a value from the KV store (downloads dir)."""
        for p in self.downloads_dir.glob(f"{key}*"):
            if p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return f.read()
                except UnicodeDecodeError:
                    with open(p, "rb") as f:
                        return f.read()
        return None

    def save_screenshot(self, name: str, page) -> str:
        """Saves a screenshot from a Playwright page to the runtime directory."""
        timestamp = int(time.time() * 1000)
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        page.screenshot(path=str(filepath))
        return str(filepath)
