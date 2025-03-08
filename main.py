from fastapi import FastAPI
from app.controllers.github_controller import router as github_router

from app.services.commits import get_repository_commits

from app.services.supabase_service import store_commits, store_repository

app = FastAPI(
    title="GitHub API",
    description="API for retrieving GitHub repository information",
    version="0.1.0",
)

# Include routers
app.include_router(github_router, prefix="/api/v1")

@app.get("/api/v1/", tags=["root"])
async def root():
    """Root endpoint that returns API information."""
    return {
        "message": "GitHub API is running",
        "docs": "/docs",
        "endpoints": {
            "github_commits": "/api/v1/github/commits?repo_url=owner/repo"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)