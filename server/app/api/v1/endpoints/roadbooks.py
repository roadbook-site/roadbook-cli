from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import shutil
from pathlib import Path

from ....core.db import get_db
from ....core.config import settings
from ....schemas import roadbook as schemas
from .... import crud

router = APIRouter()

# Ensure storage directory exists
STORAGE_PATH = Path(settings.STORAGE_DIR)
STORAGE_PATH.mkdir(parents=True, exist_ok=True)

@router.get("/", response_model=List[schemas.Roadbook])
async def read_roadbooks(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    roadbooks = await crud.roadbook.get_multi(db, skip=skip, limit=limit)
    return roadbooks

@router.post("/", response_model=schemas.Roadbook)
async def create_roadbook(
    roadbook: schemas.RoadbookCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check if exists
    existing = await crud.roadbook.get(db, id=roadbook.id)
    
    if existing:
        # Update existing
        return await crud.roadbook.update(db, db_obj=existing, obj_in=roadbook)
    
    # Create new
    # We need to manually inject author for now as it is not in the schema
    # TODO: Get actual current user
    user_id = "admin"
    
    # Using model directly to inject author, or we can update schema
    # But to use CRUD.create, we need to pass the schema.
    # Let's customize create in crud_roadbook.py or just do it manually here.
    # Manually here is safer for now to avoid complex schema changes.
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
    file: UploadFile = File(...)
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
