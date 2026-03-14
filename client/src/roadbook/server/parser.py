import re
import yaml
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Step(BaseModel):
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    original_text: str = ""

class Sheet(BaseModel):
    id: str = ""
    title: str
    description: str = ""
    url: str = ""
    locators: str = ""
    reference: str = ""
    steps: List[Step] = Field(default_factory=list)
    # 用于保留未结构化解析的其他内容，以便还原
    extra_content: str = "" 

class RoadbookModel(BaseModel):
    meta: Dict[str, Any] = Field(default_factory=dict)
    sheets: List[Sheet] = Field(default_factory=list)
    raw_preamble: str = "" # Meta 之后，第一个 Sheet 之前的内容

class RoadbookParser:
    def parse(self, content: str) -> RoadbookModel:
        # 1. Parse Meta (Frontmatter)
        meta = {}
        remaining_content = content
        
        if content.startswith("---"):
            # Split by --- but only first 2 occurrences
            parts = re.split(r"^---$", content, maxsplit=2, flags=re.MULTILINE)
            # parts[0] is empty (before first ---)
            # parts[1] is yaml content
            # parts[2] is remaining content
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1])
                except yaml.YAMLError:
                    meta = {}
                remaining_content = parts[2]
            else:
                # Malformed frontmatter?
                pass
        
        # 2. Split Sheets by H2 headers
        # Split pattern: Start of line, ##, space, Title, End of line
        # We use capturing group to keep the title
        sheet_parts = re.split(r"^##\s+(.+)$", remaining_content, flags=re.MULTILINE)
        
        raw_preamble = ""
        sheets = []
        
        if len(sheet_parts) > 0:
            raw_preamble = sheet_parts[0].strip()
            
            # sheet_parts[0] is preamble
            # sheet_parts[1] is title 1, sheet_parts[2] is content 1
            # sheet_parts[3] is title 2, sheet_parts[4] is content 2...
            
            for i in range(1, len(sheet_parts), 2):
                title = sheet_parts[i].strip()
                if i+1 < len(sheet_parts):
                    content_block = sheet_parts[i+1]
                    sheets.append(self._parse_sheet(title, content_block))
            
        return RoadbookModel(meta=meta, sheets=sheets, raw_preamble=raw_preamble)

    def _parse_sheet(self, title: str, content: str) -> Sheet:
        sheet = Sheet(title=title)
        
        # Normalize line endings
        lines = content.strip().split('\n')
        
        steps_mode = False
        extra_lines = []
        steps = []
        
        # Regex for key-value pairs like **ID**: value
        # Note: Markdown bold syntax is **text**, so we look for **Key**: Value
        # Allow empty value for keys like Steps
        kv_pattern = re.compile(r"^\*\*(.+?)\*\*:\s*(.*)$")
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check for Key-Value pairs
            kv_match = kv_pattern.match(line_stripped)
            if kv_match:
                key = kv_match.group(1).lower()
                value = kv_match.group(2).strip()
                
                if key == "id":
                    sheet.id = value
                elif key == "description":
                    sheet.description = value
                elif key == "url":
                    sheet.url = value.strip('`') # Remove backticks if present
                elif key == "locators":
                    sheet.locators = value
                elif key == "reference":
                    sheet.reference = value
                elif key == "steps":
                    steps_mode = True
                    continue # Skip this line
                else:
                    # Unknown key, keep as extra
                    extra_lines.append(line)
                continue
            
            # If in Steps mode, parse steps
            if steps_mode:
                # Match list items: 1. or - 
                step_match = re.match(r"^(\d+\.|-)\s+(.+)$", line_stripped)
                if step_match:
                    step_text = step_match.group(2)
                    steps.append(self._parse_step(step_text))
                elif line_stripped == "":
                    continue
                elif line_stripped.startswith("---"):
                    # Separator line, ignore
                    continue
                else:
                    # If we hit a non-list item and not empty, maybe steps block ended?
                    # For now, let's treat it as extra content if it's not a separator
                    extra_lines.append(line)
            else:
                if line_stripped.startswith("---"):
                    continue
                if line_stripped:
                    extra_lines.append(line)
        
        sheet.steps = steps
        sheet.extra_content = "\n".join(extra_lines)
        return sheet

    def _parse_step(self, text: str) -> Step:
        # Simple heuristic to parse ACTION "Selector" "Value"
        # Example: INPUT "#search" "keyword"
        # Example: CLICK "#btn"
        # Example: GOTO "https://..."
        
        parts = text.split(' ', 1)
        action = parts[0]
        selector = None
        value = None
        
        # This is a very basic parser, a robust one would need a proper tokenizer for quoted strings
        # For now, we return the raw text as primary, but try to extract action
        
        return Step(
            action=action,
            original_text=text
        )

    def dump(self, model: RoadbookModel) -> str:
        output = []
        
        # 1. Meta
        if model.meta:
            output.append("---")
            # dump returns string with newline at end usually
            yaml_str = yaml.dump(model.meta, allow_unicode=True, sort_keys=False).strip()
            output.append(yaml_str)
            output.append("---\n")
        
        if model.raw_preamble:
            output.append(model.raw_preamble + "\n")
            
        # 2. Sheets
        for sheet in model.sheets:
            output.append(f"## {sheet.title}")
            
            if sheet.id:
                output.append(f"**ID**: {sheet.id}")
            if sheet.description:
                output.append(f"**Description**: {sheet.description}")
            if sheet.url:
                output.append(f"**URL**: `{sheet.url}`")
            if sheet.locators:
                output.append(f"**Locators**: {sheet.locators}")
            if sheet.reference:
                output.append(f"**Reference**: {sheet.reference}")
            
            if sheet.steps:
                output.append("\n**Steps**:")
                for i, step in enumerate(sheet.steps, 1):
                    # Prefer regenerating from structured data if available, 
                    # but fallback to original text for fidelity
                    # If step.original_text is empty, we should construct it from action/selector/value
                    if step.original_text:
                        output.append(f"{i}. {step.original_text}")
                    else:
                        # Fallback construction (not implemented fully in parse yet)
                        output.append(f"{i}. {step.action}") 
            
            if sheet.extra_content:
                output.append("\n" + sheet.extra_content)
                
            output.append("\n---\n")
            
        return "\n".join(output)
