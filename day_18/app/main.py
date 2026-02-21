"""POST /api/index
    Input: file (PDF), subject (string)
    1. Save uploaded file temporarily
    2. Call smart_rag.index_by_subject(file, subject)
    3. Return chunk count

POST /api/smart-query
    Input: {"question": "..."}
    1. Call smart_rag.smart_query(question)
    2. Return result with subject detection + answer

GET /api/subjects
    Return list of available subjects

GET /health
    Return system status"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import Optional
from app.smart_rag import SmartRAGService
from app.models import QueryRequest, QueryResponse, DocumentUpload
import os
import shutil
from datetime import datetime
import uuid
app = FastAPI(
    title="smart RAG",
    description="get question and answer them",
    version="1.0"
    )

rag = SmartRAGService()
os.makedirs("./uploads", exist_ok=True)

@app.post("/api/index", response_model=DocumentUpload)
async def index_query(subject: str, file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail=f"Invalid file content : {file.content_type}")
    doc_id = str(uuid.uuid4())

    destination_path = f"./uploads/{doc_id}.pdf"

    try:
        with open(destination_path, "wb") as f: 
            shutil.copyfileobj(file.file, f)
        print(f"file successfully saved to {destination_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fail in saving file {str(e)}")
    

    chunks_size = rag.index_by_subject(destination_path, subject)
    return DocumentUpload(
        file_name= file.filename,
        upload_date= datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
        chunks_size= chunks_size
    )

@app.post("/api/smart-query", response_model=QueryResponse)
async def smart_query(request : QueryRequest):
    question = request.question
    result = rag.smart_query(question)

    return QueryResponse(
        subject= result['detected_subject'],
        answer= result['answer'],
        confidence= result['confidence'],
        sources= result['sources']
    )

