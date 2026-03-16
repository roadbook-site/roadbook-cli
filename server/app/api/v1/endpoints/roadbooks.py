from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import shutil
from pathlib import Path

from ....core.db import get_db
from ....core.config import settings
from ....schemas import roadbook as schemas
from .... import crud
from ...deps import get_current_user_by_api_key

router = APIRouter()

# Ensure storage directory exists
STORAGE_PATH = Path(settings.STORAGE_DIR)
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

@router.get("/", response_model=List[schemas.Roadbook])
async def read_roadbooks(
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    if q:
        roadbooks = await crud.roadbook.search(db, query=q, skip=skip, limit=limit)
    else:
        roadbooks = await crud.roadbook.get_multi(db, skip=skip, limit=limit)
    return roadbooks

@router.post("/", response_model=schemas.Roadbook)
async def create_roadbook(
    roadbook: schemas.RoadbookCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_by_api_key)
):
    # Check if exists
    existing = await crud.roadbook.get(db, id=roadbook.id)
    
    if existing:
        # Update existing
        return await crud.roadbook.update(db, db_obj=existing, obj_in=roadbook)
    
    # Create new
    user_id = getattr(current_user, "email", "admin")
    
    # Using model directly to inject author, or we can update schema
    from ....models.roadbook import Roadbook
    db_obj = Roadbook(
        **roadbook.model_dump(),
        author=user_id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/{roadbook_id}", response_model=schemas.Roadbook)
async def read_roadbook(
    roadbook_id: str,
    db: AsyncSession = Depends(get_db)
):
    roadbook = await crud.roadbook.get(db, id=roadbook_id)
    if roadbook is None:
        raise HTTPException(status_code=404, detail="Roadbook not found")
    return roadbook

@router.post("/{roadbook_id}/content")
def upload_roadbook_content(
    roadbook_id: str,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user_by_api_key)
):
    # Synchronous handler to run in thread pool
    file_location = STORAGE_PATH / f"{roadbook_id}.zip"
    with file_location.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "saved_at": str(file_location)}

@router.get("/{roadbook_id}/content")
def download_roadbook_content(
    roadbook_id: str
):
    file_location = STORAGE_PATH / f"{roadbook_id}.zip"
    if not file_location.exists():
        raise HTTPException(status_code=404, detail="Roadbook content not found")
    
    return FileResponse(
        path=file_location, 
        filename=f"{roadbook_id}.zip",
        media_type='application/zip'
    )
