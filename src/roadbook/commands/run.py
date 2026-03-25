import time
import os
import subprocess
import sys
import json
from pathlib import Path
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

    # Check workspace copy first for listing history
    cwd = Path.cwd()
    workspace_dir = cwd / rb_id
    target_dir = workspace_dir if workspace_dir.exists() else book.path.parent

    runs = RuntimeManager.list_runs(rb_id, book_dir=target_dir)
    if not runs:
        print_info(f"No run history for {rb_id}.")
        print_info("[Action] Start a session with 'roadbook run <id>'.")
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

def _find_run(run_id):
    """Helper to find a run across all roadbooks, checking workspace copies first."""
    books = RoadbookManager.list_roadbooks()
    cwd = Path.cwd()
    
    for book in books:
        # 1. Check workspace copy first (Priority)
        workspace_dir = cwd / book.id
        if workspace_dir.exists():
            r = RuntimeManager.get_run(book.id, run_id, book_dir=workspace_dir)
            if r:
                return r, book, workspace_dir
        
        # 2. Check original book location
        r = RuntimeManager.get_run(book.id, run_id, book_dir=book.path.parent)
        if r:
            return r, book, book.path.parent
            
    return None, None, None

def run_inspect(args):
    run_id = args.run_id
    
    found_run, found_book, book_dir = _find_run(run_id)
    
    if not found_run:
        print_error(f"Run ID '{run_id}' not found in any local roadbook.")
        print_info("[Action] Use 'roadbook logs list <id>' to find available run IDs.")
        return

    print_info(f"Inspecting Run: {run_id} (Book: {found_book.id})")
    print(f"Status: {found_run['status']}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(found_run['timestamp']))}")
    print(f"Details: {found_run.get('details')}")
    
    # Synchronization reminder
    RuntimeManager.check_sync_status(found_book.id, book_dir=book_dir)
    
    run_dir = RuntimeManager.get_runs_dir(found_book.id, book_dir=book_dir) / run_id
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
    cwd = Path.cwd()
    
    for book in books:
        # Check workspace copy
        workspace_dir = cwd / book.id
        target_dirs = [workspace_dir] if workspace_dir.exists() else []
        target_dirs.append(book.path.parent)
        
        for d in target_dirs:
            run = RuntimeManager.get_last_run(book.id, book_dir=d)
            if run:
                if latest_run is None or run['timestamp'] > latest_run['timestamp']:
                    latest_run = run
                    latest_book_id = book.id
    
    if not latest_run:
        print_info("No runs found in any roadbook.")
        print_info("[Action] Start a session with 'roadbook run <id>'.")
        return

    print_info(f"Last Run (Book: {latest_book_id}):")
    print(f"ID: {latest_run['id']}")
    print(f"Status: {latest_run['status']}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest_run['timestamp']))}")
    print(f"Details: {latest_run.get('details')}")
    print_info(f"[Action] Use 'roadbook logs inspect {latest_run['id']}' for full details.")

def run_cat(args):
    run_id = args.run_id
    found_run, found_book, book_dir = _find_run(run_id)
    
    if not found_run:
        print_error(f"Run ID '{run_id}' not found.")
        return

    run_dir = RuntimeManager.get_runs_dir(found_book.id, book_dir=book_dir) / run_id
    log_file = run_dir / "run.log"
    
    if not log_file.exists():
        print_error(f"Log file not found: {log_file}")
        print_info("[Note] Logs are only available for runs executed with updated CLI.")
        return
        
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            print(f.read())
    except Exception as e:
        print_error(f"Failed to read log file: {e}")

def run_show(args):
    run_id = args.run_id
    found_run, found_book, book_dir = _find_run(run_id)
    
    if not found_run:
        print_error(f"Run ID '{run_id}' not found.")
        return
        
    print_info(f"Run Details: {run_id}")
    print(f"  Roadbook: {found_book.id}")
    print(f"  Status:   {found_run['status']}")
    print(f"  Time:     {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(found_run['timestamp']))}")
    
    details = found_run.get('details', {})
    
    if args.error:
        print_info("\n[Error Diagnosis]")
        error_msg = details.get('error')
        if error_msg:
            print_error(error_msg)
        else:
            if found_run['status'] == 'failed':
                print_info("Run failed but no specific error message recorded in metadata.")
                print_info("[Action] Try 'roadbook logs cat <run_id>' to see full logs.")
            else:
                print_info("No error recorded (Status is success).")
    else:
        print(f"  Details:  {json.dumps(details, indent=2, ensure_ascii=False)}")
        print_info("\n[Action] Use '--error' to highlight error stack, or 'logs cat' to view full logs.")
