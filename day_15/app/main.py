from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.rag_service import RAGService
from app.models import QueryRequest, QueryResponse, DocumentUpload, DocumentInfo
import uuid
import shutil
import os

app = FastAPI(title="Document Q&A API",
               description="Upload PDFs and ask questions using AI",
                version="1.0"
            )

rag = RAGService()

os.makedirs("./uploads", exist_ok=True)

@app.post("/api/documents", response_model=DocumentUpload)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and index a PDF document

    1. Validate file type (PDF only)
    2. save file temporarily
    3. Denerate unique doc_id
    4. Index with rag.index_document()
    5. Return metadata
    """
    if file.content_type !="application/pdf":
        raise HTTPException(status_code=400, detail=f"Invalid file type {file.content_type}")
    
    doc_id = str(uuid.uuid4())

    destination_path = f"./uploads/{doc_id}.pdf"
    try:
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print(f"File successfully saved to: {destination_path}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    result = rag.index_document(destination_path, doc_id)

    if result['status'] == 'error':
        # Clean up saved file
        os.remove(destination_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index document: {result.get('error')}"
        )

    return DocumentUpload(
        doc_id=result['doc_id'],
        filename= file.filename,
        chunks=result['chunks'],
        status=result['status'],
    )

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    ASk a question about uploaded documents
    1.Validate question
    2.call rag.query(question, doc_id)
    3.Format response
    4.Return answer with sources
    """
    question = request.question
    doc_id = request.doc_id
    result = rag.query(question=question, doc_id=doc_id)

    return QueryResponse(
        question=result['question'],
        answer=result['answer'],
        sources=result['sources']
    )

@app.get("/api/documents")
async def list_documents():
    """Get list of all uploaded documents"""
    documents = rag.get_documents()
    return {
        "documents": documents,
        "total": len(documents)
    }

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the system"""
    success = rag.delete_document(doc_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Document {doc_id} not found"
        )
    
    # Clean up file if exists
    file_path = f"./uploads/{doc_id}.pdf"
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return {"message": f"Document {doc_id} deleted successfully"}

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return rag.get_stat()