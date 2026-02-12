from pydantic import BaseModel, Field
from typing import Optional, List

class DocumentUpload(BaseModel):
    """Response when document is uploaded"""
    doc_id: str
    filename: str
    chunks: int
    status: str

class QueryRequest(BaseModel):
    """Request to query documents"""
    question: str = Field(..., min_length=3)
    doc_id: Optional[str] = None

class QueryResponse(BaseModel):
    """Respose with answer and sources"""
    question: str
    answer: str
    sources: List[dict]
    confidence: Optional[float] = None

class DocumentInfo(BaseModel):
    """Document metadata"""
    doc_id: str
    filename: str
    upload_date: str
    chunks : int
