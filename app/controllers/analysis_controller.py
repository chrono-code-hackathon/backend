from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
import logging
import asyncio

from pydantic import BaseModel
from app.models.models_commit import Commit, SubCommitAnalysisList
from app.services.gemini import get_commit_analysis
from app.services.supabase_service import store_commit_analyses
from app.config.settings import settings
from app.services import commits

router = APIRouter()
logger = logging.getLogger(__name__)

class CommitAnalysisRequest(BaseModel):
    repository_url: str

async def analyze_commit(commit: Commit) -> List[Dict[str, Any]]:
    """
    Analyzes a single commit using Gemini.
    
    Parameters:
    - commit: Commit object to analyze
    
    Returns:
    - A list of analyses or an empty list if an error occurs
    """
    try:
        analysis_result = await get_commit_analysis(commit)
        if analysis_result and analysis_result.analysis:
            return analysis_result.analysis
        else:
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
        # Fetch commits from the repository
        list_commits = commits.get_repository_commits(request.repository_url)
        
        all_analyses = []
        batch_size = settings.BATCH_SIZE if hasattr(settings, 'BATCH_SIZE') else 50
        
        # Process commits in batches
        for i in range(0, len(list_commits), batch_size):
            batch = list_commits[i:i + batch_size]
            
            # Create tasks for each commit in the batch
            tasks = [analyze_commit(commit) for commit in batch]
            
            # Gather results from all tasks
            batch_analyses = await asyncio.gather(*tasks)
            
            # Extend the list of all analyses
            for analyses in batch_analyses:
                all_analyses.extend(analyses)
        
        # Store all analyses in Supabase
        if all_analyses:
            storage_result = store_commit_analyses(all_analyses)
            
            if "error" in storage_result:
                return {
                    "status": "partial_success",
                    "message": f"Analyzed {len(list_commits)} commits, but encountered an error storing results",
                    "error": storage_result["error"],
                    "analyses_count": len(all_analyses)
                }
            
            return {
                "status": "success",
                "message": f"Successfully analyzed {len(list_commits)} commits and stored {len(all_analyses)} analyses",
                "analyses_count": len(all_analyses)
            }
        else:
            return {
                "status": "warning",
                "message": f"Processed {len(list_commits)} commits, but no analyses were generated",
                "analyses_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error in analyze_commits endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing commits: {str(e)}")
