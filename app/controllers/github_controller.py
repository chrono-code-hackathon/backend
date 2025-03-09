from github import Github
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body, Request, Depends, Response
from app.services.commits import get_repository_commits
from datetime import datetime
from pydantic import BaseModel
from app.security.auth import get_github_client

router = APIRouter(
    prefix="/github",
    tags=["GitHub"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Handle OPTIONS preflight request for user endpoint
@router.options("/user")
async def options_user(response: Response):
    """
    Handle OPTIONS preflight request for the user endpoint.
    This is needed for CORS to work properly with some browsers.
    """
    # Manually add CORS headers to ensure they're present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return {}

# Handle OPTIONS preflight request for repos endpoint
@router.options("/repos")
async def options_repos(response: Response):
    """
    Handle OPTIONS preflight request for the repos endpoint.
    This is needed for CORS to work properly with some browsers.
    """
    # Manually add CORS headers to ensure they're present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return {}

class TimelineRequest(BaseModel):
    repository_url: str
    until_date: str
    access_token: Optional[str] = None

@router.get("/commits")
async def get_commits_endpoint(repo_url: str, access_token: Optional[str] = None, branch: str = None, path: str = None):
    """Get commits from a GitHub repository."""
    try:
        commits = get_repository_commits(repo_url, access_token, branch, path)
        return {"commits": commits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-timeline")
async def create_timeline(request: TimelineRequest = Body(...)):
    """Create a timeline from GitHub commits."""
    try:
        # Extract parameters
        repo_url = request.repository_url
        until_date = request.until_date
        access_token = request.access_token
        
        # Parse until_date
        try:
            until_datetime = datetime.fromisoformat(until_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SSZ)")
        
        # Get commits
        commits = get_repository_commits(repo_url, access_token)
        
        # Filter commits by date
        filtered_commits = [
            commit for commit in commits 
            if datetime.fromisoformat(commit['date'].replace('Z', '+00:00')) <= until_datetime
        ]
        
        # Create timeline
        timeline = {
            "repository": repo_url,
            "until_date": until_date,
            "commits": filtered_commits
        }
        
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating timeline: {str(e)}")

@router.get(
    "/user",
    summary="Get authenticated user information",
    responses={
        200: {"description": "User information retrieved successfully"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_info(request: Request, response: Response):
    """
    # Get Authenticated User Information
    
    Retrieves information about the authenticated GitHub user.
    
    ## Authentication
    
    Requires a valid GitHub access token in the Authorization header.
    
    ## Response
    
    JSON object containing user information from GitHub.
    
    ## Status Codes
    
    - 200: User information retrieved successfully
    - 401: Unauthorized - Invalid or missing token
    - 500: Internal server error
    """
    # Manually add CORS headers to ensure they're present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = auth_header.replace("Bearer ", "")
        if not token:
            raise HTTPException(status_code=401, detail="Access token is required")
        
        # Get GitHub client
        github = get_github_client(token)
        
        # Get authenticated user
        user = github.get_user()
        
        # Return user information
        return {
            "login": user.login,
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "html_url": user.html_url,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    except Exception as e:
        if "401" in str(e) or "Bad credentials" in str(e):
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.get(
    "/repos",
    summary="Get authenticated user repositories",
    responses={
        200: {"description": "Repositories retrieved successfully"},
        401: {"description": "Unauthorized - Invalid or missing token"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_repos(request: Request, response: Response):
    """
    # Get Authenticated User Repositories
    
    Retrieves repositories owned by the authenticated GitHub user.
    
    ## Authentication
    
    Requires a valid GitHub access token in the Authorization header.
    
    ## Response
    
    JSON array containing repository information.
    
    ## Status Codes
    
    - 200: Repositories retrieved successfully
    - 401: Unauthorized - Invalid or missing token
    - 500: Internal server error
    """
    # Manually add CORS headers to ensure they're present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = auth_header.replace("Bearer ", "")
        if not token:
            raise HTTPException(status_code=401, detail="Access token is required")
        
        # Get GitHub client
        github = get_github_client(token)
        
        # Get authenticated user
        user = github.get_user()
        
        # Get repositories
        repos = []
        for repo in user.get_repos():
            repos.append({
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "html_url": repo.html_url,
                "language": repo.language,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None
            })
        
        return repos
    except Exception as e:
        if "401" in str(e) or "Bad credentials" in str(e):
            raise HTTPException(status_code=401, detail="Invalid GitHub token")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")