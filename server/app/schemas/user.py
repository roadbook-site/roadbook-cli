from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: UUID
    api_key: Optional[str] = None

    class Config:
        from_attributes = True
