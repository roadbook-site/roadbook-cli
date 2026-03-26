import os
import sys
from pathlib import Path

def create_desktop_shortcut(target_path: str, shortcut_name: str, arguments: str = "", icon_path: str = None) -> bool:
    """
    Creates a desktop shortcut for the given executable.
    Returns True if successful, False otherwise.
    """
    try:
        desktop_dir = Path.home() / "Desktop"
        if not desktop_dir.exists():
            desktop_dir = Path.home() / "桌面" # For Chinese Windows
            
        system = sys.platform
        
        if system == "win32":
            return _create_windows_shortcut(str(desktop_dir), shortcut_name, target_path, arguments, icon_path)
        elif system == "darwin":
            return _create_macos_shortcut(str(desktop_dir), shortcut_name, target_path, arguments)
        else:
            return _create_linux_shortcut(str(desktop_dir), shortcut_name, target_path, arguments, icon_path)
            
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False

def _create_windows_shortcut(desktop_dir: str, name: str, target: str, args: str, icon: str) -> bool:
    try:
        # We use a temporary VBScript to create the shortcut to avoid requiring pywin32 dependency
        shortcut_path = os.path.join(desktop_dir, f"{name}.lnk")
        vbs_path = os.path.join(os.environ.get("TEMP", desktop_dir), "create_shortcut.vbs")
        
        vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target}"
oLink.Arguments = "{args}"
oLink.Description = "Roadbook Dedicated Browser"
"""
        if icon:
            vbs_content += f'\noLink.IconLocation = "{icon}"'
            
        vbs_content += "\noLink.Save"
        
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)
            
        os.system(f'cscript //nologo "{vbs_path}"')
        os.remove(vbs_path)
        return True
    except Exception:
        return False

def _create_macos_shortcut(desktop_dir: str, name: str, target: str, args: str) -> bool:
    try:
        # On macOS, we create a small shell script (.command file)
        shortcut_path = os.path.join(desktop_dir, f"{name}.command")
        script_content = f"""#!/bin/bash
"{target}" {args}
"""
        with open(shortcut_path, "w", encoding="utf-8") as f:
            f.write(script_content)
            
        # Make it executable
        os.chmod(shortcut_path, 0o755)
        return True
    except Exception:
        return False

def _create_linux_shortcut(desktop_dir: str, name: str, target: str, args: str, icon: str) -> bool:
    try:
        # Create a .desktop file
        shortcut_path = os.path.join(desktop_dir, f"{name}.desktop")
        desktop_content = f"""[Desktop Entry]
Version=1.0
Name={name}
Comment=Roadbook Dedicated Browser
Exec="{target}" {args}
Terminal=false
Type=Application
"""
        if icon:
            desktop_content += f"Icon={icon}\n"
            
        with open(shortcut_path, "w", encoding="utf-8") as f:
            f.write(desktop_content)
            
        os.chmod(shortcut_path, 0o755)
        return True
    except Exception:
        return False
