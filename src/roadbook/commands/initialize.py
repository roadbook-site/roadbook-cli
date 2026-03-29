import os
import re
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from ..core.roadbook import RoadbookManager
from ..core.runtime import RuntimeManager
from ..core.scaffold import ScaffoldManager
from ..utils.output import console, print_error, print_success
from ..core.i18n import t
from . import editor
import argparse

def _generate_id(name: str) -> str:
    """Generate a valid ID from the roadbook name."""
    # Convert to lowercase
    id_str = name.lower()
    # Replace spaces and underscores with hyphens
    id_str = re.sub(r'[\s_]+', '-', id_str)
    # Remove any non-alphanumeric characters except hyphens
    id_str = re.sub(r'[^a-z0-9\-]', '', id_str)
    # Remove duplicate hyphens
    id_str = re.sub(r'-+', '-', id_str)
    # Strip leading/trailing hyphens
    id_str = id_str.strip('-')
    return id_str

def init_book(args):
    """Initialize a new roadbook scaffold."""
    name = args.name
    description = args.description
    entry_url = args.entry_url
    global_scope = getattr(args, 'global_scope', False)
    
    rb_id = _generate_id(name)
    if not rb_id:
        print_error("Invalid roadbook name. Cannot generate a valid ID.")
        return
        
    # Check for duplicates
    existing_books = RoadbookManager.list_roadbooks(global_scope)
    for book in existing_books:
        if book.id == rb_id:
            print_error(f"A roadbook with ID '{rb_id}' already exists at {book.path.parent}.")
            return

    if global_scope:
        from ..core.config import get_books_dir
        work_dir = get_books_dir()
    else:
        # Create directory structure in current workspace
        cwd = Path.cwd()
        work_dir = cwd
        
    book_dir = work_dir / rb_id
    
    try:
        if not work_dir.exists():
            print(f"Initializing directory at {work_dir}")
            work_dir.mkdir(parents=True, exist_ok=True)
            
        # Check if login is required
        requires_login = False
        if hasattr(args, 'login') and args.login:
            if args.login.lower() in ['y', 'yes', 'true']:
                requires_login = True

        # Use centralized scaffold manager
        paths = ScaffoldManager.create_roadbook_scaffold(book_dir, rb_id, name, description, entry_url, requires_login=requires_login)
        with open(paths["roadbook_file"], "r", encoding="utf-8") as f:
            roadbook_content = f.read()
        ScaffoldManager.create_script_scaffold(book_dir, "python", rb_id, name, roadbook_content)
        
        if requires_login:
            console.print("\n[bold yellow]Login Required[/bold yellow]")
            console.print(f"Opening browser for you to log in to: [cyan]{entry_url}[/cyan]")
            console.print("Please complete the login process, and then press Enter here to save the state.")
            
            try:
                from playwright.sync_api import sync_playwright
                from ..core.config import load_user_config
                
                config = load_user_config()
                browser_config = config.get("browser", {})
                exe_path = browser_config.get("executable_path")
                user_data_dir = browser_config.get("user_data_dir")
                
                state_file = paths["config"] / "state.json"
                
                with sync_playwright() as p:
                    launch_args = {"headless": False}
                    if exe_path:
                        launch_args["executable_path"] = exe_path
                    
                    # 为了规避某些网站对自动化工具的检测（如 CDP 协议），
                    # 我们采用纯净的 subprocess 方式启动浏览器，
                    # 避免使用 Playwright 直接 attach，只在需要时启动它。
                    import subprocess
                    import time
                    
                    if exe_path:
                        data_dir_arg = f"--user-data-dir={user_data_dir}" if user_data_dir else f"--user-data-dir={paths['config'] / 'profile'}"
                        cmd = [
                            exe_path, 
                            data_dir_arg,
                            "--no-first-run",
                            "--no-default-browser-check",
                            "--disable-features=Translate",
                            entry_url
                        ]
                        console.print(f"[dim]Launching browser process: {' '.join(cmd)}[/dim]")
                        
                        # 启动独立浏览器进程
                        browser_proc = subprocess.Popen(cmd)
                        
                        # Wait for user input
                        input("Press Enter here after you have successfully logged in...")
                        
                        # 此时用户已经登录完成。
                        # 为了避免 Profile 被锁定，以及防止下次带 CDP 启动时 CDP 不生效，必须先关闭这个浏览器进程
                        console.print("Closing browser to release profile lock...")
                        try:
                            if browser_proc.poll() is None:
                                import sys
                                if sys.platform == "win32":
                                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(browser_proc.pid)], capture_output=True)
                                else:
                                    browser_proc.terminate()
                                    browser_proc.wait(timeout=5)
                        except Exception as e:
                            console.print(f"[dim]Note: Browser termination warning: {e}[/dim]")
                            
                        console.print("Extracting login state...")
                        try:
                            # 尝试以极短时间启动并立刻提取 state
                            extract_args = {"headless": True, "executable_path": exe_path}
                            context = p.chromium.launch_persistent_context(user_data_dir or str(paths['config'] / 'profile'), **extract_args)
                            context.storage_state(path=str(state_file))
                            context.close()
                            console.print(f"[green]✓ Login state saved to:[/green] {state_file}")
                        except Exception as extract_err:
                            console.print(f"[yellow]Warning: Could not extract state immediately (browser might be locked).[/yellow]")
                            console.print(f"Error details: {extract_err}")
                            console.print("If you closed the browser, try running the command again. If it is still open, please close it.")
                            
                    else:
                        # Fallback to Playwright native launch if no custom path
                        if user_data_dir:
                            context = p.chromium.launch_persistent_context(user_data_dir, **launch_args)
                            page = context.pages[0] if context.pages else context.new_page()
                        else:
                            browser = p.chromium.launch(**launch_args)
                            context = browser.new_context()
                            page = context.new_page()
                            
                        # 注入特殊标记的 title 以便后续定位，或者纯粹作为提示
                        page.goto(entry_url)
                        try:
                            page.evaluate("document.title = '[Roadbook Login] ' + document.title;")
                        except Exception:
                            pass
                        
                        # Wait for user input
                        input("Press Enter here after you have successfully logged in...")
                        
                        # Save state
                        context.storage_state(path=str(state_file))
                        console.print(f"[green]✓ Login state saved to:[/green] {state_file}")
                        
                        if user_data_dir:
                            context.close()
                        else:
                            browser.close()
            except Exception as e:
                print_error(f"Failed to handle interactive login: {e}")
                
    except Exception as e:
        print_error(f"Failed to initialize roadbook: {e}")
        return

    print_success(t("init_success", name=name, rb_id=rb_id))
    console.print(t("init_dir", book_dir=book_dir))
    
    # Handle auto-edit
    if args.edit:
        console.print(t("launch_editor"))
        # Construct arguments for editor
        editor_args = argparse.Namespace(
            port=8000, 
            host="127.0.0.1", 
            dir=str(book_dir),
            id=rb_id
        )
        editor.start_editor(editor_args)
        return

    # Constructing AI Agent feedback prompt
    feedback_lines = [
        t("ai_feedback_scaffold_gen", book_dir=book_dir)
    ]
    
    if description:
        feedback_lines.extend([
            t("ai_feedback_mode_ai"),
            t("ai_feedback_next_steps"),
            t("ai_feedback_ai_step1"),
            t("ai_feedback_ai_step2"),
            t("ai_feedback_ai_step3")
        ])
    else:
        feedback_lines.extend([
            t("ai_feedback_mode_manual"),
            t("ai_feedback_next_steps"),
            t("ai_feedback_manual_step1"),
            t("ai_feedback_manual_step2", rb_id=rb_id),
            t("ai_feedback_manual_step3"),
            t("ai_feedback_manual_step4")
        ])
        
    feedback_text = "\n".join(feedback_lines)
    console.print(Panel(feedback_text, title=t("ai_feedback_title"), border_style="yellow"))
