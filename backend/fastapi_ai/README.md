InterviewCoachAI FastAPI AI microservice

Endpoints:
- POST /analyze-resume: {"text": "resume text"}
- POST /generate-questions: {"role": "SWE", "experience_level": "mid", "skills": []}
- POST /evaluate-answer: {"question": "...", "answer": "...", "resume_skills": []}

Run locally:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```