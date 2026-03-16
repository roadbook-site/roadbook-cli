from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import jwt

from ..core.db import get_db
from ..core.config import settings
from ..models.user import User

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token", auto_error=False)

async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token (for Web UI)."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return user

async def get_current_user_by_api_key(
    api_key_header: str = Depends(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Validate the Bearer token or API key from the Authorization header.
    Expects format: 'Bearer {api_key}'
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    # Normally the client sends: Authorization: Bearer <api_key>
    if api_key_header.startswith("Bearer "):
        api_key_or_token = api_key_header.replace("Bearer ", "")
    else:
        api_key_or_token = api_key_header
        
    try:
        payload = jwt.decode(api_key_or_token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            if user:
                return user
    except jwt.PyJWTError:
        pass

    result = await db.execute(select(User).where(User.api_key == api_key_or_token))
    user = result.scalars().first()
    
    if not user:
        # Mock behavior for development until real user DB is heavily used
        # We can accept "mock_token_xyz" or a dummy key to bypass hard checks
        if api_key_or_token in ("mock_token_xyz", "admin_api_key"):
            import uuid
            return User(id=uuid.uuid4(), email="admin@example.com", api_key=api_key_or_token, full_name="Admin")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
        
    return user
