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

def ensure_storage_state_dir() -> Path:
    """Ensures the storage state directory exists."""
    # Standard location: <root>/.auth
    auth_dir = get_project_root() / ".auth"
    auth_dir.mkdir(parents=True, exist_ok=True)
    return auth_dir

def get_storage_state_path(filename: str = "auth.json") -> Path:
    """Returns the absolute path for a storage state file."""
    # If it's already an absolute path, return it
    if os.path.isabs(filename):
        return Path(filename)
    
    # If it contains path separators, assume relative to CWD (or project root? let's stick to CWD for flex)
    if os.sep in filename or '/' in filename:
         return Path(filename).resolve()
         
    return ensure_storage_state_dir() / filename

def wait_for_page_load(page: Page, strategy: str = "domcontentloaded", timeout: int = 10000):
    """
    Waits for the page to reach a certain state.
    Strategies: 'load', 'domcontentloaded', 'networkidle'.
    """
    try:
        page.wait_for_load_state(strategy, timeout=timeout)
    except Exception as e:
        logging.warning(f"Wait for {strategy} timed out: {e}. Continuing...")

def get_playwright_context(headless=False, cdp_url=None, storage_state_path=None):
    """
    Standard context manager for Playwright.
    Supports three modes:
    1. CDP (Connect to existing browser): pass cdp_url
    2. Storage State (Fresh browser with restored cookies/ls): pass storage_state_path
    3. Fresh (Clean slate): default
    
    Returns:
        p, browser, context, page, context_info
        context_info is a dict: {"mode": "cdp"|"storage"|"fresh", "file": str|None}
    """
    p = sync_playwright().start()
    
    # Resolve storage path if provided
    resolved_storage_path = None
    if storage_state_path:
        resolved_storage_path = get_storage_state_path(storage_state_path)

    context_info = {"mode": "fresh", "file": None}
    
    # --- Browser Launch Strategies ---
    if cdp_url:
        # Strategy 1: Connect to Existing Browser (CDP)
        # Best for: Debugging, reusing login state, avoiding bot detection.
        # Ensure Chrome is running with: --remote-debugging-port=9222
        logging.info(f"Connecting to existing browser via CDP: {cdp_url}")
        browser = p.chromium.connect_over_cdp(cdp_url)
        context_info = {"mode": "cdp", "file": None}
        
        # Crucial for CDP: reuse the existing default context to keep login state
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = browser.new_context()
            
        # Try to reuse an existing ACTIVE page first
        if context.pages:
            # Strategies for picking the "right" page could be added here
            # For now, pick the first one and bring it to front
            page = context.pages[0]
            page.bring_to_front()
        else:
            page = context.new_page()

    else:
        # Strategy 2 & 3: Fresh Browser (with optional Storage State)
        browser = p.chromium.launch(headless=headless)
        
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
        
    return p, browser, context, page, context_info
