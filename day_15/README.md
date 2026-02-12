# 📄 Document Q&A API (RAG System)

An AI-powered document question-answering system built with FastAPI and RAG (Retrieval-Augmented Generation). Upload any PDF and ask questions about it in natural language!

## ✨ Features

- 📤 **PDF Upload** - Upload any PDF document
- 🔍 **Semantic Search** - Finds relevant content by meaning, not just keywords
- 🤖 **AI-Powered Answers** - Uses Groq LLM to generate accurate answers
- 📚 **Multi-Document** - Upload and query multiple documents
- 🎯 **Filtered Queries** - Ask questions about specific documents
- 📊 **Source Citations** - Every answer includes source references
- 💾 **Persistent Storage** - Documents survive server restarts

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI |
| **Vector Database** | ChromaDB |
| **Embeddings** | HuggingFace (paraphrase-MiniLM-L6-v2) |
| **LLM** | Groq (llama-3.1-8b-instant) |
| **PDF Processing** | PyPDF |
| **RAG Framework** | LangChain |

## 🚀 Quick Start

### 1. Clone & Navigate

```bash
git clone https://github.com/NAWICH/01_foundation.git
cd 01_foundation/day_15_rag_api
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Free Groq API Key

1. Go to https://console.groq.com
2. Sign up (free)
3. Create API key

### 5. Setup Environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

**.env file:**
```
GROQ_API_KEY=your-groq-api-key-here
```

### 6. Run the Application

```bash
fastapi dev app/main.py
```

**API is now running at:** http://localhost:8000
**Interactive docs at:** http://localhost:8000/docs

---

## 📚 API Endpoints

### 📤 Upload Document

```http
POST /api/documents
Content-Type: multipart/form-data

file: [PDF file]
```

**Response:**
```json
{
  "doc_id": "abc-123-def-456",
  "filename": "my_document.pdf",
  "chunks": 23,
  "status": "success"
}
```

**Note:** Save the `doc_id` to query specific documents later!

---

### ❓ Ask a Question

**Query all documents:**
```http
POST /api/query
Content-Type: application/json

{
  "question": "What is the main topic of this document?"
}
```

**Query specific document:**
```http
POST /api/query
Content-Type: application/json

{
  "question": "What are the requirements?",
  "doc_id": "abc-123-def-456"
}
```

**Response:**
```json
{
  "question": "What are the requirements?",
  "answer": "Based on the document, the requirements are: 1) A valid ID, 2) Proof of address...",
  "sources": [
    {
      "text": "The applicant must provide a valid government-issued ID...",
      "page": 3,
      "doc_id": "abc-123-def-456",
      "source": "./uploads/abc-123-def-456.pdf"
    }
  ]
}
```

---

### 📋 List All Documents

```http
GET /api/documents
```

**Response:**
```json
{
  "documents": [
    {
      "doc_id": "abc-123",
      "source": "./uploads/abc-123.pdf"
    }
  ],
  "total": 1
}
```

---

### 🗑️ Delete Document

```http
DELETE /api/documents/{doc_id}
```

**Response:**
```json
{
  "message": "Document abc-123 deleted successfully"
}
```

---

### 📊 System Stats

```http
GET /api/stats
```

**Response:**
```json
{
  "total_documents": 3,
  "total_chunks": 145,
  "embedding_model": "paraphrase-MiniLM-L6-v2",
  "llm": "llama-3.1-8b-instant"
}
```

---

### 💚 Health Check

```http
GET /health
```

---

## 🧪 Testing with cURL

```bash
# 1. Upload a PDF
curl -X POST http://localhost:8000/api/documents \
  -F "file=@sample.pdf"

# Save the doc_id from response!

# 2. Ask about all documents
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?"}'

# 3. Ask about specific document
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Summarize this document", "doc_id": "YOUR_DOC_ID"}'

# 4. List documents
curl http://localhost:8000/api/documents

# 5. Delete document
curl -X DELETE http://localhost:8000/api/documents/YOUR_DOC_ID
```

---

## 📁 Project Structure

```
day_15_rag_api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI routes
│   ├── models.py        # Pydantic models
│   ├── rag_service.py   # Core RAG logic
│   └── config.py        # Configuration
│
├── uploads/             # Uploaded PDFs (auto-created)
├── chroma_db/           # Vector database (auto-created)
├── .env                 # API keys (do not commit!)
├── .env.example         # Template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🏗️ How It Works

### RAG Architecture

```
INDEXING (when you upload):
PDF → Extract Text → Split into Chunks → Create Embeddings → Store in ChromaDB

QUERYING (when you ask):
Question → Embed → Search ChromaDB → Get Top 4 Chunks → Send to LLM → Answer
```

### Why RAG?

| Traditional LLM | RAG System |
|----------------|------------|
| Limited to training data | Uses YOUR documents |
| Can hallucinate | Answers based on real content |
| No citations | Provides source references |
| Generic answers | Document-specific answers |

---

## 🔒 Security Notes

- API keys stored in `.env` (never committed to git)
- File type validation (PDF only)
- Files stored with UUID names (no conflicts)
- No user authentication (add for production)

---

## 📦 Dependencies

```
fastapi          # Web framework
uvicorn          # ASGI server
langchain        # RAG framework
langchain-groq   # Groq LLM integration
langchain-community # Vector store, embeddings
langchain-huggingface # HuggingFace embeddings
chromadb         # Vector database
pypdf            # PDF processing
sentence-transformers # Embedding models
python-multipart # File upload support
python-dotenv    # Environment variables
```

---

## 🌟 Use Cases

1. **Document Research** - Upload research papers, ask specific questions
2. **Legal Documents** - Upload contracts, query specific clauses
3. **Study Aid** - Upload textbooks, get explanations of concepts
4. **Lok Sewa Prep** - Upload past papers, generate practice questions
5. **Business Docs** - Upload policies, query procedures

---

## 🎓 Learning Outcomes

This project demonstrates:

1. **RAG Architecture** - Industry-standard pattern for document Q&A
2. **Vector Databases** - ChromaDB for semantic search
3. **Embeddings** - Converting text to meaningful vectors
4. **LLM Integration** - Connecting to state-of-the-art language models
5. **File Handling** - Processing uploaded files in FastAPI
6. **LangChain LCEL** - Modern AI pipeline construction
7. **Semantic Search** - Finding content by meaning not keywords
8. **Metadata Filtering** - Targeting specific documents in queries

---

## 🚀 Future Enhancements

- [ ] User authentication
- [ ] Support for .docx, .txt files
- [ ] Conversation memory (follow-up questions)
- [ ] Answer confidence scores
- [ ] Document summarization endpoint
- [ ] Batch question answering
- [ ] PostgreSQL for metadata storage
- [ ] Docker containerization
- [ ] Rate limiting

---

## 🐛 Troubleshooting

**"No module named 'langchain'"**
```bash
pip install langchain langchain-community langchain-core
```

**"Invalid API Key"**
- Check your .env file has GROQ_API_KEY set correctly
- Verify key at https://console.groq.com

**"File not found" on upload**
- Make sure `./uploads` directory exists
- It's created automatically but check permissions

**"No answer found"**
- Document might not be indexed yet
- Try re-uploading the PDF
- Check ChromaDB has data: `GET /api/stats`

**Slow first response**
- Normal! Embedding model loads on first request
- Subsequent requests are much faster

---

## 👨‍💻 Developer

**Nawich**
- GitHub: https://github.com/NAWICH
- Project: Day 15 of AI Engineering Journey
- Date: February 2026

---

## 📝 License

Educational project - free to use and learn from!

---

