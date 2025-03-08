from langchain_google_genai import ChatGoogleGenerativeAI
from app.models.models_commit import Epic, SubCommitAnalysisList, Commit, SubCommitNeighbors, SubCommitAnalysis
from app.config.settings import settings
from app.prompts.system_prompt import format_commit_analysis_prompt, format_epic_analysis_prompt, format_subcommit_neighbors_prompt

gemini_2_0_flash = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2, api_key=settings.GOOGLE_API_KEY)

model_structured_commit_analysis = gemini_2_0_flash.with_structured_output(SubCommitAnalysisList)
model_structured_subcommit_neighbors = gemini_2_0_flash.with_structured_output(SubCommitNeighbors)
model_structured_epic_analysis = gemini_2_0_flash.with_structured_output(Epic)

async def get_commit_analysis(commit: Commit) -> SubCommitAnalysisList:
    formatted_prompt = format_commit_analysis_prompt(commit)
    return await model_structured_commit_analysis.ainvoke(
        formatted_prompt
    )

async def get_epic_analysis(neighbors: SubCommitNeighbors) -> Epic:
    formatted_prompt = format_epic_analysis_prompt(neighbors)
    return await model_structured_epic_analysis.ainvoke(
        formatted_prompt
    )

async def get_subcommit_neighbors_analysis(subcommit_analysis: SubCommitAnalysis) -> SubCommitNeighbors:
    formatted_prompt = format_subcommit_neighbors_prompt(subcommit_analysis)
    return await model_structured_subcommit_neighbors.ainvoke(
        formatted_prompt
    )