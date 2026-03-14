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

from .parser import RoadbookParser, RoadbookModel

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
    """List all roadbook markdown files in the working directory."""
    files = []
    # Recursively find .md files but exclude .git, node_modules etc if needed
    # For now, let's keep it simple: recursive glob
    for f in WORK_DIR.rglob("*.md"):
        # Return relative path
        try:
            rel_path = f.relative_to(WORK_DIR)
            files.append(str(rel_path).replace("\\", "/"))
        except:
            pass
            
    return {"files": sorted(files)}

@app.get("/api/roadbooks/{filename:path}")
async def get_roadbook(filename: str):
    """Get the content of a specific roadbook."""
    file_path = WORK_DIR / filename
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
    file_path = WORK_DIR / filename
    
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
        # Resolve the directory of the roadbook
        roadbook_dir = (WORK_DIR / path).parent
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
        "home_dir": str(Path.home())
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
    WORK_DIR = p
    
    # Update static mount if assets exist in new dir
    # Note: Fastapi static files mount is not easily dynamic. 
    # But since we mounted it at startup, it points to a specific path object.
    # If we want to support assets in new dir, we might need to recreate the app or mount another path.
    # For now, let's just update WORK_DIR. The /assets endpoint might still point to old dir 
    # unless we restart server. 
    # A workaround is to not use StaticFiles for assets but a custom endpoint that serves from WORK_DIR/assets
    
    return {"status": "success", "work_dir": str(WORK_DIR)}

# Custom file serving to support dynamic WORK_DIR and relative paths
@app.get("/api/files/{filepath:path}")
async def get_file(filepath: str):
    try:
        # Resolve to handle '..' in paths safely
        file_path = (WORK_DIR / filepath).resolve()
        work_dir_resolved = WORK_DIR.resolve()
        
        # Security check: ensure the resolved path is within WORK_DIR
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

def start_server(host: str = "127.0.0.1", port: int = 8000, work_dir: str = "."):
    global WORK_DIR
    WORK_DIR = Path(work_dir).resolve()
    
    # We remove the static mount for assets and use the dynamic endpoint above
    # if assets_path.exists():
    #    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
    
    print(f"Starting Roadbook Editor Server at http://{host}:{port}")
    print(f"Working directory: {WORK_DIR}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
