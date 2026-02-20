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

from fastapi import FastAPI
