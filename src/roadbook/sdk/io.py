# src/roadbook/sdk/io.py
import os
import json
from pathlib import Path
from typing import Any, Dict

class IOManager:
    def __init__(self, outputs_dir: Path):
        self.outputs_dir = outputs_dir
        self.inputs = self._load_inputs()
        self.outputs = []
        self.output_file = outputs_dir / "output.json"

    def _load_inputs(self) -> Dict[str, Any]:
        """Loads inputs from environment variables or a predefined file."""
        # For now, inputs might be passed via ROADBOOK_INPUTS env var
        inputs_str = os.environ.get("ROADBOOK_INPUTS", "{}")
        try:
            return json.loads(inputs_str)
        except json.JSONDecodeError:
            return {}

    def get_input(self, key: str, default: Any = None) -> Any:
        return self.inputs.get(key, default)

    def push_data(self, data: Dict[str, Any]):
        """Pushes data to the output dataset."""
        self.outputs.append(data)
        # Flush to file immediately for real-time monitoring
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.outputs, f, ensure_ascii=False, indent=2)
