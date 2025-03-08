import os
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from app.models.models_commit import SubCommitAnalysis, Repository, Commit
from app.logger.logger import logger
from app.config.settings import settings

def get_client() -> Optional[Client]:
    """
    Get a Supabase client instance.
    
    Returns:
        Supabase client or None if an error occurs
    """
    try:
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_KEY
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase URL or key not found in environment variables")
            return None
        
        logger.info("Creating Supabase client")
        client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client created successfully")
        return client
    
    except Exception as e:
        logger.error(f"Error creating Supabase client: {e}")
        return None


def store_commits(commits: List[Commit]) -> Dict[str, Any]:
    """
    Store commits in Supabase, handling potential duplicates efficiently.

    Args:
        commits: List of Commit objects

    Returns:
        Dictionary with result information, including counts of inserted and existing commits.
    """
    try:
        logger.info(f"Storing {len(commits)} commits in Supabase")
        supabase = get_client()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return {"error": "Failed to initialize Supabase client"}

        commits_data = [commit.dict() for commit in commits]

        # Fetch existing commit SHAs in a single query
        existing_commits_query = supabase.table('commits').select('sha').in_('sha', [commit['sha'] for commit in commits_data])
        existing_commits_result = existing_commits_query.execute()
        existing_shas = {item['sha'] for item in existing_commits_result.data}

        new_commits_data = [commit for commit in commits_data if commit['sha'] not in existing_shas]

        inserted_count = 0
        if new_commits_data:
            try:
                # Insert new commits in a single batch
                insert_result = supabase.table('commits').insert(new_commits_data).execute()
                inserted_count = len(insert_result.data) if insert_result.data else 0
                logger.info(f"Inserted {inserted_count} new commits")
            except Exception as insert_error:
                logger.error(f"Error inserting commits: {insert_error}")
                return {"error": str(insert_error)}
        else:
            logger.info("No new commits to insert")

        existing_count = len(commits) - inserted_count
        result_message = f"Successfully processed {len(commits)} commits. Inserted {inserted_count} new commits. {existing_count} commits already existed."
        logger.info(result_message)

        return {
            "message": result_message,
            "inserted_commits": new_commits_data,
            "existing_commits": existing_count
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
        logger.info(f"Storing {len(analyses)} commit analyses in Supabase")
        # Initialize Supabase client
        supabase = get_client()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return {"error": "Failed to initialize Supabase client"}

        # Convert SubCommitAnalysis objects to dictionaries
        analyses_data = [analysis.dict() for analysis in analyses]
            
        result = supabase.table('commit_analyses').insert(analyses_data).execute()
        inserted_count = len(result.data) if result.data else 0
        
        result_message = f"Successfully processed {len(analyses)} analyses. Inserted {inserted_count} new analyses."
        logger.info(result_message)
        return {
            "message": result_message,
            "inserted_analyses": analyses
        }
    
    except Exception as e:
        logger.error(f"Error storing commit analyses: {e}")
        return {"error": str(e)}

def store_repo(repos: List[Repository]) -> Dict[str, Any]:
    """
    Store repositories in Supabase.

    Args:
        repo: List of Repository objects

    Returns:
        Dictionary with result information
    """
    try:
        logger.info(f"Storing {len(repos)} repositories in Supabase")
        # Initialize Supabase client
        supabase = get_client()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return {"error": "Failed to initialize Supabase client"}

        repos_data = [repo.dict() for repo in repos]

        # Check if repo already exists
        existing_repos = supabase.table('repositories').select('name').in_('name', [repo['name'] for repo in repos_data]).execute()
        existing_names = [item['name'] for item in existing_repos.data]

        # Filter out repos that already exist
        new_repos_data = [repo for repo in repos_data if repo['name'] not in existing_names]

        if new_repos_data:
            # Insert new repo
            try:
                result = supabase.table('repositories').insert(new_repos_data).execute()
                inserted_count = len(result.data) if result.data else 0
                logger.info(f"Inserted {inserted_count} repositories")
                return {"message": f"Successfully inserted {inserted_count} repositories", "data": new_repos_data}
            except Exception as insert_error:
                logger.error(f"Error inserting repositories: {insert_error}")
                return {"error": str(insert_error)}
        else:
            logger.info(f"Repositories already exists")
            return {"message": f"Repositories already exists"}

    except Exception as e:
        logger.error(f"Error storing repositories: {e}")
        return {"error": str(e)}


def test_connection() -> Dict[str, Any]:
    """
    Test the Supabase connection.
    
    Returns:
        Dictionary with test result
    """
    try:
        logger.info("Testing Supabase connection")
        client = get_client()
        if not client:
            logger.error("Supabase client not initialized")
            return {"error": "Supabase client not initialized"}
            
        data = client.table('test').select("*").execute()
        logger.info("Supabase connection successful")
        return {"message": "Supabase connection successful", "data": data.data}
    
    except Exception as e:
        logger.error(f"Error testing Supabase connection: {e}")
        return {"error": str(e)} 