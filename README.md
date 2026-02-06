# 🎯 InterviewCoachAI

**AI-powered mock interviews with personalized feedback** — Upload resume → Answer questions → Get AI feedback.

---

## 🚀 Quick Start

### One-Command Dev Launch (Windows PowerShell)
```bash
.\run-dev.ps1
# Opens: Backend (http://localhost:8000) + Frontend (http://localhost:3000)
```

### Manual Setup
```bash
# Terminal 1: Backend
cd backend/fastapi_ai
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
python -m http.server 3000
```

Then open: **http://localhost:3000**

---

## 📋 Features (MVP)

✅ **Resume Upload & Analysis** — Upload PDF/TXT, extract skills & experience level
✅ **Role-Specific Questions** — SWE, Data Science, Finance, Product roles (5 per interview)
✅ **Answer Evaluation**
   - Relevance Score (0-10)
   - STAR Structure Detection
   - Confidence Score (0-100)
   - Actionable feedback & improved answers
✅ **Dark Theme** — Modern, professional dark interface with Instagram gradient accents
✅ **Comprehensive Tests** — 21 passing tests covering all endpoints

---

## 🏗️ Tech Stack

| Component | Tech |
|-----------|------|
| **Frontend** | HTML/CSS/Vanilla JS (no frameworks) |
| **Backend** | FastAPI + Pydantic |
| **PDF Parsing** | pdfplumber |
| **Styling** | Dark theme with Instagram colors |

---

## 📁 Project Structure

```
├── frontend/
│   ├── index.html          # Main UI
│   ├── app.js              # Interview logic (180 lines)
│
├── backend/fastapi_ai/
│   ├── main.py             # All endpoints (375 lines)
│   └── requirements.txt
│
├── tests/
│   └── test_fastapi.py     # 21 passing tests
│
├── scripts/
│   └── verify_endpoints.py
│
├── run-dev.ps1            # Single-command launcher (Windows)
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/upload-resume` | `file: PDF/TXT` | `{skills: [], experience_level: "junior"\|"mid"\|"senior"}` |
| POST | `/analyze-resume` | `{text: string}` | `{skills: [], experience_level}` |
| POST | `/generate-questions` | `{role, experience_level, skills}` | `{questions: [{id, question}]}` |
| POST | `/evaluate-answer` | `{question, answer, resume_skills, role}` | `{relevance, structure_star, missing_points, improved_answer, confidence}` |
| GET | `/health` | - | `{status: "ok"}` |

---

## 🎨 Color Palette

- **Primary Gradient**: Pink #E1306C → Purple #833AB4
- **Accent**: Orange #FD1D1D
- **Background**: Dark #0f0f0f
- **Surface**: Dark Gray #1a1a1a
- **Text**: Light Gray #e0e0e0

---

## ✅ Testing

```bash
# Run all tests
pytest tests/

# Run endpoint verification
python scripts/verify_endpoints.py
```

---

## 📝 License

MIT License

### Why This Architecture?

✅ **Separates concerns**: Frontend ↔ API ↔ Logic
✅ **Scalable**: FastAPI can handle concurrent requests
✅ **Testable**: Each endpoint has clear contracts (Pydantic schemas)
✅ **Interview-ready talking point**: "I designed a microservices architecture with clear API contracts"

---

## 🛠️ Tech Stack

| Component | Technology | Role |
|-----------|-----------|------|
| **Backend** | FastAPI | AI microservice + API |
| **Frontend** | Vanilla JS + HTML/CSS | Interactive UI |
| **Tests** | pytest + TestClient | Comprehensive coverage |
| **Containerization** | Docker + Docker Compose | Local development + deployment |
| **Validation** | Pydantic v2 | Request/response schemas |

---

## 📂 Project Structure

```
InterviewCoachAI/
├── backend/
│   ├── fastapi_ai/
│   │   ├── main.py                  # API endpoints + logic
│   │   ├── requirements.txt         # Python dependencies
│   │   ├── Dockerfile              # Container definition
│   │   └── README.md               # Detailed API docs
│   └── django_core/                 # Placeholder (future)
│       └── README.md
├── frontend/
│   ├── index.html                  # Resume upload + interview flow
│   ├── interview.html              # Alternative layout (future)
│   └── app.js                      # Client logic + API calls
├── tests/
│   └── test_fastapi.py             # 21 comprehensive tests
├── nginx.conf                      # Reverse proxy + static serving
├── docker-compose.yml              # Multi-container orchestration
├── .env                            # Environment variables
└── README.md                       # This file
```

---

## 📡 API Specification

All endpoints return structured JSON with proper error handling.

### 1. **POST /analyze-resume**

Extract skills and experience level from resume text.

**Request:**
```json
{
  "text": "Senior SWE at Google. Python, Go, Kubernetes, AWS. 8+ years."
}
```

**Response:**
```json
{
  "skills": ["python", "kubernetes", "aws"],
  "experience_level": "senior"
}
```

---

### 2. **POST /generate-questions**

Generate 5 role-specific interview questions.

**Request:**
```json
{
  "role": "SWE",
  "experience_level": "mid",
  "skills": ["python", "docker"]
}
```

**Response:**
```json
{
  "questions": [
    {
      "id": 1,
      "question": "Explain a time you optimized a Python application for performance."
    },
    {
      "id": 2,
      "question": "Describe a system you designed and the tradeoffs you made."
    }
  ]
}
```

---

### 3. **POST /evaluate-answer**

Evaluate a candidate's interview answer and provide feedback.

**Request:**
```json
{
  "question": "Describe a time you optimized performance.",
  "answer": "Situation: Our API was slow. Task: I was asked to fix it. Action: I optimized DB queries and added caching. Result: 60% faster.",
  "resume_skills": ["python", "sql"],
  "role": "SWE"
}
```

**Response:**
```json
{
  "relevance": 7.5,
  "structure_star": true,
  "missing_points": ["Quantify impact with metrics"],
  "improved_answer": "Example of stronger answer...",
  "confidence": 78.5
}
```

---

### 4. **GET /health**

Health check endpoint (useful for Docker, load balancers).

**Response:**
```json
{
  "status": "ok",
  "service": "InterviewCoachAI FastAPI"
}
```

---

## 🧪 Testing

Run comprehensive test suite:

```bash
pytest tests/test_fastapi.py -v

# Output (should see 21 passed):
# test_health_check PASSED
# test_analyze_resume_valid PASSED
# test_generate_questions_swe_role PASSED
# test_evaluate_answer_valid_star PASSED
# ... (and 17 more)
```

**Test Coverage:**

✅ Health checks
✅ Resume analysis (valid, empty, junior/mid/senior detection)
✅ Question generation (SWE, Data, generic roles)
✅ Answer evaluation (STAR detection, metrics, skills matching)
✅ Error handling (empty fields, invalid JSON)
✅ End-to-end integration flow

---

## 🤖 AI Logic (Current MVP)

**All logic is currently hardcoded (deterministic)** — no LLM calls yet. This is intentional:

✅ No API keys needed
✅ No latency/cost
✅ Fully testable
✅ Serves as a realistic stub for interview

### Resume Analysis
- Keyword matching against a known skills list
- Experience level detection from keywords ("senior", "+10", "lead", etc.)

### Question Generation
- Role-based question banks (hardcoded)
- Difficulty adjusted by experience level

### Answer Evaluation
- **Relevance**: Word count + skill mentions + metrics detection
- **STAR Detection**: Keyword matching for situation/task/action/result
- **Confidence**: Heuristic based on length + structure + metrics

---

## 🚀 Next Steps (Future Phases)

### Phase 2: Real LLM Integration
- [ ] OpenAI API integration (`gpt-4-turbo` or `gpt-3.5-turbo`)
- [ ] Anthropic Claude integration (as alternative)
- [ ] Dynamic question generation based on resume
- [ ] Semantic answer evaluation (not just keyword matching)

### Phase 3: Django Backend
- [ ] User authentication (JWT + email signup)
- [ ] Resume storage (PostgreSQL)
- [ ] Interview history tracking
- [ ] Progress analytics (score trends)

### Phase 4: Voice & Advanced Features
- [ ] Voice recording + speech-to-text (Whisper API)
- [ ] Sentiment/confidence analysis
- [ ] Peer comparison benchmarking
- [ ] Weakness identification (e.g., "you struggle with system design")

### Phase 5: Deployment & Scaling
- [ ] AWS ECS deployment
- [ ] Redis caching for question generation
- [ ] Webhook logging for debugging
- [ ] CI/CD pipeline (GitHub Actions)

---

## 💡 Interview Talking Points

Use this project to ace your own interviews:

### Architecture
*"I designed a microservices architecture with FastAPI as an AI inference service, separate from a future Django auth/storage layer. This separation allows independent scaling of compute-intensive LLM calls."*

### Testing
*"I wrote 21 comprehensive tests using pytest, covering schema validation, edge cases, and end-to-end flows. This ensures API contracts are rock-solid before Django integrates."*

### Product Thinking
*"I started with a deterministic stub instead of immediately calling OpenAI. This let me validate the user flow and feedback quality before spending on LLM costs."*

### Scalability
*"The FastAPI service is stateless and horizontally scalable. Adding Redis caching and async workers handles 100x traffic growth."*

---

## 🛠️ Development Tips

### Local Debugging

**Check FastAPI docs:**
```
http://localhost:8000/docs
```
(Interactive Swagger UI)

**Test an endpoint from terminal:**
```bash
curl -X POST http://localhost:8000/analyze-resume \
  -H "Content-Type: application/json" \
  -d '{"text": "Python developer with 5 years experience"}'
```

**View logs:**
```bash
# Terminal running FastAPI shows detailed logs
# Terminal running pytest shows test results with --verbose
```

### Add New Features

1. **New endpoint**: Add handler in `main.py`, define Pydantic schemas
2. **New test**: Add test function in `tests/test_fastapi.py`
3. **Run tests**: `pytest tests/test_fastapi.py -v`
4. **Frontend update**: Modify `app.js` to call new endpoint

---

## 📚 References

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic v2**: https://docs.pydantic.dev/
- **pytest**: https://docs.pytest.org/
- **Docker Compose**: https://docs.docker.com/compose/

---

## 📝 License

MIT License — build, modify, and use freely.

---

## 👤 Author

Built with ❤️ in Feb 2026

---

## 🤝 Contributing

Issues & PRs welcome! This is a learning project—help improve it.

---

**Made with ❤️ for interview prep. Let's crush those interviews! 🚀**
