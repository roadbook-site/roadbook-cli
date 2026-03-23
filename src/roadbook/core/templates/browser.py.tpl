"""
Browser configuration and initialization utilities.
"""
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
import logging
import os
from pathlib import Path
import time

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes this file is at <root>/scripts/utils/browser.py
    """
    # Go up 3 levels: utils -> scripts -> root
    try:
        return Path(__file__).resolve().parent.parent.parent
    except NameError:
        # Fallback if __file__ is not defined (e.g. interactive mode)
        return Path.cwd()

def ensure_browser_dir() -> Path:
    """Ensures the browser environment directory exists for profiles and storage states."""
    # Standard location: <root>/.browser
    browser_dir = get_project_root() / ".browser"
    browser_dir.mkdir(parents=True, exist_ok=True)
    return browser_dir

def get_storage_state_path(filename: str = "auth.json") -> Path:
    """Returns the absolute path for a storage state file."""
    # If it's already an absolute path, return it
    if os.path.isabs(filename):
        return Path(filename)
    
    # If it contains path separators, assume relative to CWD (or project root? let's stick to CWD for flex)
    if os.sep in filename or '/' in filename:
         return Path(filename).resolve()
         
    return ensure_browser_dir() / filename

def get_user_data_dir(dirname: str = "profile") -> Path:
    """Returns the absolute path for a persistent user data directory (profile)."""
    if os.path.isabs(dirname):
        return Path(dirname)
    if os.sep in dirname or '/' in dirname:
        return Path(dirname).resolve()
    return ensure_browser_dir() / dirname

def wait_for_page_load(page: Page, strategy: str = "domcontentloaded", timeout: int = None):
    """
    Waits for the page to reach a certain state.
    Strategies: 'load', 'domcontentloaded', 'networkidle'.
    """
    if timeout is None:
        try:
            from roadbook.core.config import load_config
            timeout = load_config().get("scaffold", {}).get("default_timeout", 10000)
        except ImportError:
            timeout = 10000

    try:
        page.wait_for_load_state(strategy, timeout=timeout)
    except Exception as e:
        logging.warning(f"Wait for {strategy} timed out: {e}. Continuing...")

def get_playwright_context(headless=None, cdp_url=None, storage_state_path=None, user_data_dir=None):
    """
    Standard context manager for Playwright.
    Supports four modes:
    1. CDP (Connect to existing browser): pass cdp_url or set in config
    2. Profile (Persistent Context): pass user_data_dir for a persistent browser profile
    3. Storage State (Fresh browser with restored cookies/ls): pass storage_state_path
    4. Fresh (Clean slate): default

    Returns:
        p, browser, context, page, context_info
        context_info is a dict: {"mode": "cdp"|"profile"|"storage"|"fresh", "file": str|None}
    """
    browser_type_name = "chromium"
    if headless is None:
        try:
            from roadbook.core.config import load_config
            config = load_config()
            browser_config = config.get("scaffold", {})
            headless = browser_config.get("headless", False)
            browser_type_name = browser_config.get("browser_type", "chromium")
            
            # If cdp_url wasn't provided directly, check if we should auto-connect to cdp_port
            if not cdp_url:
                cdp_port = browser_config.get("cdp_port", 9222)
                if cdp_port and int(cdp_port) > 0:
                    # Optional: uncomment the following line to make auto-CDP attachment the default
                    # cdp_url = f"http://localhost:{cdp_port}"
                    pass
        except ImportError:
            headless = False

    p = sync_playwright().start()
    playwright_browser_type = getattr(p, browser_type_name, p.chromium)
    
    # Resolve storage path if provided
    resolved_storage_path = None
    if storage_state_path:
        resolved_storage_path = get_storage_state_path(storage_state_path)

    context_info = {"mode": "fresh", "file": None}
    browser, context, page = None, None, None
    
    try:
        # --- Browser Launch Strategies ---
        if cdp_url:
            # Strategy 1: Connect to Existing Browser (CDP)
            # Best for: Debugging, reusing login state, avoiding bot detection.
            # Ensure Chrome is running with: --remote-debugging-port=9222
            logging.info(f"Connecting to existing browser via CDP: {cdp_url}")
            browser = playwright_browser_type.connect_over_cdp(cdp_url)
            context_info = {"mode": "cdp", "file": None}
            
            # Crucial for CDP: reuse the existing default context to keep login state
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            if context.pages:
                page = context.pages[0]
                page.bring_to_front()
            else:
                page = context.new_page()

        elif user_data_dir:
            # Strategy 2: Profile (Persistent Context)
            resolved_profile_path = get_user_data_dir(user_data_dir)
            logging.info(f"Launching persistent context (Profile) at: {resolved_profile_path}")
            
            context = playwright_browser_type.launch_persistent_context(
                user_data_dir=resolved_profile_path,
                headless=headless
            )
            browser = context.browser
            context_info = {"mode": "profile", "file": resolved_profile_path}
            page = context.pages[0] if context.pages else context.new_page()

        else:
            # Strategy 3 & 4: Storage State or Fresh
            browser = playwright_browser_type.launch(headless=headless)
            
            # Load storage state if provided
            if resolved_storage_path and resolved_storage_path.exists():
                 logging.info(f"Loading session from: {resolved_storage_path}")
                 context = browser.new_context(storage_state=resolved_storage_path)
                 context_info = {"mode": "storage", "file": resolved_storage_path}
            elif resolved_storage_path:
                 logging.info(f"Storage state file not found at: {resolved_storage_path}. Starting fresh, will save session here.")
                 context = browser.new_context()
                 # Mark as storage mode so we save it later, even if starting fresh
                 context_info = {"mode": "storage", "file": resolved_storage_path}
            else:
                 context = browser.new_context()
                 # mode remains "fresh"
                 
            page = context.new_page()

    except Exception as e:
        if "Executable doesn't exist" in str(e):
            try:
                from roadbook.core.i18n import t
                msg_not_found = t("browser_not_found")
                msg_install = t("browser_install_prompt")
            except ImportError:
                msg_not_found = "Playwright browser core not found!"
                msg_install = "Please run the following command in terminal to install (only needed once globally):"
                
            logging.error("\n" + "="*60)
            logging.error(msg_not_found)
            logging.error(msg_install)
            logging.error("    playwright install")
            logging.error("="*60 + "\n")
            raise SystemExit(1)
        raise e
        
    return p, browser, context, page, context_info
