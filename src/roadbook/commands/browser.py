import os
import sys
import time
import socket
import subprocess
import psutil
import urllib.request
import urllib.error
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm, Prompt, IntPrompt
from rich.panel import Panel
from rich.table import Table

from ..core.config import load_user_config, save_user_config, CORE_DIR
from ..utils.browser_locator import find_all_browsers
from ..utils.shortcut import create_desktop_shortcut

console = Console()

def browser_main(args):
    """Fallback handler for `roadbook browser` without subcommand."""
    # Since argparse now handles subcommands, this might not be strictly needed,
    # but provides backward compatibility to route to init.
    if hasattr(args, "subcommand") and args.subcommand:
        pass
    else:
        console.print("[yellow]No subcommand provided. Running `browser init` by default...[/yellow]")
        browser_init(args)

def browser_init(args):
    console.print(Panel.fit("[bold cyan]Roadbook Dedicated Browser Setup[/bold cyan]\n"
                            "This wizard will help you configure a dedicated browser for Roadbook.\n"
                            "It allows Roadbook to share the same browser session with you seamlessly."))
    
    config = load_user_config()
    browser_config = config.get("browser", {})
    
    exe_path = browser_config.get("executable_path")
    
    if exe_path and os.path.exists(exe_path):
        console.print(f"\n[green]✓ Current Browser Executable:[/green] {exe_path}")
        reconfigure = Confirm.ask("Browser is already configured. Do you want to reconfigure it?", default=False)
        if not reconfigure:
            exe_path = None # Signal to keep current
    else:
        reconfigure = True
        
    if reconfigure:
        console.print("\n[bold yellow]Step 1: Locating Browser[/bold yellow]")
        detected_browsers = find_all_browsers()
        
        if detected_browsers:
            console.print("Detected the following supported browsers:")
            for i, browser in enumerate(detected_browsers, 1):
                console.print(f"  [bold cyan]{i}.[/bold cyan] {browser['name']} [dim]({browser['path']})[/dim]")
            console.print(f"  [bold cyan]0.[/bold cyan] Custom path (enter manually)")
            
            choice = IntPrompt.ask(
                "Select a browser to use", 
                choices=[str(i) for i in range(len(detected_browsers) + 1)],
                default=1
            )
            
            if choice == 0:
                exe_path = Prompt.ask("Please enter the full path to your Chrome/Edge/360 executable")
            else:
                exe_path = detected_browsers[choice - 1]["path"]
        else:
            exe_path = Prompt.ask("Could not auto-detect browser. Please enter the full path to your Chrome/Edge executable")
            
        if not os.path.exists(exe_path):
            console.print(f"[bold red]Error:[/bold red] The path '{exe_path}' does not exist.")
            return
            
        browser_config["executable_path"] = exe_path
    else:
        exe_path = browser_config.get("executable_path")

    # 2. Configure CDP Port
    console.print("\n[bold yellow]Step 2: Remote Debugging Port[/bold yellow]")
    current_port = browser_config.get("cdp_port", 9222)
    port_str = Prompt.ask("Enter CDP port (press Enter to keep default)", default=str(current_port))
    try:
        browser_config["cdp_port"] = int(port_str)
    except ValueError:
        console.print("[yellow]Invalid port, using default 9222.[/yellow]")
        browser_config["cdp_port"] = 9222

    # 3. Configure User Data Directory
    console.print("\n[bold yellow]Step 3: Dedicated Profile Directory[/bold yellow]")
    default_profile = str(CORE_DIR / "profile")
    current_profile = browser_config.get("user_data_dir") or default_profile
    
    console.print("Using a dedicated profile prevents mixing Roadbook data with your personal browsing data.")
    profile_dir = Prompt.ask("Enter profile directory path", default=current_profile)
    
    # Ensure it's absolute
    profile_dir = str(Path(profile_dir).resolve())
    browser_config["user_data_dir"] = profile_dir
    
    # Create the directory if it doesn't exist
    os.makedirs(profile_dir, exist_ok=True)
    
    # Ensure basic launch args are present
    if "launch_args" not in browser_config:
        browser_config["launch_args"] = ["--no-first-run", "--no-default-browser-check"]

    # Save Configuration
    config["browser"] = browser_config
    save_user_config(config)
    console.print("\n[green]✓ Browser configuration saved successfully![/green]")

    # 4. Create Desktop Shortcut
    console.print("\n[bold yellow]Step 4: Desktop Shortcut[/bold yellow]")
    console.print("This shortcut acts as a bridge between you and the AI agent, allowing you to share the same login state.")
    console.print("It is highly recommended to create this shortcut to easily open the shared browser.")
    create_sc = Confirm.ask("Would you like to create a desktop shortcut for this dedicated browser?", default=True)
    
    if create_sc:
        shortcut_name = "Roadbook Browser"
        args_str = f'--remote-debugging-port={browser_config["cdp_port"]} --user-data-dir="{browser_config["user_data_dir"]}" --no-first-run --no-default-browser-check'
        
        success = create_desktop_shortcut(exe_path, shortcut_name, args_str)
        if success:
            console.print(f"[bold green]✓ Shortcut '{shortcut_name}' created on your desktop![/bold green]")
            console.print("You can now double-click it to start the browser before running Roadbook scripts.")
        else:
            console.print("[bold red]Failed to create shortcut. You can also start the browser manually with [italic]roadbook browser open[/italic] or running:[/bold red]")
            console.print(f"\"{exe_path}\" {args_str}")

    console.print("\n[bold cyan]Setup Complete![/bold cyan]")
    console.print("Your Roadbook environment is now optimized for the CDP Browser Takeover mode.")

def _get_browser_info():
    """Helper to get browser config."""
    config = load_user_config()
    b_config = config.get("browser", {})
    exe_path = b_config.get("executable_path")
        
    cdp_port = b_config.get("cdp_port", 9222)
    user_data_dir = b_config.get("user_data_dir", str(CORE_DIR / "profile"))
    return exe_path, cdp_port, user_data_dir

def _check_port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

def _check_cdp_connectivity(port: int) -> bool:
    try:
        url = f"http://127.0.0.1:{port}/json/version"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                return True
    except Exception:
        pass
    return False

def _find_process_by_port(port: int):
    """Find the process ID occupying a specific port."""
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            try:
                proc = psutil.Process(conn.pid)
                return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
    return None

def browser_open(args):
    """Open the browser."""
    exe_path, cdp_port, user_data_dir = _get_browser_info()
    
    if not exe_path or not os.path.exists(exe_path):
        console.print("[bold red]Error:[/bold red] Could not find browser executable. Please run `roadbook browser init` first.")
        return
        
    console.print(f"[bold cyan]Opening Roadbook Browser...[/bold cyan]")
    console.print(f"Executable: [green]{exe_path}[/green]")
    console.print(f"CDP Port: [green]{cdp_port}[/green]")
    console.print(f"Profile: [green]{user_data_dir}[/green]")
    
    # Check if port is already open
    if _check_port_open(cdp_port):
        if _check_cdp_connectivity(cdp_port):
            console.print("[green]✓ Browser is already running and CDP is accessible.[/green]")
        else:
            console.print(f"[bold yellow]Warning:[/bold yellow] Port {cdp_port} is open, but CDP is not responding.")
            proc = _find_process_by_port(cdp_port)
            if proc:
                console.print(f"Process occupying port: {proc.name()} (PID: {proc.pid})")
            console.print("You may need to run `roadbook browser kill` to release the port.")
        return
        
    cmd = [
        exe_path,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check"
    ]
    
    try:
        # Launch detached
        if sys.platform == 'win32':
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            subprocess.Popen(cmd, start_new_session=True)
            
        console.print("[yellow]Waiting for browser to start...[/yellow]")
        # Wait a bit and check CDP
        for _ in range(10):
            time.sleep(0.5)
            if _check_cdp_connectivity(cdp_port):
                console.print("[bold green]✓ Browser launched successfully![/bold green]")
                return
                
        console.print("[bold red]Browser launched, but CDP could not be verified in time.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Failed to launch browser: {e}[/bold red]")

def browser_close(args):
    """Close the browser gracefully via CDP if possible."""
    _, cdp_port, _ = _get_browser_info()
    
    if not _check_port_open(cdp_port):
        console.print(f"Port {cdp_port} is not open. Browser is likely not running.")
        return
        
    if _check_cdp_connectivity(cdp_port):
        console.print("[cyan]Attempting to close browser via CDP...[/cyan]")
        try:
            url = f"http://127.0.0.1:{cdp_port}/json/version"
            # Since CDP /json/close doesn't close the whole browser directly in Chrome easily via HTTP endpoint,
            # we can try to close all pages, or use an API. But gracefully shutting down a browser started with
            # remote-debugging-port often requires finding the process and sending SIGTERM.
            pass
        except Exception:
            pass
            
    # Fallback to finding the process and terminating it
    proc = _find_process_by_port(cdp_port)
    if proc:
        try:
            console.print(f"Found process {proc.name()} (PID: {proc.pid}) occupying port {cdp_port}. Terminating...")
            proc.terminate()
            proc.wait(timeout=3)
            console.print("[bold green]✓ Browser closed successfully.[/bold green]")
        except psutil.TimeoutExpired:
            console.print("[yellow]Process did not terminate in time. Use `roadbook browser kill` to force close.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Failed to close browser: {e}[/bold red]")
    else:
        console.print("[yellow]Could not identify the process occupying the port to close it gracefully.[/yellow]")

def browser_kill(args):
    """Force release the port by killing the process."""
    _, cdp_port, _ = _get_browser_info()
    
    proc = _find_process_by_port(cdp_port)
    if proc:
        try:
            console.print(f"Force killing process {proc.name()} (PID: {proc.pid}) on port {cdp_port}...")
            proc.kill()
            proc.wait(timeout=3)
            console.print("[bold green]✓ Port released successfully.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Failed to kill process: {e}[/bold red]")
    else:
        if _check_port_open(cdp_port):
            console.print(f"[yellow]Port {cdp_port} is open, but could not identify the process. You may need to run as Administrator/root.[/yellow]")
        else:
            console.print(f"[green]Port {cdp_port} is already free.[/green]")

def browser_diagnose(args):
    """Diagnose browser setup."""
    exe_path, cdp_port, user_data_dir = _get_browser_info()
    
    console.print(Panel.fit("[bold cyan]Browser Diagnostics[/bold cyan]"))
    
    table = Table(show_header=False, box=None)
    
    # 1. Configured Executable
    exe_status = "[green]OK[/green]" if exe_path and os.path.exists(exe_path) else "[red]MISSING[/red]"
    table.add_row("Executable Path:", exe_path or "Not Configured", exe_status)
    
    # 2. User Data Directory
    dir_status = "[green]OK[/green]" if user_data_dir and os.path.exists(user_data_dir) else "[yellow]MISSING (will be created)[/yellow]"
    table.add_row("User Data Dir:", user_data_dir or "Not Configured", dir_status)
    
    # 3. Port Status
    port_open = _check_port_open(cdp_port)
    port_status = "[green]OPEN[/green]" if port_open else "[gray]CLOSED[/gray]"
    table.add_row(f"CDP Port ({cdp_port}):", "Is the port listening?", port_status)
    
    # 4. CDP Connectivity
    cdp_conn = False
    cdp_status = "[gray]N/A[/gray]"
    if port_open:
        cdp_conn = _check_cdp_connectivity(cdp_port)
        cdp_status = "[green]CONNECTED[/green]" if cdp_conn else "[red]NO RESPONSE[/red]"
    table.add_row("CDP Connectivity:", "Can we communicate with the browser?", cdp_status)
    
    console.print(table)
    console.print()
    
    if not exe_path or not os.path.exists(exe_path):
        console.print("-> [bold yellow]Action required:[/bold yellow] Run `roadbook browser init` to configure the browser.")
    elif port_open and not cdp_conn:
        proc = _find_process_by_port(cdp_port)
        if proc:
            console.print(f"-> [bold red]Conflict detected:[/bold red] Port {cdp_port} is occupied by {proc.name()} (PID: {proc.pid}) which is not responding to CDP.")
            console.print("   Run `roadbook browser kill` to force release the port.")
        else:
            console.print(f"-> [bold red]Conflict detected:[/bold red] Port {cdp_port} is occupied by an unknown process.")
    elif not port_open:
        console.print("-> Browser is currently not running. Use `roadbook browser open` to launch it.")
    else:
        console.print("-> [green]Everything looks good! The browser is ready for automation.[/green]")
