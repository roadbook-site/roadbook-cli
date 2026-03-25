from ..core.roadbook import RoadbookManager
from ..utils.output import print_table, print_info, print_error

def list_books(args):
    global_scope = getattr(args, 'global_scope', False)
    books = RoadbookManager.list_roadbooks(global_scope)
    
    if not books:
        scope_str = "global " if global_scope else "local "
        print_info(f"No {scope_str}roadbooks found.")
        if global_scope:
            print_info("[Action] Put roadbook packages under ~/.roadbook/ or use 'roadbook link'.")
        else:
            print_info("[Action] Use 'roadbook init <name>' to create one in the current directory.")
        return

    headers = ["ID", "Name", "Version", "Description"]
    rows = []
    for book in books:
        rows.append([
            book.id,
            book.name,
            book.version,
            book.description[:50] + "..." if len(book.description) > 50 else book.description
        ])
    
    print_table(headers, rows)

def show_book(args):
    rb_id = args.id
    global_scope = getattr(args, 'global_scope', False)
    book = RoadbookManager.get_roadbook(rb_id, global_scope)
    
    if not book:
        scope_str = "global" if global_scope else "local"
        print_error(f"Roadbook '{rb_id}' not found in {scope_str} scope.")
        print_info(f"[Action] Use 'roadbook list{ ' -g' if global_scope else ''}' to view installed roadbooks.")
        return

    print_info(f"Roadbook Details: {book.id}")
    print(f"Name: {book.name}")
    print(f"Version: {book.version}")
    print(f"Description: {book.description}")
    # print(f"Path: {book.path}")
    
    # Check if script exists
    from ..core.runtime import RuntimeManager
    book_dir = book.path.parent
    
    # Check if we have a workspace copy
    import pathlib
    cwd = pathlib.Path.cwd()
    workspace_roadbook_dir = cwd / book.id
    if workspace_roadbook_dir.exists():
        book_dir = workspace_roadbook_dir
        
    script_path = RuntimeManager.find_script(book.id, book_dir=book_dir)
    
    if script_path:
        # Synchronization reminder
        RuntimeManager.check_sync_status(book.id, book_dir=book_dir)
        
        lang_map = {".py": "Python", ".js": "NodeJS", ".ts": "TypeScript"}
        lang_name = lang_map.get(script_path.suffix, "Unknown")
        print_info(f"[Action] Run automation script ({lang_name}): roadbook run {book.id}")
    else:
        print_info(f"[Action] No automation script found. Use 'roadbook init {book.id}' to generate scaffolding.")
    
    if not book.valid:
        print_error(f"Error: {book.error}")
