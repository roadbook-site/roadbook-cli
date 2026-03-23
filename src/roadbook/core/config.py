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
PROJECT_CONFIG_FILE = Path.cwd() / ".roadbook" / "config.yaml"

DEFAULT_CONFIG = {
    "core": {
        "server_url": "http://localhost:8000",
        "timeout": 30,
        "language": "auto"
    },
    "scaffold": {
        "language": "python",
        "headless": False,
        "browser_type": "chromium",
        "cdp_port": 9222,
        "default_timeout": 10000,
        "proxy": None,
        "user_agent": None
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
            
            # Migrate old "browser" and "network" nested keys into "scaffold"
            if "browser" in config:
                if "scaffold" not in config:
                    config["scaffold"] = {}
                for bk, bv in config["browser"].items():
                    config["scaffold"][bk] = bv
                del config["browser"]
                changed = True
                
            if "network" in config:
                if "scaffold" not in config:
                    config["scaffold"] = {}
                for nk, nv in config["network"].items():
                    config["scaffold"][nk] = nv
                del config["network"]
                changed = True
                
            if "scaffold" in config and "template_dir" in config["scaffold"]:
                del config["scaffold"]["template_dir"]
                changed = True

            if changed:
                save_user_config(config)
            return config
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

DEFAULT_CONFIG_YAML = """# Roadbook Global Configuration

# Core system settings
core:
  # Base URL for the Roadbook backend server
  server_url: "http://localhost:8000"
  
  # Default timeout in seconds for API and core network requests
  timeout: 30
  
  # CLI interface language ("auto", "en", "zh")
  language: "auto"

# Options specifically controlling generated scaffolding scripts
scaffold:
  # Programming language for the generated scripts
  # Supported: "python" (JavaScript/TypeScript support planned for future)
  language: "python"
  
  # Run the generated script without a visible browser UI
  # Supported: true (hidden), false (visible)
  headless: false
  
  # Browser engine to use for Playwright
  # Supported: "chromium" (default), "firefox", "webkit"
  browser_type: "chromium"
  
  # Remote debugging port for connecting to an existing browser instance
  # 9222 is the standard port for Chromium remote debugging
  # Set to 0 or null to disable auto-connecting via CDP port
  cdp_port: 9222
  
  # Default timeout for page loads and Playwright element actions (in milliseconds)
  # Default is 10000ms (10 seconds)
  default_timeout: 10000
  
  # Optional Proxy server URL for the automated browser requests (e.g., "http://127.0.0.1:8080")
  # Supported: null (no proxy), or a valid proxy string. Note: currently needs manual integration in browser.py.tpl
  proxy: null
  
  # Optional custom User-Agent string to masquerade the browser footprint
  # Supported: null (use default Playwright UA), or a string. Note: currently needs manual integration in browser.py.tpl
  user_agent: null
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
