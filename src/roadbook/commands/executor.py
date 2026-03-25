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
from ..core.scaffold import ScaffoldManager
from ..core.parser import RoadbookParser
from ..utils.output import print_info, print_error
from .. import __version__ as SCAFFOLD_VERSION

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
    2. If there is no script, warn the user and switch to semantic guidance mode (open).
    """
    rb_id = args.id
    global_scope = getattr(args, 'global_scope', False)

    if not check_environment():
        print_info("[Guidance] Environment check failed. Please fix issues above before running.")
    
    inputs = get_inputs(args)
    if inputs is None:
        return

    book = RoadbookManager.get_roadbook(rb_id, global_scope)
    if not book:
        scope_str = "global" if global_scope else "local"
        print_error(f"Roadbook '{rb_id}' not found in {scope_str} scope.")
        print_info(f"[Action] Use 'roadbook list{ ' -g' if global_scope else ''}' to view installed roadbooks.")
        return

    book_dir = book.path.parent
    
    # Check if we have a workspace copy
    cwd = Path.cwd()
    workspace_roadbook_dir = cwd / rb_id
    if workspace_roadbook_dir.exists():
        book_dir = workspace_roadbook_dir
        
    # Synchronization reminder before checking script
    RuntimeManager.check_sync_status(rb_id, book_dir=book_dir)
        
    script_path = RuntimeManager.find_script(rb_id, book_dir=book_dir)
    
    if script_path:
        print_info("[Mode] Script execution mode.")
        print_info(f"[*] Found script: {script_path}")
        
        # Create Run ID first so script can use it
        run_id = RuntimeManager.create_run(rb_id, book_dir=book_dir)
        run_dir = RuntimeManager.get_runs_dir(rb_id, book_dir) / run_id
        
        outputs_dir = RuntimeManager.get_outputs_dir(rb_id, book_dir) / run_id
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Pass Run ID via environment variables
        env = os.environ.copy()
        env["ROADBOOK_RUN_ID"] = run_id
        env["ROADBOOK_RUN_DIR"] = str(run_dir)
        env["ROADBOOK_OUTPUTS_DIR"] = str(outputs_dir)
        
        print_info(f"[Runtime] Run ID: {run_id}")
        print_info(f"[*] Executing script...")
        
        # Prepare log file
        log_file = run_dir / "run.log"
        
        start_time = time.time()
        try:
            cmd = []
            if script_path.suffix == ".py":
                cmd = [sys.executable, str(script_path)]
            elif script_path.suffix == ".js":
                if not shutil.which("node"):
                    print_error("Node.js is not found in PATH but is required for .js scripts.")
                    return
                cmd = ["node", str(script_path)]
            elif script_path.suffix == ".ts":
                # Check for ts-node or other typescript runner
                if shutil.which("ts-node"):
                    cmd = ["ts-node", str(script_path)]
                elif shutil.which("npx"):
                    cmd = ["npx", "ts-node", str(script_path)]
                else:
                    print_error("TypeScript runtime not found. Please install ts-node (npm install -g ts-node) or ensure npx is available.")
                    return
            else:
                print_error(f"Unsupported script type: {script_path.suffix}")
                return
            
            # Execute with log capturing (tee behavior)
            with open(log_file, "wb") as f:
                process = subprocess.Popen(
                    cmd, 
                    env=env, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT
                )
                
                # Stream output to both console and file
                for line in iter(process.stdout.readline, b''):
                    sys.stdout.buffer.write(line)
                    sys.stdout.flush()
                    f.write(line)
                
                process.wait()
                
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, cmd)
            
            end_time = time.time()
            duration = end_time - start_time
            print_info(f"[Success] Script executed successfully in {duration:.2f}s.")
            
            # Try to capture outputs
            outputs = {}
            outputs_file = outputs_dir / "output.json"
            if outputs_file.exists():
                try:
                    with open(outputs_file, "r", encoding="utf-8") as f:
                        outputs = json.load(f)
                except Exception:
                    pass

            RuntimeManager.log_run_result(rb_id, run_id, "success", {
                "mode": "script", 
                "outputs": outputs,
                "timing": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration
                },
                "scaffold_version": SCAFFOLD_VERSION
            }, book_dir=book_dir)
            print_info("[Action] Use 'roadbook logs inspect <run_id>' to inspect this run.")
            
        except subprocess.CalledProcessError as e:
            end_time = time.time()
            duration = end_time - start_time
            print_error(f"Script execution failed with exit code {e.returncode} (Duration: {duration:.2f}s)")
            diagnosis = diagnose_error(e)
            print_info(f"[Guidance] {diagnosis}")
            
            RuntimeManager.log_run_result(rb_id, run_id, "failed", {
                "mode": "script", 
                "error": str(e),
                "timing": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration
                },
                "scaffold_version": SCAFFOLD_VERSION
            }, book_dir=book_dir)
            print_info("[Action] Use 'roadbook logs inspect <run_id>' to inspect failure details.")
        except Exception as e:
            print_error(f"Script execution error: {e}")
            print_info(f"[Guidance] {diagnose_error(e)}")
    else:
        from ..core.scaffold import ScaffoldManager
        
        print_info(f"[!] No automation script found for '{rb_id}'.")
        
        scaffold_paths = ScaffoldManager.get_structure_paths(book_dir)
        script_path_py = scaffold_paths["scripts"] / "script.py"
        
        print_info(f"[Action Required] Please generate an automation script to save tokens and enable reusability.")
        print_info(f"  -> Save your script to: {script_path_py}")
        print_info(f"  -> Or run 'roadbook init {rb_id}' to generate standard scaffolding.")
        print_info(f"  -> Save execution artifacts (downloads, screenshots) to: {workspace_roadbook_dir / 'output_...'}")





