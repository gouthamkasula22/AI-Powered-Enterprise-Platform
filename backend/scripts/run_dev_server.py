"""
Development Server Startup Script

Run this script to start the FastAPI development server.
"""

import uvicorn
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    # Run the development server with import string for reload
    uvicorn.run(
        "src.presentation.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )