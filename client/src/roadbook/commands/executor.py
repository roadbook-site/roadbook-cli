import time
import json
import argparse
import subprocess
import sys
import shutil
import importlib.util
import ast
from typing import Dict, Any, Optional

from ..core.roadbook import RoadbookManager
from ..core.runtime import RuntimeManager
from ..utils.output import print_info, print_error

def check_environment() -> bool:
    """
    Checks if the environment has necessary tools.
    Returns True if all good, False otherwise (and prints guidance).
    """
    all_good = True
    
    # Check Python dependencies
    required_packages = ['playwright']
    for pkg in required_packages:
        if importlib.util.find_spec(pkg) is None:
            print_error(f"[Diagnostic] Missing python package: '{pkg}'.")
            print_info(f"  -> Action: Run 'pip install {pkg}' to fix it.")
            all_good = False
            
    # Check Node.js (optional but recommended for agent-browser)
    if not shutil.which("node"):
        print_error("[Diagnostic] Node.js is not found in PATH.")
        print_info("  -> Action: Install Node.js from https://nodejs.org/")
        # We don't fail hard here, as python script might not need node if using pure playwright
    
    return all_good

def parse_inputs(inputs_str: str) -> Dict[str, Any]:
    """
    Parses inputs string into a dictionary.
    Tries JSON first, then ast.literal_eval for python-style dicts (useful in PowerShell).
    """
    if not inputs_str or inputs_str == "{}":
        return {}
    
    try:
        return json.loads(inputs_str)
    except json.JSONDecodeError:
        # Try relaxed parsing (e.g. single quotes for python dict)
        try:
            val = ast.literal_eval(inputs_str)
            if isinstance(val, dict):
                return val
        except (ValueError, SyntaxError):
            pass
        # Re-raise original error
        raise

def diagnose_error(e: Exception, mode: str = "script") -> str:
    """
    Analyzes an error and returns a helpful guidance message.
    """
    err_str = str(e)
    
    if "ModuleNotFoundError" in err_str:
        return "It seems a Python dependency is missing. Check your imports."
    
    if "playwright" in err_str and "browsers" in err_str:
        return "Playwright browsers might be missing. Run 'playwright install' to fix."
        
    if "ElementNotFound" in err_str or "Timeout" in err_str:
        return "The script failed to find an element. The page structure might have changed."
        
    return "No specific advice available. Check the logs for details."

def run_book(args):
    """
    Runs a roadbook.
    Logic:
    1. If script exists, run it (mocked for now).
    2. If no script, warn user and switch to interactive session (open).
    """
    rb_id = args.id
    inputs_str = args.inputs or "{}"
    
    if not check_environment():
        print_info("[Guidance] Environment check failed. Please fix issues above before running.")
    
    try:
        inputs = parse_inputs(inputs_str)
    except Exception:
        print_error("Invalid JSON for --inputs.")
        print_info(f"[Debug] Received: {inputs_str}")
        print_info("[Action] Pass a valid JSON string.")
        if sys.platform == "win32":
            print_info("  [Windows PowerShell Hint]")
            print_info("  Your quotes might have been stripped by PowerShell.")
            print_info("  Try wrapping the JSON in double quotes and using single quotes for keys/values:")
            print_info("    --inputs \"{'count': 5}\"")
            print_info("  Or escape inner double quotes:")
            print_info("    --inputs '{\\\"count\\\": 5}'")
        else:
            print_info("  Example: --inputs '{\"keyword\":\"iphone\"}'")
        return

    book = RoadbookManager.get_roadbook(rb_id)
    if not book:
        print_error(f"Roadbook '{rb_id}' not found.")
        print_info("[Action] Use 'roadbook list' to view installed roadbooks.")
        return

    book_dir = book.path.parent
    script_path = RuntimeManager.find_script(rb_id, book_dir=book_dir)
    
    if script_path:
        print_info("[Mode] Script execution mode.")
        print_info(f"[*] Found script: {script_path}")
        print_info("[*] Executing script...")
        
        try:
            if script_path.suffix == ".py":
                subprocess.run([sys.executable, str(script_path)], check=True)
            elif script_path.suffix == ".js":
                subprocess.run(["node", str(script_path)], check=True)
            else:
                print_error(f"Unsupported script type: {script_path.suffix}")
                return
            
            print_info("[Success] Script executed successfully.")
            
            run_id = RuntimeManager.create_run(rb_id, book_dir=book_dir)
            RuntimeManager.log_run_result(rb_id, run_id, "success", {"mode": "script"}, book_dir=book_dir)
            print_info(f"[Runtime] Run ID: {run_id}")
            print_info("[Action] Use 'roadbook logs inspect <run_id>' to inspect this run.")
            
        except subprocess.CalledProcessError as e:
            print_error(f"Script execution failed with exit code {e.returncode}")
            diagnosis = diagnose_error(e)
            print_info(f"[Guidance] {diagnosis}")
            
            run_id = RuntimeManager.create_run(rb_id, book_dir=book_dir)
            RuntimeManager.log_run_result(rb_id, run_id, "failed", {"mode": "script", "error": str(e)}, book_dir=book_dir)
            print_info(f"[Runtime] Run ID: {run_id}")
            print_info("[Action] Use 'roadbook logs inspect <run_id>' to inspect failure details.")
        except Exception as e:
            print_error(f"Script execution error: {e}")
            print_info(f"[Guidance] {diagnose_error(e)}")
    else:
        print_info(f"[!] No automation script found for '{rb_id}'.")
        
        scripts_dir = RuntimeManager.get_scripts_dir(rb_id, book_dir=book_dir)
        print_info(f"[Guidance] If you have a script, save it to: {scripts_dir / 'script.py'}")
        
        print_info("[*] Switching to interactive guidance mode...")
        start_session(args)

def start_session(args):
    """Starts a new interactive session."""
    rb_id = args.id
    inputs_str = args.inputs or "{}"
    try:
        inputs = parse_inputs(inputs_str)
    except Exception:
        print_error("Invalid JSON for --inputs.")
        print_info(f"[Debug] Received: {inputs_str}")
        print_info("[Action] Pass a valid JSON string.")
        if sys.platform == "win32":
            print_info("  [Windows PowerShell Hint]")
            print_info("  Your quotes might have been stripped by PowerShell.")
            print_info("  Try wrapping the JSON in double quotes and using single quotes for keys/values:")
            print_info("    --inputs \"{'count': 5}\"")
            print_info("  Or escape inner double quotes:")
            print_info("    --inputs '{\\\"count\\\": 5}'")
        else:
            print_info("  Example: --inputs '{\"keyword\":\"iphone\"}'")
        return

    book = RoadbookManager.get_roadbook(rb_id)
    if not book:
        print_error(f"Roadbook '{rb_id}' not found.")
        print_info("[Action] Use 'roadbook list' to view installed roadbooks.")
        return

    book_dir = book.path.parent
    run_id = RuntimeManager.create_run(rb_id, book_dir=book_dir)
    
    RuntimeManager.log_run_result(rb_id, run_id, "running", {"current_step": 0}, book_dir=book_dir)
    
    RuntimeManager.save_active_session(rb_id, run_id, current_step=0, roadbook_dir=book_dir)
    
    print_info("== Roadbook Session Started ==")
    print_info(f"ID: {rb_id}")
    print_info(f"Session: {run_id}")
    print_info("[Mode] Semantic Guide Mode is active.")
    
    if not book.sheets:
        print_error("No valid Sheets found in this Roadbook.")
        return

    print_info("\n" + "="*20 + " ROADBOOK CONTENT " + "="*20)
    for i, sheet in enumerate(book.sheets):
        print_info(f"\n--- Sheet {i+1}/{len(book.sheets)}: {sheet.title} ---")
        print_info(sheet.content)
    print_info("\n" + "="*58)

    print_info("\n[Agent Action] The entire roadbook has been provided above.")
    print_info("[Agent Action] Please read through all sheets and execute the task step by step using your browser tools.")
    print_info("[Agent Action] You do NOT need to call 'roadbook next' repeatedly.")
    print_info("[Agent Action] Once you have completed all tasks, you can simply finish your turn.")
