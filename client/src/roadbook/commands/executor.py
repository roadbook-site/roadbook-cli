import os
import time
import json
import argparse
import subprocess
import sys
import shutil
import importlib.util
import ast
from pathlib import Path
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
            
    # Check Node.js (optional but recommended for JS/TS scripts)
    if not shutil.which("node"):
        print_info("[Note] Node.js is not found. Required if you want to run JavaScript/TypeScript roadbooks.")
    
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

def get_inputs(args) -> Optional[Dict[str, Any]]:
    inputs = {}
    
    # 1. Load from file if provided
    if getattr(args, 'inputs_file', None):
        try:
            with open(args.inputs_file, 'r', encoding='utf-8') as f:
                file_inputs = json.load(f)
                if isinstance(file_inputs, dict):
                    inputs.update(file_inputs)
                else:
                    print_error(f"Invalid JSON in file (must be object): {args.inputs_file}")
                    return None
        except Exception as e:
            print_error(f"Failed to load inputs from file: {args.inputs_file}")
            print_info(f"[Detail] {e}")
            return None

    # 2. Merge/Override with CLI inputs string
    inputs_str = getattr(args, 'inputs', None)
    if inputs_str:
        try:
            cli_inputs = parse_inputs(inputs_str)
            inputs.update(cli_inputs)
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
                print_info("  Or use --inputs-file <path> to avoid quoting issues entirely.")
            else:
                print_info("  Example: --inputs '{\"keyword\":\"iphone\"}'")
            return None
            
    return inputs

def run_book(args):
    """
    Runs a roadbook.
    Logic:
    1. If script exists, run it (mocked for now).
    2. 如果没有脚本，则警告用户并切换到语义引导模式 (open).
    """
    rb_id = args.id
    
    if not check_environment():
        print_info("[Guidance] Environment check failed. Please fix issues above before running.")
    
    inputs = get_inputs(args)
    if inputs is None:
        return

    book = RoadbookManager.get_roadbook(rb_id)
    if not book:
        print_error(f"Roadbook '{rb_id}' not found.")
        print_info("[Action] Use 'roadbook list' to view installed roadbooks.")
        return

    book_dir = book.path.parent
    
    # Check if we have a workspace copy
    cwd = Path.cwd()
    workspace_roadbook_dir = cwd / ".roadbook" / rb_id
    if workspace_roadbook_dir.exists():
        book_dir = workspace_roadbook_dir
        
    script_path = RuntimeManager.find_script(rb_id, book_dir=book_dir)
    
    if script_path:
        print_info("[Mode] Script execution mode.")
        print_info(f"[*] Found script: {script_path}")
        
        # Create Run ID first so script can use it
        run_id = RuntimeManager.create_run(rb_id, book_dir=book_dir)
        run_dir = RuntimeManager.get_runs_dir(rb_id, book_dir) / run_id
        
        # Pass Run ID via environment variables
        env = os.environ.copy()
        env["ROADBOOK_RUN_ID"] = run_id
        env["ROADBOOK_RUN_DIR"] = str(run_dir)
        
        print_info(f"[Runtime] Run ID: {run_id}")
        print_info(f"[*] Executing script...")
        
        try:
            if script_path.suffix == ".py":
                subprocess.run([sys.executable, str(script_path)], check=True, env=env)
            elif script_path.suffix == ".js":
                if not shutil.which("node"):
                    print_error("Node.js is not found in PATH but is required for .js scripts.")
                    return
                subprocess.run(["node", str(script_path)], check=True, env=env)
            elif script_path.suffix == ".ts":
                # Check for ts-node or other typescript runner
                if shutil.which("ts-node"):
                    subprocess.run(["ts-node", str(script_path)], check=True, env=env)
                elif shutil.which("npx"):
                    subprocess.run(["npx", "ts-node", str(script_path)], check=True, env=env)
                else:
                    print_error("TypeScript runtime not found. Please install ts-node (npm install -g ts-node) or ensure npx is available.")
                    return
            else:
                print_error(f"Unsupported script type: {script_path.suffix}")
                return
            
            print_info("[Success] Script executed successfully.")
            
            # Try to capture outputs
            outputs = {}
            outputs_file = run_dir / "artifacts" / "outputs.json"
            if outputs_file.exists():
                try:
                    with open(outputs_file, "r", encoding="utf-8") as f:
                        outputs = json.load(f)
                except Exception:
                    pass

            RuntimeManager.log_run_result(rb_id, run_id, "success", {"mode": "script", "outputs": outputs}, book_dir=book_dir)
            print_info("[Action] Use 'roadbook logs inspect <run_id>' to inspect this run.")
            
        except subprocess.CalledProcessError as e:
            print_error(f"Script execution failed with exit code {e.returncode}")
            diagnosis = diagnose_error(e)
            print_info(f"[Guidance] {diagnosis}")
            
            RuntimeManager.log_run_result(rb_id, run_id, "failed", {"mode": "script", "error": str(e)}, book_dir=book_dir)
            print_info("[Action] Use 'roadbook logs inspect <run_id>' to inspect failure details.")
        except Exception as e:
            print_error(f"Script execution error: {e}")
            print_info(f"[Guidance] {diagnose_error(e)}")
    else:
        print_info(f"[!] No automation script found for '{rb_id}'.")
        
        cwd = Path.cwd()
        # New structure guidance
        workspace_roadbook_dir = cwd / ".roadbook" / rb_id
        workspace_script_dir = workspace_roadbook_dir / "scripts"
        runtime_dir = workspace_roadbook_dir / "runtime"
        
        print_info(f"[Action Required] Please generate an automation script to save tokens and enable reusability.")
        print_info(f"  -> Save your script to: {workspace_script_dir / 'script.py'}")
        print_info(f"  -> Save execution artifacts (downloads, screenshots) to: {workspace_roadbook_dir / 'output_...'}")
        
        print_info("[*] Switching to Semantic Guide Mode to help you build the script...")
        start_session(args)

def start_session(args):
    """Starts a new semantic guide mode session."""
    rb_id = args.id
    inputs = get_inputs(args)
    if inputs is None:
        return

    book = RoadbookManager.get_roadbook(rb_id)
    if not book:
        print_error(f"Roadbook '{rb_id}' not found.")
        print_info("[Action] Use 'roadbook list' to view installed roadbooks.")
        return

    # User Requirement: Copy roadbook to workspace .roadbook/<id>
    cwd = Path.cwd()
    workspace_roadbook_dir = cwd / ".roadbook" / rb_id
    
    if not workspace_roadbook_dir.exists():
        print_info(f"[Setup] Initializing roadbook workspace: {workspace_roadbook_dir}")
        try:
            shutil.copytree(book.path.parent, workspace_roadbook_dir, dirs_exist_ok=True)
            print_info(f"[Setup] Copied roadbook to workspace.")
        except Exception as e:
            print_error(f"Failed to copy roadbook to workspace: {e}")
            return

    # Use the workspace copy as the book_dir
    book_dir = workspace_roadbook_dir
    
    run_id = RuntimeManager.create_run(rb_id, book_dir=book_dir)
    
    # Check if script exists, if not, scaffold in workspace
    script_path = RuntimeManager.find_script(rb_id, book_dir=book_dir)
    if not script_path:
        # New structure: .roadbook/<id>/scripts/script.py
        scripts_dir = book_dir / "scripts"
        script_file = scripts_dir / "script.py"
        
        if not script_file.exists():
            try:
                scripts_dir.mkdir(parents=True, exist_ok=True)
                runtime_dir = book_dir / "runtime"
                runtime_dir.mkdir(parents=True, exist_ok=True)
                
                # Timestamped output directory logic
                timestamp_str = time.strftime('%Y_%m_%d_%H_%M')
                
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(f"""# Roadbook Automation Script for {rb_id}
# This script was auto-generated by 'roadbook open'.
# Location: {script_file}

import sys
import json
import os
import time
from pathlib import Path
# from playwright.sync_api import sync_playwright

# Runtime artifacts (downloads, screenshots) should be saved to a timestamped output directory
RUNTIME_DIR = Path(__file__).parent.parent / "runtime"
# Try to get session ID from environment (passed by CLI)
SESSION_ID = os.environ.get("ROADBOOK_RUN_ID")
if SESSION_ID:
    OUTPUT_DIR = RUNTIME_DIR / "runs" / SESSION_ID / "artifacts"
else:
    # Fallback for manual runs
    # Save to the root of the roadbook directory (parent of runtime)
    OUTPUT_DIR = RUNTIME_DIR.parent / f"output_{time.strftime('%Y_%m_%d_%H_%M')}"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run(inputs):
    print(f"Running with inputs: {{inputs}}")
    print(f"Artifacts will be saved to: {{OUTPUT_DIR}}")
    
    # Initialize structured outputs
    outputs = {}

    # TODO: Implement your automation logic here
    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=False)
    #     page = browser.new_page()
    #     page.goto("...")
    #     
    #     # Example: Save a screenshot
    #     # page.screenshot(path=OUTPUT_DIR / "screenshot.png")
    #
    #     # Example: Set output data
    #     # outputs["title"] = page.title()
    #
    #     browser.close()

    # Save structured outputs to outputs.json
    outputs_file = OUTPUT_DIR / "outputs.json"
    with open(outputs_file, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2, ensure_ascii=False)
    print(f"Structured outputs saved to: {{outputs_file}}")

if __name__ == "__main__":
    inputs = {{}}
    if len(sys.argv) > 1:
        try:
            inputs = json.loads(sys.argv[1])
        except:
            pass
    run(inputs)
""")
                print_info(f"[Scaffold] Created workspace script: {script_file}")
                print_info(f"[Action] Edit this script to implement automation for '{rb_id}'.")
                print_info(f"[Action] Outputs will be saved to: {runtime_dir}/runs/<session_id>/artifacts")
            except Exception as e:
                print_error(f"Failed to create scaffold script: {e}")
    
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
    print_info("[Agent Action] Once you have completed all tasks, you can simply finish your turn.")
