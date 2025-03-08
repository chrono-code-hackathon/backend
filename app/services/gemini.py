from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.models_commit import Epic, SubCommitAnalysisList, Commit, SubCommitNeighbors, SubCommitAnalysis
from app.config.settings import settings
from app.prompts.system_prompt import format_commit_analysis_prompt, format_epic_analysis_prompt, format_subcommit_neighbors_prompt
from app.logger.logger import logger

gemini_2_0_flash = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2, api_key=settings.GOOGLE_API_KEY)

model_structured_commit_analysis = gemini_2_0_flash.with_structured_output(SubCommitAnalysisList)
model_structured_subcommit_neighbors = gemini_2_0_flash.with_structured_output(SubCommitNeighbors)
model_structured_epic_analysis = gemini_2_0_flash.with_structured_output(Epic)

async def get_commit_analysis(commit: Commit) -> SubCommitAnalysisList:
    logger.info(f"Analyzing commit: {commit.sha}")
    formatted_prompt = format_commit_analysis_prompt(commit)
    logger.debug(f"Formatted prompt for commit analysis: {formatted_prompt}")
    analysis_result: SubCommitAnalysisList = await model_structured_commit_analysis.ainvoke(
        formatted_prompt
    )
    logger.info(f"Successfully analyzed commit: {commit.sha}")
    
    for subcommit in analysis_result.analysis:
        subcommit.commit_sha = commit.sha
    return analysis_result

async def get_epic_analysis(neighbors: SubCommitNeighbors) -> Epic:
    logger.info(f"Analyzing epic based on {len(neighbors.neighbors)} neighbors")
    formatted_prompt = format_epic_analysis_prompt(neighbors)
    logger.debug(f"Formatted prompt for epic analysis: {formatted_prompt}")
    epic_result = await model_structured_epic_analysis.ainvoke(
        formatted_prompt
    )
    logger.info(f"Successfully analyzed epic")
    return epic_result

async def get_subcommit_neighbors_analysis(subcommit_analysis: SubCommitAnalysis) -> SubCommitNeighbors:
    logger.info(f"Analyzing subcommit neighbors for: {subcommit_analysis.sub_commit_id}")
    formatted_prompt = format_subcommit_neighbors_prompt(subcommit_analysis)
    logger.debug(f"Formatted prompt for subcommit neighbors analysis: {formatted_prompt}")
    neighbors_result = await model_structured_subcommit_neighbors.ainvoke(
        formatted_prompt
    )
    logger.info(f"Successfully analyzed subcommit neighbors for: {subcommit_analysis.sub_commit_id}")
    return neighbors_result