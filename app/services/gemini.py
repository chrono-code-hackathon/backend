from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.models_commit import Epic, SubCommitAnalysisList, Commit, SubCommitNeighbors, SubCommitAnalysis, SubCommitFileAnalysis
from app.config.settings import settings
from app.prompts.system_prompt import (
    format_commit_analysis_prompt, 
    format_epic_analysis_prompt, 
    format_subcommit_neighbors_prompt,
    format_subcommit_files_prompt
)
from app.logger.logger import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result
import asyncio
import uuid
from typing import List, Dict, Any

# Add a simple cache to avoid duplicate commit analysis
_commit_analysis_cache = {}

def is_empty_analysis(result: SubCommitAnalysisList) -> bool:
    """Check if the analysis result is empty or contains no analysis."""
    return result is None or result.analysis is None or len(result.analysis) == 0

# Create base models with appropriate settings
gemini_2_0_flash = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2, api_key=settings.GOOGLE_API_KEY)
gemini_1_5_pro = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.2, api_key=settings.GOOGLE_API_KEY)

# Create structured output models with proper fallback chains
model_structured_commit_analysis = gemini_2_0_flash.with_structured_output(SubCommitAnalysisList)
model_structured_commit_analysis_fallback = gemini_1_5_pro.with_structured_output(SubCommitAnalysisList)
model_commit_with_fallback = model_structured_commit_analysis.with_fallbacks([model_structured_commit_analysis_fallback])

# Create models for file analysis
model_structured_file_analysis = gemini_2_0_flash.with_structured_output(SubCommitFileAnalysis)
model_structured_file_analysis_fallback = gemini_1_5_pro.with_structured_output(SubCommitFileAnalysis)
model_file_analysis_with_fallback = model_structured_file_analysis.with_fallbacks([model_structured_file_analysis_fallback])

model_structured_subcommit_neighbors = gemini_2_0_flash.with_structured_output(SubCommitNeighbors)
model_structured_subcommit_neighbors_fallback = gemini_1_5_pro.with_structured_output(SubCommitNeighbors)
model_neighbors_with_fallback = model_structured_subcommit_neighbors.with_fallbacks([model_structured_subcommit_neighbors_fallback])

model_structured_epic_analysis = gemini_2_0_flash.with_structured_output(Epic)
model_structured_epic_analysis_fallback = gemini_1_5_pro.with_structured_output(Epic)
model_epic_with_fallback = model_structured_epic_analysis.with_fallbacks([model_structured_epic_analysis_fallback])

@retry(
    stop=stop_after_attempt(settings.retries),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception) | retry_if_result(is_empty_analysis),
    reraise=True
)
async def get_commit_analysis(commit: Commit) -> SubCommitAnalysisList:
    # Check if we've already analyzed this commit
    if commit.sha in _commit_analysis_cache:
        logger.info(f"Using cached analysis for commit: {commit.sha}")
        return _commit_analysis_cache[commit.sha]
        
    logger.info(f"Analyzing commit: {commit.sha}")
    formatted_prompt = format_commit_analysis_prompt(commit)
    logger.debug(f"Formatted prompt for commit analysis: {formatted_prompt}")
    try:
        analysis_result: SubCommitAnalysisList = await model_commit_with_fallback.ainvoke(
            formatted_prompt
        )
        
        # If Gemini returns None, try fallback model directly
        if analysis_result is None:
            logger.warning(f"Gemini returned None for commit {commit.sha}. Trying fallback model directly...")
            analysis_result = await model_structured_commit_analysis_fallback.ainvoke(
                formatted_prompt
            )
    except Exception as e:
        logger.error(f"Failed to analyze commit {commit.sha}: {str(e)}")
        logger.error(f"AI Error details: {repr(e)}")
        raise  # Re-raise to trigger retry

    if is_empty_analysis(analysis_result):
        logger.warning(f"LLM returned empty analysis for commit {commit.sha}. Retrying...")
        logger.error(f"Empty analysis result: {repr(analysis_result)}")
        raise Exception("Empty analysis result")  # Force retry

    logger.info(f"Successfully analyzed commit: {commit.sha}")
    
    # Set commit_sha for each subcommit
    for subcommit in analysis_result.analysis:
        subcommit.commit_sha = commit.sha
    
    # Only perform file analysis if the commit has files
    if commit.files and len(commit.files) > 0:
        # Now perform file analysis for each subcommit
        file_analysis_tasks = [get_subcommit_file_analysis(commit, subcommit) for subcommit in analysis_result.analysis]
        file_analysis_results = await asyncio.gather(*file_analysis_tasks, return_exceptions=True)
        
        # Assign files to each subcommit
        for i, result in enumerate(file_analysis_results):
            if isinstance(result, Exception):
                logger.error(f"Error analyzing files for subcommit {analysis_result.analysis[i].title}: {str(result)}, AI Error: {result}")
            else:
                analysis_result.analysis[i].files = result.files
    else:
        logger.warning(f"Commit {commit.sha} has no files, skipping file analysis")
    
    # Cache the result before returning
    _commit_analysis_cache[commit.sha] = analysis_result
    
    return analysis_result

@retry(
    stop=stop_after_attempt(settings.retries),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def get_subcommit_file_analysis(commit: Commit, subcommit: SubCommitAnalysis) -> SubCommitFileAnalysis:
    """
    Analyze which files from the commit belong to a specific subcommit.
    
    Args:
        commit: The original commit containing all files
        subcommit: The subcommit to analyze for file relevance
        
    Returns:
        SubCommitFileAnalysis with the list of files relevant to this subcommit
    """
    # Safety check - ensure commit has files
    if not commit.files or len(commit.files) == 0:
        logger.warning(f"No files to analyze for subcommit: {subcommit.title}")
        return SubCommitFileAnalysis(files=[])
        
    logger.info(f"Analyzing files for subcommit: {subcommit.title}")
    formatted_prompt = format_subcommit_files_prompt(commit, subcommit)
    logger.debug(f"Formatted prompt for subcommit file analysis: {formatted_prompt}")
    
    try:
        file_analysis_result = await model_file_analysis_with_fallback.ainvoke(
            formatted_prompt
        )
        
        # If Gemini returns None, try fallback model directly
        if file_analysis_result is None:
            logger.warning(f"Gemini returned None for file analysis of subcommit {subcommit.title}. Trying fallback model directly...")
            file_analysis_result = await model_structured_file_analysis_fallback.ainvoke(
                formatted_prompt
            )
    except Exception as e:
        logger.error(f"Failed to analyze files for subcommit {subcommit.title}: {str(e)}")
        logger.error(f"AI Error details: {repr(e)}")
        raise  # Re-raise to trigger retry
    
    logger.info(f"Successfully analyzed files for subcommit: {subcommit.title}")
    return file_analysis_result

async def analyze_commits_batch(commits: List[Commit]) -> List[SubCommitAnalysis]:
    """
    Analyze a batch of commits concurrently using asyncio.gather
    
    Args:
        commits: List of Commit objects to analyze
        
    Returns:
        List of SubCommitAnalysis objects
    """
    logger.info(f"Starting concurrent analysis of {len(commits)} commits")
    
    # Create tasks for each commit
    tasks = [get_commit_analysis(commit) for commit in commits]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    all_analyses = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Error analyzing commit {commits[i].sha}: {str(result)}")
            logger.error(f"AI Error details: {repr(result)}")
        elif result and result.analysis:
            all_analyses.extend(result.analysis)
        else:
            logger.warning(f"No analyses generated for commit: {commits[i].sha}")
            if result:
                logger.error(f"Empty result details: {repr(result)}")
    
    logger.info(f"Completed concurrent analysis, generated {len(all_analyses)} analyses")
    return all_analyses

@retry(
    stop=stop_after_attempt(settings.retries),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def get_epic_analysis(neighbors: SubCommitNeighbors) -> Epic:
    logger.info(f"Analyzing epic based on {len(neighbors.neighbors)} neighbors")
    formatted_prompt = format_epic_analysis_prompt(neighbors)
    logger.debug(f"Formatted prompt for epic analysis: {formatted_prompt}")
    
    try:
        epic_result = await model_epic_with_fallback.ainvoke(
            formatted_prompt
        )
        
        # If Gemini returns None, try fallback model directly
        if epic_result is None:
            logger.warning(f"Gemini returned None for epic analysis. Trying fallback model directly...")
            epic_result = await model_structured_epic_analysis_fallback.ainvoke(
                formatted_prompt
            )
    except Exception as e:
        logger.error(f"Failed to analyze epic: {str(e)}")
        logger.error(f"AI Error details: {repr(e)}")
        raise  # Re-raise to trigger retry
        
    logger.info(f"Successfully analyzed epic")
    return epic_result

@retry(
    stop=stop_after_attempt(settings.retries),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def get_subcommit_neighbors_analysis(subcommit_analysis: SubCommitAnalysis) -> SubCommitNeighbors:
    logger.info(f"Analyzing subcommit neighbors for: {subcommit_analysis.title}")
    formatted_prompt = format_subcommit_neighbors_prompt(subcommit_analysis)
    logger.debug(f"Formatted prompt for subcommit neighbors analysis: {formatted_prompt}")
    
    try:
        neighbors_result = await model_neighbors_with_fallback.ainvoke(
            formatted_prompt
        )
        
        # If Gemini returns None, try fallback model directly
        if neighbors_result is None:
            logger.warning(f"Gemini returned None for neighbors analysis of {subcommit_analysis.title}. Trying fallback model directly...")
            neighbors_result = await model_structured_subcommit_neighbors_fallback.ainvoke(
                formatted_prompt
            )
    except Exception as e:
        logger.error(f"Failed to analyze subcommit neighbors for {subcommit_analysis.title}: {str(e)}")
        logger.error(f"AI Error details: {repr(e)}")
        raise  # Re-raise to trigger retry
        
    logger.info(f"Successfully analyzed subcommit neighbors for: {subcommit_analysis.title}")
    return neighbors_result
