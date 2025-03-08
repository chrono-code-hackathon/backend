from app.test.mock_commits import mock_commits
from app.services.gemini import get_commit_analysis
import asyncio
import json

async def main():
    analyses = []
    for commit in mock_commits:
        analysis = await get_commit_analysis(commit)
        analyses.append(analysis)

    for i, analysis in enumerate(analyses):
        print(f"--- Analysis {i+1}/{len(analyses)} ---")
        print(json.dumps(analysis.model_dump(), indent=4))
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())
