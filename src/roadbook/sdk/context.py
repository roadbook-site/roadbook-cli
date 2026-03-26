# src/roadbook/sdk/context.py
import os
import sys
from pathlib import Path
from contextlib import contextmanager

from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page

from .io import IOManager
from .storage import Storage
from .logger import get_logger

class RoadbookContext:
    def __init__(self, rb_id: str = None, root_dir: str = None, run_dir: str = None, outputs_dir: str = None, headless: bool = None, cdp_url: str = None, site_overrides: dict = None):
        self.logger = get_logger()
        self.rb_id = rb_id
        self.site_overrides = site_overrides or {}
        
        # 1. 自动推导项目根目录 (基于 rb_id, env 或是向上查找 .rb)
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            self.root_dir = self._find_project_root()
        
        # 2. 核心路径定义
        self.rb_dir = self.root_dir / ".rb"
        
        # 如果退回到了全局大本营 (~/.roadbook)，配置和 profile 在 .core 中
        if self.root_dir.name == ".roadbook":
            self.rb_dir = self.root_dir / ".core"
            
        self.profile_dir = self.rb_dir / "profile"
        
        # 3. 运行环境与输出隔离
        env_run_dir = os.environ.get("ROADBOOK_RUN_DIR")
        env_outputs_dir = os.environ.get("ROADBOOK_OUTPUTS_DIR")
        
        if run_dir:
            self.run_dir = Path(run_dir)
            self.outputs_dir = Path(outputs_dir) if outputs_dir else Path(run_dir).parent.parent / "outputs" / Path(run_dir).name
        elif env_run_dir:
            self.run_dir = Path(env_run_dir)
            self.outputs_dir = Path(env_outputs_dir) if env_outputs_dir else Path(env_run_dir).parent.parent / "outputs" / Path(env_run_dir).name
        else:
            self.run_dir = self.root_dir / "runtime" / "local_run"
            self.outputs_dir = self.root_dir / "outputs" / "local_run"
            
        # Ensure directories exist
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.rb_dir.mkdir(parents=True, exist_ok=True)
        
        self.io = IOManager(self.outputs_dir)
        self.storage = Storage(self.run_dir, self.outputs_dir)
        
        # 4. 载入统一配置
        self._load_config(headless, cdp_url)

        # Playwright internals
        self._playwright: Playwright = None
        self._context: BrowserContext = None
        self.page: Page = None
        self.current_sheet = None

    def _find_project_root(self) -> Path:
        """根据 rb_id 或环境变量定位路书项目根目录"""
        # 1. 如果传入了 rb_id，利用管理器查找
        if self.rb_id:
            try:
                from roadbook.core.roadbook import RoadbookManager
                book = RoadbookManager.get_roadbook(self.rb_id, global_scope=False)
                if not book:
                    book = RoadbookManager.get_roadbook(self.rb_id, global_scope=True)
                
                if book:
                    return book.path.parent
            except ImportError:
                pass
                
        # 2. 如果之前 executor 通过环境变量设置了 RUN_DIR
        env_run_dir = os.environ.get("ROADBOOK_RUN_DIR")
        if env_run_dir:
            return Path(env_run_dir).parent.parent

        # 3. 如果没传参数，退回查找 .rb 模式
        current_dir = Path.cwd()
        for parent in [current_dir, *current_dir.parents]:
            if (parent / ".rb").exists() or (parent / "roadbook.md").exists():
                return parent

        # 4. 彻底找不到，使用全局大本营
        try:
            from roadbook.core.config import get_roadbook_dir
            return get_roadbook_dir()
        except ImportError:
            return Path.home() / ".roadbook"

    def _load_config(self, headless_override=None, cdp_override=None):
        try:
            from roadbook.core.config import load_config
            self._cli_config = load_config(self.root_dir)
        except Exception:
            self._cli_config = {}
        
        scaffold_config = self._cli_config.get("scaffold", {})
        
        # Merge site_overrides
        # headless logic: site_overrides (e.g. force_headful -> headless=False) > user param > config
        user_headless = headless_override if headless_override is not None else scaffold_config.get("headless", False)
        if "force_headful" in self.site_overrides and self.site_overrides["force_headful"]:
            self.headless = False
        elif "headless" in self.site_overrides:
            self.headless = self.site_overrides["headless"]
        else:
            self.headless = user_headless
            
        self.browser_mode = scaffold_config.get("browser_mode", "auto")
        self.stealth_mode = self.site_overrides.get("stealth_mode", False)
        
        if cdp_override:
            self.cdp_url = cdp_override
        else:
            cdp_port = scaffold_config.get("cdp_port")
            self.cdp_url = f"http://localhost:{cdp_port}" if cdp_port else None
            
        self.viewport = self.site_overrides.get("viewport", scaffold_config.get("viewport", None))
        if isinstance(self.viewport, str): # e.g. "1920x1080"
            parts = self.viewport.split('x')
            if len(parts) == 2:
                self.viewport = {"width": int(parts[0]), "height": int(parts[1])}
                
        self.global_delay = self.site_overrides.get("global_delay", scaffold_config.get("global_delay", 0))
            
        self.state_file = self.rb_dir / "state.json"

    def __enter__(self):
        self.logger.info("Starting Roadbook Context...")
        
        try:
             # Patch for asyncio inside sync
             import asyncio
             if asyncio.get_running_loop():
                 try:
                     import nest_asyncio
                     nest_asyncio.apply()
                 except ImportError:
                     pass
        except Exception:
             pass 

        self._playwright = sync_playwright().start()
        
        scaffold_config = getattr(self, "_cli_config", {}).get("scaffold", {})
        browser_type_name = scaffold_config.get("browser_type", "chromium")
        browser_type = getattr(self._playwright, browser_type_name, self._playwright.chromium)
        
        connected = False
        if self.browser_mode == "cdp" or (self.browser_mode == "auto" and self.cdp_url):
            self.logger.info(f"Attempting to connect to CDP at {self.cdp_url}...")
            try:
                browser = browser_type.connect_over_cdp(self.cdp_url)
                self._context = browser.contexts[0] if browser.contexts else browser.new_context()
                self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
                connected = True
                self.logger.info("Successfully connected to existing browser via CDP.")
            except Exception as e:
                self.logger.info("CDP connection failed, falling back to standalone browser.")
        
        if not connected:
            self.logger.info(f"Launching ephemeral context (headless={self.headless}, stealth={self.stealth_mode})...")
            launch_args = {"headless": self.headless}
            
            # Stealth mode args (basic implementation)
            if self.stealth_mode:
                launch_args["args"] = ["--disable-blink-features=AutomationControlled"]
                
            self._browser_instance = browser_type.launch(**launch_args)
            
            context_args = {"no_viewport": False}
            if getattr(self, "viewport", None) and isinstance(self.viewport, dict):
                context_args["viewport"] = self.viewport
                
            if self.state_file.exists():
                context_args["storage_state"] = str(self.state_file)
                self.logger.info(f"Loaded previous storage state from {self.state_file.name}.")
                
            self._context = self._browser_instance.new_context(**context_args)
            
            # Add stealth script if needed
            if self.stealth_mode:
                self._context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
            self.page = self._context.new_page()
            
        default_timeout = scaffold_config.get("default_timeout", 30000)
        self._context.set_default_timeout(default_timeout)
            
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Error encountered: {exc_val}")
            if self.page:
                try:
                    self.storage.save_screenshot("error_state", self.page)
                except Exception:
                    pass
                    
        # Auto-save state if we own the context
        if self._context and hasattr(self, "state_file"):
            try:
                self._context.storage_state(path=str(self.state_file))
                self.logger.info(f"Automatically saved storage state to {self.state_file.name}")
            except Exception as e:
                self.logger.warning(f"Failed to auto-save storage state: {e}")
                
        self.logger.info("Closing Roadbook Context...")
        if self._context:
            self._context.close()
        if hasattr(self, "_browser_instance") and self._browser_instance:
            self._browser_instance.close()
        if self._playwright:
            self._playwright.stop()

    def human_intervene_for_login(self, success_selector: str = None, message: str = "Please complete the login or verification in the browser.", timeout: int = 600000, wait_for_user_input: bool = False):
        """
        Pauses the execution to allow a human to log in or solve a CAPTCHA.
        """
        self.logger.warning("=====================================================")
        self.logger.warning(" HUMAN INTERVENTION REQUIRED ")
        self.logger.warning(message)
        if success_selector:
            self.logger.warning(f" Waiting for selector: '{success_selector}' to be visible.")
        if wait_for_user_input or not success_selector:
             self.logger.warning(" Press Enter in the terminal when done...")
        self.logger.warning("=====================================================")
        
        try:
            if wait_for_user_input or not success_selector:
                # Wait for terminal input (Enter)
                input("Press Enter to continue after you have logged in...")
                self.logger.info("Manual confirmation received, resuming execution...")
            elif success_selector:
                # Wait for the user to login and the target selector to appear
                self.page.locator(success_selector).wait_for(state="visible", timeout=timeout)
                self.logger.info("Login successful, resuming execution...")
        except Exception as e:
            self.logger.error(f"Failed to verify login within {timeout}ms timeout: {e}")
            raise RuntimeError(f"Login intervention failed or timed out: {e}")

    @contextmanager
    def sheet(self, name: str):
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
