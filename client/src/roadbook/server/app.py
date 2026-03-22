from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from pathlib import Path
import shutil
import uvicorn

from ..core.parser import RoadbookParser, RoadbookModel

app = FastAPI(title="Roadbook Editor API")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser = RoadbookParser()

# We will set this when starting the server
WORK_DIR = Path.cwd()
MODE = "default"

# Static directory for UI
STATIC_DIR = Path(__file__).parent / "static"

@app.get("/")
async def read_index():
    """Serve the editor UI."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Editor UI not found. Please ensure static files are installed."}

@app.get("/api/roadbooks")
async def list_roadbooks():
    """List roadbook.md files with depth limit."""
    files = []
    max_depth = 3
    target_name = "roadbook.md"
    
    # Use os.walk for better control over depth
    for root, dirs, filenames in os.walk(WORK_DIR):
        # Calculate depth
        try:
            rel_dir = Path(root).relative_to(WORK_DIR)
            depth = len(rel_dir.parts)
            if str(rel_dir) == ".": depth = 0
        except ValueError:
            continue

        if depth >= max_depth:
            dirs[:] = [] # Stop recursing
            continue
            
        # Ignore hidden directories like .git, .venv, node_modules
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
        
        for filename in filenames:
            if filename.lower() == target_name:
                try:
                    file_path = Path(root) / filename
                    # Return path relative to WORK_DIR to keep it short in UI
                    # (Web will use it as relative path to call back APIs)
                    rel_path = file_path.relative_to(WORK_DIR)
                    files.append(str(rel_path).replace("\\", "/"))
                except:
                    pass
            
    return {"files": sorted(files)}

@app.get("/api/roadbooks/{filename:path}")
async def get_roadbook(filename: str):
    """Get the content of a specific roadbook."""
    # Handle absolute path or relative to WORK_DIR
    file_path = Path(filename)
    if not file_path.is_absolute():
        file_path = WORK_DIR / filename
        
    if file_path.is_dir() and (file_path / "roadbook.md").exists():
        file_path = file_path / "roadbook.md"
        
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        model = parser.parse(content)
        return model
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/roadbooks/{filename:path}")
async def save_roadbook(filename: str, data: RoadbookModel):
    """Save the roadbook content."""
    file_path = Path(filename)
    if not file_path.is_absolute():
        file_path = WORK_DIR / filename
        
    if file_path.is_dir() and (file_path / "roadbook.md").exists():
        file_path = file_path / "roadbook.md"
    
    try:
        # Generate markdown content
        content = parser.dump(data)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return {"status": "success", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    path: Optional[str] = None
):
    """Upload an image to the assets directory of the specific roadbook."""
    if path:
        # Resolve the directory of the roadbook. 
        # Path(path) handles absolute paths correctly (ignoring WORK_DIR if absolute)
        # If relative, it joins with WORK_DIR.
        roadbook_path = Path(path)
        if not roadbook_path.is_absolute():
            roadbook_path = WORK_DIR / path
            
        roadbook_dir = roadbook_path.parent
        assets_dir = roadbook_dir / "assets"
    else:
        assets_dir = WORK_DIR / "assets"
        
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    file_location = assets_dir / file.filename
    
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"filename": file.filename, "url": f"./assets/{file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get server configuration."""
    return {
        "work_dir": str(WORK_DIR),
        "home_dir": str(Path.home()),
        "mode": MODE
    }

@app.post("/api/chdir")
async def change_dir(data: Dict[str, str]):
    """Change working directory."""
    new_path = data.get("path")
    if not new_path:
         raise HTTPException(status_code=400, detail="Path is required")
         
    p = Path(new_path)
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=400, detail="Directory does not exist")
        
    global WORK_DIR
    WORK_DIR = p.resolve()
    
    return {"status": "success", "work_dir": str(WORK_DIR)}

# Custom file serving to support dynamic WORK_DIR and absolute paths
@app.get("/api/files/{filepath:path}")
async def get_file(filepath: str):
    try:
        # Resolve to handle '..' in paths safely
        # If filepath is absolute, (WORK_DIR / filepath) equals filepath (on Windows/Posix).
        # We need to be careful about what we serve.
        file_path = Path(filepath)
        
        if not file_path.is_absolute():
            file_path = (WORK_DIR / filepath).resolve()
        else:
            file_path = file_path.resolve()

        work_dir_resolved = WORK_DIR.resolve()
        
        # Security check: ensure the resolved path is within WORK_DIR OR we are in a permissive mode?
        # Since we changed list_roadbooks to potentially return absolute paths inside subfolders of WORK_DIR,
        # checking startswith(WORK_DIR) should still pass for those files.
        # But if the user provides an absolute path to C:\Windows\System32... we probably should block it.
        # So maintaining the check is safer, assuming list_roadbooks only returns files under WORK_DIR.
        
        if not str(file_path).startswith(str(work_dir_resolved)):
             # Allow if file_path is exactly what we listed?
             # For now, let's keep the restriction. If list_roadbooks scans WORK_DIR recursively,
             # all valid roadbooks are inside WORK_DIR.
             pass
             # But wait, verify strictness. 
             # If work_dir is C:\Users\zds\ and file is C:\Users\zds\.roadbook\book.md -> OK.
             
        if not str(file_path).startswith(str(work_dir_resolved)):
             raise HTTPException(status_code=403, detail="Access denied")
            
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")

@app.get("/assets/{filename:path}")
async def get_asset(filename: str):
    # Fallback for old references
    file_path = WORK_DIR / "assets" / filename
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Asset not found")

def start_server(host: str = "127.0.0.1", port: int = 8000, work_dir: str = ".", mode: str = "default"):
    global WORK_DIR, MODE
    WORK_DIR = Path(work_dir).resolve()
    MODE = mode
    
    # We remove the static mount for assets and use the dynamic endpoint above
    # if assets_path.exists():
    #    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    
    print(f"Starting Roadbook Editor Server at http://{host}:{port}")
    print(f"Working directory: {WORK_DIR}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
