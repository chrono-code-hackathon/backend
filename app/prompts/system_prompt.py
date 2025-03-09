from typing import List
from app.models.models_commit import Commit, File, SubCommitNeighbors, SubCommitAnalysis

def format_commit_analysis_prompt(commit: Commit):
    system_prompt = """
You are a Commit Expert Analyzer specializing in code analysis and software development patterns.

# Task
Identify distinct logical units of work ("SubCommits") within this single GitHub commit.

# SubCommit Definition
A SubCommit is ONE focused, logical change within a larger commit. Example: a commit might contain bug fixes, documentation updates, and refactoring - each is a separate SubCommit.

# Analysis Requirements
For EACH SubCommit, provide:
1. Title: Concise description (5-10 words)
2. Idea: Core purpose of this specific change (1-2 sentences)
3. Description: Technical explanation of changes, implementation details, and implications (3-5 sentences)
4. Type: Categorize as FEATURE, BUG, REFACTOR, DOCS, TEST, STYLE, CHORE, MILESTONE, or WARNING

# Guidelines
- Identify ALL distinct units of work
- Each SubCommit must focus on ONE logical change
- Support conclusions with specific code evidence
- If truly only one logical change exists, return just one SubCommit
"""

    # Format the commit details to include in the prompt
    files_details = "\n".join([f"- {file.filename} (additions: {file.additions}, deletions: {file.deletions}, changes: {file.changes}, status: {file.status}, patch: {file.patch})" for file in commit.files])

    commit_details = f"""
# Commit Details
- Message: {commit.message}
- Author: {commit.author}
- Date: {commit.date}
- Files Changed: {len(commit.files)} files
{files_details}
"""

    # Combine the system prompt with the commit details
    return system_prompt + commit_details

def format_epic_analysis_prompt(neighbors: SubCommitNeighbors) -> str:
    """
    Formats the prompt for epic analysis.

    Args:
        neighbors: SubCommitNeighbors object containing the neighboring sub-commits.

    Returns:
        str: The formatted prompt.
    """
    system_prompt = """
You are an Epic Title Generator for software development projects.

# Task
Generate a precise, concise title (5-8 words) for an epic that groups these related subcommits.

# Guidelines
- Title must capture the common theme or purpose
- Be extremely specific about what changed
- Focus on technical substance, not process
- Avoid generic terms like "improvements" or "updates"
"""

    subcommits_details = "\n".join([f"""
## SubCommit
- Title: {subcommit.title}
- Idea: {subcommit.idea}
- Description: {subcommit.description}
- Type: {subcommit.type}
""" for subcommit in neighbors.subcommits])

    prompt = f"""
# SubCommits Details
{subcommits_details}
"""

    return system_prompt + prompt

def format_subcommit_neighbors_prompt(subcommit_analysis: SubCommitAnalysis) -> str:
    """
    Formats the prompt for finding neighboring sub-commits.

    Args:
        subcommit_analysis: SubCommitAnalysis object representing the sub-commit.

    Returns:
        str: The formatted prompt.
    """
    system_prompt = """
You are a Semantic Similarity Analyzer for code changes.

# Task
Identify semantically similar sub-commits from the provided list.

# Similarity Criteria (in priority order)
1. Technical domain (authentication, database, UI, etc.)
2. Modified components or subsystems
3. Problem being solved
4. Implementation approach
5. Change type (feature, bug fix, etc.)

# Output Requirements
Return ONLY the most similar sub-commits, ranked by similarity.
"""

    subcommit_details = f"""
## Target SubCommit
- Title: {subcommit_analysis.title}
- Idea: {subcommit_analysis.idea}
- Description: {subcommit_analysis.description}
- Type: {subcommit_analysis.type}
"""

    prompt = f"""
# Target SubCommit Details
{subcommit_details}

# Candidate SubCommits (to be provided at runtime)
[List of other sub-commits will be inserted here]

# Instructions
Return ONLY the most similar sub-commits. Exclude the target sub-commit from results.
"""

    return system_prompt + prompt

def format_subcommit_files_prompt(commit: Commit, subcommit: SubCommitAnalysis) -> str:
    """
    Format a prompt for analyzing which files from a commit belong to a specific subcommit.
    
    Args:
        commit: The original commit containing all files
        subcommit: The subcommit to analyze for file relevance
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""
    # File Analysis Task
    
    ## Original Commit
    - SHA: {commit.sha}
    - Message: {commit.message}
    - Description: {commit.description or "N/A"}
    
    ## Files in Original Commit
    {format_files_list(commit.files)}
    
    ## SubCommit Information
    - Title: {subcommit.title}
    - Idea: {subcommit.idea}
    - Description: {subcommit.description}
    - Type: {subcommit.type}
    
    ## Task
    Analyze which specific files from the original commit are relevant to this particular logical unit of work (SubCommit).
   
    """
    
    return prompt

def format_files_list(files: List[File]) -> str:
    """Helper function to format the list of files for the prompt"""
    files_text = ""
    for i, file in enumerate(files):
        files_text += f"""
        File {i+1}:
        - Filename: {file.filename}
        - Status: {file.status}
        - Changes: +{file.additions}, -{file.deletions}, total: {file.changes}
        - Patch:
        ```
        {file.patch or "No patch available"}
        ```
        
        """
    return files_text
