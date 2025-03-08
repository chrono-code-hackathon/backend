from pydantic import BaseModel, Field
from typing import List, Optional

class File(BaseModel):
    """
    Represents a file changed in a commit.
    """
    filename: str = Field(description="The name of the file.")
    additions: int = Field(description="The number of lines added in this file.")
    deletions: int = Field(description="The number of lines deleted in this file.")
    changes: int = Field(description="The total number of lines changed (additions + deletions).")
    status: str = Field(description="The status of the file (e.g., 'modified', 'added', 'deleted').")
    raw_url: str = Field(description="URL to view the raw content of the file at this commit.")
    blob_url: str = Field(description="URL to view the file's blob (content) in the repository.")
    patch: Optional[str] = Field(default=None, description="The patch (diff) for the file, showing the exact changes.")

class Commit(BaseModel):
    """
    Represents a Git commit.
    """
    created_at: str = Field(description="Timestamp indicating when the commit was recorded.")
    repo_name: str = Field(description="The name of the repository the commit belongs to.")
    sha: str = Field(description="The SHA hash of the commit.")
    author: str = Field(description="The name of the commit author.")
    date: str = Field(description="The date of the commit.")
    message: str = Field(description="The commit message.")
    url: str = Field(description="URL to view the commit in the repository.")
    author_email: str = Field(description="The email address of the commit author.")
    description: Optional[str] = Field(default=None, description="A more detailed description of the commit.")
    author_url: str = Field(description="URL to the author's profile or page.")
    files: List[File] = Field(description="A list of files changed in this commit.")

from enum import Enum
from pydantic import BaseModel, Field
from typing import List

class CommitType(str, Enum):
    """
    Classify this commit into EXACTLY ONE of the following categories based on its primary purpose:
    FEATURE: New functionality, capabilities, or user-facing enhancements
    BUG: Correction of errors, unexpected behavior, or issues affecting functionality
    REFACTOR: Code restructuring, optimization, or cleanup without changing external behavior
    DOCS: Documentation updates, comments, README changes, or other non-code explanatory content
    TEST: Addition or modification of test cases, test infrastructure, or testing utilities
    STYLE: Code formatting, whitespace changes, or other cosmetic adjustments
    CHORE: Routine maintenance tasks, dependency updates, version bumps, or build process changes
    MILESTONE: Significant project achievement, version release, or major integration point
    WARNING: Introduction of potential issues, technical debt, or code that requires future attention
    """
    FEATURE = "FEATURE"
    BUG = "BUG"
    REFACTOR = "REFACTOR"
    DOCS = "DOCS"
    TEST = "TEST"
    STYLE = "STYLE"
    CHORE = "CHORE"
    MILESTONE = "MILESTONE"
    WARNING = "WARNING"

    def __str__(self):
        return self.value

class SubCommitAnalysis(BaseModel):
    """
    Represents a logical unit of work identified within a larger commit.
    
    A SubCommit is a focused, single-purpose change that may be part of a larger commit.
    For example, a single GitHub commit might contain multiple logical changes like
    fixing a bug, updating documentation, and refactoring code - each would be a separate SubCommit.
    """
    title: str = Field(description="A concise, descriptive title summarizing this specific unit of work within the commit.")
    idea: str = Field(description="The core concept or purpose behind this specific change, explaining the 'why' of this particular modification.")
    description: str = Field(description="A detailed technical explanation of what was changed, how it works, why it matters, and any potential implications or considerations.")
    type: CommitType = Field(description="The category of change (e.g., 'bug fix', 'feature', 'refactoring', 'documentation', 'performance', 'security', etc.).")
    commit_sha: str = Field(default="", description="IGNORE THIS FIELD. It is automatically populated by the system.")
    epic: str = Field(default="", description="IGNORE THIS FIELD. It is automatically populated by the system.")
    
class SubCommitAnalysisList(BaseModel):
    """
    Represents a collection of logical units of work (SubCommits) identified within a single GitHub commit.
    
    Since many commits modify multiple files and address multiple concerns or topics,
    this model contains all the distinct logical units of work that were identified
    within a single commit. Each SubCommit focuses on ONE logical change, even if
    the original commit contained multiple unrelated changes.
    """
    analysis: List[SubCommitAnalysis] = Field(description="The list of SubCommit analyses, where each item represents a distinct, focused unit of work identified within the original commit.")

class Epic(BaseModel):
    """
    Represents an Epic, grouping related sub-commits.
    """
    title: str = Field(description="Generate a full very short title for an epic given the subcommits lists, must be very precise the title representing the changes in the subcommits")

class SubCommitNeighbors(BaseModel):
    """
    Represents the neighboring sub-commits of a given sub-commit.
    This model contains a list of the most semantically similar sub-commits to a given input sub-commit.
    """
    subcommits: List[SubCommitAnalysis] = Field(description="The list of sub-commits that are the most similar neighbors to the given sub-commit, based on semantic similarity.")
