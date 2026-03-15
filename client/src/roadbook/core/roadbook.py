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
    def get_search_paths() -> List[Path]:
        paths = []
        # Workspace (High priority)
        cwd = Path.cwd()
        # 1. Check .roadbook/ in cwd (New Structure: .roadbook/<id>)
        local_books = cwd / ".roadbook"
        if local_books.exists():
            paths.append(local_books)
        
        # 2. Check global books (Low priority)
        global_books = get_books_dir()
        if global_books.exists():
            paths.append(global_books)
            
        return paths

    @staticmethod
    def list_roadbooks() -> List[RoadbookMeta]:
        search_paths = RoadbookManager.get_search_paths()
        roadbooks = []
        seen_ids = set()
        
        for books_dir in search_paths:
            if not books_dir.exists():
                continue

            # Recursive search for roadbook.md
            # Exclude .core and other dot dirs except .roadbook itself (handled by caller)
            for rb_path in books_dir.rglob("roadbook.md"):
                # Skip hidden directories like .core inside books_dir
                if ".core" in str(rb_path):
                    continue
                    
                meta = RoadbookManager._parse_meta(rb_path)
                if meta.id not in seen_ids:
                    roadbooks.append(meta)
                    seen_ids.add(meta.id)
        
        return roadbooks

    @staticmethod
    def get_roadbook(rb_id: str) -> Optional[RoadbookMeta]:
        search_paths = RoadbookManager.get_search_paths()
        
        for books_dir in search_paths:
            # 1. Try direct path (standard structure: books/{id}/roadbook.md)
            direct_path = books_dir / rb_id / "roadbook.md"
            if direct_path.exists():
                meta = RoadbookManager._parse_meta(direct_path)
                if meta.id == rb_id:
                    return meta
            
            # 2. Search recursively if not found or ID mismatch
            for rb_path in books_dir.rglob("roadbook.md"):
                if rb_path == direct_path:
                    continue
                    
                # Optimization: Check if parent directory name matches ID
                if rb_path.parent.name == rb_id:
                    meta = RoadbookManager._parse_meta(rb_path)
                    if meta.id == rb_id:
                        return meta

            # 3. Full scan
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
            
            # Simple Frontmatter parser
            yaml_content = ""
            if content.startswith('---'):
                end_idx = content.find('---', 3)
                if end_idx != -1:
                    yaml_str = content[3:end_idx]
                    try:
                        data = yaml.safe_load(yaml_str)
                        if not isinstance(data, dict):
                             raise ValueError("YAML frontmatter must be a dictionary")
                    except yaml.YAMLError as e:
                        return RoadbookMeta(
                            id=file_path.parent.name,
                            name="Invalid YAML",
                            version="?",
                            description=str(e),
                            path=file_path,
                            valid=False,
                            error=f"YAML Error: {e}"
                        )

                    # Validate required fields
                    # id is optional, can be inferred from directory name
                    # name is required
                    
                    rb_id = data.get('id', file_path.parent.name)
                    name = data.get('name', 'Unknown')
                    version = str(data.get('version', '0.0.0'))
                    description = data.get('description', '')
                    
                    sheets = RoadbookManager._parse_sheets(content)
                    
                    return RoadbookMeta(
                        id=rb_id,
                        name=name,
                        version=version,
                        description=description,
                        path=file_path,
                        sheets=sheets
                    )
            
            # Fallback if no frontmatter or not starting with ---
            # Try to parse as pure YAML if file extension is .yaml/.yml? 
            # But standard is .md with frontmatter.
            
            return RoadbookMeta(
                id=file_path.parent.name,
                name="Invalid Roadbook",
                version="?",
                description="No frontmatter found.",
                path=file_path,
                valid=False,
                error="No frontmatter found",
                sheets=[]
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
