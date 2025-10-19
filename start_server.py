"""
Startup script for the restructured FastAPI service
"""

import os
import subprocess
import sys
from pathlib import Path

# Optional imports for checking requirements
try:
    import fastapi
    import uvicorn
    import sqlalchemy
    import psycopg2
    REQUIREMENTS_AVAILABLE = True
except ImportError:
    REQUIREMENTS_AVAILABLE = False


def check_requirements():
    """Check if required packages are installed."""
    if REQUIREMENTS_AVAILABLE:
        print("✅ All required packages are installed")
        return True
    else:
        print("❌ Missing required packages")
        print("Please install requirements: pip install -r requirements.txt")
        return False


def check_database():
    """Check database connection."""
    try:
        from app.db.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   App will run without database functionality")
        return True  # Allow app to run even without database


def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")


def main():
    """Main startup function."""
    print("🚀 Struct-Recipt-Intilligent FastAPI Service")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        return
    
    # Check database (but don't stop if it fails)
    check_database()
    
    # Start server
    start_server()


if __name__ == "__main__":
    main()