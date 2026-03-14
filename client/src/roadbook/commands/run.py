import time
import os
import subprocess
import sys
from ..core.roadbook import RoadbookManager
from ..core.runtime import RuntimeManager
from ..utils.output import print_table, print_info, print_error

def run_history(args):
    rb_id = args.id
    book = RoadbookManager.get_roadbook(rb_id)
    if not book:
        print_error(f"Roadbook '{rb_id}' not found.")
        print_info("[Action] Use 'roadbook list' to view installed roadbooks.")
        return

    runs = RuntimeManager.list_runs(rb_id, book_dir=book.path.parent)
    if not runs:
        print_info(f"No run history for {rb_id}.")
        print_info("[Action] Start a session with 'roadbook open <id>' or execute with 'roadbook run <id>'.")
        return

    print_info(f"Run History for {rb_id}:")
    headers = ["Run ID", "Status", "Time", "Details"]
    rows = []
    for r in runs:
        ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r['timestamp']))
        # Summarize details
        detail_str = str(r.get('details', {}))
        if len(detail_str) > 50:
            detail_str = detail_str[:47] + "..."
        
        rows.append([r['id'], r['status'], ts_str, detail_str])
    
    print_table(headers, rows)

def run_inspect(args):
    run_id = args.run_id
    
    found_run = None
    found_book = None
    
    books = RoadbookManager.list_roadbooks()
    for book in books:
        r = RuntimeManager.get_run(book.id, run_id, book_dir=book.path.parent)
        if r:
            found_run = r
            found_book = book
            break
    
    if not found_run:
        print_error(f"Run ID '{run_id}' not found in any local roadbook.")
        print_info("[Action] Use 'roadbook logs list <id>' to find available run IDs.")
        return

    print_info(f"Inspecting Run: {run_id} (Book: {found_book.id})")
    print(f"Status: {found_run['status']}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(found_run['timestamp']))}")
    print(f"Details: {found_run.get('details')}")
    
    run_dir = RuntimeManager.get_runs_dir(found_book.id, book_dir=found_book.path.parent) / run_id
    print(f"Directory: {run_dir}")
    print_info("[Action] Opening run directory...")
    
    # Open folder
    if sys.platform == 'win32':
        os.startfile(run_dir)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', run_dir])
    else:
        subprocess.Popen(['xdg-open', run_dir])

def run_last(args):
    books = RoadbookManager.list_roadbooks()
    latest_run = None
    latest_book_id = None
    
    for book in books:
        run = RuntimeManager.get_last_run(book.id, book_dir=book.path.parent)
        if run:
            if latest_run is None or run['timestamp'] > latest_run['timestamp']:
                latest_run = run
                latest_book_id = book.id
    
    if not latest_run:
        print_info("No runs found in any roadbook.")
        print_info("[Action] Start a session with 'roadbook open <id>' or execute with 'roadbook run <id>'.")
        return

    print_info(f"Last Run (Book: {latest_book_id}):")
    print(f"ID: {latest_run['id']}")
    print(f"Status: {latest_run['status']}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest_run['timestamp']))}")
    print(f"Details: {latest_run.get('details')}")
    print_info(f"[Action] Use 'roadbook logs inspect {latest_run['id']}' for full details.")
