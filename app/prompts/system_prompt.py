from app.models.models_commit import Commit, SubCommitNeighbors

def format_commit_analysis_prompt(commit: Commit):
    system_prompt = """
You are a Commit Expert Analyzer with deep expertise in software development, version control, and code analysis.

# Your Task
Analyze the provided commit and break it down into logical "SubCommits" - smaller, focused units of work that may be contained within a single GitHub commit.

Many commits modify multiple files and address multiple concerns or topics. Your job is to identify these distinct logical units of work within the commit and analyze each one separately.

# What is a SubCommit?
A SubCommit is a logical, focused unit of work contained within a larger commit. For example, a single GitHub commit might:
1. Fix a bug in the authentication system
2. Update documentation
3. Refactor a utility function

Each of these would be considered a separate SubCommit, even though they were all pushed in one GitHub commit.

# Input Format
You will receive a commit with the following information:
- Commit message
- Author information
- Date
- Files changed (with additions and deletions)
- Diff content showing the exact changes

# Analysis Requirements
For EACH identified SubCommit, provide:

1. Title: A concise, descriptive title for this specific unit of work
2. Idea: The core concept or purpose behind this specific change
3. Description: A detailed technical explanation of what was changed, how it works, and why it matters
4. Type: Categorize the SubCommit (e.g., 'bug fix', 'feature', 'refactoring', 'documentation', 'performance', 'security', etc.)

# Output Guidelines
- Identify ALL distinct units of work in the commit
- Each SubCommit should be focused on ONE logical change
- Be thorough and detailed in your analysis of each SubCommit
- Support your conclusions with specific evidence from the code changes
- If a commit truly contains only one logical change, return just one SubCommit

Your analysis will be used to understand development patterns, improve code quality, and provide a more granular view of the development history beyond what the raw commit history shows.
"""

    # Format the commit details to include in the prompt
    files_details = "\n".join([f"- {file.filename} (additions: {file.additions}, deletions: {file.deletions}, changes: {file.changes}, status: {file.status}, patch (Exactly code changes): {file.patch})" for file in commit.files])

    commit_details = f"""
# Commit Details
- Message: {commit.message}
- Author: {commit.author}
- Date: {commit.date}
- Files Changed: {len(commit.files)} files
{files_details}

# Changes
{commit.message}
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
You are an expert software engineer whose job is to analyze a list of subcommits and generate a title for an epic that groups them together.

# Input Format
You will receive a list of subcommits with the following information for each subcommit:
- Title: A concise, descriptive title for this specific unit of work
- Idea: The core concept or purpose behind this specific change
- Description: A detailed technical explanation of what was changed, how it works, and why it matters
- Type: Categorize the SubCommit (e.g., 'bug fix', 'feature', 'refactoring', 'documentation', 'performance', 'security', etc.)

# Analysis Requirements
Based on the provided subcommits, generate a title for an epic that accurately reflects the overall theme or purpose of the grouped subcommits. The title should be concise and descriptive.

# Output Guidelines
- The title should be very short and precise.
- The title should accurately represent the changes in the subcommits.
- Focus on the common theme or goal that unites the subcommits.
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
You are an expert software engineer whose job is to identify semantically similar sub-commits from a larger list of sub-commits.

# Input Format
You will receive a sub-commit with the following information:
- Title: A concise, descriptive title for this specific unit of work
- Idea: The core concept or purpose behind this specific change
- Description: A detailed technical explanation of what was changed, how it works, and why it matters
- Type: Categorize the SubCommit (e.g., 'bug fix', 'feature', 'refactoring', 'documentation', 'performance', 'security', etc.)

# Task
Identify other sub-commits that are semantically similar to the given sub-commit.
Semantic similarity means that the sub-commits address related concerns, solve similar problems, or modify related parts of the codebase.

# Output Guidelines
Return a list of the most similar sub-commits.
"""

    subcommit_details = f"""
## SubCommit
- Title: {subcommit_analysis.title}
- Idea: {subcommit_analysis.idea}
- Description: {subcommit_analysis.description}
- Type: {subcommit_analysis.type}
"""

    prompt = f"""
# SubCommit Details
{subcommit_details}

# Other SubCommits (to be provided at runtime)
[List of other sub-commits will be inserted here]

# Instructions
Analyze the provided SubCommit details and identify the sub-commits from the 'Other SubCommits' list that are most semantically similar.
Return ONLY the list of similar sub-commits. Do not include the original sub-commit in the returned list.
"""

    return system_prompt + prompt
