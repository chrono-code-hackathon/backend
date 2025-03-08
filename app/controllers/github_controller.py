from github import Github
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from app.services.commits import get_repository_commits
from datetime import datetime
from pydantic import BaseModel
router = APIRouter()


class TimelineRequest(BaseModel):
    repository_url: str
    until_date: str
    access_token: Optional[str] = None


@router.get("/commits")
async def get_commits_endpoint(repo_url: str, access_token: Optional[str] = None, branch: str = None, path: str = None):
    """
    Endpoint to retrieve commits from a GitHub repository.
    """
    return get_repository_commits(repo_url, access_token, branch, path)


@router.post("/create-timeline")
async def create_timeline(request: TimelineRequest = Body(...)):
    """
    Endpoint to create a timeline of commits up to a specified date.
    
    Parameters:
    - repository_url: URL of the GitHub repository
    - until_date: Date string in the same format as the Commit.date field
    - access_token: Optional GitHub access token for private repositories
    
    Returns:
    - A timeline of commits up to the specified date
    """
    try:
        # Get all commits from the repository
        commits = get_repository_commits(request.repository_url, request.access_token)
        
        # Filter commits based on the until_date
        filtered_commits = [
            commit for commit in commits 
            if datetime.strptime(commit.date, "%Y-%m-%dT%H:%M:%SZ") <= datetime.strptime(request.until_date, "%Y-%m-%dT%H:%M:%SZ")
        ]
        
        return {
            "repository_url": request.repository_url,
            "until_date": request.until_date,
            "total_commits": len(filtered_commits),
            "timeline": filtered_commits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating timeline: {str(e)}")