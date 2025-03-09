from typing import List, Dict, Any
from pydantic import BaseModel

class Document(BaseModel):
    vector: List[float]
    subcommit_id: str
    metadata: Dict[str, Any]
