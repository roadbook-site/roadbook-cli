# src/roadbook/sdk/context.py
import os
import sys
from pathlib import Path
from contextlib import contextmanager

from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

from .io import IOManager
from .storage import Storage
from .logger import get_logger

class RoadbookContext:
    def __init__(self, run_dir: str = None, outputs_dir: str = None, headless: bool = None, cdp_url: str = None):
        if run_dir:
            self.run_dir = Path(run_dir)
            self.outputs_dir = Path(outputs_dir) if outputs_dir else Path(run_dir).parent.parent / "outputs" / Path(run_dir).name
        else:
            # Fallback or from env
            env_dir = os.environ.get("ROADBOOK_RUN_DIR")
            env_outputs_dir = os.environ.get("ROADBOOK_OUTPUTS_DIR")
            
            # In standard setup, it's runtime/run_xxxx. For ad-hoc local runs without CLI, use runtime/local_run
            self.run_dir = Path(env_dir) if env_dir else Path.cwd() / "runtime" / "local_run"
            self.outputs_dir = Path(env_outputs_dir) if env_outputs_dir else Path.cwd() / "outputs" / "local_run"
            
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        self.io = IOManager(self.outputs_dir)
        self.storage = Storage(self.run_dir, self.outputs_dir)
        self.logger = get_logger()
        
        # Load unified CLI configuration if available
        try:
            from roadbook.core.config import load_config
            self._cli_config = load_config()
        except ImportError:
            self._cli_config = {}
            
        scaffold_config = self._cli_config.get("scaffold", {})
        
        # Determine headless and cdp via CLI config merging (explicit param > config > default)
        self.headless = headless if headless is not None else scaffold_config.get("headless", False)
        
        if cdp_url:
            self.cdp_url = cdp_url
        else:
            cdp_port = scaffold_config.get("cdp_port")
            if cdp_port:
                self.cdp_url = f"http://localhost:{cdp_port}"
            else:
                self.cdp_url = None
                
        # Playwright internals
        self._playwright: Playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self.page: Page = None
        
        self.current_sheet = None

    def __enter__(self):
        self.logger.info("Starting Roadbook Context...")
        
        # Patch for Sync API inside asyncio loop (common in Agent setups/Jupyter)
        try:
            import asyncio
            if asyncio.get_running_loop():
                try:
                    import nest_asyncio
                    nest_asyncio.apply()
                except ImportError:
                    self.logger.warning("asyncio loop running but nest_asyncio not installed. Playwright Sync API might fail.")
        except RuntimeError:
            pass # No running loop

        self._playwright = sync_playwright().start()
        
        # Determine launch parameters
        scaffold_config = getattr(self, "_cli_config", {}).get("scaffold", {})
        browser_type_name = scaffold_config.get("browser_type", "chromium")
        browser_type = getattr(self._playwright, browser_type_name, self._playwright.chromium)
        
        connected = False
        if self.cdp_url:
            self.logger.info(f"Attempting to connect to CDP at {self.cdp_url}...")
            try:
                self._browser = browser_type.connect_over_cdp(self.cdp_url)
                self._context = self._browser.contexts[0] if self._browser.contexts else self._browser.new_context()
                self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
                connected = True
                self.logger.info("Successfully connected to existing browser via CDP.")
            except Exception as e:
                self.logger.warning(f"Failed to connect to CDP at {self.cdp_url}: {e}. Falling back to launching a new browser...")
        
        if not connected:
            self.logger.info(f"Launching new {browser_type_name} browser (headless={self.headless})...")
            self._browser = browser_type.launch(headless=self.headless)
            self._context = self._browser.new_context()
            self.page = self._context.new_page()
            
        # Set default timeout if configured
        default_timeout = scaffold_config.get("default_timeout", 30000)
        self._context.set_default_timeout(default_timeout)
            
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Error encountered: {exc_val}")
            # Automatically take screenshot on error
            if self.page:
                try:
                    self.storage.save_screenshot("error_state", self.page)
                    self.logger.info("Saved error state screenshot.")
                except Exception as e:
                    self.logger.error(f"Failed to take error screenshot: {e}")
                    
        self.logger.info("Closing Roadbook Context...")
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    @contextmanager
    def sheet(self, name: str):
        """
        Sheet-level binding for structured execution.
        """
        self.current_sheet = name
        self.logger.info(f"--- Entering Sheet: {name} ---")
        try:
            yield
            self.logger.info(f"--- Completed Sheet: {name} ---")
        except Exception as e:
            self.logger.error(f"--- Failed in Sheet: {name} ---")
            raise e
        finally:
            self.current_sheet = None

    def get_input(self, key: str, default=None):
        return self.io.get_input(key, default)

    def push_data(self, data: dict):
        self.io.push_data(data)
