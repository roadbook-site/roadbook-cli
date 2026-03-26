import os
import sys
import shutil
import site
from rich.console import Console
from rich.panel import Panel

def check_path_warning(print_warning=True):
    """Check if 'roadbook' is in PATH. If not, print a helpful warning."""
    cmd_name = "roadbook.exe" if os.name == "nt" else "roadbook"
    
    # If the command is found in PATH, everything is fine.
    if shutil.which(cmd_name) is not None:
        return True, "Found in PATH"

    # Try to guess where it was installed
    paths = []
    
    # 1. Try sysconfig (most accurate for user install)
    import sysconfig
    try:
        user_scripts = sysconfig.get_path('scripts', f'{os.name}_user')
        if user_scripts:
            paths.append(user_scripts)
    except Exception:
        pass
        
    # 2. Try sysconfig global
    try:
        global_scripts = sysconfig.get_path('scripts')
        if global_scripts:
            paths.append(global_scripts)
    except Exception:
        pass

    # 3. Fallbacks
    if site.USER_BASE:
        paths.append(os.path.join(site.USER_BASE, "Scripts" if os.name == "nt" else "bin"))
    paths.append(os.path.join(sys.prefix, "Scripts" if os.name == "nt" else "bin"))
    
    expected_dir = paths[0] if paths else "your Python Scripts directory"
    for p in paths:
        if os.path.exists(os.path.join(p, cmd_name)):
            expected_dir = p
            break
            
    if print_warning:
        warning_msg = (
            f"[yellow]Warning: The '{cmd_name}' command is not in your system PATH.[/yellow]\n"
            "This usually happens when installing via pip in a user directory or sandbox.\n\n"
            "[bold]Solutions:[/bold]\n"
            f"1. Add [cyan]{expected_dir}[/cyan] to your system PATH environment variable.\n"
            "2. Or continue using [cyan]python -m roadbook[/cyan] instead of [cyan]roadbook[/cyan]."
        )
        
        console = Console()
        console.print(Panel(warning_msg, title="PATH Warning", border_style="yellow"))
        
    return False, expected_dir
