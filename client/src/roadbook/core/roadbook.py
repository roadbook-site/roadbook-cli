import os
import yaml
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .config import get_books_dir

@dataclass
class RoadbookSheet:
    title: str
    content: str
    index: int

@dataclass
class RoadbookMeta:
    id: str
    name: str
    version: str
    description: str
    path: Path
    valid: bool = True
    error: str = ""
    sheets: List[RoadbookSheet] = None

class RoadbookManager:
    @staticmethod
    def list_roadbooks() -> List[RoadbookMeta]:
        books_dir = get_books_dir()
        roadbooks = []
        
        if not books_dir.exists():
            return []

        # Recursive search for roadbook.md
        for rb_path in books_dir.rglob("roadbook.md"):
            meta = RoadbookManager._parse_meta(rb_path)
            roadbooks.append(meta)
        
        return roadbooks

    @staticmethod
    def get_roadbook(rb_id: str) -> Optional[RoadbookMeta]:
        books_dir = get_books_dir()
        
        # 1. Try direct path (standard structure: books/{id}/roadbook.md)
        direct_path = books_dir / rb_id / "roadbook.md"
        if direct_path.exists():
            meta = RoadbookManager._parse_meta(direct_path)
            # Only return if ID matches (or if parsing failed but we want to return the error object)
            # If meta.id is inferred from folder name, it will match.
            # If meta.id is in YAML and differs, we should respect the file content?
            # If user asks for 'foo' and we found 'books/foo/roadbook.md' which says 'id: bar',
            # technically that's not 'foo'. But usually users imply path or ID.
            # Let's check if meta.id matches.
            if meta.id == rb_id:
                return meta
        
        # 2. Search recursively if not found or ID mismatch
        for rb_path in books_dir.rglob("roadbook.md"):
            # Skip the direct path we already checked
            if rb_path == direct_path:
                continue
                
            # Optimization: Check if parent directory name matches ID
            if rb_path.parent.name == rb_id:
                meta = RoadbookManager._parse_meta(rb_path)
                if meta.id == rb_id:
                    return meta

        # 3. Full scan (slowest, but finds ID regardless of folder name)
        for rb_path in books_dir.rglob("roadbook.md"):
            if rb_path == direct_path: continue
            
            meta = RoadbookManager._parse_meta(rb_path)
            if meta.id == rb_id:
                return meta
                
        return None

    @staticmethod
    def _parse_sheets(content: str) -> List[RoadbookSheet]:
        sheets = []
        # Find all H2 headers (## Title) and their content
        # Split the content by ## 
        parts = re.split(r'^##\s+(.+)$', content, flags=re.MULTILINE)
        
        # parts[0] is everything before the first ## (usually frontmatter + intro)
        # parts[1] is first title, parts[2] is first content, etc.
        if len(parts) > 1:
            sheet_idx = 0
            for i in range(1, len(parts), 2):
                title = parts[i].strip()
                # Remove trailing --- if present, and strip whitespace
                sheet_content = parts[i+1].split('---')[0].strip()
                
                sheets.append(RoadbookSheet(
                    title=title,
                    content=sheet_content,
                    index=sheet_idx
                ))
                sheet_idx += 1
                
        return sheets

    @staticmethod
    def _parse_meta(file_path: Path) -> RoadbookMeta:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            sheets = RoadbookManager._parse_sheets(content)
            
            # Simple Frontmatter parser
            if content.startswith('---'):
                end_idx = content.find('---', 3)
                if end_idx != -1:
                    yaml_content = content[3:end_idx]
                    data = yaml.safe_load(yaml_content)
                    
                    # Validate required fields
                    required = ['id', 'name', 'version']
                    for req in required:
                        if req not in data:
                            return RoadbookMeta(
                                id=file_path.parent.name,
                                name="Invalid Roadbook",
                                version="?",
                                description="Missing required metadata fields.",
                                path=file_path,
                                valid=False,
                                error=f"Missing field: {req}"
                            )

                    return RoadbookMeta(
                        id=data.get('id', file_path.parent.name),
                        name=data.get('name', 'Unknown'),
                        version=str(data.get('version', '0.0.0')),
                        description=data.get('description', ''),
                        path=file_path,
                        sheets=sheets
                    )
            
            return RoadbookMeta(
                id=file_path.parent.name,
                name="Invalid Roadbook",
                version="?",
                description="No frontmatter found.",
                path=file_path,
                valid=False,
                error="No frontmatter found",
                sheets=sheets
            )
            
        except Exception as e:
            return RoadbookMeta(
                id=file_path.parent.name,
                name="Error",
                version="?",
                description=str(e),
                path=file_path,
                valid=False,
                error=str(e),
                sheets=[]
            )
