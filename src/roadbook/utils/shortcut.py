import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    try:
        from ctypes import create_unicode_buffer, windll
    except Exception:
        create_unicode_buffer = None
        windll = None

def create_desktop_shortcut(target_path: str, shortcut_name: str, arguments: str = "", icon_path: str = None) -> bool:
    """
    Creates a desktop shortcut for the given executable.
    Returns True if successful, False otherwise.
    """
    try:
        desktop_dir = _resolve_desktop_dir()
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
        vbs_path = os.path.join(tempfile.gettempdir(), "create_shortcut.vbs")

        # Ensure strings are properly quoted for VBScript
        def q(s: Optional[str]) -> str:
            if not s:
                return ""
            return s.replace('"', '""')

        vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{q(shortcut_path)}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{q(target)}"
oLink.Arguments = "{q(args)}"
oLink.Description = "Roadbook Dedicated Browser"
"""
        if icon:
            vbs_content += f'\noLink.IconLocation = "{icon}"'
            
        vbs_content += "\noLink.Save"
        
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_content)

        # Run cscript and check return code
        try:
            proc = subprocess.run(["cscript", "//nologo", vbs_path], check=False, capture_output=True, text=True)
            if proc.returncode != 0:
                # print stderr for diagnostics (caller may be CLI; keep brief)
                try:
                    print(f"create_desktop_shortcut cscript error: {proc.stderr.strip()}")
                except Exception:
                    pass
                # keep the vbs for debugging
                return False
        finally:
            try:
                if os.path.exists(vbs_path):
                    os.remove(vbs_path)
            except Exception:
                pass
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


def _resolve_desktop_dir() -> str:
    """Resolve the user's desktop path in a cross-platform way, using Windows API when available."""
    home = Path.home()
    # Default candidates
    candidates = [home / "Desktop", home / "桌面"]

    if sys.platform == "win32" and windll and create_unicode_buffer:
        try:
            buf = create_unicode_buffer(260)
            # CSIDL_DESKTOPDIRECTORY = 0x10
            windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buf)
            p = Path(buf.value)
            if p.exists():
                return str(p)
        except Exception:
            pass

    for c in candidates:
        if c.exists():
            return str(c)

    # Fallback to home if desktop not found
    return str(home)
