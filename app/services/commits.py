
from typing import List, Dict, Any, Optional
from github import Github
from fastapi import HTTPException

def get_repository_commits(repo_url: str, access_token: Optional[str] = None, branch: str = None, path: str = None) -> List[Dict[Any, Any]]:
    """
    Get all commits from a repository.
    
    Args:
        repo_url: Full GitHub repository URL or owner/repo format
        access_token: GitHub personal access token for authenticated requests.
                      If None, uses unauthenticated access with rate limits.
        branch: Branch name to get commits from (optional)
        path: Path to get commits for (optional)
        
    Returns:
        List of commit data dictionaries
    """
    try:
        github = Github(access_token) if access_token else Github()

        # Extract owner and repo name from URL if full URL is provided
        if "github.com" in repo_url:
            parts = repo_url.rstrip('/').split('/')
            if len(parts) >= 2:
                owner_repo = '/'.join(parts[-2:])
            else:
                raise ValueError(f"Invalid GitHub URL: {repo_url}")
        else:
            owner_repo = repo_url
        
        repo = github.get_repo(owner_repo)
        commits = repo.get_commits(sha=branch, path=path)
        
        # Convert commits to serializable format
        result = []
        for commit in commits:
            commit_data = {
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": {
                    "name": commit.commit.author.name,
                    "email": commit.commit.author.email,
                    "date": commit.commit.author.date.isoformat() if commit.commit.author.date else None
                },
                "url": commit.html_url,
                "stats": {
                    "additions": commit.stats.additions,
                    "deletions": commit.stats.deletions,
                    "total": commit.stats.total
                } if hasattr(commit, 'stats') else None
            }
            result.append(commit_data)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching commits: {str(e)}")
