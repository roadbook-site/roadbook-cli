import os
from pathlib import Path
from typing import Dict, Any, Optional
import pkgutil
from .parser import RoadbookParser, RoadbookModel

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
            "outputs": book_dir / "outputs",
            "roadbook_file": book_dir / "roadbook.md"
        }

    @staticmethod
    def create_roadbook_scaffold(book_dir: Path, rb_id: str, name: str, description: str, entry_url: str = "https://www.example.com"):
        """Creates the full roadbook scaffold (directories + roadbook.md)."""
        paths = ScaffoldManager.get_structure_paths(book_dir)
        
        # Create Directories
        paths["scripts"].mkdir(parents=True, exist_ok=True)
        paths["runtime"].mkdir(parents=True, exist_ok=True)
        paths["outputs"].mkdir(parents=True, exist_ok=True)
        
        # Create roadbook.md
        if not paths["roadbook_file"].exists():
            content = ScaffoldManager._generate_roadbook_md_content(rb_id, name, description, entry_url)
            with open(paths["roadbook_file"], "w", encoding="utf-8") as f:
                f.write(content)
        
        return paths

    @staticmethod
    def create_script_scaffold(book_dir: Path, language: str = "python", rb_id: str = "roadbook", name: str = "Roadbook", roadbook_content: str = "") -> Path:
        """Creates the script scaffold if it doesn't exist."""
        paths = ScaffoldManager.get_structure_paths(book_dir)
        scripts_dir = paths["scripts"]
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        script_path = None
        
        # Try to parse roadbook content to model if provided
        roadbook_model = None
        if roadbook_content:
            try:
                parser = RoadbookParser()
                roadbook_model = parser.parse(roadbook_content)
            except Exception:
                pass

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
                content = ScaffoldManager._generate_python_script_template(rb_id, name, roadbook_model)
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(content)
        
        return script_path

    @staticmethod
    def _generate_roadbook_md_content(rb_id, name, description, entry_url="https://www.example.com"):
        template_bytes = pkgutil.get_data(__package__, "templates/roadbook.md.tpl")
        if not template_bytes:
            raise RuntimeError("Could not find roadbook.md.tpl template")
        template_str = template_bytes.decode("utf-8")
        
        return template_str.replace("{rb_id}", rb_id)\
                           .replace("{name}", name)\
                           .replace("{description}", description)\
                           .replace("{entry_url}", entry_url)

    @staticmethod
    def _generate_browser_utils_content():
        template_bytes = pkgutil.get_data(__package__, "templates/browser.py.tpl")
        if not template_bytes:
            raise RuntimeError("Could not find browser.py.tpl template")
        return template_bytes.decode("utf-8")

    @staticmethod
    def _generate_python_script_template(rb_id, name, roadbook_model: Optional[RoadbookModel] = None):
        import datetime
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Logic Generation
        logic_blocks = []
        
        if roadbook_model:
            # Group sheets by type
            setup_sheets = [s for s in roadbook_model.sheets if s.type == "setup"]
            process_sheets = [s for s in roadbook_model.sheets if s.type == "process" or not s.type]
            delivery_sheets = [s for s in roadbook_model.sheets if s.type == "delivery"]
            
            # --- Setup Phase ---
            if setup_sheets:
                logic_blocks.append("            # --- Phase 1: Setup ---")
                for i, sheet in enumerate(setup_sheets, 1):
                    logic_blocks.append(f'            # Phase 1.{i}: {sheet.title}')
                    logic_blocks.append(f'            logger.info("Phase 1.{i}: {sheet.title}")')
                    logic_blocks.append(f'            with step("{sheet.title}"):  # ID: {sheet.id}')
                    if sheet.url:
                        logic_blocks.append(f'                # URL: {sheet.url}')
                        logic_blocks.append(f'                if "{sheet.url}" != "{{entry_url}}":')
                        logic_blocks.append(f'                     page.goto("{sheet.url}")')
                    if sheet.steps:
                        for s in sheet.steps:
                            logic_blocks.append(f'                # {s.original_text or s.action}')
                    logic_blocks.append(f'                pass')
                    logic_blocks.append('')
            
            # --- Process Phase ---
            if process_sheets:
                logic_blocks.append("            # --- Phase 2: Process ---")
                for i, sheet in enumerate(process_sheets, 1):
                    logic_blocks.append(f'            # Phase 2.{i}: {sheet.title}')
                    logic_blocks.append(f'            logger.info("Phase 2.{i}: {sheet.title}")')
                    logic_blocks.append(f'            with step("{sheet.title}"):  # ID: {sheet.id}')
                    if sheet.description:
                        logic_blocks.append(f'                # {sheet.description}')
                    if sheet.steps:
                        for s in sheet.steps:
                            logic_blocks.append(f'                # {s.original_text or s.action}')
                    
                    # Provide a helpful placeholder comment for function extraction
                    func_name = sheet.id if sheet.id else f"process_sheet_{i}"
                    func_name = func_name.replace('-', '_').replace(' ', '_').lower()
                    logic_blocks.append(f'                # {func_name}(page, data)')
                    logic_blocks.append(f'                pass')
                    logic_blocks.append('')
            
            # --- Delivery Phase ---
            if delivery_sheets:
                logic_blocks.append("            # --- Phase 3: Delivery ---")
                for i, sheet in enumerate(delivery_sheets, 1):
                    logic_blocks.append(f'            # Phase 3.{i}: {sheet.title}')
                    logic_blocks.append(f'            logger.info("Phase 3.{i}: {sheet.title}")')
                    logic_blocks.append(f'            with step("{sheet.title}"):  # ID: {sheet.id}')
                    if sheet.steps:
                        for s in sheet.steps:
                            logic_blocks.append(f'                # {s.original_text or s.action}')
                    logic_blocks.append(f'                pass')
                    logic_blocks.append('')
                
        else:
            # Default Template if no model
            logic_blocks.append("            # --- Phase 1: Initialization ---")
            logic_blocks.append("            logger.info(\"Phase 1: Initialization\")")
            logic_blocks.append("            page.goto(entry_url)")
            # Use wait_for_page_load for better stability
            logic_blocks.append("            wait_for_page_load(page, \"domcontentloaded\")")
            logic_blocks.append("")
            logic_blocks.append("            # --- Phase 2: Process ---")
            logic_blocks.append("            # Phase 2.1: Process Sheet 1 (Example)")
            logic_blocks.append("            logger.info(\"Phase 2.1: sample sheet title\")")
            logic_blocks.append("            with step(\"Process Sheet 1\"):")
            logic_blocks.append("                # process_sheet_1(page, data)")
            logic_blocks.append("                pass")
            logic_blocks.append("")
            logic_blocks.append("            # Phase 2.2: Process Sheet 2 (Example)")
            logic_blocks.append("            logger.info(\"Phase 2.2: sample sheet title 2\")")
            logic_blocks.append("            with step(\"Process Sheet 2\"):")
            logic_blocks.append("                # process_sheet_2(page, data)")
            logic_blocks.append("                pass")
            logic_blocks.append("")
            logic_blocks.append("            # --- Phase 3: Delivery ---")
            logic_blocks.append("            logger.info(\"Phase 3: Delivery\")")
            logic_blocks.append("            data[\"result\"] = \"Operation completed successfully\"")

        logic_body = "\n".join(logic_blocks)
        
        template_bytes = pkgutil.get_data(__package__, "templates/script.py.tpl")
        if not template_bytes:
            raise RuntimeError("Could not find script.py.tpl template")
        template_str = template_bytes.decode("utf-8")
        
        entry_url_fallback = roadbook_model.meta.get('entry_url', 'https://www.example.com') if roadbook_model else 'https://www.example.com'
        
        return template_str.replace("{name}", name)\
                           .replace("{rb_id}", rb_id)\
                           .replace("{date_str}", date_str)\
                           .replace("{entry_url_fallback}", entry_url_fallback)\
                           .replace("{logic_body}", logic_body)
