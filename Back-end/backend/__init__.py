"""
AIVA AI Video Platform Backend Module
=====================================

This module contains all the core functionality extracted from main.py,
organized into logical sections by functionality.
"""
import asyncio
from .config import app, engine, Base, async_session
from .models import *
from .auth import verify_password, get_password_hash, create_access_token
from .routes import *

# Database initialization
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables initialized")

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Shutting down backend...")

__all__ = [
    'app',
    'engine',
    'Base',
    'async_session',
    'verify_password',
    'get_password_hash',
    'create_access_token',
]
