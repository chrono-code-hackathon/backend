import os
from github import Github
from typing import List, Optional
from app.models.models_commit import Commit, File

def get_repository_commits(repo_name: str="octokerbs/50Cent-Dolar-Blue-Bot", access_token: Optional[str] = os.getenv("GITHUB_ACCESS_TOKEN"), branch: str = None, path: str = None) -> List[Commit]:
    """
    Get all commits from a GitHub repository.
    Args:
        repo_name: The full name of the repository (e.g., "username/repo")
                   Default is "octokerbs/50Cent-Dolar-Blue-Bot"
        access_token: GitHub personal access token (optional)
        
    Returns:
        List of Commit objects
    """
    
    g = Github(access_token) if access_token else Github()

    try:
        repo = g.get_repo(repo_name)
        commits = repo.get_commits()
        
        result = []
        for commit in commits:
            full_commit = repo.get_commit(commit.sha)

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

            commit_data = Commit(
                sha=full_commit.sha,
                author=full_commit.author.login,
                date=str(full_commit.commit.author.date),
                message=full_commit.commit.message,
                url=full_commit.url,
                author_email=full_commit.commit.author.email,
                description="",
                author_url=full_commit.author.url,
                repo_id=str(repo.id),
                files=commit_files
            )
            result.append(commit_data)
        return result
    
    except Exception as e:
        print(f"Error fetching commits: {e}")
        return []

