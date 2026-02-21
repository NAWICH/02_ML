from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DocumentUpload(BaseModel):
    file_name: str
    upload_date: str
    chunks_size: int
    
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    subject: str
    answer: str
    confidence: float
    sources: List[Dict[str, Any]]