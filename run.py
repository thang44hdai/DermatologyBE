"""
Launcher script for Dermatology Backend API
Run this from the project root directory
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    
    print("=" * 50)
    print("  Dermatology Backend API")
    print("=" * 50)
    print(f"Starting server on http://{settings.HOST}:{settings.PORT}")
    print(f"Swagger UI: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
