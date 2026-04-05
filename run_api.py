"""
Entry point to start the FastAPI server with Uvicorn.

Usage:
    python run_api.py
    # or via uvicorn directly:
    uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
