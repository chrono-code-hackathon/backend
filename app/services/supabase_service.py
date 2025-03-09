from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from app.models.models_commit import SubCommitAnalysis, Repository, Commit, SubCommitAnalysisSupabase
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

async def store_commits(commits: List[Commit]) -> Dict[str, Any]:
    """
    Store commits in Supabase in batches, handling potential duplicates efficiently.

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

        inserted_commits = []
        existing_commits = []
        errors = []
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50

        for i in range(0, len(commits), batch_size):
            batch = commits[i:i + batch_size]
            commits_data = [commit.model_dump() for commit in batch]

            # Prepare data for insertion
            for commit_data in commits_data:
                try:
                    result = supabase.table('commits').insert(commit_data).execute()
                    if result.data:
                        inserted_commits.append(commit_data)
                except Exception as e:
                    if "duplicate key value violates unique constraint" in str(e):
                        logger.warning(f"Commit with SHA {commit_data['sha']} already exists.")
                        existing_commits.append(commit_data['sha'])
                    else:
                        logger.error(f"Error inserting commit {commit_data['sha']}: {str(e)}")
                        errors.append(str(e))

        inserted_count = len(inserted_commits)
        existing_count = len(existing_commits)
        
        if errors:
            error_message = f"Errors occurred during commit insertion: {errors}"
            logger.error(error_message)
            return {"error": error_message}

        result_message = f"Successfully processed {len(commits)} commits. Inserted {inserted_count} new commits. {existing_count} commits already existed."
        logger.info(result_message)

        return {
            "message": result_message,
            "inserted_commits": inserted_commits,
            "existing_commits": existing_commits
        }

    except Exception as e:
        logger.error(f"Error storing commits: {e}")
        return {"error": str(e)}


def store_commit_analyses(analyses: List[SubCommitAnalysis]) -> Dict[str, Any]:
    """
    Store commit analyses in Supabase.
    
#     Args:
#         analyses: List of SubCommitAnalysis objects
        
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
        analyses_data = [analysis.model_dump() for analysis in analyses]

        # Fetch existing commit_sha values
        existing_analyses_query = supabase.table('commit_analyses').select('commit_sha').in_('commit_sha', [analysis['commit_sha'] for analysis in analyses_data])
        existing_analyses_result = existing_analyses_query.execute()
        existing_commit_shas = {item['commit_sha'] for item in existing_analyses_result.data}

        # Filter out analyses that already exist
        new_analyses_data = [analysis for analysis in analyses_data if analysis['commit_sha'] not in existing_commit_shas]
            
        inserted_count = 0
        if new_analyses_data:
            result = supabase.table('commit_analyses').insert(new_analyses_data).execute()
            inserted_count = len(result.data) if result.data else 0
        
        result_message = f"Successfully processed {len(analyses)} analyses. Inserted {inserted_count} new analyses."
        logger.info(result_message)
        return {
            "message": result_message,
            "inserted_analyses": new_analyses_data
        }
    
    except Exception as e:
        logger.error(f"Error storing commit analyses: {e}")
        return {"error": str(e)}

class AlreadyAnalyzedRepositoryError(Exception):
    """Exception raised for errors in the repository."""
    def __init__(self, message="Repository has already been analyzed."):
        self.message = message
        super().__init__(self.message)

def store_repo(repos: List[Repository]) -> Dict[str, Any]:
    """
    Store repository information in Supabase.
    Handles potential duplicate key errors by checking for existing repositories.
    
    Args:
        repos: List of Repository objects to store
        
    Returns:
        Dict with status of the operation
    """
    try:
        supabase = get_client()
        if not supabase:
            return {"error": "Failed to connect to Supabase"}
        
        logger.info(f"Storing {len(repos)} repositories in Supabase")
        
        # Convert Repository objects to dictionaries
        new_repos_data = [repo.model_dump() for repo in repos]
        
        # Attempt to insert repositories into Supabase
        try:
            result = supabase.table('repositories').insert(new_repos_data).execute()
            # Success case - just return the data
            return {"message": f"Successfully stored repositories", "data": result.data}
        except Exception as e:
            logger.error(f"Error inserting repositories: {str(e)}")
            # Check if the error is a duplicate key violation
            if "duplicate key value violates unique constraint" in str(e):
                logger.warning("Duplicate key violation detected. Repository likely already analyzed.")
                return {"error": "Repository already analyzed", "code": "duplicate_key"}
            else:
                # If it's another type of error, return the error message
                return {"error": str(e)}
            
    except Exception as e:
        logger.error(f"Error storing repositories: {str(e)}")
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
from typing import List, Dict, Any
from app.models.models_commit import SubCommitAnalysis
from supabase import Client

def get_all_commit_analyses(repository_url: str) -> Dict[str, List[SubCommitAnalysisSupabase]]:
    """
    Retrieve commit analyses from the 'commit_analyses' table in Supabase for a specific repository.
    
    Process:
    1. Get repository ID from the repository URL
    2. Get all commit SHAs associated with that repository ID
    3. Get all commit analyses that match those commit SHAs

    Args:
        repository_url: URL of the repository to get analyses for

    Returns:
        A dictionary containing either the fetched data (as a list of SubCommitAnalysis objects) or an error message.
    """
    try:
        logger.info(f"Retrieving commit analyses for repository: {repository_url}")
        
        supabase: Client = get_client()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return {"error": "Failed to initialize Supabase client"}

        # Step 1: Get repository ID from the repository URL
        repo_result = supabase.table('repositories').select("id").eq('url', repository_url).execute()
        
        if not repo_result.data:
            logger.info(f"No repository found with URL: {repository_url}")
            return {"data": []}
            
        repo_id = repo_result.data[0]['id']
        logger.info(f"Found repository ID: {repo_id}")
        
        # Step 2: Get all commit SHAs associated with that repository ID
        commits_result = supabase.table('commits').select("sha").eq('repo_id', repo_id).execute()
        
        if not commits_result.data:
            logger.info(f"No commits found for repository: {repository_url}")
            return {"data": []}
            
        # Extract commit SHAs
        commit_shas = [commit['sha'] for commit in commits_result.data]
        logger.info(f"Found {len(commit_shas)} commits for repository")
        
        # Step 3: Get all commit analyses that match those commit SHAs
        analyses_result = supabase.table('commit_analyses').select("*").in_('commit_sha', commit_shas).execute()

        if analyses_result.data:
            logger.info(f"Successfully retrieved {len(analyses_result.data)} commit analyses.")
            
            # Deserialize each item to a SubCommitAnalysis object
            analyses: List[SubCommitAnalysisSupabase] = [SubCommitAnalysisSupabase(**item) for item in analyses_result.data]
            
            return {"data": analyses, "repo_id": repo_id}
        else:
            logger.info(f"No commit analyses found for repository: {repository_url}")
            return {"data": []}

    except Exception as e:
        logger.error(f"Error retrieving commit analyses for repository {repository_url}: {e}")
        return {"error": str(e)}

def get_commit_analysis(subcommit_id: str) -> Dict[str, Any]:
    """
    Retrieve a single commit analysis from the 'commit_analyses' table in Supabase by commit SHA.

    Args:
        commit_sha: The SHA of the commit to retrieve

    Returns:
        A dictionary containing either the fetched data (as a SubCommitAnalysis object) or an error message.
    """
    try:
        logger.info(f"Retrieving commit analysis for SidHA: {subcommit_id}")
        supabase: Client = get_client()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return {"error": "Failed to initialize Supabase client"}

        result = supabase.table('commit_analyses').select("*").eq('id', subcommit_id).execute()

        if result.data and len(result.data) > 0:
            logger.info(f"Successfully retrieved commit analysis for SidHA: {subcommit_id}")
            
            # Deserialize the item to a SubCommitAnalysis object
            analysis = SubCommitAnalysis(**result.data[0])
            
            return {"data": analysis}
        else:
            logger.info(f"No commit analysis found for SidHA: {subcommit_id}")
            return {"data": None}

    except Exception as e:
        logger.error(f"Error retrieving commit analysis for SidHA: {subcommit_id}: {e}")
        return {"error": str(e)}