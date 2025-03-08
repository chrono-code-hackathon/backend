from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Commit(BaseModel):
    created_at: datetime
    repo_name: str
    sha: str
    author: str
    date: str
    message: str
    url: str
    author_email: str
    description: Optional[str]
    author_url: str

class CommitAnalysis(BaseModel):
    id: int
    created_at: datetime
    repo_name: str
    title: str
    idea: str
    description: str
    commit_sha: str
    type: str
