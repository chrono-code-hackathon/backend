from fastapi import APIRouter, HTTPException
from typing import List, Optional
import asyncio

from pydantic import BaseModel
from app.models.models_commit import Commit, SubCommitAnalysis
from app.services.gemini import get_commit_analysis, analyze_commits_batch
from app.services.supabase_service import store_commit_analyses
from app.config.settings import settings
from app.services import commits
from app.services.commits import AlreadyAnalyzedRepositoryError
from app.logger.logger import logger

router = APIRouter()

class CommitAnalysisRequest(BaseModel):
    repository_url: str

class UpdateAnalysisRequest(BaseModel):
    repository_url: str
    branch: Optional[str] = None
    path: Optional[str] = None

async def analyze_commit(commit: Commit) -> List[SubCommitAnalysis]:
    """
    Analyzes a single commit using Gemini.
    
    Parameters:
    - commit: Commit object to analyze
    
    Returns:
    - A list of analyses or an empty list if an error occurs
    """
    try:
        logger.info(f"Analyzing commit: {commit.sha}")
        analysis_result = await get_commit_analysis(commit)
        if analysis_result and analysis_result.analysis:
            logger.info(f"Successfully analyzed commit: {commit.sha}")
            return analysis_result.analysis
        else:
            logger.warning(f"No analyses generated for commit: {commit.sha}")
            return []
    except Exception as e:
        logger.error(f"Error analyzing commit {commit.sha}: {str(e)}")
        return []

@router.post("/analyze-commits")
async def analyze_commits(request: CommitAnalysisRequest):
    """
    Endpoint to analyze commits from a repository using Gemini and store the results in Supabase.
    
    Parameters:
    - repository_url: URL of the repository to analyze
    
    Returns:
    - A summary of the analysis and storage operation
    """
    try:
        logger.info(f"Received request to analyze commits from repository: {request.repository_url}")
        
        try:
            # Fetch commits from the repository
            list_commits = await commits.get_repository_commits(request.repository_url)
            
            # Handle the case where no commits are returned (either repo not found or no commits)
            if not list_commits:
                logger.warning(f"No commits found or repository not found: {request.repository_url}")
                return {
                    "status": "not_found",
                    "message": f"Repository {request.repository_url} not found or no new commits available.",
                    "analyses_count": 0
                }
            
            logger.info(f"Fetched {len(list_commits)} commits from repository: {request.repository_url}")
        
        except AlreadyAnalyzedRepositoryError as e:
            logger.warning(f"Repository {request.repository_url} has already been analyzed.")
            return {
                "status": "already_analyzed",
                "message": f"Repository {request.repository_url} has already been analyzed.",
                "analyses_count": 0
            }
        
        all_analyses: List[SubCommitAnalysis] = []
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
        logger.info(f"Using batch size: {batch_size}")
        
        # Create batches
        batches = [list_commits[i:i + batch_size] for i in range(0, len(list_commits), batch_size)]
        logger.info(f"Split commits into {len(batches)} batches")
        
        # Process all batches concurrently
        batch_tasks = [analyze_commits_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Combine all results
        for batch_result in batch_results:
            if batch_result:
                all_analyses.extend(batch_result)
        
        logger.info(f"Generated a total of {len(all_analyses)} analyses")
        
        # Store all analyses in Supabase
        if all_analyses:
            logger.info("Storing analyses in Supabase")
            storage_result = store_commit_analyses(all_analyses)
            
            if "error" in storage_result:
                logger.error(f"Error storing analyses in Supabase: {storage_result['error']}")
                return {
                    "status": "partial_success",
                    "message": f"Analyzed {len(list_commits)} commits, but encountered an error storing results.",
                    "error": storage_result["error"],
                    "analyses_count": len(all_analyses)
                }
            
            logger.info(f"Successfully stored {len(all_analyses)} analyses in Supabase")
            return {
                "status": "success",
                "message": f"Successfully analyzed {len(list_commits)} commits and stored {len(all_analyses)} analyses.",
                "analyses_count": len(all_analyses)
            }
        else:
            logger.warning("No analyses were generated for the commits.")
            return {
                "status": "warning",
                "message": f"Processed {len(list_commits)} commits, but no analyses were generated.",
                "analyses_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error in analyze_commits endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing commits: {str(e)}")

@router.post("/update-analysis")
async def update_analysis(request: UpdateAnalysisRequest):
    """
    Endpoint to analyze only new commits from a repository that has already been analyzed.
    
    Parameters:
    - repository_url: URL of the repository to analyze
    - branch: Optional branch to analyze (default is the repository's default branch)
    - path: Optional path to filter commits by
    
    Returns:
    - A summary of the analysis and storage operation
    """
    try:
        logger.info(f"Received request to analyze new commits from repository: {request.repository_url}")
        
        # Fetch only new commits from the repository
        list_commits = await commits.get_new_repository_commits(
            request.repository_url, 
            branch=request.branch, 
            path=request.path
        )
        
        # Handle the case where no new commits are found
        if not list_commits:
            logger.info(f"No new commits found for repository: {request.repository_url}")
            return {
                "status": "success",
                "message": f"No new commits to analyze for repository {request.repository_url}.",
                "analyses_count": 0
            }
        
        logger.info(f"Fetched {len(list_commits)} new commits from repository: {request.repository_url}")
        
        all_analyses: List[SubCommitAnalysis] = []
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
        logger.info(f"Using batch size: {batch_size}")
        
        # Create batches
        batches = [list_commits[i:i + batch_size] for i in range(0, len(list_commits), batch_size)]
        logger.info(f"Split commits into {len(batches)} batches")
        
        # Process all batches concurrently
        batch_tasks = [analyze_commits_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Combine all results
        for batch_result in batch_results:
            if batch_result:
                all_analyses.extend(batch_result)
        
        logger.info(f"Generated a total of {len(all_analyses)} analyses")
        
        # Store all analyses in Supabase
        if all_analyses:
            logger.info("Storing analyses in Supabase")
            storage_result = store_commit_analyses(all_analyses)
            
            if "error" in storage_result:
                logger.error(f"Error storing analyses in Supabase: {storage_result['error']}")
                return {
                    "status": "partial_success",
                    "message": f"Analyzed {len(list_commits)} new commits, but encountered an error storing results.",
                    "error": storage_result["error"],
                    "analyses_count": len(all_analyses)
                }
            
            logger.info(f"Successfully stored {len(all_analyses)} analyses in Supabase")
            return {
                "status": "success",
                "message": f"Successfully analyzed {len(list_commits)} new commits and stored {len(all_analyses)} analyses.",
                "analyses_count": len(all_analyses)
            }
        else:
            logger.warning("No analyses were generated for the new commits.")
            return {
                "status": "warning",
                "message": f"Processed {len(list_commits)} new commits, but no analyses were generated.",
                "analyses_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error in update_analysis endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing new commits: {str(e)}")
