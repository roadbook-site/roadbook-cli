import shutil
from pathlib import Path
from ..core.roadbook import RoadbookManager
from ..utils.output import print_info, print_error, print_success

def remove_book(args):
    """Remove a roadbook."""
    rb_id = args.id
    global_scope = getattr(args, 'global_scope', False)
    
    book = RoadbookManager.get_roadbook(rb_id, global_scope)
    
    if not book:
        scope_str = "global" if global_scope else "local"
        print_error(f"Roadbook '{rb_id}' not found in {scope_str} scope.")
        return

    book_dir = book.path.parent
    
    try:
        # Check if it's a symlink first to avoid deleting the target directory's contents
        if book_dir.is_symlink():
            print_info(f"Roadbook '{rb_id}' is a symlink. Unlinking instead of deleting.")
            book_dir.unlink()
            print_success(f"Successfully unlinked roadbook '{rb_id}'.")
        else:
            print_info(f"Deleting roadbook directory: {book_dir}")
            shutil.rmtree(book_dir)
            print_success(f"Successfully removed roadbook '{rb_id}'.")
    except Exception as e:
        print_error(f"Failed to remove roadbook '{rb_id}': {e}")
