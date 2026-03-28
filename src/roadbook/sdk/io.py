# src/roadbook/sdk/io.py
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("roadbook.sdk.io")

class InputManager:
    """Manages script inputs with schema validation and default hydration."""
    
    def __init__(self, rb_dir: Path, scripts_dir: Path):
        self.rb_dir = rb_dir
        self.scripts_dir = scripts_dir
        self.schema = self._load_schema()
        self.inputs = self._load_and_validate_inputs()

    def _load_schema(self) -> Dict[str, Any]:
        schema_path = self.scripts_dir / "input_schema.json"
        if schema_path.exists():
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load input schema from {schema_path}: {e}")
        return {}

    def _load_and_validate_inputs(self) -> Dict[str, Any]:
        """Loads inputs from execution environment and validates against schema."""
        raw_inputs = {}
        
        # Load from injected file path (managed by executor)
        input_file = os.environ.get("ROADBOOK_INPUT_FILE")
        if input_file and Path(input_file).exists():
            try:
                with open(input_file, "r", encoding="utf-8") as f:
                    raw_inputs = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load input from {input_file}: {e}")
        else:
            # Fallback to env var (useful for simple cloud/remote execution without files)
            inputs_str = os.environ.get("ROADBOOK_INPUTS", "{}")
            try:
                raw_inputs = json.loads(inputs_str)
            except json.JSONDecodeError:
                pass
                
        # Hydrate defaults and Validate
        if self.schema:
            try:
                import jsonschema
                
                # Hydrate defaults before validation
                properties = self.schema.get("properties", {})
                for key, prop_schema in properties.items():
                    if key not in raw_inputs and "default" in prop_schema:
                        raw_inputs[key] = prop_schema["default"]
                        
                # Validate
                jsonschema.validate(instance=raw_inputs, schema=self.schema)
            except ImportError:
                logger.warning("jsonschema package not installed, skipping input validation.")
            except Exception as e:
                # We fail fast if validation fails
                raise ValueError(f"Input validation failed: {e}")
                
        return raw_inputs

    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific input value."""
        return self.inputs.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """Get all parsed and validated inputs."""
        return self.inputs


class DatasetManager:
    """Manages structured data outputs (streaming to jsonl, supports configurable formats)."""
    
    def __init__(self, outputs_dir: Path, scripts_dir: Path):
        self.outputs_dir = outputs_dir
        self.scripts_dir = scripts_dir
        # Ensure outputs_dir exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load output format preference (default to jsonl)
        # In the future, this could be read from rb.config or environment variables
        self.output_format = os.environ.get("ROADBOOK_OUTPUT_FORMAT", "jsonl").lower()
        
        # Set primary result file name
        self.default_dataset_file = self.outputs_dir / f"result.{self.output_format}"
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        schema_path = self.scripts_dir / "output_schema.json"
        if schema_path.exists():
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load output schema from {schema_path}: {e}")
        return {}

    def emit_output(self, data: Dict[str, Any], validate: bool = True):
        """Emits data to the output dataset."""
        if validate and self.schema:
            try:
                import jsonschema
                jsonschema.validate(instance=data, schema=self.schema)
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Output validation warning: {e}")
                
        # Handle different output formats
        if self.output_format == "jsonl":
            with open(self.default_dataset_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        elif self.output_format == "json":
            # For JSON, we need to read, append, and rewrite the array
            # This is less efficient than jsonl but supported for user preference
            current_data = []
            if self.default_dataset_file.exists():
                try:
                    with open(self.default_dataset_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            current_data = json.loads(content)
                            if not isinstance(current_data, list):
                                current_data = [current_data]
                except Exception as e:
                    logger.warning(f"Failed to read existing JSON: {e}")
            
            current_data.append(data)
            with open(self.default_dataset_file, "w", encoding="utf-8") as f:
                json.dump(current_data, f, ensure_ascii=False, indent=2)
        elif self.output_format == "csv":
            import csv
            file_exists = self.default_dataset_file.exists()
            with open(self.default_dataset_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)
        else:
            # Fallback to jsonl
            with open(self.default_dataset_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
