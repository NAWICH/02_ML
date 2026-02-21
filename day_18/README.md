# 🧠 Day 18: Smart RAG with Subject Classification
### Neural Network + RAG Combined System

An intelligent Q&A system that uses a neural network to classify questions by subject, then performs subject-filtered RAG retrieval for more accurate answers.

---

## What's Different from Day 15?

**Day 15 RAG (Basic):**
```
Question → Search ALL documents → LLM → Answer
Problem: Searches through irrelevant content
```

**Day 18 Smart RAG:**
```
Question → Neural Network (classify subject)
        → Search ONLY that subject's chunks
        → LLM → More accurate answer
        
Improvement: Narrower search = less noise = better answers
```

---

## Architecture

```
┌─────────────┐
│   Question  │
└──────┬──────┘
       │
       ↓
┌──────────────────────┐
│ Subject Classifier   │  ← Neural Network from Day 17
│ (Neural Network)     │     Predicts: GK/Math/Nepali/etc.
└──────┬───────────────┘
       │
       ↓
  Confidence > 0.6?
       │
   ┌───┴───┐
   │       │
  YES     NO
   │       │
   ↓       ↓
Filter   Search
by      ALL
subject  docs
   │       │
   └───┬───┘
       ↓
┌──────────────────────┐
│ ChromaDB Retrieval   │  ← Get top 4 relevant chunks
└──────┬───────────────┘
       │
       ↓
┌──────────────────────┐
│ Groq LLM             │  ← Generate answer from context
└──────┬───────────────┘
       │
       ↓
   Answer + Sources
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| Neural Network | PyTorch (from Day 17) |
| Embeddings | HuggingFace (paraphrase-MiniLM-L6-v2) |
| Vector Database | ChromaDB |
| LLM | Groq (llama-3.3-70b-versatile) |
| RAG Framework | LangChain |

---

## Project Structure

```
day_18_smart_rag/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI routes
│   ├── classifier.py        # SubjectClassifier (loads Day 17 model)
│   ├── smart_rag.py         # SmartRAGService (RAG + filtering)
│   └── models.py            # Pydantic models
│
├── models/
│   ├── question_classifier.pth    # Neural network weights (Day 17)
│   └── label_encoder.npy          # Subject name mapping (Day 17)
│
├── data/                    # Subject-specific content
│   ├── gk_content.pdf
│   ├── math_content.pdf
│   └── ...
│
├── uploads/                 # Uploaded PDFs (auto-created)
├── chroma_db/              # Vector database (auto-created)
├── .env
├── requirements.txt
└── README.md
```

---

## API Endpoints

### 1. Index Document by Subject

```http
POST /api/index?subject=GK
Content-Type: multipart/form-data

file: [PDF file]
```

**Response:**
```json
{
  "file_name": "nepal_history.pdf",
  "upload_date": "2026-02-21 14:30:00",
  "chunks_size": 47
}
```

---

### 2. Smart Query

```http
POST /api/smart-query
Content-Type: application/json

{
  "question": "What is the capital of Nepal?"
}
```

**Response:**
```json
{
  "subject": "GK",
  "answer": "The capital of Nepal is Kathmandu, which serves as the political and cultural center of the country.",
  "confidence": 0.94,
  "sources": [
    {
      "text": "Kathmandu is the capital and largest city of Nepal...",
      "page": 3,
      "doc_id": "unknown",
      "source": "./uploads/abc-123.pdf"
    }
  ]
}
```

---

### 3. Get Subjects

```http
GET /api/subjects
```

**Response:**
```json
{
  "subjects": ["GK", "Math", "Nepali", "English", "Science"]
}
```

---

### 4. Health Check

```http
GET /health
```

---

## How It Works

### Step 1: Indexing
```
1. Upload PDF with subject label
2. Extract text from PDF
3. Split into 1000-char chunks (200 overlap)
4. Add metadata: {"subject": "GK", "page": 3}
5. Convert to embeddings
6. Store in ChromaDB
```

### Step 2: Querying
```
1. User asks: "What is Nepal's capital?"
2. Neural network classifies: GK (94% confident)
3. Confidence > 0.6 → filter by GK
4. Retrieve top 4 GK-only chunks
5. Send chunks + question to Groq LLM
6. Return answer with detected subject
```

### Step 3: Fallback
```
If confidence < 0.6:
  → Don't trust classifier
  → Search ALL subjects
  → Slower but safer
```

---

## Key Features

### 1. Subject-Aware Retrieval
```
Before: Search 1000 chunks (all subjects)
After:  Search 200 chunks (one subject only)
Result: 5x faster, more accurate
```

### 2. Confidence-Based Fallback
```
High confidence (>60%): Trust classifier, filter by subject
Low confidence (<60%):  Search all subjects (safer)
```

### 3. Source Attribution
```
Every answer includes:
- Which chunks were used
- Page numbers
- Subject classification
- Confidence score
```

---

## Installation

```bash
# Install dependencies
pip install fastapi uvicorn python-dotenv
pip install torch langchain langchain-community langchain-huggingface
pip install chromadb groq sentence-transformers

# Copy Day 17 model files
cp ../day_17_classifier/question_classifier.pth ./models/
cp ../day_17_classifier/label_encoder.npy ./models/

# Setup environment
cp .env.example .env
# Add your GROQ_API_KEY
```

---

## Usage

### Start Server
```bash
fastapi dev app/main.py
```

### Upload Subject Content
```bash
curl -X POST "http://localhost:8000/api/index?subject=GK" \
  -F "file=@data/nepal_history.pdf"
```

### Ask Questions
```bash
curl -X POST "http://localhost:8000/api/smart-query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of Nepal?"}'
```

---

## Performance Comparison

| Metric | Day 15 RAG | Day 18 Smart RAG |
|--------|------------|------------------|
| Search space | All chunks | Filtered by subject |
| Retrieval speed | Baseline | 3-5x faster |
| Answer accuracy | Good | Better (less noise) |
| API calls | 1 (LLM only) | 1 (LLM only)* |

*Neural network runs locally, no API call

---

## Limitations

### 1. Classifier Accuracy
```
Trained on: 192 LLM-generated questions
Limitation: May misclassify real human-written questions
Impact: Wrong subject → wrong chunks → wrong answer
```

### 2. Subject Boundary Ambiguity
```
Question: "What percentage of Nepal is mountainous?"
Could be: GK (geography) or Math (percentage calculation)
Impact: Classifier must choose one
```

### 3. Small Training Data
```
Day 17 model: 192 samples
Production need: 1000+ samples per subject
Current state: Works but not production-ready
```

---

## Future Improvements

- [ ] Multi-subject classification (allow 2+ subjects)
- [ ] Active learning (improve classifier with user feedback)
- [ ] Hybrid retrieval (combine filtered + unfiltered results)
- [ ] Confidence visualization in UI
- [ ] Real Lok Sewa question fine-tuning

---

## What I Learned

### Technical
- How to integrate neural networks into production pipelines
- Metadata filtering in vector databases
- Confidence thresholds for fallback logic
- Combining multiple AI systems (classifier + RAG)

### Design Decisions
- Why confidence threshold = 0.6 (balance accuracy vs safety)
- When to trust ML predictions vs fallback
- How to structure error handling in multi-stage pipelines
- Importance of source attribution in AI answers

---

## Connection to Lok Sewa Business

```
Current system: Generate questions by subject (user specifies)
Day 18 addition: Auto-classify user questions by subject

Use case:
Student asks: "नेपालको राजधानी के हो?"
System:
  1. Detects subject: GK
  2. Generates similar GK questions
  3. Returns practice set focused on GK
  
Result: More personalized practice experience
```

---

## Developer

**Nawich**
- GitHub: https://github.com/NAWICH
- Day 18 of 30-day AI Engineering Journey
- Date: February 2026

---

*Built on: Day 15 (RAG) + Day 17 (Neural Network Classifier)*
*Next: Day 19 - Transfer Learning & Fine-tuning*