import time
from ..core.roadbook import RoadbookManager
from ..core.runtime import RuntimeManager
from ..utils.output import print_table, print_info, print_error

def script_ls(args):
    rb_id = args.id
    global_scope = getattr(args, 'global_scope', False)
    book = RoadbookManager.get_roadbook(rb_id, global_scope)
    if not book:
        scope_str = "global" if global_scope else "local"
        print_error(f"Roadbook '{rb_id}' not found in {scope_str} scope.")
        print_info(f"[Action] Use 'roadbook list{ ' -g' if global_scope else ''}' to view installed roadbooks.")
        return

    scripts = RuntimeManager.list_scripts(rb_id, book_dir=book.path.parent)
    
    if not scripts:
        print_info(f"No scripts found for {rb_id}.")
        print_info(f"[Action] Run 'roadbook run {rb_id}' to trigger semantic guide mode and generate candidate scripts.")
        return

    print_info(f"Scripts for {rb_id}:")
    headers = ["Name", "Lang", "Size (bytes)", "Last Modified"]
    rows = []
    for s in scripts:
        mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(s['mtime']))
        rows.append([s['name'], s['lang'], str(s['size']), mtime_str])
    
    print_table(headers, rows)

def script_clean(args):
    rb_id = args.id
    global_scope = getattr(args, 'global_scope', False)
    book = RoadbookManager.get_roadbook(rb_id, global_scope)
    if not book:
        scope_str = "global" if global_scope else "local"
        print_error(f"Roadbook '{rb_id}' not found in {scope_str} scope.")
        print_info(f"[Action] Use 'roadbook list{ ' -g' if global_scope else ''}' to view installed roadbooks.")
        return

    RuntimeManager.clean_scripts(rb_id, book_dir=book.path.parent)
    print_info(f"Cleaned scripts for {rb_id}.")
    print_info("[Action] Use 'roadbook script ls <id>' to verify current script cache.")
