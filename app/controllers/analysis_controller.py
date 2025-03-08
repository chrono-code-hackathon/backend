from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
import asyncio

from pydantic import BaseModel
from app.models.models_commit import Commit, SubCommitAnalysisList, SubCommitAnalysis
from app.services.gemini import get_commit_analysis
from app.services.supabase_service import store_commit_analyses
from app.config.settings import settings
from app.services import commits
from app.logger.logger import logger

router = APIRouter()

class CommitAnalysisRequest(BaseModel):
    repository_url: str

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
    Endpoint to analyze a list of commits using Gemini in batches and store the results in Supabase.
    
    Parameters:
    - repository_url: URL of the repository to analyze
    
    Returns:
    - A summary of the analysis and storage operation
    """
    try:
        logger.info(f"Received request to analyze commits from repository: {request.repository_url}")
        # Fetch commits from the repository
        list_commits = commits.get_repository_commits(request.repository_url)
        logger.info(f"Fetched {len(list_commits)} commits from repository: {request.repository_url}")
        
        all_analyses: List[SubCommitAnalysis] = []
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
        logger.info(f"Using batch size: {batch_size}")
        
        # Process commits in batches
        for i in range(0, len(list_commits), batch_size):
            batch = list_commits[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1} of size {len(batch)}")
            
            # Create tasks for each commit in the batch
            tasks = [analyze_commit(commit) for commit in batch]
            
            # Gather results from all tasks
            batch_analyses = await asyncio.gather(*tasks)
            logger.info(f"Completed analysis for batch {i // batch_size + 1}")
            
            # Extend the list of all analyses
            for analyses_list in batch_analyses:
                if analyses_list:
                    all_analyses.extend(analyses_list)
        
        logger.info(f"Generated a total of {len(all_analyses)} analyses")
        # Store all analyses in Supabase
        if all_analyses:
            logger.info("Storing analyses in Supabase")
            storage_result = store_commit_analyses(all_analyses)
            
            if "error" in storage_result:
                logger.error(f"Error storing analyses in Supabase: {storage_result['error']}")
                return {
                    "status": "partial_success",
                    "message": f"Analyzed {len(list_commits)} commits, but encountered an error storing results",
                    "error": storage_result["error"],
                    "analyses_count": len(all_analyses)
                }
            
            logger.info(f"Successfully stored {len(all_analyses)} analyses in Supabase")
            return {
                "status": "success",
                "message": f"Successfully analyzed {len(list_commits)} commits and stored {len(all_analyses)} analyses",
                "analyses_count": len(all_analyses)
            }
        else:
            logger.warning("No analyses were generated for the commits")
            return {
                "status": "warning",
                "message": f"Processed {len(list_commits)} commits, but no analyses were generated",
                "analyses_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error in analyze_commits endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing commits: {str(e)}")
