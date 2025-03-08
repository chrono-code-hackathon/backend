import os
import logging
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from app.models.models_commit import SubCommitAnalysis

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

def store_commits(commits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Store commits in Supabase.
    
    Args:
        commits: List of commit dictionaries
        
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
            commit_data = {
                'sha': commit['sha'],
                'repo_name': commit['repo_name'],
                'author': commit['author'],
                'author_email': commit['author_email'],
                'date': commit['date'],
                'message': commit['message'],
                'url': commit.get('url', 'Not url'),
                'description': commit['description'],
                'author_url': commit.get('author_url', None)
            }
            
            # Check if commit already exists
            existing = supabase.table('commits').select('sha').eq('sha', commit['sha']).execute()
            
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
    
def store_commit_analyses(analyses: List[SubCommitAnalysis]) -> Dict[str, Any]:
    """
    Store commit analyses in Supabase.
    
    Args:
        analyses: List of SubCommitAnalysis objects
        
    Returns:
        Dictionary with result information
    """
    try:
        # Initialize Supabase client
        supabase = get_client()
        if not supabase:
            return {"error": "Failed to initialize Supabase client"}

        # Convert SubCommitAnalysis objects to dictionaries
        analyses_data = [analysis.dict() for analysis in analyses]
            
        supabase.table('commit_analyses').insert(analyses_data).execute()
        
        return {
            "message": f"Successfully processed {len(analyses)} analyses. Inserted {len(analyses)} new analyses.",
            "inserted_analyses": analyses
        }
    
    except Exception as e:
        logger.error(f"Error storing commit analyses: {e}")
        return {"error": str(e)}


def test_connection() -> Dict[str, Any]:
    """
    Test the Supabase connection.
    
    Returns:
        Dictionary with test result
    """
    try:
        client = get_client()
        if not client:
            return {"error": "Supabase client not initialized"}
            
        data = client.table('test').select("*").execute()
        return {"message": "Supabase connection successful", "data": data.data}
    
    except Exception as e:
        logger.error(f"Error testing Supabase connection: {e}")
        return {"error": str(e)} 