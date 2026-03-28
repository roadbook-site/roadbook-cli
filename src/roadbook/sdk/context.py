# src/roadbook/sdk/context.py
import os
import sys
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page

from .io import InputManager, DatasetManager
from .storage import KeyValueStore
from .logger import get_logger

class RoadbookContext:
    def __init__(self, rb_id: str = None, root_dir: str = None, run_dir: str = None, outputs_dir: str = None, cdp_url: str = None, site_overrides: dict = None):
        self.logger = get_logger()
        self.rb_id = rb_id
        self.site_overrides = site_overrides or {}
        
        # 1. 自动推导项目根目录 (基于 rb_id, env 或是向上查找 .rb)
        if root_dir:
            self.root_dir = Path(root_dir)
        else:
            self.root_dir = self._find_project_root()
            
        self.scripts_dir = self.root_dir / "scripts"
        
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
        
        # 4. Initialize I/O managers
        self.input_manager = InputManager(self.rb_dir, self.scripts_dir)
        self.dataset_manager = DatasetManager(self.outputs_dir, self.scripts_dir)
        self.kv = KeyValueStore(self.run_dir, self.outputs_dir)
        
        # 5. 载入统一配置
        self._load_config(cdp_url)

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

    def _load_config(self, cdp_override=None):
        try:
            from roadbook.core.config import load_config
            self._cli_config = load_config(self.root_dir)
        except Exception:
            self._cli_config = {}
        
        # Merge browser config
        browser_config = self._cli_config.get("browser", {})
        
        self.browser_mode = browser_config.get("mode", "cdp")
        self.executable_path = browser_config.get("executable_path")
        self.user_data_dir = browser_config.get("user_data_dir")
        self.launch_args = browser_config.get("launch_args", ["--no-first-run", "--no-default-browser-check"])
        
        if cdp_override:
            self.cdp_url = cdp_override
        else:
            cdp_port = browser_config.get("cdp_port", 9222)
            self.cdp_url = f"http://localhost:{cdp_port}" if cdp_port else None
            
        self.viewport = self.site_overrides.get("viewport", browser_config.get("viewport", None))
        if isinstance(self.viewport, str): # e.g. "1920x1080"
            parts = self.viewport.split('x')
            if len(parts) == 2:
                self.viewport = {"width": int(parts[0]), "height": int(parts[1])}
                
        self.global_delay = self.site_overrides.get("global_delay", browser_config.get("global_delay", 0))
            
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
        
        browser_config = getattr(self, "_cli_config", {}).get("browser", {})
        browser_type_name = browser_config.get("browser_type", "chromium")
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
                self.logger.info(f"CDP connection failed. Attempting to launch local browser and retry CDP...")
                try:
                    import subprocess
                    import time
                    import urllib.parse
                    from roadbook.utils.browser_locator import find_chrome_executable
                    
                    # Try to get executable from config, fallback to auto-detect
                    exe_path = self.executable_path or find_chrome_executable()
                    
                    if exe_path:
                        parsed_url = urllib.parse.urlparse(self.cdp_url)
                        port = parsed_url.port or 9222
                        
                        # Use configured user_data_dir or default to profile_dir
                        data_dir = self.user_data_dir or self.profile_dir
                        
                        cmd = [
                            exe_path,
                            f"--remote-debugging-port={port}",
                            f"--user-data-dir={data_dir}"
                        ]
                        
                        # Add configured launch args
                        if hasattr(self, "launch_args") and isinstance(self.launch_args, list):
                            cmd.extend(self.launch_args)
                        
                        self.logger.info(f"Launching local browser: {exe_path}")
                        self._local_browser_proc = subprocess.Popen(cmd)
                        
                        # Wait for the browser to start and bind to the port
                        time.sleep(3.0)
                        
                        # Retry CDP connection
                        self.logger.info(f"Retrying CDP connection to {self.cdp_url}...")
                        try:
                            browser = browser_type.connect_over_cdp(self.cdp_url)
                            self._context = browser.contexts[0] if browser.contexts else browser.new_context()
                            self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
                            connected = True
                            self.logger.info("Successfully connected to local browser via CDP.")
                        except Exception as cdp_err:
                            self.logger.error(f"Failed to connect to browser CDP port {port} after launch.")
                            self.logger.error("Hint: The port might be occupied, or the browser failed to start.")
                            self.logger.error(f"Try running: `netstat -ano | findstr :{port}` (Windows) or `lsof -i :{port}` (Mac/Linux) to check for port conflicts.")
                            raise cdp_err
                    else:
                        self.logger.warning("Could not find local Chrome/Edge executable.")
                        self.logger.warning("Hint: Run `roadbook browser` to configure your dedicated browser path.")
                except Exception as ex:
                    self.logger.warning(f"Failed to launch or connect to local browser: {ex}")
        
        if not connected:
            self.logger.warning("CDP connection and local launch failed. Falling back to standalone headless browser.")
            self.logger.warning("Hint: Run `roadbook browser` to configure your dedicated browser.")
            if self.browser_mode == "standalone":
                self.logger.info(f"Launching ephemeral standalone context...")
                launch_args = {"headless": False}
                
                self._browser_instance = browser_type.launch(**launch_args)
                
                context_args = {"no_viewport": False}
                if getattr(self, "viewport", None) and isinstance(self.viewport, dict):
                    context_args["viewport"] = self.viewport
                    
                if self.state_file.exists():
                    context_args["storage_state"] = str(self.state_file)
                    self.logger.info(f"Loaded previous storage state from {self.state_file.name}.")
                    
                self._context = self._browser_instance.new_context(**context_args)
                self.page = self._context.new_page()
            else:
                self.logger.error("Failed to connect to local browser and standalone mode is not enabled.")
                raise RuntimeError("Failed to connect to local browser via CDP.")
            
        default_timeout = getattr(self, "_cli_config", {}).get("browser", {}).get("default_timeout", 30000)
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
                
        # Auto-export schemas if models are bound
        if getattr(self, "_input_model", None) or getattr(self, "_output_model", None):
            self.export_schemas()
                
        self.logger.info("Closing Roadbook Context...")
        if self._context:
            self._context.close()
        if hasattr(self, "_browser_instance") and self._browser_instance:
            self._browser_instance.close()
        if self._playwright:
            self._playwright.stop()

    def wait_for_human_action(self, success_selector: str = None, message: str = "Please complete the required action (e.g., login, CAPTCHA) in the browser.", timeout: int = 600000, wait_for_user_input: bool = False):
        """
        Pauses the execution to allow a human to perform actions like login, solving a CAPTCHA, or passing bot detection.
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
                input("Press Enter to continue after you have completed the action...")
                self.logger.info("Manual confirmation received, resuming execution...")
            elif success_selector:
                # Wait for the user to complete action and the target selector to appear
                self.page.locator(success_selector).wait_for(state="visible", timeout=timeout)
                self.logger.info("Action successful, resuming execution...")
        except Exception as e:
            self.logger.error(f"Failed to verify action within {timeout}ms timeout: {e}")
            raise RuntimeError(f"Human intervention failed or timed out: {e}")

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

    def get_input(self, key: str, default: Any = None) -> Any:
        """Helper to get input from InputManager."""
        return self.input_manager.get(key, default)

    def get_inputs(self) -> Dict[str, Any]:
        """Helper to get all inputs from InputManager."""
        return self.input_manager.get_all()

    def bind_schemas(self, input_model=None, output_model=None):
        """Bind Pydantic models for Input and Output to act as SSOT (Single Source of Truth)."""
        self._input_model = input_model
        self._output_model = output_model
        return self

    def export_schemas(self):
        """Export bound Pydantic models to JSON schema files."""
        import json
        if not self.scripts_dir.exists():
            return
            
        if getattr(self, "_input_model", None):
            try:
                schema = self._input_model.model_json_schema()
                with open(self.scripts_dir / "input_schema.json", "w", encoding="utf-8") as f:
                    json.dump(schema, f, indent=4, ensure_ascii=False)
                self.logger.info("Exported input_schema.json from Pydantic model.")
            except Exception as e:
                self.logger.warning(f"Failed to export input schema: {e}")
                
        if getattr(self, "_output_model", None):
            try:
                schema = self._output_model.model_json_schema()
                with open(self.scripts_dir / "output_schema.json", "w", encoding="utf-8") as f:
                    json.dump(schema, f, indent=4, ensure_ascii=False)
                self.logger.info("Exported output_schema.json from Pydantic model.")
            except Exception as e:
                self.logger.warning(f"Failed to export output schema: {e}")

    def push_data(self, data: Any, validate: bool = True):
        """Helper to push structured data via DatasetManager."""
        # Validate against bound Pydantic model if available
        output_model = getattr(self, "_output_model", None)
        if validate and output_model:
            try:
                if hasattr(data, "model_dump"):
                    # It's already a Pydantic instance, we assume it's valid
                    data = data.model_dump()
                else:
                    # Validate dict by instantiating the model
                    data = output_model(**data).model_dump()
            except Exception as e:
                self.logger.error(f"Data validation failed against bound output_model: {e}")
                raise
        
        # If it's still a Pydantic model (validate=False case)
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        self.dataset_manager.push_data(data, validate)
