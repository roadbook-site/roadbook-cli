import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from ....core.db import get_db
from ....core.config import settings
from ....core.security import create_access_token
from ...deps import get_current_user_from_token, get_current_user_by_api_key
from ....crud.crud_user import user as user_crud
from ....schemas.user import UserCreate

router = APIRouter()

@router.get("/config")
async def get_auth_config():
    """Return public configuration required for authenticating with 3rd parties"""
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID
    }

@router.post("/login/google")
async def login_google(
    token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
) -> Any:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500, 
            detail="Google Login is not configured on the server. Missing GOOGLE_CLIENT_ID."
        )

    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        email = idinfo['email']
        name = idinfo.get('name', '')
        provider_id = idinfo['sub']
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google token: {str(e)}")

    user = await user_crud.get_by_email(db, email=email)
    if not user:
        user_in = UserCreate(
            email=email,
            full_name=name,
            provider="google",
            provider_id=provider_id,
            password=""  # Allow empty because of OAuth
        )
        user = await user_crud.create(db, obj_in=user_in)

    access_token = create_access_token(subject=str(user.id))
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email,
        "name": user.full_name
    }

@router.get("/me")
async def get_me(
    current_user = Depends(get_current_user_by_api_key)
) -> Any:
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "api_key": current_user.api_key,
    }

@router.post("/api-keys")
async def generate_api_key(
    current_user = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db)
) -> Any:
    api_key = f"rb-{secrets.token_urlsafe(32)}"
    current_user.api_key = api_key
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return {"api_key": current_user.api_key}

