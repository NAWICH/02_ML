# 🇳🇵 Lok Sewa Preparation API

An AI-powered platform for Nepal's Lok Sewa Aayog (Public Service Commission) exam preparation. Generates fresh practice questions daily using LLMs, tracks progress, and provides detailed explanations.

## ✨ Features

### Core Features
- 🔐 **User Authentication** - JWT token-based auth with bcrypt
- 👑 **Premium/Free Tiers** - Embedded in JWT token
- 📊 **Progress Tracking** - Solved/failed per subject
- 🚫 **No Repeats** - Vector similarity prevents duplicate questions

### AI Features
- 🤖 **AI Question Generation** - Groq LLM generates fresh MCQ questions
- 📚 **RAG-Powered** - Questions based on past Lok Sewa papers
- 💡 **Smart Explanations** - AI explains WHY answer is correct/incorrect
- 🎯 **Subject Filtering** - GK, Math, Nepali, English, Science, Current Affairs
- 📈 **Difficulty Levels** - Easy, Medium, Hard

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI |
| **Database** | SQLite |
| **Authentication** | JWT (python-jose) + bcrypt |
| **LLM** | Groq (llama-3.3-70b-versatile) |
| **Vector Database** | ChromaDB |
| **Embeddings** | HuggingFace (paraphrase-MiniLM-L6-v2) |
| **RAG Framework** | LangChain |

## 📋 Prerequisites

- Python 3.10+
- Groq API key (free at console.groq.com)

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/NAWICH/01_foundation.git
cd 01_foundation/day_16_loksewa
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

### 5. Setup Environment Variables
```bash
cp .env.example .env
```

Edit `.env`:
```env
JWT_SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
TOKEN_EXPIRY_MINUTES=60
GROQ_API_KEY=your-groq-api-key-here
```

Generate secure JWT key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Create Study Material PDF
```bash
# Install reportlab
pip install reportlab

# Generate PDF from study material
python create_pdf.py
```

### 7. Run Application
```bash
fastapi dev app/main.py
```

**API available at:** http://localhost:8000  
**Interactive docs:** http://localhost:8000/docs

---

## 📚 API Reference

### Authentication (Public)

#### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "full_name": "Ram Bahadur",
  "email": "ram@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "id": 1,
  "full_name": "Ram Bahadur",
  "email": "ram@example.com",
  "is_premium": false,
  "created_at": "2026-02-14T10:00:00"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "ram@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "is_premium": false
}
```

---

### Questions (Protected)

#### Generate Questions
```http
POST /api/questions/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "subject": "GK",
  "difficulty": "medium",
  "count": 5
}
```

**Available subjects:** `GK`, `Math`, `Nepali`, `English`, `Science`, `CurrentAffairs`  
**Available difficulties:** `easy`, `medium`, `hard`  
**Free users:** max 5 questions | **Premium:** up to 10

**Response:**
```json
{
  "questions": [
    {
      "id": "abc-123-def",
      "subject": "GK",
      "difficulty": "medium",
      "question": "What is the capital of Nepal?",
      "options": {
        "A": "Pokhara",
        "B": "Kathmandu",
        "C": "Biratnagar",
        "D": "Butwal"
      }
    }
  ],
  "count": 5,
  "subject": "GK",
  "difficulty": "medium"
}
```

**Note:** Correct answer is NOT included. Submit answer to reveal!

#### Submit Answer
```http
POST /api/questions/submit
Authorization: Bearer <token>
Content-Type: application/json

{
  "question_id": "abc-123-def",
  "selected_option": "B"
}
```

**Response:**
```json
{
  "is_correct": true,
  "selected": "B",
  "correct": "B",
  "explanation": "Kathmandu is the capital and largest city of Nepal, serving as the center of political, cultural, and commercial activities since the unification of Nepal.",
  "points_earned": 10
}
```

#### Get Question History
```http
GET /api/questions/history
Authorization: Bearer <token>
```

---

### User (Protected)

#### My Profile
```http
GET /api/users/me
Authorization: Bearer <token>
```

#### My Statistics
```http
GET /api/users/me/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_attempted": 25,
  "total_solved": 18,
  "total_failed": 7,
  "accuracy": 72.0
}
```

---

### Premium Routes

#### Advanced Question Generation (Premium Only)
```http
POST /api/questions/generate/advanced
Authorization: Bearer <premium-token>
Content-Type: application/json

{
  "subject": "Math",
  "difficulty": "hard",
  "count": 10
}
```

#### Upgrade to Premium
```http
POST /api/upgrade
Authorization: Bearer <token>
```

*In production: integrate eSewa/Khalti payment before upgrading*

---

## 📁 Project Structure

```
day_16_loksewa/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI routes
│   ├── models.py            # Pydantic models
│   ├── database.py          # SQLite operations
│   ├── auth.py              # Authentication
│   └── question_service.py  # AI question generation
│
├── data/
│   └── loksewa_questions.pdf  # Study material (indexed at startup)
│
├── chroma_db/               # Vector database (auto-created)
├── database.db              # SQLite database (auto-created)
├── create_pdf.py            # Script to generate PDF
├── loksewa_questions.txt    # Raw study material
├── .env                     # API keys (never commit!)
├── .env.example             # Template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🗄️ Database Schema

```sql
-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_premium INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

-- Generated Questions (prevents repeats)
CREATE TABLE questions (
    id TEXT PRIMARY KEY,          -- UUID
    subject TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_option TEXT NOT NULL, -- Never sent to client!
    explanation TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- User Attempts
CREATE TABLE user_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question_id TEXT NOT NULL,
    selected_option TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    attempted_at TEXT NOT NULL
);
```

---

## 🏗️ How AI Question Generation Works

```
1. Startup: Index loksewa_questions.pdf into ChromaDB

2. Generate Request:
   User asks for 5 GK medium questions
           ↓
   Retrieve relevant context from ChromaDB
           ↓
   Send context + prompt to Groq LLM
           ↓
   LLM returns structured JSON with 5 questions
           ↓
   Check each question for duplicates (vector similarity)
           ↓
   Save new questions to SQLite + ChromaDB
           ↓
   Return questions WITHOUT correct answers

3. Submit Answer:
   User submits answer
           ↓
   Get correct answer from SQLite (server-side only!)
           ↓
   Send question + user answer to LLM
           ↓
   LLM generates educational explanation
           ↓
   Save attempt, return result + explanation
```

---

## 🔒 Security Features

- **Passwords** hashed with bcrypt
- **JWT tokens** expire after 60 minutes
- **Premium status** embedded in token (no extra DB query)
- **Correct answers** NEVER sent to client (only revealed on submit)
- **Duplicate attempts** prevented per user
- **SQL injection** prevented with parameterized queries
- **Input validation** with Pydantic models

---

## 🧪 Testing

### Quick Test Flow
```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Test User","email":"test@test.com","password":"password123"}'

# 2. Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123"}'

# 3. Generate Questions (use token from step 2)
curl -X POST http://localhost:8000/api/questions/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subject":"GK","difficulty":"medium","count":3}'

# 4. Submit Answer (use question_id from step 3)
curl -X POST http://localhost:8000/api/questions/submit \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_id":"QUESTION_ID","selected_option":"B"}'
```

---

## 🌟 Subjects Covered

| Subject | Topics |
|---------|--------|
| **GK** | Nepal history, geography, constitution, government |
| **Nepali** | Grammar, comprehension, literature |
| **English** | Grammar, vocabulary, reading |
| **Math** | Arithmetic, algebra, reasoning |
| **Science** | Physics, chemistry, biology, environment |
| **CurrentAffairs** | Recent Nepal and world events |

---

## 🚀 Roadmap to Production

- [ ] WhatsApp Bot (Twilio API) - Send daily questions
- [ ] eSewa/Khalti payment integration
- [ ] Simple mobile-friendly frontend
- [ ] Email notifications
- [ ] Streak system (daily practice rewards)
- [ ] Leaderboard
- [ ] Subject-wise performance analytics
- [ ] Docker containerization
- [ ] Deploy to Railway/Render

---

## 💰 Business Model

**Free Tier:**
- 5 questions per session
- Basic subjects
- Standard explanations

**Premium (NPR 500/month):**
- 10 questions per session
- All subjects + difficulty levels
- Advanced AI explanations
- Performance analytics
- Priority support

**Target Market:** 300,000+ annual Lok Sewa aspirants in Nepal

---

## 🐛 Common Issues

**"Failed to generate questions"**
- Check GROQ_API_KEY in .env
- Verify internet connection
- Try again (LLM occasionally fails)

**"No study material found"**
- Run `python create_pdf.py` first
- Check `./data/` directory exists

**"Invalid credentials"**
- Use correct email (not username)
- Check password (min 8 characters)

---

## 📖 Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangChain Docs](https://python.langchain.com/)
- [Groq Console](https://console.groq.com/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Lok Sewa Official](https://psc.gov.np/)

---

## 👨‍💻 Developer

**Nawich**  
GitHub: https://github.com/NAWICH  
Project: Day 16 of AI Engineering Journey  
Date: February 2026

---

*Built as part of a 30-day intensive AI Engineering journey*  