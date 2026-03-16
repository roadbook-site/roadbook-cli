from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: Optional[str] = None
    provider: Optional[str] = None
    provider_id: Optional[str] = None

class UserUpdate(UserBase):
    password: Optional[str] = None
    full_name: Optional[str] = None

class User(UserBase):
    id: UUID
    api_key: Optional[str] = None
    provider: Optional[str] = None

    class Config:
        from_attributes = True
