import os
import sys
from pathlib import Path
from ..core.roadbook import RoadbookManager
from ..core.config import get_books_dir
from ..utils.output import print_info, print_error, print_success

def link_book(args):
    """Symlink local roadbook to global directory."""
    global_dir = get_books_dir()
    
    # Ensure global directory exists
    global_dir.mkdir(parents=True, exist_ok=True)
    
    rb_id = getattr(args, 'id', None)
    
    # Get local roadbooks
    local_books = RoadbookManager.list_roadbooks(global_scope=False)
    
    if not local_books:
        print_error("No local roadbooks found to link.")
        print_info("[Action] Run 'roadbook init <name>' first.")
        return
        
    books_to_link = []
    if rb_id:
        # Find specific book
        for book in local_books:
            if book.id == rb_id:
                books_to_link.append(book)
                break
        if not books_to_link:
            print_error(f"Local roadbook '{rb_id}' not found.")
            return
    else:
        # Link all local books
        books_to_link = local_books
        
    for book in books_to_link:
        source_dir = book.path.parent.resolve()
        target_link = global_dir / book.id
        
        try:
            # Check if target already exists
            if target_link.exists() or target_link.is_symlink():
                if target_link.is_symlink():
                    existing_target = target_link.readlink()
                    if existing_target == source_dir:
                        print_info(f"Roadbook '{book.id}' is already linked.")
                        continue
                    else:
                        print_info(f"Overwriting existing link for '{book.id}'.")
                        target_link.unlink()
                else:
                    print_error(f"Cannot link '{book.id}'. A real directory already exists at {target_link}.")
                    continue
            
            # Create symlink
            # On Windows, creating directory symlinks might require admin privileges or Developer Mode.
            # Using junctions/symlinks: os.symlink with target_is_directory=True
            try:
                os.symlink(source_dir, target_link, target_is_directory=True)
                print_success(f"Successfully linked '{book.id}' -> {source_dir}")
            except OSError as e:
                if sys.platform == "win32" and getattr(e, 'winerror', 0) == 1314:
                    print_error(f"Failed to create symlink for '{book.id}' due to Windows permissions.")
                    print_info("[Action] Enable 'Developer Mode' in Windows settings, or run terminal as Administrator.")
                else:
                    raise
                    
        except Exception as e:
            print_error(f"Error linking '{book.id}': {e}")

