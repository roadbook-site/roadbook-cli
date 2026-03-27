import json
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
    
    # Parse and Display Schemas
    scripts_dir = book_dir / "scripts"
    input_schema_path = scripts_dir / "input_schema.json"
    output_schema_path = scripts_dir / "output_schema.json"
    
    if input_schema_path.exists():
        try:
            with open(input_schema_path, "r", encoding="utf-8") as f:
                input_schema = json.load(f)
            
            print("\n[Input Schema]")
            properties = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            if properties:
                headers = ["Field", "Type", "Required", "Description"]
                rows = []
                for key, prop in properties.items():
                    is_required = "Yes" if key in required else "No"
                    desc = prop.get("description", "")
                    # Append default value to description if present
                    if "default" in prop:
                        desc += f" (Default: {prop['default']})"
                    rows.append([key, prop.get("type", "any"), is_required, desc])
                print_table(headers, rows)
            else:
                print("  No input properties defined.")
        except Exception as e:
            print_error(f"Failed to parse input schema: {e}")
            
    if output_schema_path.exists():
        try:
            with open(output_schema_path, "r", encoding="utf-8") as f:
                output_schema = json.load(f)
                
            print("\n[Output Schema]")
            properties = output_schema.get("properties", {})
            if properties:
                headers = ["Field", "Type", "Description"]
                rows = []
                for key, prop in properties.items():
                    rows.append([key, prop.get("type", "any"), prop.get("description", "")])
                print_table(headers, rows)
            else:
                print("  No output properties defined.")
        except Exception as e:
            print_error(f"Failed to parse output schema: {e}")
            
    print("")

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
