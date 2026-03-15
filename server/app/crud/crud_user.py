from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from .base import CRUDBase
from ..models.roadbook import User
from ..schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()
    
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalars().first()
        
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        obj_in_data = obj_in.model_dump()
        password = obj_in_data.pop("password")
        hashed_password = pwd_context.hash(password)
        db_obj = User(**obj_in_data, hashed_password=hashed_password)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

user = CRUDUser(User)
