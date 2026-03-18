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
            outputs_file = run_dir / "artifacts" / "outputs.json"
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
        
        print_info("[*] Switching to Semantic Guide Mode to help you build the script...")
        start_session(args)

from roadbook.core.config import ROADBOOK_DIR

def find_workspace_dot_roadbook(start_path: Path) -> Path:
    """
    Locates the .roadbook directory for the current workspace.
    Logic:
    1. If start_path is inside a .roadbook dir, return that .roadbook dir.
    2. Traverse up from start_path to find a directory containing .roadbook.
    3. If found, return that .roadbook.
    4. If not found, assume current directory is root and return start_path / .roadbook.
    """
    # 1. Check if inside .roadbook
    current = start_path
    while current != current.parent:
        if current.name == ".roadbook":
            return current
        current = current.parent
    
    # 2. Check upwards for existence of .roadbook
    current = start_path
    while current != current.parent:
        candidate = current / ".roadbook"
        if candidate.is_dir():
            return candidate
        current = current.parent
        
    # 3. Not found, default to CWD/.roadbook
    return start_path / ".roadbook"

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

    cwd = Path.cwd()
    
    # 1. Locate the effective .roadbook directory (Local or Global)
    dot_roadbook_dir = find_workspace_dot_roadbook(cwd)
    
    # 2. Check if we are in Global Environment
    # If the located .roadbook is the global one (~/.roadbook), we treat it as "Global Mode"
    is_global_env = False
    try:
        if dot_roadbook_dir.resolve() == ROADBOOK_DIR.resolve():
            is_global_env = True
    except Exception:
        pass
        
    # 3. Determine Target Book Directory
    # We check if the book already exists inside the located .roadbook structure
    # This handles both "Global In-Place" and "Local Existing Copy" scenarios
    
    target_book_dir = None
    
    # Search for rb_id inside dot_roadbook_dir (recursively, but typically shallow)
    # We look for roadbook.md with matching ID
    if dot_roadbook_dir.exists():
        for path in dot_roadbook_dir.rglob("roadbook.md"):
            # Optimization: Skip deep nesting if possible, but rglob is okay for .roadbook which is usually clean
            try:
                # Check ID matching (simple path name check first for speed)
                if path.parent.name == rb_id:
                     target_book_dir = path.parent
                     break
                
                # Fallback: Read content
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read(1024)
                    if f"id: {rb_id}" in content or f"id:{rb_id}" in content:
                        target_book_dir = path.parent
                        break
            except Exception:
                continue
    
    # 4. Copy Logic
    # Premise: The roadbook MUST be in the .roadbook directory (or its subdirectories).
    # If it is not found there, we copy it.
    
    if target_book_dir:
        print_info(f"[Setup] Using existing roadbook in workspace: {target_book_dir}")
        book_dir = target_book_dir
    else:
        # Not found in .roadbook, so we copy it to .roadbook/<id>
        # Note: If dot_roadbook_dir is Global, and book was not found there, 
        # it means we are installing a new book into Global (if we have permissions/intent).
        # However, typically 'open' implies a working session.
        # If is_global_env is True, we are modifying global state.
        
        target_book_dir = dot_roadbook_dir / rb_id
        
        print_info(f"[Setup] Initializing roadbook workspace: {target_book_dir}")
        try:
            shutil.copytree(book.path.parent, target_book_dir, dirs_exist_ok=True)
            print_info(f"[Setup] Copied roadbook to workspace.")
            book_dir = target_book_dir
        except Exception as e:
            print_error(f"Failed to copy roadbook to workspace: {e}")
            return

    # Check Script State (4 States)
    script_path = RuntimeManager.find_script(rb_id, book_dir=book_dir)
    _handle_script_state(rb_id, book_dir, script_path)

def _handle_script_state(rb_id: str, book_dir: Path, script_path: Optional[Path]):
    """Extracted logic for handling script state after roadbook dir is determined."""
    if not script_path:
        # State 1: No Script (Generate Scaffold)
        print_info(f"[Status] No automation script found for '{rb_id}'.")
        
        # Read roadbook content
        roadbook_path = book_dir / "roadbook.md"
        book_content = ""
        if roadbook_path.exists():
            try:
                with open(roadbook_path, "r", encoding="utf-8") as f:
                    book_content = f.read()
            except Exception:
                pass
        
        try:
            # Delegate to ScaffoldManager
            # We force language="python" as requested by user ("先实现Python版本吧，其他的版本先删掉")
            script_path = ScaffoldManager.create_script_scaffold(
                book_dir=book_dir,
                language="python",
                rb_id=rb_id,
                name=rb_id,
                roadbook_content=book_content
            )
            
            if script_path and script_path.exists():
                print_info(f"[Action] Script scaffold generated: {script_path}")
                print_info(f"  -> Please implement automation logic.")
                print_info(f"  -> Agent Hint: 已为您生成了脚本脚手架 `scripts/script.py`。当前处于语义引导模式，请阅读路书内容，并开始编写自动化逻辑。")
            else:
                print_error("Failed to generate script scaffold.")

        except Exception as e:
            print_error(f"Failed to generate scaffold: {e}")

    if script_path:
        print_info("[Status] Script ready. Starting semantic guide...")
        # TODO: Implement actual semantic guide interaction here
        pass





