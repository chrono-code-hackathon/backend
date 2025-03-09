from fastapi import FastAPI, Depends, HTTPException, Security, Request, Response
from fastapi.security import APIKeyHeader, APIKeyQuery
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.controllers.github_controller import router as github_router
from app.controllers.analysis_controller import router as analysis_router
from app.controllers.auth_controller import auth_router
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

# Custom middleware to ensure CORS headers are added to all responses
class CORSHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

app = FastAPI(
    title="GitHub API",
    description="API for retrieving GitHub repository information",
    version="0.1.0",
    # Only apply API key validation to non-auth endpoints
    # dependencies=[Depends(get_api_key)],
)

# Configure CORS - MUST be added before any routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],  # Allows all headers
    expose_headers=["*"],  # Expose all headers
    max_age=86400,  # Cache preflight requests for 24 hours
)

# Add custom CORS header middleware as a backup
app.add_middleware(CORSHeaderMiddleware)

# Example of how to restrict to specific domains in production:
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",  # React development server
#         "https://your-production-frontend.com",
#         "https://your-staging-frontend.com",
#     ],
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
#     allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
#     expose_headers=["Content-Length", "Content-Type"],
#     max_age=86400,  # Cache preflight requests for 24 hours
# )

# Include routers
# Include auth router at both /api/v1/auth and /auth to support both paths
app.include_router(auth_router, prefix="/api/v1")  # No API key required for auth endpoints
app.include_router(auth_router, prefix="")  # Also include at root path for direct access

# Include github router at both /api/v1/github and /github to support both paths
# Remove API key dependency for GitHub endpoints to simplify authentication
app.include_router(github_router, prefix="/api/v1")
app.include_router(github_router, prefix="")  # Also include at root path for direct access

# Include analysis router only at /api/v1/analysis
app.include_router(analysis_router, prefix="/api/v1", dependencies=[Depends(get_api_key)])

@app.get("/api/v1/", tags=["root"])
async def root():
    """Root endpoint that returns API information."""
    return {
        "message": "GitHub API is running",
        "docs": "/docs",
        "endpoints": {
            "github_commits": "/api/v1/github/commits?repo_url=owner/repo",
            "analysis_commits": "/api/v1/analysis/commits?repo_url=owner/repo",
            "auth_exchange_code": "/auth/exchange_code or /api/v1/auth/exchange_code",
            "github_user": "/github/user or /api/v1/github/user"
        }
    }

# Add OPTIONS handler for the root path
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """
    Global OPTIONS handler to support CORS preflight requests.
    """
    return {}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)