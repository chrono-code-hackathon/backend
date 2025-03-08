from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
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
    repo_id: str
    files: List[File]

class CommitAnalysis(BaseModel):
    id: int
    created_at: datetime
    title: str
    idea: str
    description: str
    commit_sha: str
    type: str
    epic: str 
    files: List[File]
