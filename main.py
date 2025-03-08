from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, APIKeyQuery
from app.controllers.github_controller import router as github_router
from app.controllers.analysis_controller import router as analysis_router
import uvicorn
from app.config.settings import settings

API_KEY = settings.API_KEY
API_KEY_NAME = "Authorization"

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
):
    if api_key_query == API_KEY:
        return api_key_query
    elif api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials"
        )

app = FastAPI(
    title="GitHub API",
    description="API for retrieving GitHub repository information",
    version="0.1.0",
    dependencies=[Depends(get_api_key)],
)

# Include routers
app.include_router(github_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")

@app.get("/api/v1/", tags=["root"])
async def root():
    """Root endpoint that returns API information."""
    return {
        "message": "GitHub API is running",
        "docs": "/docs",
        "endpoints": {
            "github_commits": "/api/v1/github/commits?repo_url=owner/repo",
            "analysis_commits": "/api/v1/analysis/commits?repo_url=owner/repo"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)