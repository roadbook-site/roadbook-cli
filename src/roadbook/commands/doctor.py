import sys
import shutil
import platform
import socket
import importlib.util
import subprocess
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..core.config import load_config

console = Console()

def check_python():
    """Check Python version."""
    version = sys.version_info
    is_ok = version.major == 3 and version.minor >= 8
    return is_ok, f"{version.major}.{version.minor}.{version.micro}"

def check_package(name):
    """Check if a Python package is installed."""
    spec = importlib.util.find_spec(name)
    if spec:
        try:
            from importlib.metadata import version
            ver = version(name)
            return True, ver
        except:
            pass
        
        try:
            mod = importlib.import_module(name)
            ver = getattr(mod, "__version__", "unknown")
            return True, ver
        except:
            return True, "installed"
    return False, "missing"

def check_command(cmd):
    """Check if a command is available in PATH."""
    path = shutil.which(cmd)
    return path is not None, path or "missing"

def check_cdp_port(host="localhost", port=9222):
    """Check if Chrome DevTools Protocol port is open."""
    try:
        # Try a quick socket connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return True, f"Port {port} Open"
        else:
            return False, f"Port {port} Closed"
    except Exception as e:
        return False, f"Error: {e}"

def check_network(url):
    """Check connectivity to a URL."""
    try:
        resp = requests.get(url, timeout=3)
        return True, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, "Unreachable"

def run_doctor(args):
    """Run diagnostics."""
    config = load_config()
    
    # Extract config
    # 1. CDP Port: Priority to 'cdp_port' then 'browser.cdp_port' then 9222
    try:
        cdp_port = int(config.get("cdp_port") or config.get("browser", {}).get("cdp_port", 9222))
    except ValueError:
        cdp_port = 9222
    
    # 2. Language: Default to Python
    target_lang = "python"

    console.print(Panel("Roadbook Doctor: Environment Diagnostics", style="bold blue"))
    print(f"Target Language: {target_lang}")
    print(f"Configured CDP Port: {cdp_port}")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    # 1. System Info
    py_ok, py_ver = check_python()
    table.add_row("Python", "[green]PASS[/green]" if py_ok else "[red]FAIL[/red]", f"v{py_ver} (>=3.8)")
    
    # Check Roadbook PATH
    from ..utils.env import check_path_warning
    cmd_name = "roadbook.exe" if sys.platform == "win32" else "roadbook"
    path_ok, path_detail = check_path_warning(print_warning=False)
    table.add_row(f"Roadbook PATH ({cmd_name})", "[green]PASS[/green]" if path_ok else "[yellow]WARN[/yellow]", "Found in PATH" if path_ok else f"Missing. Expecting in {path_detail}")

    # 2. Dependencies
    pw_ok, pw_ver = check_package("playwright")
    table.add_row("Playwright Pkg", "[green]PASS[/green]" if pw_ok else "[red]FAIL[/red]", f"v{pw_ver}")
    
    # 3. Node.js
    node_ok, node_path = check_command("node")
    node_status = "[green]PASS[/green]"
    if not node_ok:
        if target_lang in ["javascript", "typescript", "js", "ts"]:
             node_status = "[red]FAIL[/red]"
        else:
             node_status = "[yellow]WARN[/yellow]" # Optional for Python
    table.add_row("Node.js", node_status, node_path)

    # 4. Browsers (Playwright)
    browser_status = "[gray]UNKNOWN[/gray]"
    browser_detail = "Skipped"
    
    # Check explicitly configured path first
    configured_exe = config.get("browser", {}).get("executable_path")
    if configured_exe and os.path.exists(configured_exe):
        browser_status = "[green]PASS[/green]"
        browser_detail = f"Configured path found: {configured_exe}"
    elif configured_exe:
         browser_status = "[red]FAIL[/red]"
         browser_detail = f"Configured path not found: {configured_exe}"
    elif pw_ok:
        try:
            # Check if browsers are installed by checking executables via CLI
            # 'playwright install --dry-run' outputs needed browsers
            # We just want to know if user can run it.
            # Let's try to find if we can locate the browser executable path without launching
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                # executable_path is a method on BrowserType
                from roadbook.utils.browser_locator import find_chrome_executable
                path = find_chrome_executable()
                
                if path:
                    browser_status = "[green]PASS[/green]"
                    browser_detail = f"Chromium found"
                else:
                    browser_status = "[yellow]WARN[/yellow]"
                    browser_detail = "Chromium not found"
        except Exception as e:
            browser_status = "[red]FAIL[/red]"
            browser_detail = f"Error: {str(e)}"
    table.add_row("Browser (Local)", browser_status, browser_detail)

    # 5. CDP (Remote Debugging)
    cdp_ok, cdp_msg = check_cdp_port(port=cdp_port)
    cdp_status = "[green]ACTIVE[/green]" if cdp_ok else "[yellow]INACTIVE[/yellow]"
    table.add_row(f"Chrome Remote (CDP:{cdp_port})", cdp_status, cdp_msg)

    # 6. Network (GitHub check removed as requested)
    # net_gh, msg_gh = check_network("https://github.com")
    # table.add_row("Network (GitHub)", "[green]OK[/green]" if net_gh else "[red]FAIL[/red]", msg_gh)

    console.print(table)
    
    # Summary & Advice
    console.print("\n[bold]Diagnostic Summary:[/bold]")
    
    issues = []
    if not py_ok:
        issues.append("[red]Python version is too old. Please upgrade to Python 3.8+.[/red]")
    
    if not pw_ok:
        issues.append("[red]Playwright is not installed.[/red] Run: `pip install playwright`")
    elif browser_status == "[yellow]WARN[/yellow]" or browser_status == "[red]FAIL[/red]":
        issues.append("[yellow]Playwright browsers might be missing.[/yellow] Run: `playwright install`")

    if not cdp_ok:
        cmd_prefix = "roadbook" if path_ok else "python -m roadbook"
        issues.append(f"[dim]Remote Debugging is inactive (Port {cdp_port} closed).[/dim]")
        issues.append("  -> To launch a dedicated browser with remote debugging enabled:")
        issues.append(f"     Run: `{cmd_prefix} browser open`")
        issues.append("  -> Otherwise, Roadbook will launch a temporary instance automatically.")
    
    if node_status == "[red]FAIL[/red]":
        issues.append("[red]Node.js is missing but required for JavaScript/TypeScript roadbooks.[/red]")

    if not path_ok:
        issues.append(f"[yellow]The '{cmd_name}' command is not in your system PATH.[/yellow]")
        issues.append(f"  -> Please add [cyan]{path_detail}[/cyan] to your PATH, or use `python -m roadbook`.")

    if not issues:
        console.print("[green]Everything looks good![/green]")
    else:
        for issue in issues:
            console.print(f"- {issue}")
            
    console.print("\n[dim]Note: Diagnostics are based on your current configuration.[/dim]")
    console.print("[dim]Use `roadbook config list` to view or `roadbook config set <key> <value>` to change settings.[/dim]")
            
    console.print("")
