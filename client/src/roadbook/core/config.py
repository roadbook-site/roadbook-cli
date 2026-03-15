import os
from pathlib import Path
import yaml
from typing import Dict, Any

# Default paths
HOME_DIR = Path.home()
if os.environ.get("ROADBOOK_HOME"):
    ROADBOOK_DIR = Path(os.environ["ROADBOOK_HOME"])
else:
    ROADBOOK_DIR = HOME_DIR / ".roadbook"

# New Structure:
# ~/.roadbook/
#   .core/        (System files)
#     config.yaml
#   <rb-id>/      (Roadbooks)

CORE_DIR = ROADBOOK_DIR / ".core"
BOOKS_DIR = ROADBOOK_DIR  # Books are now direct children
USER_CONFIG_FILE = CORE_DIR / "config.yaml"
PROJECT_CONFIG_FILE = Path.cwd() / ".roadbook" / "config.yaml"

DEFAULT_CONFIG = {
    "server_url": "http://localhost:8000",
    "token": None,
    "scaffold_defaults": {
        "language": "python",
        "headless": False,
        "browser_type": "chromium"
    }
}

def ensure_roadbook_dir():
    """Ensure the ~/.roadbook directory structure exists."""
    if not ROADBOOK_DIR.exists():
        ROADBOOK_DIR.mkdir(parents=True)
    
    if not CORE_DIR.exists():
        CORE_DIR.mkdir()
    
    # Config Migration
    if not USER_CONFIG_FILE.exists():
        legacy_config = ROADBOOK_DIR / "config.yaml"
        if legacy_config.exists():
            try:
                legacy_config.rename(USER_CONFIG_FILE)
            except Exception:
                pass
        
        if not USER_CONFIG_FILE.exists():
            save_user_config(DEFAULT_CONFIG)
            
    # Session Migration
    legacy_session = ROADBOOK_DIR / "active_session.json"
    new_session = CORE_DIR / "active_session.json"
    if legacy_session.exists() and not new_session.exists():
        try:
            legacy_session.rename(new_session)
        except Exception:
            pass

def get_roadbook_dir() -> Path:
    ensure_roadbook_dir()
    return ROADBOOK_DIR

def get_books_dir() -> Path:
    ensure_roadbook_dir()
    return BOOKS_DIR

def _merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge dictionary configurations."""
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result

def load_user_config() -> Dict[str, Any]:
    ensure_roadbook_dir()
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

def load_project_config() -> Dict[str, Any]:
    if PROJECT_CONFIG_FILE.exists():
        try:
            with open(PROJECT_CONFIG_FILE, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

def load_config() -> Dict[str, Any]:
    """
    Load configuration with priority:
    1. Project Config (./.roadbook/config.yaml)
    2. User Config (~/.roadbook/config.yaml)
    3. Default Config
    """
    config = DEFAULT_CONFIG.copy()
    user_config = load_user_config()
    config = _merge_config(config, user_config)
    
    project_config = load_project_config()
    config = _merge_config(config, project_config)
    
    return config

def save_user_config(config: Dict[str, Any]):
    if not CORE_DIR.exists():
        CORE_DIR.mkdir(parents=True, exist_ok=True)
    with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)

def get_token():
    config = load_config()
    return config.get("token")

def set_token(token):
    # Only update user config for token
    config = load_user_config()
    config["token"] = token
    save_user_config(config)

def get_server_url():
    config = load_config()
    return config.get("server_url", "http://localhost:8000")
