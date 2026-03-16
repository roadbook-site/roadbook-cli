from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .core.config import settings
from .core.db import engine, Base
from .api.v1.api import api_router
from . import models  # Import models to register them with Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print(f"API Prefix: {settings.API_V1_STR}")
    print("Routes:")
    for route in app.routes:
        print(f"Path: {route.path} Name: {route.name}")
        
    yield

app = FastAPI(
    title=settings.PROJECT_NAME, 
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/login")
async def login_page():
    # Serve our simple website at /login
    return FileResponse("static/index.html")

@app.get("/")
async def root():
    return {"message": "Welcome to Roadbook Server"}

@app.get("/ping")
async def ping():
    return {"message": "pong"}
