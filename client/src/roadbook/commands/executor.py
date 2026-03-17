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
        
        # Load config for defaults
        from roadbook.core.config import load_config
        config = load_config()
        scaffold_defaults = config.get("scaffold_defaults", {})
        default_lang = scaffold_defaults.get("language", "python")
        
        # Read and parse roadbook content
        roadbook_path = book_dir / "roadbook.md"
        book_content = ""
        roadbook_model = None
        if roadbook_path.exists():
            try:
                with open(roadbook_path, "r", encoding="utf-8") as f:
                    book_content = f.read()
                
                # Try to parse into model for structured generation
                try:
                    parser = RoadbookParser()
                    roadbook_model = parser.parse(book_content)
                except Exception:
                    pass
            except Exception:
                pass
        
        # Determine file extension and template based on language
        if default_lang.lower() in ["node", "nodejs", "javascript", "js"]:
            ext = ".js"
            template = get_js_template(rb_id, book_content, roadbook_model)
        elif default_lang.lower() in ["typescript", "ts"]:
            ext = ".ts"
            template = get_ts_template(rb_id, book_content, roadbook_model)
        else:
            ext = ".py"
            template = get_python_template(rb_id, book_content, roadbook_model)

        # New structure: .roadbook/<id>/scripts/script<ext>
        scripts_dir = book_dir / "scripts"
        script_file = scripts_dir / f"script{ext}"
        
        if not script_file.exists():
            try:
                scripts_dir.mkdir(parents=True, exist_ok=True)
                runtime_dir = book_dir / "runtime"
                runtime_dir.mkdir(parents=True, exist_ok=True)
                
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(template)
                    
                print_info(f"[Action] Script scaffold generated: {script_file}")
                print_info(f"  -> Please implement automation logic.")
                print_info(f"  -> Agent Hint: 已为您生成了脚本脚手架 `scripts/script{ext}`。当前处于语义引导模式，请阅读路书内容，并开始编写自动化逻辑。")
                
# Replaced original logic block


                script_path = script_file
                
            except Exception as e:
                print_error(f"Failed to generate scaffold: {e}")

    if script_path:
        print_info("[Status] Script ready. Starting semantic guide...")
        # TODO: Implement actual semantic guide interaction here
        # For now just inform user
        pass

# Define templates
SCAFFOLD_VERSION = "1.1.0"

def get_python_template(rb_id, book_content="", roadbook_model=None):
    import datetime
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    commented_content = ""
    # Only if roadbook_model is NOT provided, use full content dump as header
    if book_content and not roadbook_model:
        commented_content = "\\n".join([f"# {line}" for line in book_content.splitlines()])

    # Generate Structured Logic if model is available
    logic_body = "    # TODO: Implement your automation logic here\\n    pass"
    if roadbook_model:
        steps_code = []
        steps_code.append("    # ==========================================")
        steps_code.append("    # Structural Guide from Roadbook")
        steps_code.append("    # ==========================================")
        
        # Meta info
        if roadbook_model.meta:
            steps_code.append(f"    # Meta: {json.dumps(roadbook_model.meta, ensure_ascii=False)}")
        
        steps_code.append("")
        
        for sheet in roadbook_model.sheets:
            steps_code.append(f"    # ----------------------------------------------------------------")
            steps_code.append(f"    # Sheet: {sheet.title} (ID: {sheet.id})")
            if sheet.description:
                desc_lines = sheet.description.splitlines()
                for d in desc_lines:
                    steps_code.append(f"    # Description: {d}")
            if sheet.url:
                steps_code.append(f"    # URL: {sheet.url}")
            steps_code.append(f"    # ----------------------------------------------------------------")
            
            steps_code.append(f'    with step("{sheet.title}"):')
            if sheet.steps:
                for s in sheet.steps:
                    steps_code.append(f"        # {s.original_text or s.action}")
                steps_code.append("        pass")
            else:
                steps_code.append("        pass")
            steps_code.append("")
        logic_body = "\\n".join(steps_code)

    content_header = ""
    if commented_content:
        content_header = f"""
# ==============================================================================
# Roadbook Content
# ==============================================================================
{commented_content}
# ==============================================================================
"""

    return f"""# Roadbook Automation Script for {rb_id}
# Scaffold Version: {SCAFFOLD_VERSION}
# Generated at: {date_str}
# This script was auto-generated by 'roadbook open'.
{content_header}
import sys
import json
import os
import time
from pathlib import Path
from contextlib import contextmanager
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
    OUTPUT_DIR = RUNTIME_DIR.parent / f"output_{{time.strftime('%Y_%m_%d_%H_%M')}}"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Step Profiling Helper
STEPS_TIMING = {{}}

@contextmanager
def step(name):
    print(f"[*] Step Started: {{name}}...")
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        STEPS_TIMING[name] = duration
        print(f"    -> Step Finished: {{name}} (Duration: {{duration:.2f}}s)")

def run(inputs):
    print(f"Running with inputs: {{inputs}}")
    print(f"Artifacts will be saved to: {{OUTPUT_DIR}}")
    
    # Initialize structured outputs
    outputs = {{}}

{logic_body}


    # Save structured outputs to outputs.json
    outputs_file = OUTPUT_DIR / "outputs.json"
    
    # Attach timing metrics to outputs (optional, but helpful)
    outputs["_steps_timing"] = STEPS_TIMING
    
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
"""

def get_js_template(rb_id, book_content="", roadbook_model=None):
    import datetime
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    commented_content = ""
    if book_content:
        commented_content = "\\n".join([f"// {line}" for line in book_content.splitlines()])

    return f"""// Roadbook Automation Script for {rb_id}
// Scaffold Version: {SCAFFOLD_VERSION}
// Generated at: {date_str}
// This script was auto-generated by 'roadbook open'.

/* ==============================================================================
Roadbook Content (Reference)
============================================================================== */
{commented_content}
/* ============================================================================== */

const fs = require('fs');
const path = require('path');
// const {{ chromium }} = require('playwright');

// Runtime artifacts setup
const RUNTIME_DIR = path.join(__dirname, '..', 'runtime');
const SESSION_ID = process.env.ROADBOOK_RUN_ID;
let OUTPUT_DIR;

if (SESSION_ID) {{
    OUTPUT_DIR = path.join(RUNTIME_DIR, 'runs', SESSION_ID, 'artifacts');
}} else {{
    const timestamp = new Date().toISOString().replace(/[:.]/g, '_');
    OUTPUT_DIR = path.join(RUNTIME_DIR, '..', `output_${{timestamp}}`);
}}

if (!fs.existsSync(OUTPUT_DIR)) {{
    fs.mkdirSync(OUTPUT_DIR, {{ recursive: true }});
}}

// Step Profiling Helper
const STEPS_TIMING = {{}};

async function step(name, fn) {{
    console.log(`[*] Step Started: ${{name}}...`);
    const startTime = Date.now();
    try {{
        return await fn();
    }} finally {{
        const duration = (Date.now() - startTime) / 1000;
        STEPS_TIMING[name] = duration;
        console.log(`    -> Step Finished: ${{name}} (Duration: ${{duration.toFixed(2)}}s)`);
    }}
}}

async function run(inputs) {{
    console.log(`Running with inputs: ${{JSON.stringify(inputs)}}`);
    console.log(`Artifacts will be saved to: ${{OUTPUT_DIR}}`);

    // Initialize structured outputs
    const outputs = {{}};

    // TODO: Implement your automation logic here
    // await step("Browser Launch", async () => {{
    //     // const browser = await chromium.launch({{ headless: false }});
    //     // const page = await browser.newPage();
    // }});
    
    // await step("Navigate", async () => {{
    //     // await page.goto('...');
    // }});
    //
    // // Example: Save a screenshot
    // // await step("Capture", async () => {{
    // //     await page.screenshot({{ path: path.join(OUTPUT_DIR, 'screenshot.png') }});
    // // }});
    //
    // // Example: Set output data
    // // outputs['title'] = await page.title();
    //
    // // await browser.close();

    // Save structured outputs
    const outputsFile = path.join(OUTPUT_DIR, 'outputs.json');
    
    // Attach timing metrics to outputs
    outputs["_steps_timing"] = STEPS_TIMING;
    
    fs.writeFileSync(outputsFile, JSON.stringify(outputs, null, 2));
    console.log(`Structured outputs saved to: ${{outputsFile}}`);
}}

if (require.main === module) {{
    let inputs = {{}};
    if (process.argv.length > 2) {{
        try {{
            inputs = JSON.parse(process.argv[2]);
        }} catch (e) {{
            // ignore
        }}
    }}
    run(inputs).catch((error) => {{
        console.error(error);
        process.exit(1);
    }});
}}
"""

def run(inputs):
    # Dummy run function to avoid import errors if needed, 
    # but strictly speaking this file is a module for commands.
    pass

def get_ts_template(rb_id, book_content="", roadbook_model=None):
    import datetime
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    commented_content = ""
    if book_content:
        commented_content = "\\n".join([f"// {line}" for line in book_content.splitlines()])

    return f"""// Roadbook Automation Script for {rb_id}
// Scaffold Version: {SCAFFOLD_VERSION}
// Generated at: {date_str}
// This script was auto-generated by 'roadbook open'.

/* ==============================================================================
Roadbook Content (Reference)
============================================================================== */
{commented_content}
/* ============================================================================== */

import * as fs from 'fs';
import * as path from 'path';
// import {{ chromium }} = require('playwright');

// Runtime artifacts setup
const RUNTIME_DIR = path.join(__dirname, '..', 'runtime');
const SESSION_ID = process.env.ROADBOOK_RUN_ID;
let OUTPUT_DIR: string;

if (SESSION_ID) {{
    OUTPUT_DIR = path.join(RUNTIME_DIR, 'runs', SESSION_ID, 'artifacts');
}} else {{
    const timestamp = new Date().toISOString().replace(/[:.]/g, '_');
    OUTPUT_DIR = path.join(RUNTIME_DIR, '..', `output_${{timestamp}}`);
}}

if (!fs.existsSync(OUTPUT_DIR)) {{
    fs.mkdirSync(OUTPUT_DIR, {{ recursive: true }});
}}

// Step Profiling Helper
const STEPS_TIMING: Record<string, number> = {{}};

async function step<T>(name: string, fn: () => Promise<T>): Promise<T> {{
    console.log(`[*] Step Started: ${{name}}...`);
    const startTime = Date.now();
    try {{
        return await fn();
    }} finally {{
        const duration = (Date.now() - startTime) / 1000;
        STEPS_TIMING[name] = duration;
        console.log(`    -> Step Finished: ${{name}} (Duration: ${{duration.toFixed(2)}}s)`);
    }}
}}

async function run(inputs: any) {{
    console.log(`Running with inputs: ${{JSON.stringify(inputs)}}`);
    console.log(`Artifacts will be saved to: ${{OUTPUT_DIR}}`);

    // Initialize structured outputs
    const outputs: Record<string, any> = {{}};

    // TODO: Implement your automation logic here
    // await step("Browser Launch", async () => {{
    //     // const browser = await chromium.launch({{ headless: false }});
    //     // const page = await browser.newPage();
    // }});
    
    // await step("Navigate", async () => {{
    //     // await page.goto('...');
    // }});
    //
    // // Example: Save a screenshot
    // // await step("Capture", async () => {{
    // //     await page.screenshot({{ path: path.join(OUTPUT_DIR, 'screenshot.png') }});
    // // }});
    //
    // // Example: Set output data
    // // outputs['title'] = await page.title();
    //
    // // await browser.close();

    // Save structured outputs
    const outputsFile = path.join(OUTPUT_DIR, 'outputs.json');
    
    // Attach timing metrics to outputs
    outputs["_steps_timing"] = STEPS_TIMING;
    
    fs.writeFileSync(outputsFile, JSON.stringify(outputs, null, 2));
    console.log(`Structured outputs saved to: ${{outputsFile}}`);
}}

if (require.main === module) {{
    let inputs = {{}};
    if (process.argv.length > 2) {{
        try {{
            inputs = JSON.parse(process.argv[2]);
        }} catch (e) {{
            // ignore
        }}
    }}
    run(inputs).catch((error) => {{
        console.error(error);
        process.exit(1);
    }});
}}
"""
