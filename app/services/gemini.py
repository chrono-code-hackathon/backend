from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from app.models.models_commit import Epic, SubCommitAnalysisList, Commit, SubCommitNeighbors, SubCommitAnalysis
from app.config.settings import settings
from app.prompts.system_prompt import format_commit_analysis_prompt, format_epic_analysis_prompt, format_subcommit_neighbors_prompt
from app.logger.logger import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import asyncio
from typing import List, Dict, Any

# Create base models with appropriate settings
gemini_2_0_flash = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2, api_key=settings.GOOGLE_API_KEY)
gpt_4o = ChatOpenAI(model="gpt-4o", temperature=0.2, api_key=settings.OPENAI_API_KEY)

# Create structured output models with proper fallback chains
model_structured_commit_analysis = gemini_2_0_flash.with_structured_output(SubCommitAnalysisList)
model_structured_commit_analysis_fallback = gpt_4o.with_structured_output(SubCommitAnalysisList)
model_commit_with_fallback = model_structured_commit_analysis.with_fallbacks([model_structured_commit_analysis_fallback])

model_structured_subcommit_neighbors = gemini_2_0_flash.with_structured_output(SubCommitNeighbors)
model_structured_subcommit_neighbors_fallback = gpt_4o.with_structured_output(SubCommitNeighbors)
model_neighbors_with_fallback = model_structured_subcommit_neighbors.with_fallbacks([model_structured_subcommit_neighbors_fallback])

model_structured_epic_analysis = gemini_2_0_flash.with_structured_output(Epic)
model_structured_epic_analysis_fallback = gpt_4o.with_structured_output(Epic)
model_epic_with_fallback = model_structured_epic_analysis.with_fallbacks([model_structured_epic_analysis_fallback])

@retry(
    stop=stop_after_attempt(settings.retries),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def get_commit_analysis(commit: Commit) -> SubCommitAnalysisList:
    logger.info(f"Analyzing commit: {commit.sha}")
    formatted_prompt = format_commit_analysis_prompt(commit)
    logger.debug(f"Formatted prompt for commit analysis: {formatted_prompt}")
    analysis_result: SubCommitAnalysisList = await model_commit_with_fallback.ainvoke(
        formatted_prompt
    )
    logger.info(f"Successfully analyzed commit: {commit.sha}")
    
    for subcommit in analysis_result.analysis:
        subcommit.commit_sha = commit.sha
    return analysis_result

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
        elif result and result.analysis:
            all_analyses.extend(result.analysis)
        else:
            logger.warning(f"No analyses generated for commit: {commits[i].sha}")
    
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
    epic_result = await model_epic_with_fallback.ainvoke(
        formatted_prompt
    )
    logger.info(f"Successfully analyzed epic")
    return epic_result

@retry(
    stop=stop_after_attempt(settings.retries),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
async def get_subcommit_neighbors_analysis(subcommit_analysis: SubCommitAnalysis) -> SubCommitNeighbors:
    logger.info(f"Analyzing subcommit neighbors for: {subcommit_analysis.sub_commit_id}")
    formatted_prompt = format_subcommit_neighbors_prompt(subcommit_analysis)
    logger.debug(f"Formatted prompt for subcommit neighbors analysis: {formatted_prompt}")
    neighbors_result = await model_neighbors_with_fallback.ainvoke(
        formatted_prompt
    )
    logger.info(f"Successfully analyzed subcommit neighbors for: {subcommit_analysis.sub_commit_id}")
    return neighbors_result