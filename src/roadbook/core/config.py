import os
from pathlib import Path
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

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
#     credentials.env
#   <rb-id>/      (Roadbooks)

CORE_DIR = ROADBOOK_DIR / ".core"
BOOKS_DIR = ROADBOOK_DIR  # Books are now direct children
USER_CONFIG_FILE = CORE_DIR / "config.yaml"
USER_ENV_FILE = CORE_DIR / "credentials.env"
PROJECT_CONFIG_FILE = Path.cwd() / ".rb" / "config.yaml"

DEFAULT_CONFIG = {
    "core": {
        "server_url": "http://localhost:8000",
        "timeout": 30,
        "language": "auto"
    },
    "scaffold": {
        "language": "python"
    },
    "browser": {
        "mode": "cdp",
        "cdp_port": 9222,
        "executable_path": None,
        "user_data_dir": None,
        "launch_args": [
            "--no-first-run",
            "--no-default-browser-check"
        ]
    }
}

def ensure_roadbook_dir():
    """Ensure the ~/.roadbook directory structure exists."""
    if not ROADBOOK_DIR.exists():
        ROADBOOK_DIR.mkdir(parents=True)
    
    if not CORE_DIR.exists():
        CORE_DIR.mkdir()
        
    if not BOOKS_DIR.exists():
        BOOKS_DIR.mkdir()
    
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
                config = yaml.safe_load(f) or {}
                
            # Clean up deprecated top-level fields
            changed = False
            for key in ["api_key", "token"]:
                if key in config:
                    del config[key]
                    changed = True
            if "core" in config and "api_key" in config["core"]:
                del config["core"]["api_key"]
                changed = True
            
            # Migrate old "browser" and "network" nested keys
            # network is deprecated, move to browser? Actually let's just delete it or keep it as is.
            if "network" in config:
                del config["network"]
                changed = True
                
            # Migrate old browser fields from scaffold to browser
            if "scaffold" in config:
                if "template_dir" in config["scaffold"]:
                    del config["scaffold"]["template_dir"]
                    changed = True
                
                # Move browser related fields from scaffold to browser
                browser_fields = ["mode", "cdp_port", "executable_path", "user_data_dir", "launch_args"]
                if "browser" not in config:
                    config["browser"] = {}
                
                for field in browser_fields:
                    if field in config["scaffold"]:
                        config["browser"][field] = config["scaffold"][field]
                        del config["scaffold"][field]
                        changed = True

            if changed:
                save_user_config(config)
            return config
        except Exception:
            pass
    return {}

def load_project_config(project_root: Path = None) -> Dict[str, Any]:
    config_file = project_root / ".rb" / "config.yaml" if project_root else PROJECT_CONFIG_FILE
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

def load_config(project_root: Path = None) -> Dict[str, Any]:
    """
    Load configuration with priority:
    1. Project Config (./.rb/config.yaml or specified root)
    2. User Config (~/.roadbook/.core/config.yaml)
    3. Default Config
    """
    config = DEFAULT_CONFIG.copy()
    user_config = load_user_config()
    config = _merge_config(config, user_config)

    project_config = load_project_config(project_root)
    config = _merge_config(config, project_config)
    
    return config

DEFAULT_CONFIG_YAML = """# Roadbook Default Configuration

core:
  server_url: http://localhost:8000
  timeout: 30
  language: auto

browser:
  mode: cdp                   # cdp (connect to local browser) or standalone (playwright launch)
  cdp_port: 9222              # Remote debugging port
  executable_path: null       # Path to Chrome/Edge executable. Null means auto-detect
  user_data_dir: null         # Path to user data profile. Null means use default ~/.roadbook/.core/profile
  launch_args:                # Additional args when launching browser
    - "--no-first-run"
    - "--no-default-browser-check"
    # - "--disable-blink-features=AutomationControlled"
"""

def save_user_config(config: Dict[str, Any]):
    if not CORE_DIR.exists():
        CORE_DIR.mkdir(parents=True, exist_ok=True)
        
    # If saving the exact default config, write with comments
    if config == DEFAULT_CONFIG:
        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_YAML)
    else:
        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False)

def save_project_config(config: Dict[str, Any]):
    project_dir = PROJECT_CONFIG_FILE.parent
    if not project_dir.exists():
        project_dir.mkdir(parents=True, exist_ok=True)
    with open(PROJECT_CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)

def load_env_configs():
    """Load environment variables from standard roadbook env files."""
    # Load user global env first
    if USER_ENV_FILE.exists():
        load_dotenv(dotenv_path=USER_ENV_FILE)
    
    # Then project env (which can override)
    project_env = Path.cwd() / ".env"
    if project_env.exists():
        load_dotenv(dotenv_path=project_env)

def get_api_key():
    load_env_configs()
    # 1. Check environment variable
    if "ROADBOOK_API_KEY" in os.environ:
        return os.environ["ROADBOOK_API_KEY"]
    
    # 2. Check old config.yaml fallback
    config = load_config()
    return config.get("core", {}).get("api_key") or config.get("api_key")

def set_api_key(api_key):
    if not CORE_DIR.exists():
        CORE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Standard format for python-dotenv set_key or just write to file
    content = ""
    if USER_ENV_FILE.exists():
        with open(USER_ENV_FILE, "r") as f:
            content = f.read()
            
    lines = content.splitlines()
    new_lines = []
    found = False
    for line in lines:
        if line.startswith("ROADBOOK_API_KEY="):
            new_lines.append(f"ROADBOOK_API_KEY={api_key}")
            found = True
        else:
            new_lines.append(line)
            
    if not found:
        new_lines.append(f"ROADBOOK_API_KEY={api_key}")
        
    with open(USER_ENV_FILE, "w") as f:
        f.write("\n".join(new_lines) + "\n")
        
    # Remove from config.yaml if it exists to migrate completely
    config = load_user_config()
    if "api_key" in config:
        del config["api_key"]
    if "core" in config and "api_key" in config["core"]:
        del config["core"]["api_key"]
    save_user_config(config)

def get_server_url():
    config = load_config()
    return config.get("core", {}).get("server_url", "http://localhost:8000")
