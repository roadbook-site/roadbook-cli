import os
from pathlib import Path

# Default paths
HOME_DIR = Path.home()
if os.environ.get("ROADBOOK_HOME"):
    ROADBOOK_DIR = Path(os.environ["ROADBOOK_HOME"])
else:
    ROADBOOK_DIR = HOME_DIR / ".roadbook"

BOOKS_DIR = ROADBOOK_DIR / "books"
CONFIG_FILE = ROADBOOK_DIR / "config.yaml"

def ensure_roadbook_dir():
    """Ensure the ~/.roadbook directory structure exists."""
    if not ROADBOOK_DIR.exists():
        ROADBOOK_DIR.mkdir(parents=True)
        print(f"Created roadbook directory at: {ROADBOOK_DIR}")
    
    if not BOOKS_DIR.exists():
        BOOKS_DIR.mkdir()
        print(f"Created books directory at: {BOOKS_DIR}")
    
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("# Roadbook CLI Configuration\n")
            f.write("token: null\n")
        print(f"Created config file at: {CONFIG_FILE}")

def get_roadbook_dir() -> Path:
    ensure_roadbook_dir()
    return ROADBOOK_DIR

def get_books_dir() -> Path:
    ensure_roadbook_dir()
    return BOOKS_DIR
