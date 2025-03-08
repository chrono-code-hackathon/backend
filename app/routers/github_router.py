from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from app.controllers.github_controller import GitHubController

router = APIRouter(
    prefix="/github",
    tags=["github"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get the GitHub controller
def get_github_controller():
    # You could add authentication or configuration here if needed
    return GitHubController()

@router.get("/commits", response_model=List[Dict[Any, Any]])
async def get_commits(
    repo_url: str = Query(..., description="GitHub repository URL or owner/repo format"),
    branch: Optional[str] = Query(None, description="Branch name (optional)"),
    path: Optional[str] = Query(None, description="File path to filter commits (optional)"),
    github_controller: GitHubController = Depends(get_github_controller)
):
    """
    Get all commits from a GitHub repository.
    
    - **repo_url**: GitHub repository URL (e.g., https://github.com/owner/repo) or owner/repo format
    - **branch**: Optional branch name to filter commits
    - **path**: Optional file path to filter commits
    """
    try:
        commits = github_controller.get_repository_commits(repo_url, branch, path)
        return commits
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 