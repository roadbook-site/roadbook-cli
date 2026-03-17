from roadbook.server.app import start_server
from roadbook.core.config import get_books_dir, get_roadbook_dir
from roadbook.core.roadbook import RoadbookManager
import webbrowser
import threading
import time
import os
from pathlib import Path
import urllib.parse
import urllib.request
import socket
import json

def is_port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def is_roadbook_service(host, port):
    try:
        url = f"http://{host}:{port}/"
        with urllib.request.urlopen(url, timeout=0.5) as response:
            if response.status == 200:
                content = response.read(4096).decode('utf-8', errors='ignore')
                return "<title>Roadbook Explorer</title>" in content
    except:
        pass
    return False

def update_server_workdir(host, port, work_dir):
    try:
        url = f"http://{host}:{port}/api/chdir"
        data = json.dumps({"path": work_dir}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status == 200
    except Exception as e:
        print(f"Failed to update remote server directory: {e}")
        return False


def start_editor(args):
    """Start the roadbook editor server."""
    start_port = args.port
    host = args.host
    
    port = start_port
    reuse_instance = False
    max_retries = 20
    
    # Check for available port ONLY (No reuse as requested)
    for p in range(start_port, start_port + max_retries):
        if not is_port_in_use(host, p):
             port = p
             break
    else:
        print(f"Error: Could not find an available port in range {start_port}-{start_port + max_retries}")
        return

    # 1. Determine Working Directory
    if args.dir:
        work_dir = args.dir
        if not os.path.isabs(work_dir):
            work_dir = os.path.abspath(work_dir)
    else:
        # Determine working directory based on priority:
        # 1. Local .roadbook in current directory
        # 2. If no local .roadbook, use current directory directly? 
        #    The user requested "use current directory as starting point".
        #    But roadbook server expects a root containing .md files.
        #    If current dir has .roadbook folder, use that as root? No, usually parent.
        
        # Rule:
        # If .roadbook exists in CWD, serve CWD/.roadbook
        # Else, serve CWD directly (so users can see MD files in CWD) or global?
        # Standard behavior: Roadbook files are in a .roadbook folder usually.
        # But for viewing arbitrary MDs, CWD is better.
        
        cwd = Path.cwd()
        local_roadbook = cwd / ".roadbook"
        global_roadbook = get_books_dir()
        
        if local_roadbook.exists():
             work_dir = str(local_roadbook)
        elif (cwd / ".git").exists() or any(cwd.glob("*.md")):
             # If it looks like a project root, use it?
             # But the server recursively scans.
             # Let's default to global ONLY if explicit ID requires it, otherwise use CWD if it seems relevant.
             # Actually, the user's request "use current directory as starting point" implies they want CWD to be the root.
             # But usually roadbooks are in .roadbook/.
             
             # Compromise:
             # If .roadbook exists, root is .roadbook.
             # Else root is Global.
             
             # WAIT, user said "roadbook init ... take current directory".
             # And "roadbook edit ... take current directory".
             
             # If I run `roadbook edit` in `C:\MyProject`, I expect to see roadbooks relevant to MyProject.
             # If `C:\MyProject\.roadbook` exists, show that.
             # If NOT, maybe show `C:\MyProject`?
             
             # Let's stick to the convention: Roadbooks are in `.roadbook`.
             # If `.roadbook` exists in CWD, use it.
             # If NOT, use GLOBAL.
             
             # BUT, the user issue was: "click a roadbook... relative path...".
             # If the server is at `C:\code_dev...` and I open `books/my-test/roadbook.md` (which is in global),
             # then the server MUST be at global for that link to work.
             
             # If the user provides an ID that is found in Global but not Local, 
             # we MUST set root to Global.
             pass

        # Updated Priority:
        # 1. If ID provided:
        #    a. Check Local .roadbook
        #    b. Check Global .roadbook
        #    c. Set work_dir to where it was found.
        # 2. If NO ID provided:
        #    a. If Local .roadbook exists -> Local
        #    b. Else -> Global
        
        work_dir = str(global_roadbook) # Default
        mode = "Global"
        
        if args.id:
            # Check local first
            if (local_roadbook / args.id).exists() or (local_roadbook / f"{args.id}.md").exists():
                work_dir = str(local_roadbook)
                mode = "Local (.roadbook)"
            # Check global next
            elif (global_roadbook / args.id).exists() or (global_roadbook / f"{args.id}.md").exists():
                work_dir = str(global_roadbook)
                mode = "Global (User Home)"
            # Check CWD for direct file match ?
            elif (cwd / args.id).exists():
                 # If user passed a relative path to a file in CWD
                 # e.g. roadbook edit mybook.md
                 work_dir = str(cwd)
                 mode = "Current Directory"
        else:
            if local_roadbook.exists():
                work_dir = str(local_roadbook)
                mode = "Local (.roadbook)"
        
        print(f"Roadbook Editor starting in [{mode}] mode.")
        print(f"Serving directory: {work_dir}")

             
    # Ensure work_dir exists
    Path(work_dir).mkdir(parents=True, exist_ok=True)
         
    url = f"http://{host}:{port}"
    
    # 2. Handle Optional ID Argument
    if args.id:
        print(f"Locating roadbook: {args.id}...")
        
        target_file = None
        work_path = Path(work_dir)
        
        # Simple search in work_dir
        # 1. Check if ID is likely a relative or absolute path
        p = Path(args.id)
        if p.is_absolute():
            # If absolute, verify it's inside work_dir? The new logic allows absolute paths if server supports it.
            # But the server (app.py) checks if file is inside WORK_DIR for security. 
            # So we should ensure it stays within WORK_DIR, or broaden WORK_DIR.
            # But earlier logic defines WORK_DIR based on finding .roadbook or Global.
            # If the absolute path is completely unrelated, the server might reject it (403).
            # But assuming the user uses ID which usually implies lookup OR a path they know is there.
            
            # Let's just use absolute path.
             target_file = str(p.resolve()).replace("\\", "/")
             
        elif (work_path / args.id).exists():
            # Use absolute path
             target_abs = (work_path / args.id).resolve()
             if target_abs.is_file():
                 target_file = str(target_abs).replace("\\", "/")
             elif (target_abs / "roadbook.md").exists():
                 target_file = str((target_abs / "roadbook.md").resolve()).replace("\\", "/")
                 
        elif (work_path / f"{args.id}.md").exists():
             target_file = str((work_path / f"{args.id}.md").resolve()).replace("\\", "/")
            
        elif args.id.endswith(".md") and (work_path / args.id).exists():
             target_file = str((work_path / args.id).resolve()).replace("\\", "/")

        else:
            # 3. Scan all MD files
            print("Scanning for ID match...")
            found = False
            for f in work_path.rglob("*.md"):
                # Check if parent folder matches ID or filename (minus .md) matches ID
                if f.parent.name == args.id or f.stem == args.id:
                     # Use absolute path
                     target_file = str(f.resolve()).replace('\\', '/')
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
        print(f"Warning: Roadbook '{args.id}' not found in {work_dir}")
        print("Opening editor at root...")
        url = f"http://{host}:{port}/?open={args.id if args.id else ''}"

    print(f"Opening Roadbook Editor at {url}...")
    print(f"Roadbook Editor starting in [{mode}] mode.")
    print(f"Serving roadbooks from: {work_dir}")
    
    # Open browser after a short delay to let server start
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)
        
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Pass 'mode' to server
    start_server(host=host, port=port, work_dir=work_dir, mode=mode)
