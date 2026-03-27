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
            "config": book_dir / ".rb",
            "scripts": book_dir / "scripts",
            "runtime": book_dir / "runtime",
            "outputs": book_dir / "outputs",
            "roadbook_file": book_dir / "roadbook.md"
        }

    @staticmethod
    def create_roadbook_scaffold(book_dir: Path, rb_id: str, name: str, description: str, entry_url: str = "https://www.example.com"):
        """Creates the full roadbook scaffold (directories + roadbook.md)."""
        paths = ScaffoldManager.get_structure_paths(book_dir)
        
        # Create directories
        paths["config"].mkdir(parents=True, exist_ok=True)
        paths["scripts"].mkdir(parents=True, exist_ok=True)
        paths["runtime"].mkdir(parents=True, exist_ok=True)
        paths["outputs"].mkdir(parents=True, exist_ok=True)
        
        # Create config.yaml in the project root (.rb/config.yaml) if it doesn't exist
        config_file = paths["config"] / "config.yaml"
        if not config_file.exists():
            from .config import DEFAULT_CONFIG_YAML
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(DEFAULT_CONFIG_YAML)
        
        # Create roadbook.md
        if not paths["roadbook_file"].exists():
            content = ScaffoldManager._generate_roadbook_md_content(rb_id, name, description, entry_url)
            with open(paths["roadbook_file"], "w", encoding="utf-8") as f:
                f.write(content)

        # Create .gitignore
        gitignore_file = book_dir / ".gitignore"
        if not gitignore_file.exists():
            with open(gitignore_file, "w", encoding="utf-8") as f:
                f.write(".rb/profile/\noutputs/\nruntime/\n__pycache__/\n*.pyc\n")
        
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
            tests_dir = scripts_dir / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            (scripts_dir / "utils").mkdir(parents=True, exist_ok=True)

            # 1.5 Create sample test file with Agent Instructions
            sample_test_py = tests_dir / "sample_test.py"
            if not sample_test_py.exists():
                with open(sample_test_py, "w", encoding="utf-8") as f:
                    f.write(
                        "\"\"\"\n"
                        "[AGENT INSTRUCTION - MICRO TESTING]\n"
                        "Before modifying the main script.py, use this directory to write minimal tests.\n"
                        "Focus on ONE single element or interaction (e.g., just clicking a complex dropdown).\n"
                        "Once the logic is verified here, merge it back into the main script.py.\n"
                        "\"\"\"\n"
                        "from playwright.sync_api import sync_playwright\n\n"
                        "def test_single_element():\n"
                        "    with sync_playwright() as p:\n"
                        "        browser = p.chromium.launch(headless=False)\n"
                        "        page = browser.new_page()\n"
                        "        # Add your micro-test logic here\n"
                        "        browser.close()\n\n"
                        "if __name__ == '__main__':\n"
                        "    test_single_element()\n"
                    )

            # 2. Create __init__.py for utils
            init_py = scripts_dir / "utils" / "__init__.py"
            if not init_py.exists():
                with open(init_py, "w") as f:
                    pass

            # 3. Create script.py
            script_path = scripts_dir / "script.py"
            if not script_path.exists():
                content = ScaffoldManager._generate_python_script_template(rb_id, name, roadbook_model)
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    
            # 4. Create input/output schemas and local INPUT.json
            input_schema_path = scripts_dir / "input_schema.json"
            if not input_schema_path.exists():
                schema_content = ScaffoldManager._generate_schema_template("input", name, roadbook_model)
                with open(input_schema_path, "w", encoding="utf-8") as f:
                    f.write(schema_content)
                    
            output_schema_path = scripts_dir / "output_schema.json"
            if not output_schema_path.exists():
                schema_content = ScaffoldManager._generate_schema_template("output", name, roadbook_model)
                with open(output_schema_path, "w", encoding="utf-8") as f:
                    f.write(schema_content)
                    
            local_input_path = paths["config"] / "INPUT.json"
            if not local_input_path.exists():
                with open(local_input_path, "w", encoding="utf-8") as f:
                    f.write('{\n    "search_query": "example",\n    "max_items_to_fetch": 10\n}\n')
                    
            # 5. Create requirements.txt
            req_path = scripts_dir / "requirements.txt"
            if not req_path.exists():
                with open(req_path, "w", encoding="utf-8") as f:
                    f.write("playwright\njsonschema\n")
        
        return script_path

    @staticmethod
    def _generate_schema_template(schema_type: str, name: str, roadbook_model: Optional[RoadbookModel] = None) -> str:
        import json
        
        schema = {
            "title": f"{name} {schema_type.capitalize()} Schema",
            "type": "object",
            "properties": {}
        }
        
        if roadbook_model and roadbook_model.meta and roadbook_model.meta.get(f"{schema_type}s"):
            fields = roadbook_model.meta.get(f"{schema_type}s", {})
            if isinstance(fields, dict):
                required = []
                for key, desc in fields.items():
                    schema["properties"][key] = {
                        "type": "string",
                        "description": desc
                    }
                    required.append(key)
                if required:
                    schema["required"] = required
        else:
            # Provide a basic example if no model/meta is available
            if schema_type == "input":
                schema["properties"] = {
                    "search_query": {
                        "type": "string",
                        "description": "Example: A search keyword to use on the site"
                    },
                    "max_items_to_fetch": {
                        "type": "integer",
                        "description": "Example: Maximum number of items to extract",
                        "default": 10
                    }
                }
            else:
                schema["properties"] = {
                    "title": {
                        "type": "string",
                        "description": "The title of the extracted item"
                    },
                    "url": {
                        "type": "string",
                        "description": "The URL of the extracted item"
                    }
                }
                    
        return json.dumps(schema, indent=4, ensure_ascii=False)

    @staticmethod
    def _generate_roadbook_md_content(rb_id, name, description, entry_url="https://www.example.com"):
        import uuid
        template_bytes = pkgutil.get_data(__package__, "templates/roadbook.md.tpl")
        if not template_bytes:
            raise RuntimeError("Could not find roadbook.md.tpl template")
        template_str = template_bytes.decode("utf-8")
        
        return template_str.replace("{rb_id}", rb_id)\
                           .replace("{name}", name)\
                           .replace("{description}", description)\
                           .replace("{entry_url}", entry_url)\
                           .replace("{uuid_1}", uuid.uuid4().hex[:5])\
                           .replace("{uuid_2}", uuid.uuid4().hex[:5])\
                           .replace("{uuid_3}", uuid.uuid4().hex[:5])\
                           .replace("{uuid_4}", uuid.uuid4().hex[:5])

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
                logic_blocks.append("        # --- Phase 1: Setup ---")
                for i, sheet in enumerate(setup_sheets, 1):
                    logic_blocks.append(f'        with rb.sheet("{sheet.title}"):  # ID: {sheet.id}')
                    if sheet.url:
                        logic_blocks.append(f'            # URL: {sheet.url}')
                        logic_blocks.append(f'            # if "{sheet.url}" != entry_url:')
                        logic_blocks.append(f'            #     page.goto("{sheet.url}")')
                    if sheet.steps:
                        for s in sheet.steps:
                            logic_blocks.append(f'            # {s.original_text or s.action}')
                    logic_blocks.append(f'            pass')
                    logic_blocks.append('')
            
            # --- Process Phase ---
            if process_sheets:
                logic_blocks.append("        # --- Phase 2: Process ---")
                for i, sheet in enumerate(process_sheets, 1):
                    logic_blocks.append(f'        with rb.sheet("{sheet.title}"):  # ID: {sheet.id}')
                    if sheet.description:
                        logic_blocks.append(f'            # {sheet.description}')
                    if sheet.steps:
                        for s in sheet.steps:
                            logic_blocks.append(f'            # {s.original_text or s.action}')
                    
                    # Provide a helpful placeholder comment for function extraction
                    func_name = sheet.id if sheet.id else f"process_sheet_{i}"
                    func_name = func_name.replace('-', '_').replace(' ', '_').lower()
                    logic_blocks.append(f'            # [AGENT INSTRUCTION] Implement logic for {func_name} here.')
                    logic_blocks.append(f'            # {func_name}(page, rb)')
                    logic_blocks.append(f'            pass')
                    logic_blocks.append('')
            
            # --- Delivery Phase ---
            if delivery_sheets:
                logic_blocks.append("        # --- Phase 3: Delivery ---")
                for i, sheet in enumerate(delivery_sheets, 1):
                    logic_blocks.append(f'        with rb.sheet("{sheet.title}"):  # ID: {sheet.id}')
                    if sheet.steps:
                        for s in sheet.steps:
                            logic_blocks.append(f'            # {s.original_text or s.action}')
                    logic_blocks.append(f'            pass')
                    logic_blocks.append('')
                
        else:
            # Default Template if no model
            logic_blocks.append("        # --- Phase 1: Initialization ---")
            logic_blocks.append("        with rb.sheet(\"Initialization\"):")
            logic_blocks.append("            page.goto(\"{entry_url_fallback}\")")
            logic_blocks.append("            pass")

        logic_body = "\n".join(logic_blocks)
        
        # Build site_constraints
        site_constraints_dict = {}
        if roadbook_model:
            for s in roadbook_model.sheets:
                if s.type == "setup" and s.constraints:
                    site_constraints_dict.update(s.constraints)
        
        import json
        constraints_str = json.dumps(site_constraints_dict, indent=4)
        # Convert JSON booleans/null to Python syntax
        constraints_str = constraints_str.replace(": false", ": False").replace(": true", ": True").replace(": null", ": None")
        
        # Indent everything by 4 spaces
        constraints_indented = ""
        for line in constraints_str.split("\n"):
            constraints_indented += f"    {line}\n"
            
        site_constraints_block = f"    # Agent extracted site constraints from setup sheet\n    site_constraints = {constraints_indented.strip()}"
        
        template_bytes = pkgutil.get_data(__package__, "templates/script.py.tpl")
        if not template_bytes:
            raise RuntimeError("Could not find script.py.tpl template")
        template_str = template_bytes.decode("utf-8")
        
        entry_url_fallback = roadbook_model.meta.get('entry_url', 'https://www.example.com') if roadbook_model else 'https://www.example.com'
        
        return template_str.replace("{name}", name)\
                           .replace("{rb_id}", rb_id)\
                           .replace("{date_str}", date_str)\
                           .replace("{entry_url_fallback}", entry_url_fallback)\
                           .replace("{logic_body}", logic_body)\
                           .replace("{site_constraints_block}", site_constraints_block)
