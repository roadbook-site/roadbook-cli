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
    print_info("[Mode] Interactive guidance is active.")
    print_info("[Status] Waiting for step execution.")
    print_info("[Action] Use 'roadbook next' to get one step at a time.")
    print_info("[Action] Execute each step with your browser tool (Playwright / agent-browser / other agent tool).")
    print_info("[Loop] Repeat: next -> execute -> check (optional) -> next.")

def next_step(args):
    session = RuntimeManager.load_active_session()
    if not session:
        print_error("No active session found.")
        print_info("[Action] Start one with 'roadbook open <id>' or 'roadbook run <id>'.")
        return
        
    rb_id = session['roadbook_id']
    roadbook_dir = session.get('roadbook_dir')
    run_id = session['run_id']
    current_step = session['current_step']
    
    book = RoadbookManager.get_roadbook(rb_id)
    if not book:
        print_error(f"Roadbook '{rb_id}' not found.")
        return
        
    sheets = book.sheets
    
    if not sheets:
        print_error("No valid Sheets found in this Roadbook.")
        print_info("[Action] Ensure your roadbook.md has '## Title' sections for each sheet.")
        return
    
    if current_step >= len(sheets):
        print_info("== All sheets completed! ==")
        RuntimeManager.log_run_result(rb_id, run_id, "completed", {"total_sheets": len(sheets)}, book_dir=roadbook_dir)
        RuntimeManager.clear_active_session()
        print_info("[Status] Autonomous Explorer session closed.")
        print_info("[Action] Use 'roadbook logs last' to review the latest run.")
        print_info("[Action] If the execution was successful, consider saving the generated script.")
        return
        
    sheet = sheets[current_step]
    print_info(f"== Sheet {current_step + 1}/{len(sheets)}: {sheet.title} ==")
    
    # Output the raw content of the sheet for the agent to read
    print_info(sheet.content)
    
    print_info("-" * 40)
    print_info("[Agent Action] Please act autonomously based on the context above.")
    print_info("[Agent Action] Use browser tools (Playwright/agent-browser) to achieve the goal of this Sheet.")
    print_info("[Agent Action] When you believe this Sheet is completed, run 'roadbook next' to proceed to the next Sheet.")
    print_info("[Agent Action] If you need to verify the state, you can run 'roadbook check'.")
    
    RuntimeManager.save_active_session(rb_id, run_id, current_step + 1, roadbook_dir=roadbook_dir)

def check_step(args):
    session = RuntimeManager.load_active_session()
    if not session:
        print_error("No active session found.")
        print_info("[Action] Start one with 'roadbook open <id>' or 'roadbook run <id>'.")
        return
        
    rb_id = session['roadbook_id']
    current_step = session['current_step']
    
    book = RoadbookManager.get_roadbook(rb_id)
    if not book:
        print_error(f"Roadbook '{rb_id}' not found.")
        return
        
    sheets = book.sheets
    
    print_info("== Status Check ==")
    print_info(f"Roadbook ID: {rb_id}")
    print_info(f"Run ID: {session['run_id']}")
    
    if not sheets:
        print_info("Status: Active, but no sheets found in roadbook.")
        return
        
    # session['current_step'] is actually the *next* sheet to be executed because we incremented it in next_step
    # So the sheet currently being worked on is current_step - 1
    working_sheet_idx = current_step - 1
    
    if working_sheet_idx < 0:
        print_info("Status: Session started, waiting for first 'roadbook next'.")
    elif working_sheet_idx >= len(sheets):
        print_info("Status: All sheets have been handed out.")
    else:
        sheet = sheets[working_sheet_idx]
        print_info(f"Current Sheet: {working_sheet_idx + 1}/{len(sheets)}: {sheet.title}")
        print_info("Status: Autonomous Explorer is currently executing this sheet.")
        
        # Extract and show Assertions if they exist in the sheet content
        assertions = []
        in_assertions = False
        for line in sheet.content.split('\n'):
            if 'Assertions' in line or '断言' in line:
                in_assertions = True
                continue
            if in_assertions:
                if line.startswith('##') or line.startswith('---'):
                    break
                if line.strip().startswith('- [ ]') or line.strip().startswith('*'):
                    assertions.append(line.strip())
                    
        if assertions:
            print_info("\n[Checkpoint] Expected Assertions for this Sheet:")
            for assertion in assertions:
                print_info(f"  {assertion}")
            print_info("\n[Agent Action] Verify the above conditions before calling 'roadbook next'.")
        else:
            print_info("\n[Agent Action] No explicit assertions defined. Ensure the general goal of this sheet is met.")
            
    print_info("\n[Action] Continue with 'roadbook next' to get the next instruction.")
