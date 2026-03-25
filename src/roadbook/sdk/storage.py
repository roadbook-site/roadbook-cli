# src/roadbook/sdk/storage.py
import os
import time
from pathlib import Path

class Storage:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.screenshots_dir = run_dir / "screenshots"
        self.artifacts_dir = run_dir / "artifacts"
        
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def save_screenshot(self, name: str, page) -> str:
        """Saves a screenshot from a Playwright page."""
        timestamp = int(time.time() * 1000)
        filename = f"{name}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        page.screenshot(path=str(filepath))
        return str(filepath)
    
    def save_artifact(self, name: str, content: str) -> str:
        """Saves a text/JSON artifact."""
        filepath = self.artifacts_dir / name
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return str(filepath)
