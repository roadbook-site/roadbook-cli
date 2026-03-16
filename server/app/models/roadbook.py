from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
import uuid
from ..core.db import Base

class Roadbook(Base):
    __tablename__ = "roadbooks"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    version = Column(String)
    author = Column(String)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Vector embedding for semantic search (e.g. 1536 dimensions for OpenAI ada-002)
    embedding = Column(Vector(1536))

