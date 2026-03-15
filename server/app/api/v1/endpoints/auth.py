from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

router = APIRouter()

@router.post("/login/access-token")
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Mock login
    if form_data.username == "admin" and form_data.password == "admin":
        return {
            "access_token": "mock_token_xyz",
            "token_type": "bearer"
        }
    raise HTTPException(status_code=400, detail="Incorrect email or password")
