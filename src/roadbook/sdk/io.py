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
    """Manages structured data outputs (streaming to jsonl)."""
    
    def __init__(self, outputs_dir: Path, scripts_dir: Path):
        self.outputs_dir = outputs_dir
        self.scripts_dir = scripts_dir
        self.dataset_dir = outputs_dir / "dataset"
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.default_dataset_file = self.dataset_dir / "default.jsonl"
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

    def push_data(self, data: Dict[str, Any], validate: bool = True):
        """Pushes data to the output dataset."""
        if validate and self.schema:
            try:
                import jsonschema
                jsonschema.validate(instance=data, schema=self.schema)
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Output validation warning: {e}")
                
        # Append to jsonl file
        with open(self.default_dataset_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
