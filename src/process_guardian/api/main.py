"""Main entry point for Process Guardian FastAPI server."""

from fastapi.middleware.cors import CORSMiddleware
from process_guardian.api.app import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("process_guardian.api.main:app", host="0.0.0.0", port=8000, reload=True)
