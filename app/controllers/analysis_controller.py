from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
import logging

from pydantic import BaseModel
from app.models.models_commit import Commit, SubCommitAnalysisList
from app.services.gemini import get_commit_analysis
from app.services.supabase_service import store_commit_analyses

router = APIRouter()
logger = logging.getLogger(__name__)

class CommitAnalysisRequest(BaseModel):
    commits: List[Commit]

@router.post("/analyze-commits")
async def analyze_commits(request: CommitAnalysisRequest = Body(...)):
    """
    Endpoint to analyze a list of commits using Gemini and store the results in Supabase.
    
    Parameters:
    - commits: List of Commit objects to analyze
    
    Returns:
    - A summary of the analysis and storage operation
    """
    try:
        all_analyses = []
        
        # Process each commit
        for commit in request.commits:
            try:
                # Get analysis from Gemini
                analysis_result = await get_commit_analysis(commit)
                
                # Add analyses to the collection
                if analysis_result and analysis_result.analyses:
                    all_analyses.extend(analysis_result.analyses)
                    
            except Exception as e:
                logger.error(f"Error analyzing commit {commit.sha}: {str(e)}")
                # Continue with other commits even if one fails
        
        # Store all analyses in Supabase
        if all_analyses:
            storage_result = store_commit_analyses(all_analyses)
            
            if "error" in storage_result:
                return {
                    "status": "partial_success",
                    "message": f"Analyzed {len(request.commits)} commits, but encountered an error storing results",
                    "error": storage_result["error"],
                    "analyses_count": len(all_analyses)
                }
            
            return {
                "status": "success",
                "message": f"Successfully analyzed {len(request.commits)} commits and stored {len(all_analyses)} analyses",
                "analyses_count": len(all_analyses)
            }
        else:
            return {
                "status": "warning",
                "message": f"Processed {len(request.commits)} commits, but no analyses were generated",
                "analyses_count": 0
            }
            
    except Exception as e:
        logger.error(f"Error in analyze_commits endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing commits: {str(e)}")
