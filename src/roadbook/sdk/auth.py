from enum import Enum
import time
import subprocess
import sys
from typing import Optional, Dict, Any

class AuthMode(Enum):
    LONG_LIVED = 1              # 模式一：无反爬，Token有效长。登录一次即可。
    SESSION_ONLY = 2            # 模式二：无反爬，登录状态保存在session中，每次需重新登录。
    ANTI_BOT_INTERACTIVE = 3    # 模式三：有反爬，CDP连接状态下无法正常登录，需断开CDP让用户手工登录。
    EXTREME_PROTECTION = 4      # 模式四：极端保护，不可用或全手工。

class Authenticator:
    def __init__(self, context):
        """
        :param context: RoadbookContext instance
        """
        self.ctx = context
        self.logger = context.logger
        self.snapshots: Dict[str, Any] = {}

    def ensure_login(self, mode: AuthMode, verify_selector: str, entry_url: str, verify_url_pattern: str = None, login_timeout: int = 120000, anti_bot_strategy: str = "disconnect"):
        """
        确保当前处于登录状态，根据不同的模式采用不同的登录策略。
        注: 如果之前有 state.json (Standalone) 或存在有效的 Profile (CDP)，
        底层在初始化时已自动加载，此时 is_logged_in 就会直接返回 True。
        """
        self.logger.info(f"Checking login status using selector: {verify_selector} or URL pattern: {verify_url_pattern}")
        
        if self.is_logged_in(verify_selector, verify_url_pattern):
            self.logger.info("Already logged in (State/Profile is valid). Skipping auth flow.")
            return True

        self.logger.warning("Not logged in (State expired or missing). Starting authentication flow...")
        
        if mode == AuthMode.LONG_LIVED or mode == AuthMode.SESSION_ONLY:
            # 模式1或2：直接在当前页面进行自动化或交互式登录
            self.ctx.page.goto(entry_url)
            self.ctx.wait_for_human_action(
                success_selector=verify_selector,
                message=f"Please log in manually at {entry_url}",
                timeout=login_timeout
            )
            # 登录完成后，上下文会自动在 exit 时保存 state.json

        elif mode == AuthMode.ANTI_BOT_INTERACTIVE:
            self.logger.warning(f"Using ANTI_BOT_INTERACTIVE mode (Strategy: {anti_bot_strategy}). Suspending CDP session...")
            
            if anti_bot_strategy == "disconnect":
                # 策略A：只断开CDP连接，保留当前浏览器窗口供用户操作
                self._interactive_disconnect_login(entry_url)
            else:
                # 策略B：彻底关闭当前浏览器，用 subprocess 启动纯净进程
                self._interactive_pure_login(entry_url)
            
            # 重新连接浏览器，此时它会使用刚刚更新过的 state/profile
            self.logger.info("Resuming CDP session...")
            self.ctx.reconnect()
            
            # 再次验证
            self.ctx.page.goto(entry_url)
            if not self.is_logged_in(verify_selector, verify_url_pattern):
                raise RuntimeError("Login failed or state was not preserved after interactive login.")
                
        elif mode == AuthMode.EXTREME_PROTECTION:
            raise NotImplementedError("Extreme protection mode requires manual intervention outside of automation.")

        return True

    def is_logged_in(self, verify_selector: str, verify_url_pattern: str = None) -> bool:
        """
        根据给定的 selector 或 URL 判断是否已登录。
        为了提高鲁棒性，如果有 verify_url_pattern，会优先验证 URL。
        """
        if verify_url_pattern:
            import re
            if re.search(verify_url_pattern, self.ctx.page.url):
                return True

        if not verify_selector:
            return False

        try:
            # 增加重试机制和更宽松的状态判断
            locator = self.ctx.page.locator(verify_selector)
            # 等待 DOM 加载，防止 SSR 延迟或骨架屏
            locator.wait_for(state="attached", timeout=5000)
            return locator.is_visible()
        except Exception:
            # 尝试通过 JS evaluate 兜底检测（防止在 Shadow DOM 中）
            try:
                is_exist = self.ctx.page.evaluate(f"() => !!document.querySelector('{verify_selector}')")
                return is_exist
            except Exception:
                return False

    def _interactive_disconnect_login(self, url: str):
        """仅断开 CDP 连接，让用户在当前已打开的浏览器中操作，完成后重连"""
        try:
            self.ctx.page.goto(url)
        except Exception:
            pass
            
        self.logger.info("Disconnecting CDP to avoid detection...")
        if self.ctx._context and self.ctx._context.browser:
            try:
                self.ctx._context.browser.disconnect()
            except Exception as e:
                self.logger.warning(f"Error disconnecting CDP: {e}")
                
        self.logger.warning("=====================================================")
        self.logger.warning(" CDP DISCONNECTED FOR LOGIN ")
        self.logger.warning(f" Please manually log in on the opened browser at {url}")
        self.logger.warning(" Once you are successfully logged in, press Enter here.")
        self.logger.warning("=====================================================")
        
        if not sys.stdin.isatty():
            raise RuntimeError("Interactive login requested but no TTY is available.")
            
        input("Press Enter here after you have successfully logged in...")
        # The reconnect is handled in ensure_login via self.ctx.reconnect()

    def _interactive_pure_login(self, url: str):
        """挂起当前上下文，用 subprocess 启动纯净浏览器供用户登录"""
        exe_path = self.ctx.executable_path
        if not exe_path:
            from roadbook.utils.browser_locator import find_chrome_executable
            exe_path = find_chrome_executable()

        if not exe_path:
            raise RuntimeError("Cannot find Chrome executable for pure-browser login.")

        # 关闭当前的 Playwright/CDP 上下文释放 Profile 锁定
        if self.ctx._context:
            self.ctx._context.close()
        
        # 尝试杀掉可能残留的浏览器进程
        if hasattr(self.ctx, "_local_browser_proc") and self.ctx._local_browser_proc:
            try:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.ctx._local_browser_proc.pid)], capture_output=True)
                else:
                    self.ctx._local_browser_proc.terminate()
            except Exception:
                pass

        user_data_dir = self.ctx.user_data_dir or str(self.ctx.profile_dir)
        cmd = [
            exe_path,
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=Translate",
            url
        ]
        
        self.logger.info(f"Launching clean browser process for anti-bot login...")
        browser_proc = subprocess.Popen(cmd)
        
        self.logger.warning("=====================================================")
        self.logger.warning(" CLEAN BROWSER LAUNCHED FOR LOGIN ")
        self.logger.warning(" Please complete the login process in the newly opened browser.")
        self.logger.warning(" Once you are successfully logged in, press Enter here.")
        self.logger.warning("=====================================================")
        
        if not sys.stdin.isatty():
            self.logger.error("No TTY available. Killing clean browser process...")
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(browser_proc.pid)], capture_output=True)
            else:
                browser_proc.terminate()
            raise RuntimeError("Interactive pure login requested but no TTY is available.")
            
        input("Press Enter here after you have successfully logged in...")
        
        self.logger.info("Closing clean browser to release profile lock...")
        try:
            if browser_proc.poll() is None:
                if sys.platform == "win32":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(browser_proc.pid)], capture_output=True)
                else:
                    browser_proc.terminate()
                    browser_proc.wait(timeout=5)
        except Exception as e:
            self.logger.warning(f"Browser termination warning: {e}")

        # 稍微等一下文件系统释放锁
        time.sleep(2)
        
        # 接下来由上层重新挂载Playwright即可提取或使用state

    # ---------------------------------------------------------
    # DOM 状态对比功能 (助力 Agent 识别登录状态变化)
    # ---------------------------------------------------------
    def _get_snapshot_dir(self):
        snapshot_dir = self.ctx.run_dir / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        return snapshot_dir

    def snapshot_state(self, name: str):
        """使用 Radar 扫描并保存当前页面的交互元素快照（同时持久化到文件系统）"""
        import json
        elements = self.ctx.radar.scan_interactive_elements()
        snapshot_data = {
            "url": self.ctx.page.url,
            "title": self.ctx.page.title(),
            "elements": elements
        }
        self.snapshots[name] = snapshot_data
        
        # 持久化到文件
        try:
            file_path = self._get_snapshot_dir() / f"{name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"State snapshot '{name}' saved with {len(elements)} elements to {file_path.name}.")
        except Exception as e:
            self.logger.warning(f"Failed to persist snapshot '{name}' to disk: {e}")

    def diff_states(self, pre_name: str, post_name: str) -> Dict[str, Any]:
        """对比两个状态快照，找出新增和消失的元素。如果内存中不存在则尝试从文件系统加载。"""
        import json
        
        def _load_snapshot(name):
            if name in self.snapshots:
                return self.snapshots[name]
            
            # 尝试从文件系统加载
            file_path = self._get_snapshot_dir() / f"{name}.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.snapshots[name] = data
                        return data
                except Exception as e:
                    self.logger.warning(f"Failed to load snapshot '{name}' from disk: {e}")
            return None

        pre_data = _load_snapshot(pre_name)
        post_data = _load_snapshot(post_name)

        if not pre_data or not post_data:
            raise ValueError(f"Snapshots '{pre_name}' and '{post_name}' must exist in memory or disk.")
            
        pre_elements = {f"{e['tag']}:{e.get('text', '')}": e for e in pre_data["elements"]}
        post_elements = {f"{e['tag']}:{e.get('text', '')}": e for e in post_data["elements"]}
        
        pre_keys = set(pre_elements.keys())
        post_keys = set(post_elements.keys())
        
        disappeared_keys = pre_keys - post_keys
        appeared_keys = post_keys - pre_keys
        
        return {
            "disappeared": [pre_elements[k] for k in disappeared_keys],
            "appeared": [post_elements[k] for k in appeared_keys]
        }
