import os
from github import Github
from typing import List, Optional, Dict, Any
import httpx
from fastapi import status
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
    Get all commits from a GitHub repository using GitHub REST API v3.
    
    Args:
        repo_url: The URL of the repository (e.g., "https://github.com/username/repo")
        access_token: GitHub personal access token (optional)
        branch: The branch to get commits from (optional)
        path: The path to filter commits by (optional)
        
    Returns:
        List of Commit objects
    """
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Fetching commits from repo: {repo_url}, branch: {branch}, path: {path}")
            
            # Extract owner and repo name from URL
            repo_name = repo_url.split("github.com/")[1]
            repo_name = repo_name.replace(".git", "") if repo_name.endswith(".git") else repo_name
            owner, repo = repo_name.split("/")
            
            # Set up API headers
            headers = {
                "Accept": "application/vnd.github.v3+json"
            }
            if access_token:
                headers["Authorization"] = f"token {access_token}"
            
            # Get repository information
            repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_response = await client.get(repo_api_url, headers=headers)
            
            if repo_response.status_code != status.HTTP_200_OK:
                logger.error(f"Error finding repository: {repo_response.json()}")
                return []
                
            repo_data = repo_response.json()
            logger.info(f"Repository found: {repo_data['full_name']}")
            
            # Store repository information
            repo_obj = Repository(
                id=str(repo_data['id']),
                name=repo_data['full_name'],
                url=repo_url,
            )
            
            try:
                repo_storage_result = supabase_service.store_repo([repo_obj])
                logger.info(f"Repository storage result: {repo_storage_result}")
                
                # Check if the repository already exists
                if "error" in repo_storage_result and repo_storage_result.get("code") == "duplicate_key":
                    raise AlreadyAnalyzedRepositoryError(f"Repository {repo_url} has already been analyzed.")
                    
            except Exception as e:
                if isinstance(e, AlreadyAnalyzedRepositoryError):
                    raise e
                logger.error(f"Error storing repository: {str(e)}")
            
            # Prepare API URL for commits
            commits_api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            params = {}
            
            if branch:
                params["sha"] = branch
            if path:
                params["path"] = path
            
            # Process commits in batches for better memory management
            batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
            params["per_page"] = batch_size
            
            commit_list = []
            page = 1
            total_commits = 0
            
            while True:
                params["page"] = page
                commits_response = await client.get(commits_api_url, headers=headers, params=params)
                
                if commits_response.status_code != status.HTTP_200_OK:
                    logger.error(f"Error fetching commits: {commits_response.json()}")
                    break
                    
                commits_data = commits_response.json()
                if not commits_data:
                    break
                    
                total_commits += len(commits_data)
                logger.info(f"Processing page {page}, fetched {len(commits_data)} commits")
                
                for commit_data in commits_data:
                    try:
                        # Get detailed commit information
                        commit_sha = commit_data["sha"]
                        commit_detail_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
                        commit_detail_response = await client.get(commit_detail_url, headers=headers)
                        
                        if commit_detail_response.status_code != status.HTTP_200_OK:
                            logger.error(f"Error fetching commit details for {commit_sha}: {commit_detail_response.json()}")
                            continue
                            
                        full_commit = commit_detail_response.json()
                        
                        # Process files
                        commit_files = []
                        for file in full_commit.get("files", []):
                            commit_files.append(File(
                                filename=file.get("filename", ""),
                                additions=file.get("additions", 0),
                                deletions=file.get("deletions", 0),
                                changes=file.get("changes", 0),
                                status=file.get("status", ""),
                                raw_url=file.get("raw_url", ""),
                                blob_url=file.get("blob_url", ""),
                                patch=file.get("patch", ""),
                            ))
                        
                        # Handle case where author might be None
                        author_login = full_commit.get("author", {}).get("login", "anonymous") if full_commit.get("author") else "anonymous"
                        author_url = full_commit.get("author", {}).get("url", "") if full_commit.get("author") else ""
                        
                        commit_obj = Commit(
                            sha=full_commit["sha"],
                            author=author_login,
                            date=full_commit["commit"]["author"]["date"],
                            message=full_commit["commit"]["message"],
                            url=full_commit["html_url"],
                            author_email=full_commit["commit"]["author"]["email"],
                            description="",
                            author_url=author_url,
                            repo_id=str(repo_data["id"]),
                            files=commit_files
                        )
                        commit_list.append(commit_obj)
                        
                    except Exception as e:
                        logger.error(f"Error processing commit {commit_data.get('sha', 'unknown')}: {str(e)}")
                        continue
                
                # Check if there are more pages
                if len(commits_data) < batch_size:
                    break
                    
                page += 1
            
            logger.info(f"Total commits processed: {total_commits}")
            
            # Store commits
            if commit_list:
                commit_storage_result = await supabase_service.store_commits(commit_list)
                logger.info(f"Commit storage result success.")
                
                if "existing_commits" in commit_storage_result and len(commit_list) == len(commit_storage_result["existing_commits"]):
                    logger.info("All commits already analyzed.")
                    return []
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
    Get only new commits from a GitHub repository that haven't been analyzed yet using GitHub REST API v3.
    
    Args:
        repo_url: The URL of the repository (e.g., "https://github.com/username/repo")
        access_token: GitHub personal access token (optional)
        branch: The branch to get commits from (optional)
        path: The path to filter commits by (optional)
        
    Returns:
        List of new Commit objects that haven't been analyzed yet
    """
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Fetching new commits from repo: {repo_url}, branch: {branch}, path: {path}")
            
            # Extract owner and repo name from URL
            repo_name = repo_url.split("github.com/")[1]
            repo_name = repo_name.replace(".git", "") if repo_name.endswith(".git") else repo_name
            owner, repo = repo_name.split("/")
            
            # Set up API headers
            headers = {
                "Accept": "application/vnd.github.v3+json"
            }
            if access_token:
                headers["Authorization"] = f"token {access_token}"
            
            # Get repository information
            repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"
            repo_response = await client.get(repo_api_url, headers=headers)
            
            if repo_response.status_code != status.HTTP_200_OK:
                logger.error(f"Error finding repository: {repo_response.json()}")
                return []
                
            repo_data = repo_response.json()
            repo_id = str(repo_data["id"])
            logger.info(f"Repository found: {repo_data['full_name']}")
            
            # Fetch existing commits from Supabase for this repository
            supabase = supabase_service.get_client()
            if not supabase:
                logger.error("Failed to initialize Supabase client")
                return []
                
            existing_commits_result = supabase.table('commits').select('sha').eq('repo_id', repo_id).execute()
            existing_commit_shas = {item['sha'] for item in existing_commits_result.data} if existing_commits_result.data else set()
            logger.info(f"Found {len(existing_commit_shas)} existing commits in the database for repository {repo_id}")
            
            # Prepare API URL for commits
            commits_api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            params = {}
            
            if branch:
                params["sha"] = branch
            if path:
                params["path"] = path
            
            # Process commits in batches for better memory management
            batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
            params["per_page"] = batch_size
            
            commit_list = []
            page = 1
            processed_count = 0
            new_count = 0
            
            while True:
                params["page"] = page
                commits_response = await client.get(commits_api_url, headers=headers, params=params)
                
                if commits_response.status_code != status.HTTP_200_OK:
                    logger.error(f"Error fetching commits: {commits_response.json()}")
                    break
                    
                commits_data = commits_response.json()
                if not commits_data:
                    break
                    
                processed_count += len(commits_data)
                logger.info(f"Processing page {page}, fetched {len(commits_data)} commits")
                
                for commit_data in commits_data:
                    commit_sha = commit_data["sha"]
                    
                    # Skip if commit already exists in database
                    if commit_sha in existing_commit_shas:
                        logger.debug(f"Skipping existing commit: {commit_sha}")
                        continue
                        
                    new_count += 1
                    try:
                        # Get detailed commit information
                        commit_detail_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
                        commit_detail_response = await client.get(commit_detail_url, headers=headers)
                        
                        if commit_detail_response.status_code != status.HTTP_200_OK:
                            logger.error(f"Error fetching commit details for {commit_sha}: {commit_detail_response.json()}")
                            continue
                            
                        full_commit = commit_detail_response.json()
                        
                        # Process files
                        commit_files = []
                        for file in full_commit.get("files", []):
                            commit_files.append(File(
                                filename=file.get("filename", ""),
                                additions=file.get("additions", 0),
                                deletions=file.get("deletions", 0),
                                changes=file.get("changes", 0),
                                status=file.get("status", ""),
                                raw_url=file.get("raw_url", ""),
                                blob_url=file.get("blob_url", ""),
                                patch=file.get("patch", ""),
                            ))
                        
                        # Handle case where author might be None
                        author_login = full_commit.get("author", {}).get("login", "anonymous") if full_commit.get("author") else "anonymous"
                        author_url = full_commit.get("author", {}).get("url", "") if full_commit.get("author") else ""
                        
                        commit_obj = Commit(
                            sha=full_commit["sha"],
                            author=author_login,
                            date=full_commit["commit"]["author"]["date"],
                            message=full_commit["commit"]["message"],
                            url=full_commit["html_url"],
                            author_email=full_commit["commit"]["author"]["email"],
                            description="",
                            author_url=author_url,
                            repo_id=repo_id,
                            files=commit_files
                        )
                        commit_list.append(commit_obj)
                        
                    except Exception as e:
                        logger.error(f"Error processing commit {commit_sha}: {str(e)}")
                        continue
                
                # Check if there are more pages
                if len(commits_data) < batch_size:
                    break
                    
                page += 1
            
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