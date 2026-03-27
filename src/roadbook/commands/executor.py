import os
import time
import json
import argparse
import subprocess
import sys
import shutil
import importlib.util
import ast
import csv
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

def validate_inputs_with_guidance(inputs: Dict[str, Any], book_dir: Path, rb_id: str) -> bool:
    """
    Validates inputs against input_schema.json and provides friendly guidance if missing.
    Returns True if valid, False otherwise.
    """
    schema_path = book_dir / "scripts" / "input_schema.json"
    if not schema_path.exists():
        return True
        
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
            
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        missing_fields = []
        for req in required_fields:
            if req not in inputs:
                missing_fields.append(req)
                
        if missing_fields:
            print_error("Missing required inputs.")
            print_info("\n[Guidance] The following parameters are required but were not provided:")
            
            # Print missing fields with descriptions
            for field in missing_fields:
                prop = properties.get(field, {})
                desc = prop.get("description", "No description")
                prop_type = prop.get("type", "any")
                print(f"  - {field} ({prop_type}): {desc}")
                
            # Generate a JSON example
            example = {}
            for key, prop in properties.items():
                if key in required_fields:
                    prop_type = prop.get("type", "string")
                    if prop_type == "string":
                        example[key] = "..."
                    elif prop_type == "integer" or prop_type == "number":
                        example[key] = 0
                    elif prop_type == "boolean":
                        example[key] = True
                    elif prop_type == "array":
                        example[key] = []
                    else:
                        example[key] = "..."
                        
            example_json = json.dumps(example, indent=2)
            single_line_json = json.dumps(example)
            print_info("\n[Action] Please provide them using --inputs or a file:")
            if sys.platform == "win32":
                print(f"  roadbook run {rb_id} --inputs \"{single_line_json.replace('\"', '\\\"')}\"")
            else:
                print(f"  roadbook run {rb_id} --inputs '{single_line_json}'")
                
            print_info("\nOr create/edit .rb/INPUT.json with:")
            print(example_json)
            
            return False
            
        return True
    except Exception as e:
        # If schema parsing fails, we just warn and proceed, let the script handle it
        print_info(f"[Warning] Failed to parse input_schema.json: {e}")
        return True

def get_inputs(args, book_dir: Path) -> Optional[Dict[str, Any]]:
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
    elif getattr(args, 'inputs', None):
        # 2. Merge/Override with CLI inputs string if provided
        inputs_str = getattr(args, 'inputs')
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
    else:
        # 3. Default to .rb/INPUT.json for local runs if no other input is provided
        default_input_path = book_dir / ".rb" / "INPUT.json"
        if default_input_path.exists():
            try:
                with open(default_input_path, 'r', encoding='utf-8') as f:
                    file_inputs = json.load(f)
                    if isinstance(file_inputs, dict):
                        inputs.update(file_inputs)
            except Exception as e:
                print_error(f"Failed to load default local input from {default_input_path}")
                print_info(f"[Detail] {e}")
            
    return inputs

def check_and_install_dependencies(book_dir: Path):
    """Checks requirements.txt and installs missing dependencies into .rb/site-packages."""
    req_file = book_dir / "scripts" / "requirements.txt"
    if not req_file.exists():
        return
        
    import hashlib
    try:
        with open(req_file, "rb") as f:
            req_hash = hashlib.md5(f.read()).hexdigest()
    except Exception:
        return
        
    venv_dir = book_dir / ".rb" / ".venv"
    hash_file = venv_dir / "req.hash"
    
    if hash_file.exists():
        try:
            with open(hash_file, "r") as f:
                if f.read().strip() == req_hash:
                    return # Already installed
        except Exception:
            pass
            
    print_info("[Dependencies] Installing/Updating dependencies from requirements.txt...")
    site_packages = book_dir / ".rb" / "site-packages"
    site_packages.mkdir(parents=True, exist_ok=True)
    
    cmd = [sys.executable, "-m", "pip", "install", "--target", str(site_packages), "-r", str(req_file)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        venv_dir.mkdir(parents=True, exist_ok=True)
        with open(hash_file, "w") as f:
            f.write(req_hash)
        print_info("[Dependencies] Installation complete.")
    except subprocess.CalledProcessError as e:
        print_error("Failed to install dependencies.")
        if e.output:
            print_info(f"[Details] {e.output.decode('utf-8', errors='ignore')}")

def convert_dataset_format(dataset_file: Path, outputs_dir: Path, output_format: str):
    """
    Converts a jsonl dataset file to the specified format.
    Supported formats: json, csv, xlsx
    """
    data_list = []
    try:
        with open(dataset_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data_list.append(json.loads(line))
    except Exception as e:
        raise ValueError(f"Could not read dataset jsonl: {e}")
        
    if not data_list:
        return

    output_file = outputs_dir / f"dataset.{output_format}"
    
    if output_format == "json":
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
        print_info(f"  -> Saved to {output_file}")
            
    elif output_format == "csv":
        # Extract all possible keys from all rows to form the header
        keys = set()
        for row in data_list:
            keys.update(row.keys())
        header = list(keys)
        
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            for row in data_list:
                writer.writerow(row)
        print_info(f"  -> Saved to {output_file}")
                
    elif output_format == "xlsx":
        # Requires openpyxl
        try:
            import openpyxl
        except ImportError:
            raise ValueError("The 'openpyxl' package is required to export to xlsx. Please run 'pip install openpyxl'.")
            
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Dataset"
        
        keys = set()
        for row in data_list:
            keys.update(row.keys())
        header = list(keys)
        
        # Write header
        for col_idx, col_name in enumerate(header, 1):
            ws.cell(row=1, column=col_idx, value=col_name)
            
        # Write rows
        for row_idx, row_data in enumerate(data_list, 2):
            for col_idx, col_name in enumerate(header, 1):
                # Convert dict/list to string to avoid openpyxl errors
                val = row_data.get(col_name)
                if isinstance(val, (dict, list)):
                    val = json.dumps(val, ensure_ascii=False)
                ws.cell(row=row_idx, column=col_idx, value=val)
                
        wb.save(output_file)
        print_info(f"  -> Saved to {output_file}")
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


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
        
    inputs = get_inputs(args, book_dir)
    if inputs is None:
        return
        
    # Validate inputs and provide guidance if missing
    if not validate_inputs_with_guidance(inputs, book_dir, rb_id):
        return
        
    # Synchronization reminder before checking script
    RuntimeManager.check_sync_status(rb_id, book_dir=book_dir)
        
    script_path = RuntimeManager.find_script(rb_id, book_dir=book_dir)
    
    if script_path:
        print_info("[Mode] Script execution mode.")
        print_info(f"[*] Found script: {script_path}")
        
        # Check and install dependencies
        check_and_install_dependencies(book_dir)
        
        # Create Run ID first so script can use it
        run_id = RuntimeManager.create_run(rb_id, book_dir=book_dir)
        run_dir = RuntimeManager.get_runs_dir(rb_id, book_dir) / run_id
        
        outputs_dir = RuntimeManager.get_outputs_dir(rb_id, book_dir) / run_id
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Write inputs to a temporary file in run_dir for the SDK to consume
        input_file = run_dir / "injected_inputs.json"
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(inputs, f, ensure_ascii=False)
        
        # Pass Run ID and Input via environment variables
        env = os.environ.copy()
        env["ROADBOOK_RUN_ID"] = run_id
        env["ROADBOOK_RUN_DIR"] = str(run_dir)
        env["ROADBOOK_OUTPUTS_DIR"] = str(outputs_dir)
        env["ROADBOOK_INPUT_FILE"] = str(input_file)
        
        # Add local site-packages to PYTHONPATH
        site_packages = book_dir / ".rb" / "site-packages"
        if site_packages.exists():
            existing_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{site_packages}{os.pathsep}{existing_pp}" if existing_pp else str(site_packages)
        
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
            
            # Post-processing: Convert output format if needed
            output_format = getattr(args, 'output_format', 'jsonl')
            dataset_file = outputs_dir / "dataset" / "default.jsonl"
            if dataset_file.exists() and output_format != 'jsonl':
                print_info(f"[Post-processing] Converting dataset to {output_format} format...")
                try:
                    convert_dataset_format(dataset_file, outputs_dir, output_format)
                except Exception as conv_err:
                    print_error(f"Failed to convert dataset to {output_format}: {conv_err}")
            
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





