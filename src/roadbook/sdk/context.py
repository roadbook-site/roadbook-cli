# src/roadbook/sdk/context.py
import os
import sys
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any

from playwright.sync_api import sync_playwright, Playwright, BrowserContext, Page

from .io import InputManager, DatasetManager
from .storage import StorageManager
from .logger import get_logger
from .radar import Radar
from .auth import Authenticator

class AgentBreakpointInterrupt(Exception):
    """Raised when execution needs to pause for Agent/Human intervention at a crossroads."""
    pass

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
            import time
            import uuid
            run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
            self.run_dir = self.root_dir / "runtime" / run_id
            self.outputs_dir = self.root_dir / "outputs" / run_id
            
        # Ensure directories exist
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.rb_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. Initialize I/O managers
        self.input_manager = InputManager(self.rb_dir, self.scripts_dir)
        self.dataset_manager = DatasetManager(self.outputs_dir, self.scripts_dir)
        self.storage = StorageManager(self.run_dir, self.outputs_dir)
        
        # 5. 载入统一配置
        self._load_config(cdp_url)

        # 6. Breakpoint & State tracking
        self.state = {}
        self.resume_target_sheet = None
        self.crossroads_file = self.rb_dir / "crossroads.json"
        self._load_resume_state()

        # Playwright internals
        self._playwright: Playwright = None
        self._context: BrowserContext = None
        self.page: Page = None
        self.current_sheet = None

    def _load_resume_state(self):
        """Loads state from a previous crossroads pause if a reply exists."""
        if self.crossroads_file.exists():
            try:
                import json
                with open(self.crossroads_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # We only resume if the agent has provided a reply
                if "reply" in data:
                    self.resume_target_sheet = data.get("sheet_id")
                    self.state = data.get("state", {})
                    self.logger.info(f"Loaded resume state. Fast-forwarding to sheet: {self.resume_target_sheet}")
            except Exception as e:
                self.logger.warning(f"Failed to load crossroads resume state: {e}")

    @property
    def auth(self) -> Authenticator:
        """
        获取鉴权管理器，用于处理多模式登录及状态对比。
        """
        if not hasattr(self, '_auth'):
            self._auth = Authenticator(self)
        return self._auth

    @property
    def radar(self) -> Radar:
        """
        获取当前页面的 Radar 扫描工具。
        可以在路书脚本中通过 rb.radar.scan_all() 等方法调用。
        """
        if not self.page:
            raise ValueError("Page is not initialized yet. Ensure you are running within the RoadbookContext.")
        if not hasattr(self, '_radar') or getattr(self, '_radar').page != self.page:
            self._radar = Radar(self.page)
        return self._radar

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
            self.cdp_url = cdp_override.rstrip('/')
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

    def reconnect(self):
        """Re-establishes the browser connection (useful after suspending for pure-browser login)."""
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
        
        # We need to re-run the connection logic
        self._connect_browser()
        return self

    def _connect_browser(self):
        """Internal method to handle browser connection/launching logic."""
        browser_config = getattr(self, "_cli_config", {}).get("browser", {})
        browser_type_name = browser_config.get("browser_type", "chromium")
        browser_type = getattr(self._playwright, browser_type_name, self._playwright.chromium)
        
        def _resolve_cdp_url(url: str) -> str:
            if url.startswith("http://") or url.startswith("https://"):
                import urllib.request
                import json
                version_url = f"{url.rstrip('/')}/json/version"
                try:
                    with urllib.request.urlopen(version_url, timeout=3) as response:
                        data = json.loads(response.read().decode("utf-8"))
                        if "webSocketDebuggerUrl" in data:
                            return data["webSocketDebuggerUrl"]
                except Exception as e:
                    self.logger.debug(f"Failed to resolve websocket URL from {version_url}: {e}")
            return url
        
        connected = False
        if self.browser_mode == "cdp" or (self.browser_mode == "auto" and self.cdp_url):
            self.logger.info(f"Attempting to connect to CDP at {self.cdp_url}...")
            try:
                connect_url = _resolve_cdp_url(self.cdp_url)
                browser = browser_type.connect_over_cdp(connect_url)
                self._context = browser.contexts[0] if browser.contexts else browser.new_context()
                self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
                connected = True
                self.logger.info("Successfully connected to existing browser via CDP.")
            except Exception as e:
                self.logger.info(f"CDP connection failed: {e}. Attempting to launch local browser and retry CDP...")
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
                            connect_url = _resolve_cdp_url(self.cdp_url)
                            browser = browser_type.connect_over_cdp(connect_url)
                            self._context = browser.contexts[0] if browser.contexts else browser.new_context()
                            self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
                            connected = True
                            self.logger.info("Successfully connected to local browser via CDP.")
                        except Exception as cdp_err:
                            self.logger.error(f"Failed to connect to browser CDP port {port} after launch.")
                            raise cdp_err
                    else:
                        self.logger.warning("Could not find local Chrome/Edge executable.")
                except Exception as ex:
                    self.logger.warning(f"Failed to launch or connect to local browser: {ex}")
        
        if not connected:
            self.logger.warning("Falling back to standalone headless browser.")
            if self.browser_mode == "standalone":
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
                raise RuntimeError("Failed to connect to local browser via CDP.")
            
        default_timeout = getattr(self, "_cli_config", {}).get("browser", {}).get("default_timeout", 30000)
        self._context.set_default_timeout(default_timeout)

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
        self._connect_browser()
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

    def pause_for_manual_action(self, message: str = "Please complete the required action in the browser.", debug: bool = False):
        """
        Pauses the execution to allow a human to perform manual actions (e.g., login, CAPTCHA).
        This is an experimental/debug tool used when you don't know the success selector yet.
        
        If debug=True, it will take a screenshot and DOM snapshot before and after the action,
        saving them to the run directory to help you compare states and write selectors later.
        """
        self.logger.warning("=====================================================")
        self.logger.warning(" HUMAN INTERVENTION REQUIRED (MANUAL PAUSE) ")
        self.logger.warning(message)
        self.logger.warning(" Input 1 and press Enter in the terminal when done...")
        self.logger.warning("=====================================================")
        
        import sys
        if not sys.stdin.isatty():
            self.logger.error("Cannot wait for human action in a non-interactive (non-TTY) environment.")
            raise RuntimeError("Human intervention requested but no TTY is available.")
            
        debug_dir = self.run_dir / "debug_snapshots"
        timestamp = None
        if debug:
            debug_dir.mkdir(parents=True, exist_ok=True)
            import time
            timestamp = int(time.time())
            try:
                self.page.screenshot(path=str(debug_dir / f"before_{timestamp}.png"), full_page=True)
                with open(debug_dir / f"before_{timestamp}.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                self.logger.info(f"Saved 'before' snapshots to {debug_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to take 'before' snapshot: {e}")

        # Wait for terminal input (Enter)
        while True:
            user_input = input("Input 1 and press Enter to continue after you have completed the action: ")
            if user_input.strip() == "1":
                self.logger.info("Manual confirmation received, resuming execution...")
                break
            else:
                print("Invalid input, please input 1 and press Enter.")
                
        if debug and timestamp:
            try:
                self.page.screenshot(path=str(debug_dir / f"after_{timestamp}.png"), full_page=True)
                with open(debug_dir / f"after_{timestamp}.html", "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                self.logger.info(f"Saved 'after' snapshots to {debug_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to take 'after' snapshot: {e}")

    def wait_for_condition(self, success_selector: str, message: str = "Waiting for condition to be met...", require_confirmation: bool = False, timeout: int = 120000):
        """
        Production-ready method to wait for a specific selector to appear, indicating an action was successful.
        
        If require_confirmation=True, it will additionally pause in the terminal for user confirmation 
        *after* the selector is found. This is useful when you have written a selector but aren't 100% sure it's correct.
        """
        self.logger.info(f"Waiting for selector: '{success_selector}' (Timeout: {timeout}ms)")
        if message:
            self.logger.info(message)
            
        try:
            self.page.locator(success_selector).wait_for(state="visible", timeout=timeout)
            self.logger.info(f"Selector '{success_selector}' is now visible.")
        except Exception as e:
            self.logger.error(f"Failed to verify selector '{success_selector}' within {timeout}ms: {e}")
            raise RuntimeError(f"Condition not met or timed out: {e}")
            
        if require_confirmation:
            self.logger.warning("=====================================================")
            self.logger.warning(" CONDITION MET, SECONDARY CONFIRMATION REQUIRED ")
            self.logger.warning(f" The selector '{success_selector}' appeared, but require_confirmation is True.")
            self.logger.warning(" Input 1 and press Enter in the terminal to continue...")
            self.logger.warning("=====================================================")
            import sys
            if not sys.stdin.isatty():
                raise RuntimeError("Secondary confirmation requested but no TTY is available.")
            while True:
                user_input = input("Input 1 and press Enter to confirm: ")
                if user_input.strip() == "1":
                    self.logger.info("Secondary confirmation received, resuming...")
                    break
                else:
                    print("Invalid input, please input 1 and press Enter.")

    def wait_for_human_action(self, success_selector: str = None, message: str = "Please complete the required action (e.g., login, CAPTCHA) in the browser.", timeout: int = 120000, wait_for_user_input: bool = False):
        """
        DEPRECATED: Use `pause_for_manual_action` or `wait_for_condition` instead.
        """
        self.logger.warning("DeprecationWarning: `wait_for_human_action` is deprecated. Use `pause_for_manual_action` or `wait_for_condition` instead.")
        if success_selector and not wait_for_user_input:
            self.wait_for_condition(success_selector, message=message, timeout=timeout, require_confirmation=False)
        elif success_selector and wait_for_user_input:
            self.wait_for_condition(success_selector, message=message, timeout=timeout, require_confirmation=True)
        else:
            self.pause_for_manual_action(message=message, debug=False)

    def should_run(self, sheet_name: str) -> bool:
        """
        Determines whether the current sheet should be executed or skipped.
        If we are resuming from a crossroads, we skip all sheets until we reach the target sheet.
        """
        if self.resume_target_sheet:
            if sheet_name == self.resume_target_sheet:
                self.logger.info(f"Reached resume target sheet: {sheet_name}. Resuming normal execution.")
                self.resume_target_sheet = None  # Clear so subsequent sheets run
                return True
            else:
                self.logger.info(f"Fast-forwarding (Skipping) sheet: {sheet_name}")
                return False
        return True

    @contextmanager
    def sheet(self, name: str):
        self.current_sheet = name
        active = self.should_run(name)
        
        if active:
            self.logger.info(f"--- Entering Sheet: {name} ---")
        try:
            yield active
            if active:
                self.logger.info(f"--- Completed Sheet: {name} ---")
        except AgentBreakpointInterrupt:
            # We don't want to log this as a standard error failure
            raise
        except Exception as e:
            if active:
                self.logger.error(f"--- Failed in Sheet: {name} ---")
            raise e
        finally:
            self.current_sheet = None

    def crossroads(self, question: str, options: list = None) -> Any:
        """
        Pauses execution and hands off to the Agent (or Human) to make a decision.
        It saves the current context (URL, state) and raises AgentBreakpointInterrupt.
        When the script is re-run after a reply is provided, it fast-forwards to here and returns the reply.
        """
        import json
        
        # Check if we are resuming and have a reply
        if self.crossroads_file.exists():
            try:
                with open(self.crossroads_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if data.get("sheet_id") == self.current_sheet and "reply" in data:
                    reply = data["reply"]
                    self.logger.info(f"Received reply from Agent: {reply}")
                    
                    # Navigate back to the saved URL before returning
                    saved_url = data.get("url")
                    if saved_url and self.page and self.page.url != saved_url:
                        self.logger.info(f"Restoring page URL: {saved_url}")
                        self.page.goto(saved_url)
                        try:
                            self.page.wait_for_load_state("networkidle", timeout=10000)
                        except Exception:
                            pass
                    
                    # Clean up the crossroads file so it doesn't trigger again
                    self.crossroads_file.unlink()
                    return reply
            except Exception as e:
                self.logger.warning(f"Error reading reply from crossroads: {e}")

        # If no reply, we need to create the breakpoint
        current_url = self.page.url if self.page else None
        
        # Save a debug screenshot for the agent
        screenshot_path = ""
        if self.page:
            try:
                screenshot_file = self.run_dir / "crossroads_snapshot.png"
                self.page.screenshot(path=str(screenshot_file), full_page=True)
                screenshot_path = str(screenshot_file.absolute())
            except Exception:
                pass

        # Handle Pydantic state dumping if needed
        state_dict = self.state
        if hasattr(self.state, "model_dump"):
            state_dict = self.state.model_dump()
        elif hasattr(self.state, "dict"):
            state_dict = self.state.dict()

        crossroads_data = {
            "status": "waiting_for_agent",
            "sheet_id": self.current_sheet,
            "url": current_url,
            "question": question,
            "options": options or [],
            "state": state_dict,
            "screenshot": screenshot_path,
            "instructions_for_agent": "Please analyze the 'question' and 'screenshot'. Add your answer as a new field 'reply' (e.g., \"reply\": \"your answer\") to this JSON file and save it."
        }

        with open(self.crossroads_file, "w", encoding="utf-8") as f:
            json.dump(crossroads_data, f, indent=2, ensure_ascii=False)
            
        # Ensure browser state is saved immediately
        if self._context and hasattr(self, "state_file"):
            try:
                self._context.storage_state(path=str(self.state_file))
            except Exception:
                pass

        print("\n" + "="*70)
        print(" 🛑 CROSSROADS: AGENT HANDOFF REQUIRED 🛑 ".center(70, "="))
        print("="*70)
        print("Roadbook execution paused because a decision is needed.\n")
        print(f"❓ Question: {question}")
        if options:
            print(f"👉 Options: {options}")
        print("\n[ACTION REQUIRED]")
        print(f"1. Agent: Read the file: {self.crossroads_file}")
        if screenshot_path:
            print(f"2. Agent: Review the screenshot: {screenshot_path}")
        print("3. Agent: Add your answer by inserting a `\"reply\": \"...\"` field into the JSON file.")
        print("4. Resume: Run `roadbook run` again. The script will automatically fast-forward to this exact spot and resume.")
        print("="*70 + "\n")

        raise AgentBreakpointInterrupt(f"Execution paused at Crossroads. Waiting for reply to: {question}")

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
                
                self._sync_input_file(self._input_model)
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

    def _sync_input_file(self, input_model):
        """Syncs the latest validated inputs back to .rb/INPUT.json."""
        import json
        try:
            rb_dir = self.scripts_dir.parent / ".rb"
            if not rb_dir.exists():
                return
                
            input_file = rb_dir / "INPUT.json"
            
            # Get current raw inputs that were used in this run
            raw_inputs = self.input_manager.get_all()
            
            # Use Pydantic to validate, hydrate defaults, and strip extra fields
            try:
                validated_inputs = input_model(**raw_inputs).model_dump(mode='json')
                
                with open(input_file, "w", encoding="utf-8") as f:
                    json.dump(validated_inputs, f, indent=4, ensure_ascii=False)
                self.logger.info("Synced .rb/INPUT.json with latest validated inputs.")
            except Exception as e:
                self.logger.warning(f"Could not sync .rb/INPUT.json (validation failed): {e}")
        except Exception as e:
            self.logger.warning(f"Failed to sync .rb/INPUT.json: {e}")

    def get_output_dir(self) -> Path:
        """Returns the output directory path for the current run."""
        return self.outputs_dir

    def emit_output(self, data: Any, validate: bool = True):
        """Helper to emit structured output data matching TaskOutput."""
        # Log the output path on first emit
        if not hasattr(self, "_has_emitted"):
            self.logger.info(f"Emitting outputs to: {self.dataset_manager.default_dataset_file}")
            self._has_emitted = True

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

        self.dataset_manager.emit_output(data, validate)
