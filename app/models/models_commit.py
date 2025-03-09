from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

class Repository(BaseModel):
    name: str
    id: str
    url: str
    
class File(BaseModel):
    filename: str
    additions: int
    deletions: int
    changes: int
    status: str
    raw_url: str
    blob_url: str
    patch: Optional[str]


class Commit(BaseModel):
    sha: str
    author: str
    date: str
    message: str
    url: str
    author_email: str
    description: Optional[str]
    author_url: str
    repo_id: str = ""
    files: List[File]

class CommitType(str, Enum):
    """
    Classify this commit into EXACTLY ONE of the following categories based on its primary purpose:
    FEATURE: New functionality, capabilities, or user-facing enhancements
    BUG: Correction of errors, unexpected behavior, or issues affecting functionality
    REFACTOR: Code restructuring, optimization, or cleanup without changing external behavior
    DOCS: Documentation updates, comments, README changes, or other non-code explanatory content
    CHORE: Routine maintenance tasks, dependency updates, version bumps, or build process changes
    MILESTONE: Significant project achievement, version release, or major integration point
    WARNING: Introduction of potential issues, technical debt, or code that requires future attention
    """
    FEATURE = "FEATURE"
    BUG = "BUG"
    REFACTOR = "REFACTOR"
    DOCS = "DOCS"
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
    title: str = Field(description="A concise, specific title (5-10 words) that precisely captures what this unit of work accomplishes.")
    idea: str = Field(description="The core concept or purpose (max 15 sentences) explaining why this change was made and what problem it solves.")
    description: str = Field(description="A comprehensive technical explanation detailing implementation specifics, architectural changes, and potential downstream effects.")
    type: CommitType = Field(description="The primary category that best represents the nature of this change, selected from the CommitType enum.")
    commit_sha: str = Field(default="", description="The SHA identifier of the parent commit. Automatically populated by the system.")
    epic: str = Field(default="", description="The epic title that groups related sub-commits. Automatically populated by the system.")
    files: List[File] = Field(default_factory=list, description="The specific files modified as part of this logical unit of work, including their patches and change statistics.")

class SubCommitAnalysisList(BaseModel):
    """
    Represents a collection of logical units of work (SubCommits) identified within a single GitHub commit.
    
    Since many commits modify multiple files and address multiple concerns or topics,
    this model contains all the distinct logical units of work that were identified
    within a single commit. Each SubCommit focuses on ONE logical change, even if
    the original commit contained multiple unrelated changes.
    """
    analysis: List[SubCommitAnalysis] = Field(description="The complete set of distinct, focused units of work extracted from the original commit, where each unit addresses exactly one logical change or purpose.")

class Epic(BaseModel):
    """
    Represents an Epic, grouping related sub-commits.
    
    An Epic captures the common theme or purpose across multiple related sub-commits,
    providing a higher-level view of software development activities.
    """
    title: str = Field(description="A precise, concise title (5-8 words) that captures the common theme or technical purpose unifying the related sub-commits, focusing on technical substance rather than process, and avoiding generic terms like 'improvements' or 'updates'.")

class SubCommitNeighbors(BaseModel):
    """
    Represents the neighboring sub-commits of a given sub-commit.
    
    This model contains a list of the most semantically similar sub-commits to a given input sub-commit,
    based on technical domain, modified components, problem being solved, implementation approach,
    and change type.
    """
    subcommits: List[SubCommitAnalysis] = Field(description="A collection of sub-commits that share semantic similarity with a reference sub-commit, ordered by relevance and thematic connection.")
