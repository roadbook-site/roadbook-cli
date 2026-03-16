import os
import asyncio
import uuid
from app.core.db import AsyncSessionLocal
from app import crud
from app.schemas.user import UserCreate

async def create_initial_user():
    async with AsyncSessionLocal() as db:
        user_in = UserCreate(
            username="admin",
            email="admin@roadbook.com",
            password=os.getenv("ADMIN_PASSWORD", "secret_password")
        )
        # Check if exists
        user = await crud.user.get_by_username(db, username=user_in.username)
        if not user:
            user = await crud.user.create(db, obj_in=user_in)
            print(f"User 'admin' created successfully: {user.id}")
        else:
            print(f"User 'admin' already exists: {user.id}")

if __name__ == "__main__":
    asyncio.run(create_initial_user())
