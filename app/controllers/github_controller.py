from github import Github
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from app.services.commits import get_repository_commits
router = APIRouter()


@router.get("/commits")
async def get_commits_endpoint(repo_url: str, access_token: Optional[str] = None, branch: str = None, path: str = None):
    """
    Endpoint to retrieve commits from a GitHub repository.
    """
    return get_repository_commits(repo_url, access_token, branch, path)