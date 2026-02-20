from pydantic import BaseModel, Field
from typing import Optional

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    subject: str