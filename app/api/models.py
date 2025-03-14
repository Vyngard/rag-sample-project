from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

class DocumentBase(BaseModel):
    content: str
    meta_info: Optional[Dict[str, Any]] = {}

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class Query(BaseModel):
    query: str
    top_k: Optional[int] = 3
    model: Optional[str] = "gpt-3.5-turbo"

class RAGResponse(BaseModel):
    answer: str
    sources: List[Document]