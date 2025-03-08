from datetime import datetime
import os
from github import Github
from typing import List, Optional
from app.models.models_commit import Commit, File
from app.config.settings import settings
from app.logger.logger import logger

def get_repository_commits(repo_url: str, access_token: Optional[str] = settings.GITHUB_ACCESS_TOKEN, branch: str = None, path: str = None) -> List[Commit]:
    """
    Get all commits from a GitHub repository.
    Args:
        repo_url: The URL of the repository (e.g., "https://github.com/username/repo")
        access_token: GitHub personal access token (optional)
        branch: The branch to get commits from (optional)
        path: The path to filter commits by (optional)
        
    Returns:
        List of Commit objects
    """
    
    g = Github(access_token) if access_token else Github()

    try:
        logger.info(f"Fetching commits from repo: {repo_url}, branch: {branch}, path: {path}")
        repo_name = repo_url.split("github.com/")[1]
        repo_name = repo_name.replace(".git", "") if repo_name.endswith(".git") else repo_name
        repo = g.get_repo(repo_name)
        logger.info(f"Repository found: {repo.full_name}")
        
        if branch and path:
            commits = repo.get_commits(sha=branch, path=path)
            logger.info(f"Fetching commits from branch: {branch} and path: {path}")
        elif branch:
            commits = repo.get_commits(sha=branch)
            logger.info(f"Fetching commits from branch: {branch}")
        else:
            commits = repo.get_commits()
            logger.info("Fetching all commits from default branch")
        
        result = []
        for commit in commits:
            full_commit = repo.get_commit(commit.sha)
            logger.debug(f"Processing commit: {full_commit.sha}")

            files = full_commit.files
            commit_files = []
            for file in files:
                commit_files.append(File(
                    filename=file.filename,
                    additions=file.additions,
                    deletions=file.deletions,
                    changes=file.changes,
                    status=file.status,
                    raw_url=file.raw_url,
                    blob_url=file.blob_url,
                    patch=file.patch,
                ))
            
            author_name = full_commit.author.login if full_commit.author else "N/A"
            author_url = full_commit.author.html_url if full_commit.author else "N/A"

            commit_data = Commit(
                created_at=str(full_commit.commit.author.date),
                sha=full_commit.sha,
                author=author_name,
                date=str(full_commit.commit.author.date),
                message=full_commit.commit.message,
                url=full_commit.html_url,
                author_email=full_commit.commit.author.email,
                description=full_commit.commit.message,
                author_url=author_url,
                repo_id=repo.id,
                files= commit_files
                
            )
            result.append(commit_data)
        logger.info(f"Successfully fetched {len(result)} commits.")
        return result
    
    except Exception as e:
        logger.error(f"Error fetching commits: {e}")
        return []