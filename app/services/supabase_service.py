import os
import logging
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from app.models.models_commit import Commit
from github import Github
import os

logger = logging.getLogger(__name__)

def get_client() -> Optional[Client]:
    """
    Get a Supabase client instance.
    
    Returns:
        Supabase client or None if an error occurs
    """
    try:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase URL or key not found in environment variables")
            return None
        
        return create_client(supabase_url, supabase_key)
    
    except Exception as e:
        logger.error(f"Error creating Supabase client: {e}")
        return None
def store_repository(repo_name: str) -> Dict[str, Any]:
    """
    Store repository information in Supabase.
    
    Args:
        repo_name: String containing repository name in format "owner/repo"
        
    Returns:
        Dictionary with result information
    """
    try:
        # Initialize Supabase client
        supabase = get_client()
        if not supabase:
            return {"error": "Failed to initialize Supabase client"}
        
        access_token = os.getenv("GITHUB_ACCESS_TOKEN")
        g = Github(access_token) if access_token else Github()
        
        try:
            github_repo = g.get_repo(repo_name)
            
            repo_data = {
                'id': str(github_repo.id),
                'name': github_repo.name,
                'url': github_repo.html_url
            }
            
            # Check if repository already exists
            existing = supabase.table('repositories').select('id').eq('id', repo_data['id']).execute()
            
            if not existing.data:
                # Insert new repository
                result = supabase.table('repositories').insert(repo_data).execute()
                return {"message": "Repository stored successfully", "data": result.data}
            else:
                # Update existing repository
                result = supabase.table('repositories').update(repo_data).eq('id', repo_data['id']).execute()
                return {"message": "Repository updated successfully", "data": result.data}
                
        except Exception as e:
            logger.error(f"Error fetching repository from GitHub: {e}")
            return {"error": f"Failed to fetch repository from GitHub: {str(e)}"}
    
    except Exception as e:
        logger.error(f"Error storing repository: {e}")
        return {"error": f"Failed to store repository: {str(e)}"}

def store_commits(commits: List[Commit]) -> Dict[str, Any]:
    """
    Store commits in Supabase.
    
    Args:
        commits: List of Commit objects
        
    Returns:
        Dictionary with result information
    """
    try:
        # Initialize Supabase client
        supabase = get_client()
        if not supabase:
            return {"error": "Failed to initialize Supabase client"}
        
        inserted_commits = []
        commit_count = 0
        
        for commit in commits:
            commit_count += 1
            
            # Convert the files list to a format suitable for JSONB storage
            files_json = [file.model_dump() for file in commit.files]
            
            commit_data = {
                'sha': commit.sha,
                'author': commit.author,
                'date': commit.date,
                'message': commit.message,
                'url': commit.url,
                'author_email': commit.author_email,
                'description': commit.description,
                'author_url': commit.author_url,
                'repo_id': commit.repo_id,
                'files': files_json  # Store files as JSONB
            }
            
            # Check if commit already exists
            existing = supabase.table('commits').select('sha').eq('sha', commit.sha).execute()
            
            if not existing.data:
                # Insert new commit
                result = supabase.table('commits').insert(commit_data).execute()
                if result.data:
                    inserted_commits.append(commit_data)
        
        return {
            "message": f"Successfully processed {commit_count} commits. Inserted {len(inserted_commits)} new commits.",
            "inserted_commits": inserted_commits
        }
    
    except Exception as e:
        logger.error(f"Error storing commits: {e}")
        return {"error": str(e)}
    
# def store_commit_analyses(analyses: List[SubCommitAnalysis]) -> Dict[str, Any]:
#     """
#     Store commit analyses in Supabase.
    
#     Args:
#         analyses: List of SubCommitAnalysis objects
        
#     Returns:
#         Dictionary with result information
#     """
#     try:
#         # Initialize Supabase client
#         supabase = get_client()
#         if not supabase:
#             return {"error": "Failed to initialize Supabase client"}

#         # Convert SubCommitAnalysis objects to dictionaries
#         analyses_data = [analysis.dict() for analysis in analyses]
            
#         supabase.table('commit_analyses').insert(analyses_data).execute()
        
#         return {
#             "message": f"Successfully processed {len(analyses)} analyses. Inserted {len(analyses)} new analyses.",
#             "inserted_analyses": analyses
#         }
    
#     except Exception as e:
#         logger.error(f"Error storing commit analyses: {e}")
#         return {"error": str(e)}


# def test_connection() -> Dict[str, Any]:
#     """
#     Test the Supabase connection.
    
#     Returns:
#         Dictionary with test result
#     """
#     try:
#         client = get_client()
#         if not client:
#             return {"error": "Supabase client not initialized"}
            
#         data = client.table('test').select("*").execute()
#         return {"message": "Supabase connection successful", "data": data.data}
    
#     except Exception as e:
#         logger.error(f"Error testing Supabase connection: {e}")
#         return {"error": str(e)} 