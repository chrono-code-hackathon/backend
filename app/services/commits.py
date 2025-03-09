from datetime import datetime
import os
from github import Github
from typing import List, Optional
from app.models.models_commit import Commit, File, SubCommitAnalysis, Repository
from app.config.settings import settings
from app.logger.logger import logger
from app.services import supabase_service

# Add this custom exception class
class AlreadyAnalyzedRepositoryError(Exception):
    """Exception raised when a repository has already been analyzed."""
    pass

async def get_repository_commits(repo_url: str, access_token: Optional[str] = settings.GITHUB_ACCESS_TOKEN, branch: str = None, path: str = None) -> List[Commit]:
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
    
    g = Github(access_token, per_page=100, retry=3) if access_token else Github()

    try:
        logger.info(f"Fetching commits from repo: {repo_url}, branch: {branch}, path: {path}")
        repo_name = repo_url.split("github.com/")[1]
        repo_name = repo_name.replace(".git", "") if repo_name.endswith(".git") else repo_name
        try:
            repo = g.get_repo(repo_name)
            print(repo)
            logger.info(f"Repository found: {repo.full_name}")
        except Exception as e:
            logger.error(f"Error finding repository: {e}")
            return []

        # Store repository information
        repo_data = Repository(
            id=str(repo.id),
            name=repo.owner.login + "/" + repo.name,
            url=repo.url,
        )
        try:
            repo_storage_result = supabase_service.store_repo([repo_data])
            logger.info(f"Repository storage result: {repo_storage_result}")
            
            # Check if the repository already exists
            if "error" in repo_storage_result and repo_storage_result.get("code") == "duplicate_key":
                raise AlreadyAnalyzedRepositoryError(f"Repository {repo_url} has already been analyzed.")
                
        except Exception as e:
            if isinstance(e, AlreadyAnalyzedRepositoryError):
                raise e
            logger.error(f"Error storing repository: {str(e)}")
        
        if branch and path:
            try:
                commits = repo.get_commits(sha=branch, path=path)
                logger.info(f"Fetching commits from branch: {branch} and path: {path}")
            except Exception as e:
                logger.error(f"Error fetching commits from branch {branch} and path {path}: {e}")
                return []
        elif branch:
            try:
                commits = repo.get_commits(sha=branch)
                logger.info(f"Fetching commits from branch: {branch}")
            except Exception as e:
                logger.error(f"Error fetching commits from branch {branch}: {e}")
                return []
        else:
            try:
                commits = repo.get_commits()
                logger.info("Fetching all commits from default branch")
            except Exception as e:
                logger.error(f"Error fetching commits from default branch: {e}")
                return []
        
        # Process commits in batches for better memory management
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
        commit_list = []
        
        # Get total count for logging
        total_commits = commits.totalCount
        logger.info(f"Total commits to process: {total_commits}")
        
        # Process commits in batches to avoid memory issues with large repositories
        for i, commit in enumerate(commits):
            try:
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
                
                # Handle case where author might be None
                author_login = full_commit.author.login if full_commit.author else "anonymous"
                author_url = full_commit.author.url if full_commit.author else ""
                
                commit_data = Commit(
                    sha=full_commit.sha,
                    author=author_login,
                    date=str(full_commit.commit.author.date),
                    message=full_commit.commit.message,
                    url=full_commit.url,
                    author_email=full_commit.commit.author.email,
                    description="",
                    author_url=author_url,
                    repo_id=str(repo.id),
                    files=commit_files
                )
                commit_list.append(commit_data)
                
                # Log progress periodically
                if (i + 1) % batch_size == 0:
                    logger.info(f"Processed {i + 1}/{total_commits} commits")
                    
            except Exception as e:
                logger.error(f"Error processing commit {commit.sha}: {str(e)}")
                # Continue with the next commit instead of failing the entire process
                continue
     
        # Store commits
        if commit_list:
            commit_storage_result = await supabase_service.store_commits(commit_list)
            logger.info(f"Commit storage result: {commit_storage_result}")
            
            if "existing_commits" in commit_storage_result and len(commit_list) == len(commit_storage_result["existing_commits"]):
                logger.info("All commits already analyzed.")
                return []  # Or return a specific message indicating all commits were already analyzed
            elif "inserted_commits" in commit_storage_result:
                logger.info(f"Successfully fetched {len(commit_list)} commits and stored them with analyses.")
                return commit_list
            else:
                logger.warning("No commits were stored or all already existed, but the 'existing_commits' key wasn't present.")
                return []

        logger.info(f"No commits to store.")
        return []
    
    except AlreadyAnalyzedRepositoryError as e:
        logger.warning(f"Repository {repo_url} has already been analyzed.")
        raise e
    except Exception as e:
        logger.error(f"Error fetching commits: {e}")
        return []

async def get_new_repository_commits(repo_url: str, access_token: Optional[str] = settings.GITHUB_ACCESS_TOKEN, branch: str = None, path: str = None) -> List[Commit]:
    """
    Get only new commits from a GitHub repository that haven't been analyzed yet.
    
    Args:
        repo_url: The URL of the repository (e.g., "https://github.com/username/repo")
        access_token: GitHub personal access token (optional)
        branch: The branch to get commits from (optional)
        path: The path to filter commits by (optional)
        
    Returns:
        List of new Commit objects that haven't been analyzed yet
    """
    
    g = Github(access_token) if access_token else Github()

    try:
        logger.info(f"Fetching new commits from repo: {repo_url}, branch: {branch}, path: {path}")
        repo_name = repo_url.split("github.com/")[1]
        repo_name = repo_name.replace(".git", "") if repo_name.endswith(".git") else repo_name
        try:
            repo = g.get_repo(repo_name)
            logger.info(f"Repository found: {repo.full_name}")
        except Exception as e:
            logger.error(f"Error finding repository: {e}")
            return []

        # Get repository ID
        repo_id = str(repo.id)
        
        # Fetch existing commits from Supabase for this repository
        supabase = supabase_service.get_client()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return []
            
        existing_commits_result = supabase.table('commits').select('sha').eq('repo_id', repo_id).execute()
        existing_commit_shas = {item['sha'] for item in existing_commits_result.data} if existing_commits_result.data else set()
        logger.info(f"Found {len(existing_commit_shas)} existing commits in the database for repository {repo_id}")
        
        # Fetch all commits from GitHub
        if branch and path:
            try:
                commits = repo.get_commits(sha=branch, path=path)
                logger.info(f"Fetching commits from branch: {branch} and path: {path}")
            except Exception as e:
                logger.error(f"Error fetching commits from branch {branch} and path {path}: {e}")
                return []
        elif branch:
            try:
                commits = repo.get_commits(sha=branch)
                logger.info(f"Fetching commits from branch: {branch}")
            except Exception as e:
                logger.error(f"Error fetching commits from branch {branch}: {e}")
                return []
        else:
            try:
                commits = repo.get_commits()
                logger.info("Fetching all commits from default branch")
            except Exception as e:
                logger.error(f"Error fetching commits from default branch: {e}")
                return []
        
        # Process commits in batches for better memory management
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
        commit_list = []
        
        # Get total count for logging
        total_commits = commits.totalCount
        logger.info(f"Total commits to check: {total_commits}")
        processed_count = 0
        new_count = 0
        
        for commit in commits:
            processed_count += 1
            
            # Skip if commit already exists in database
            if commit.sha in existing_commit_shas:
                logger.debug(f"Skipping existing commit: {commit.sha}")
                continue
                
            new_count += 1
            try:
                full_commit = repo.get_commit(commit.sha)
                logger.debug(f"Processing new commit: {full_commit.sha}")

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
                
                # Handle case where author might be None
                author_login = full_commit.author.login if full_commit.author else "anonymous"
                author_url = full_commit.author.url if full_commit.author else ""
                
                commit_data = Commit(
                    sha=full_commit.sha,
                    author=author_login,
                    date=str(full_commit.commit.author.date),
                    message=full_commit.commit.message,
                    url=full_commit.url,
                    author_email=full_commit.commit.author.email,
                    description="",
                    author_url=author_url,
                    repo_id=repo_id,
                    files=commit_files
                )
                commit_list.append(commit_data)
                
                # Log progress periodically
                if processed_count % batch_size == 0:
                    logger.info(f"Processed {processed_count}/{total_commits} commits, found {new_count} new commits")
                    
            except Exception as e:
                logger.error(f"Error processing commit {commit.sha}: {str(e)}")
                # Continue with the next commit instead of failing the entire process
                continue
     
        logger.info(f"Completed processing {processed_count} commits, found {new_count} new commits")
        
        # Store new commits
        if commit_list:
            commit_storage_result = await supabase_service.store_commits(commit_list)
            logger.info(f"New commit storage result: {commit_storage_result}")
            
            if "inserted_commits" in commit_storage_result:
                logger.info(f"Successfully fetched {len(commit_list)} new commits and stored them.")
                return commit_list
            else:
                logger.warning("No new commits were stored.")
                return []

        logger.info(f"No new commits to store.")
        return []
    
    except Exception as e:
        logger.error(f"Error fetching new commits: {e}")
        return []