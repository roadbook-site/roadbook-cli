from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RoadbookBase(BaseModel):
    name: str
    description: Optional[str] = None
    version: str
    is_public: bool = True

class RoadbookCreate(RoadbookBase):
    id: str

class RoadbookUpdate(RoadbookBase):
    pass

class Roadbook(RoadbookBase):
    id: str
    author: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class RoadbookSearch(BaseModel):
    query: str
    limit: int = 10
