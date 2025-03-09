from typing import List, Dict, Any
from pydantic import BaseModel

class Document(BaseModel):
    vector: list[float]
    subcommit_id: int
    metadata: Dict[str, Any]
