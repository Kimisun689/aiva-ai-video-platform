"""
AI Video Generation Platform - New Modular Backend Entry Point

This is a complete drop-in replacement for main.py using modular backend.

Usage:
    uv run main_new.py
"""
import uvicorn
from backend import app, engine, Base


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 AIVA AI Video Platform - Modular Backend")
    print("=" * 60)
    print("📍 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔧 Press Ctrl+C to stop")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
