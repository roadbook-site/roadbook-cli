import os
from pathlib import Path
from typing import Dict, Any

class ScaffoldManager:
    """
    Centralized manager for Roadbook project structure and file generation.
    Ensures consistency between 'init' and 'run' commands.
    """

    @staticmethod
    def get_structure_paths(book_dir: Path) -> Dict[str, Path]:
        """Returns standard paths for a roadbook directory."""
        return {
            "root": book_dir,
            "scripts": book_dir / "scripts",
            "runtime": book_dir / "runtime",
            "roadbook_file": book_dir / "roadbook.md"
        }

    @staticmethod
    def create_roadbook_scaffold(book_dir: Path, rb_id: str, name: str, description: str):
        """Creates the full roadbook scaffold (directories + roadbook.md)."""
        paths = ScaffoldManager.get_structure_paths(book_dir)
        
        # Create Directories
        paths["scripts"].mkdir(parents=True, exist_ok=True)
        paths["runtime"].mkdir(parents=True, exist_ok=True)
        
        # Create roadbook.md
        if not paths["roadbook_file"].exists():
            content = ScaffoldManager._generate_roadbook_md_content(rb_id, name, description)
            with open(paths["roadbook_file"], "w", encoding="utf-8") as f:
                f.write(content)
        
        return paths

    @staticmethod
    def create_script_scaffold(book_dir: Path, language: str = "python", rb_id: str = "roadbook", name: str = "Roadbook") -> Path:
        """Creates the script scaffold if it doesn't exist."""
        paths = ScaffoldManager.get_structure_paths(book_dir)
        scripts_dir = paths["scripts"]
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        script_path = None
        
        if language == "python":
            # 1. Create subdirectories
            (scripts_dir / "tests").mkdir(parents=True, exist_ok=True)
            (scripts_dir / "utils").mkdir(parents=True, exist_ok=True)

            # 2. Create __init__.py for utils
            init_py = scripts_dir / "utils" / "__init__.py"
            if not init_py.exists():
                with open(init_py, "w") as f:
                    pass

            # 3. Create utils/browser.py
            browser_py = scripts_dir / "utils" / "browser.py"
            if not browser_py.exists():
                with open(browser_py, "w", encoding="utf-8") as f:
                    f.write(ScaffoldManager._generate_browser_utils_content())

            # 4. Create script.py
            script_path = scripts_dir / "script.py"
            if not script_path.exists():
                content = ScaffoldManager._generate_python_script_template(rb_id, name)
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(content)
        
        return script_path

    @staticmethod
    def _generate_roadbook_md_content(rb_id, name, description):
        # Base YAML frontmatter
        yaml_frontmatter = f"""---
id: "{rb_id}"
name: "{name}"
version: "1.0"
owner: "user"
platform: "desktop"
description: "{description}"
tags: []
inputs: 
  target_url: 
    description: "The starting URL"
    default: "https://www.google.com"
outputs: {{}}
---
"""
        
        return f"""{yaml_frontmatter}
## Initialization
**ID**: init
**Type**: setup
**Description**: Verify browser environment (connection method) and authentication state.
**URL**: `{{{{target_url}}}}`
**Locators**: `body`

**Steps**:
1. `GOTO "{{{{target_url}}}}"`
2. `WAIT "networkidle"`

**Assertions**:
- [ ] Browser connected successfully (Launch or Attach)
- [ ] Target page loaded
- [ ] Authentication verified (Logged in or Login not required)

---

## Process Sheet 1
**ID**: process_sheet_1
**Type**: process
**Description**: [Describe the first main logic, e.g. "Process Sheet 1 Data"]
**URL**: `{{{{target_url}}}}`
**Locators**: `#main-content`, `text="Dashboard"`

**Steps**:
1. [Please fill in specific steps, e.g., `CLICK "#search-btn"`]
2. [Use semantic selectors, e.g., `INPUT "text=Search" "iPhone"`]
3. [Supported standard actions: GOTO, CLICK, INPUT, HOVER, WAIT, EXTRACT]

**Assertions**:
- [ ] [Please add checkpoints, e.g., Search result list loaded]

---

## Process Sheet 2
**ID**: process_sheet_2
**Type**: process
**Description**: [Describe the next main logic, e.g. "Process Sheet 2 Data"]
**URL**: `{{{{target_url}}}}`

**Steps**:
1. [Continue with the next part of the process]

**Assertions**:
- [ ] [Checkpoint for this step]

---

## Delivery
**ID**: delivery
**Type**: delivery
**Description**: Summarize deliverables and end the journey.

**Steps**:
1. [Output final result]

**Assertions**:
- [ ] Task completed
- [ ] Deliverables saved
"""

    @staticmethod
    def _generate_browser_utils_content():
        return '''"""
Browser configuration and initialization utilities.
"""
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
import logging

def get_playwright_context(headless=False):
    """
    Standard context manager for Playwright.
    """
    p = sync_playwright().start()
    
    # --- Browser Launch Strategies ---
    
    # Strategy 1: Fresh Browser (Default)
    # Best for: Clean state, reproducible runs, CI/CD, and initial exploration.
    browser = p.chromium.launch(headless=headless)
    
    # Strategy 2: Connect to Existing Browser (CDP)
    # Best for: Debugging, reusing login state, avoiding bot detection.
    # To use: 
    # 1. Run Chrome with: --remote-debugging-port=9222
    # 2. Uncomment line below:
    # browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    context = browser.new_context()
    page = context.new_page()
    return p, browser, context, page
'''

    @staticmethod
    def _generate_python_script_template(rb_id, name):
        return f'''"""
Automation script for roadbook: {name} ({rb_id})
Generated by Roadbook CLI.
"""
import sys
import os
import json
import logging
import time
from pathlib import Path

# Add current directory to path so we can import utils
sys.path.append(str(Path(__file__).parent))

try:
    from utils.browser import get_playwright_context
except ImportError:
    # Fallback if utils not present or path issue
    def get_playwright_context(headless=False):
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        return p, browser, context, page

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run(inputs: dict) -> dict:
    """
    Main execution entry point.
    """
    logger.info(f"Starting execution for {{inputs}}")
    
    target_url = inputs.get("target_url", "https://www.google.com")
    data = {{}}
    
    try:
        # Initialize Browser using shared utility
        # headless=False allows you to see the browser action. Set to True for production.
        p, browser, context, page = get_playwright_context(headless=False)
        
        try:
            # --- Phase 1: Initialization ---
            logger.info("Phase 1: Initialization")
            page.goto(target_url)
            page.wait_for_load_state("networkidle")
            # TODO: Add login logic or environmental checks here
            
            # --- Phase 2: Main Process ---
            # Suggestion: Break down complex logic into multiple steps/functions
            
            # Phase 2.1: Process Sheet 1 (Example)
            logger.info("Phase 2.1: Process Sheet 1")
            # process_sheet_1(page, data)

            # Phase 2.2: Process Sheet 2 (Example)
            logger.info("Phase 2.2: Process Sheet 2")
            # process_sheet_2(page, data)
            
            # --- Phase 3: Delivery ---
            logger.info("Phase 3: Delivery")
            # Save results, upload files, or return structured data
            data["result"] = "Operation completed successfully"
            
            # Example: Save to Output Directory
            output_dir = os.environ.get("ROADBOOK_OUTPUT_DIR")
            if output_dir:
                output_path = Path(output_dir) / "result.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                logger.info(f"Result saved to: {{output_path}}")
            
            logger.info("All steps completed successfully")
            
        finally:
            browser.close()
            p.stop()
            
        return {{"status": "success", "data": data}}

    except Exception as e:
        logger.error(f"Execution failed: {{e}}", exc_info=True)
        return {{"status": "failed", "error": str(e)}}

if __name__ == "__main__":
    # Standard Entry Point for CLI Execution
    try:
        if len(sys.argv) > 1:
            try:
                # Try parsing as JSON first
                cli_inputs = json.loads(sys.argv[1])
            except json.JSONDecodeError:
                # If not JSON, maybe treat as key=value or just empty
                cli_inputs = {{}}
        else:
             cli_inputs = {{}}
        
        result = run(cli_inputs)
        
        # Ensure result is printed to stdout for capture
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({{"status": "failed", "error": str(e)}}))
        sys.exit(1)
'''
