import os
import re
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from ..core.roadbook import RoadbookManager
from ..core.runtime import RuntimeManager
from ..core.scaffold import ScaffoldManager
from ..utils.output import console, print_error, print_success
from ..core.i18n import t
from . import editor
import argparse

def _generate_id(name: str) -> str:
    """Generate a valid ID from the roadbook name."""
    # Convert to lowercase
    id_str = name.lower()
    # Replace spaces and underscores with hyphens
    id_str = re.sub(r'[\s_]+', '-', id_str)
    # Remove any non-alphanumeric characters except hyphens
    id_str = re.sub(r'[^a-z0-9\-]', '', id_str)
    # Remove duplicate hyphens
    id_str = re.sub(r'-+', '-', id_str)
    # Strip leading/trailing hyphens
    id_str = id_str.strip('-')
    return id_str

def init_book(args):
    """Initialize a new roadbook scaffold."""
    name = args.name
    description = args.description
    entry_url = args.entry_url
    global_scope = getattr(args, 'global_scope', False)
    
    rb_id = _generate_id(name)
    if not rb_id:
        print_error("Invalid roadbook name. Cannot generate a valid ID.")
        return
        
    # Check for duplicates
    existing_books = RoadbookManager.list_roadbooks(global_scope)
    for book in existing_books:
        if book.id == rb_id:
            print_error(f"A roadbook with ID '{rb_id}' already exists at {book.path.parent}.")
            return

    if global_scope:
        from ..core.config import get_books_dir
        work_dir = get_books_dir()
    else:
        # Create directory structure in current workspace
        cwd = Path.cwd()
        work_dir = cwd
        
    book_dir = work_dir / rb_id
    
    try:
        if not work_dir.exists():
            print(f"Initializing directory at {work_dir}")
            work_dir.mkdir(parents=True, exist_ok=True)
            
        # Use centralized scaffold manager
        paths = ScaffoldManager.create_roadbook_scaffold(book_dir, rb_id, name, description, entry_url)
        with open(paths["roadbook_file"], "r", encoding="utf-8") as f:
            roadbook_content = f.read()
        ScaffoldManager.create_script_scaffold(book_dir, "python", rb_id, name, roadbook_content)
        
    except Exception as e:
        print_error(f"Failed to initialize roadbook: {e}")
        return

    print_success(t("init_success", name=name, rb_id=rb_id))
    console.print(t("init_dir", book_dir=book_dir))
    
    # Handle auto-edit
    if args.edit:
        console.print(t("launch_editor"))
        # Construct arguments for editor
        editor_args = argparse.Namespace(
            port=8000, 
            host="127.0.0.1", 
            dir=str(book_dir),
            id=rb_id
        )
        editor.start_editor(editor_args)
        return

    # Constructing AI Agent feedback prompt
    feedback_lines = [
        t("ai_feedback_scaffold_gen", book_dir=book_dir)
    ]
    
    if description:
        feedback_lines.extend([
            t("ai_feedback_mode_ai"),
            t("ai_feedback_next_steps"),
            t("ai_feedback_ai_step1"),
            t("ai_feedback_ai_step2"),
            t("ai_feedback_ai_step3")
        ])
    else:
        feedback_lines.extend([
            t("ai_feedback_mode_manual"),
            t("ai_feedback_next_steps"),
            t("ai_feedback_manual_step1"),
            t("ai_feedback_manual_step2", rb_id=rb_id),
            t("ai_feedback_manual_step3"),
            t("ai_feedback_manual_step4")
        ])
        
    feedback_text = "\n".join(feedback_lines)
    console.print(Panel(feedback_text, title=t("ai_feedback_title"), border_style="yellow"))
