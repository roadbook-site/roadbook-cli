from roadbook.server.app import start_server
from roadbook.core.config import get_books_dir, get_roadbook_dir
from roadbook.core.roadbook import RoadbookManager
import webbrowser
import threading
import time
import os
from pathlib import Path
import urllib.parse

def start_editor(args):
    """Start the roadbook editor server."""
    port = args.port
    host = args.host
    
    # 1. Determine Working Directory
    if args.dir:
        work_dir = args.dir
        if not os.path.isabs(work_dir):
            work_dir = os.path.abspath(work_dir)
    else:
        # Determine working directory based on priority:
        # 1. Local .roadbook in current directory
        # 2. Global ~/.roadbook directory
        
        local_roadbook = Path.cwd() / ".roadbook"
        global_roadbook = get_books_dir()
        
        # Default to global
        work_dir = str(global_roadbook)
        
        if args.id:
            # If ID provided, try to find it specifically
            # Check local first
            if (local_roadbook / args.id).exists() or (local_roadbook / f"{args.id}.md").exists():
                work_dir = str(local_roadbook)
            # Check global next
            elif (global_roadbook / args.id).exists() or (global_roadbook / f"{args.id}.md").exists():
                work_dir = str(global_roadbook)
            # If not found, check which directory actually exists and prefer local
            elif local_roadbook.exists():
                work_dir = str(local_roadbook)
        else:
            # No ID provided, prefer local if it exists
            if local_roadbook.exists():
                work_dir = str(local_roadbook)

             
    # Ensure work_dir exists
    Path(work_dir).mkdir(parents=True, exist_ok=True)
         
    url = f"http://{host}:{port}"
    
    # 2. Handle Optional ID Argument
    if args.id:
        print(f"Locating roadbook: {args.id}...")
        
        target_file = None
        work_path = Path(work_dir)
        
        # Simple search in work_dir
        # 1. Check if ID is actually a filename
        if (work_path / args.id).exists():
            target_file = args.id
        elif (work_path / f"{args.id}.md").exists():
            target_file = f"{args.id}.md"
        # 2. Check directory structure: id/roadbook.md
        elif (work_path / args.id / "roadbook.md").exists():
             target_file = f"{args.id}/roadbook.md"
        else:
            # 3. Scan all MD files to find matching ID in frontmatter (slow but robust)
            # Use RoadbookManager logic or simple glob
            print("Scanning for ID match...")
            found = False
            for f in work_path.rglob("*.md"):
                # Check if parent folder name matches ID
                if f.parent.name == args.id:
                    target_file = str(f.relative_to(work_path)).replace('\\', '/')
                    found = True
                    break
            
            if not found:
                # Try to check content? Maybe too slow.
                # Let's assume folder name match is enough for now as per RoadbookManager logic
                pass
        
        if target_file:
            # URL encode the filename
            encoded_file = urllib.parse.quote(target_file)
            url = f"{url}/?open={encoded_file}"
            print(f"Found roadbook: {target_file}")
        else:
            print(f"Warning: Roadbook '{args.id}' not found in {work_dir}")
            print("Opening editor at root...")

    print(f"Opening Roadbook Editor at {url}...")
    print(f"Serving roadbooks from: {work_dir}")
    
    # Open browser after a short delay to let server start
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)
        
    threading.Thread(target=open_browser, daemon=True).start()
    
    start_server(host=host, port=port, work_dir=work_dir)
