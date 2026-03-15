from fastapi import APIRouter
from .endpoints import roadbooks, auth

api_router = APIRouter()
api_router.include_router(roadbooks.router, prefix="/roadbooks", tags=["roadbooks"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
