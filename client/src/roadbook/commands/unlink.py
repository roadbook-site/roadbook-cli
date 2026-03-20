import os
from pathlib import Path
from ..core.roadbook import RoadbookManager
from ..core.config import get_books_dir
from ..utils.output import print_info, print_error, print_success

def unlink_book(args):
    """Remove symlink of a roadbook from the global directory."""
    global_dir = get_books_dir()
    rb_id = getattr(args, 'id', None)
    
    if rb_id:
        target_link = global_dir / rb_id
        _unlink_target(target_link, rb_id)
    else:
        # If no ID is provided, try to unlink all local roadbooks from global
        local_books = RoadbookManager.list_roadbooks(global_scope=False)
        if not local_books:
            print_error("No local roadbooks found to unlink.")
            return
            
        for book in local_books:
            target_link = global_dir / book.id
            _unlink_target(target_link, book.id)

def _unlink_target(target_link: Path, rb_id: str):
    if not target_link.exists() and not target_link.is_symlink():
        print_info(f"No global link found for '{rb_id}'.")
        return
        
    if not target_link.is_symlink():
        print_error(f"Cannot unlink '{rb_id}'. It is a real directory in the global scope, not a symlink.")
        print_info(f"[Action] If you want to delete it, use 'roadbook remove {rb_id} -g'.")
        return
        
    try:
        target_link.unlink()
        print_success(f"Successfully unlinked '{rb_id}' from global directory.")
    except Exception as e:
        print_error(f"Failed to unlink '{rb_id}': {e}")
