from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import pdfplumber
import io
import re


app = FastAPI(
    title="InterviewCoachAI - FastAPI AI microservice",
    description="AI-powered interview coaching platform backend",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://[::1]",
        "http://[::1]:3000",
        "http://[::1]:8000",
        # GitHub Pages
        "https://jashkad8967.github.io",
        # Allow any HTTPS origin (for compatibility)
        "https://*.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ResumeAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Resume text content")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "John Doe\nSWE at Google\nSkills: Python, SQL, Docker\n5+ years experience"
            }
        }
    )


class ResumeAnalysisResponse(BaseModel):
    skills: List[str] = Field(default_factory=list, description="Extracted technical skills")
    experience_level: str = Field(..., description="Inferred experience level")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skills": ["python", "sql", "docker"],
                "experience_level": "senior"
            }
        }
    )


class QuestionGenerationRequest(BaseModel):
    skills: List[str] = Field(default_factory=list, description="Skills from resume")
    experience_level: str = Field(..., description="Experience level")
    role: str = Field(..., description="Target job role")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "skills": ["python", "sql", "docker"],
                "experience_level": "senior",
                "role": "software engineer"
            }
        }
    )


class InterviewQuestion(BaseModel):
    id: int = Field(..., description="Question ID")
    question: str = Field(..., description="Question text")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "question": "Describe a time you optimized database performance."
            }
        }
    )


class QuestionGenerationResponse(BaseModel):
    questions: List[InterviewQuestion] = Field(default_factory=list, description="Generated questions")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "questions": [
                    {"id": 1, "question": "Describe a time you optimized database performance."},
                    {"id": 2, "question": "How do you handle conflicting priorities?"}
                ]
            }
        }
    )


class AnswerEvaluationRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Interview question")
    answer: str = Field(..., min_length=1, description="Candidate's answer")
    resume_skills: List[str] = Field(default_factory=list, description="Skills from resume")
    role: Optional[str] = Field(None, description="Target role for context")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "Describe a time you optimized performance.",
                "answer": "I optimized a Python backend by caching database queries...",
                "resume_skills": ["python", "sql"],
                "role": "software engineer"
            }
        }
    )


class AnswerEvaluationResponse(BaseModel):
    relevance: float = Field(..., ge=0, le=10, description="Relevance score (0-10)")
    structure_star: bool = Field(..., description="STAR method detected")
    missing_points: List[str] = Field(default_factory=list, description="Improvement suggestions")
    improved_answer: str = Field(..., description="Example of a stronger answer")
    confidence: float = Field(..., ge=0, le=100, description="Confidence/delivery score (0-100)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "relevance": 7.5,
                "structure_star": True,
                "missing_points": ["Add metrics to show impact"],
                "improved_answer": "Situation: Our API was slow. Task: I led optimization...",
                "confidence": 85.0
            }
        }
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.post("/upload-resume", response_model=ResumeAnalysisResponse)
async def upload_resume(file: UploadFile = File(...)) -> ResumeAnalysisResponse:
    """Upload a PDF or text file and extract resume text, then analyze it."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    try:
        content = await file.read()
        text = ""
        
        # Handle PDF files
        if file.filename.lower().endswith(".pdf"):
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        # Handle text files
        elif file.filename.lower().endswith((".txt", ".text")):
            text = content.decode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Analyze the extracted text
        req = ResumeAnalysisRequest(text=text)
        return await analyze_resume(req)
    
    except pdfplumber.exceptions.PDFException:
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/analyze-resume", response_model=ResumeAnalysisResponse)
async def analyze_resume(req: ResumeAnalysisRequest) -> ResumeAnalysisResponse:
    if not req.text or len(req.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Resume text cannot be empty")
    
    text_lower = req.text.lower()
    
    skill_keywords = {
        "python": ["python", "django", "flask", "fastapi", "pandas", "numpy"],
        "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
        "sql": ["sql", "mysql", "postgresql", "sqlite", "oracle"],
        "docker": ["docker", "kubernetes", "k8s", "container"],
        "aws": ["aws", "ec2", "s3", "lambda", "cloudformation"],
        "git": ["git", "github", "gitlab", "bitbucket"],
        "linux": ["linux", "ubuntu", "centos", "bash", "shell"],
        "api": ["api", "rest", "graphql", "json", "http"],
        "testing": ["pytest", "unittest", "jest", "selenium", "cypress"],
        "ci/cd": ["jenkins", "github actions", "gitlab ci", "travis", "circleci"]
    }
    
    detected_skills = []
    for skill, keywords in skill_keywords.items():
        if any(kw in text_lower for kw in keywords):
            detected_skills.append(skill)
    
    experience_score = 0
    
    senior_keywords = ["senior", "lead", "principal", "architect", "manager", "director"]
    if any(kw in text_lower for kw in senior_keywords):
        experience_score += 3
    
    years_match = re.search(r'(\d+)\+?\s*years?', text_lower)
    if years_match:
        years = int(years_match.group(1))
        if years >= 7:
            experience_score += 3
        elif years >= 4:
            experience_score += 2
        elif years >= 2:
            experience_score += 1
    
    advanced_skills = ["architect", "distributed", "microservices", "scalability"]
    if any(kw in text_lower for kw in advanced_skills):
        experience_score += 2
    
    if experience_score >= 5:
        level = "senior"
    elif experience_score >= 3:
        level = "mid"
    else:
        level = "junior"
    
    return ResumeAnalysisResponse(skills=detected_skills, experience_level=level)


@app.post("/generate-questions", response_model=QuestionGenerationResponse)
async def generate_questions(req: QuestionGenerationRequest) -> QuestionGenerationResponse:
    questions_pool = []
    
    behavioral = [
        "Tell me about a time you solved a difficult problem.",
        "Describe a situation where you had to learn something new quickly.",
        "Tell me about a time you received critical feedback and how you handled it.",
        "Describe a project where you had to work with a difficult team member.",
        "Tell me about a time you had to make a tough decision under pressure."
    ]
    questions_pool.extend(behavioral)
    
    skill_questions = {
        "python": ["How do you handle memory management in Python?", "Explain Python's GIL and when it matters.", "How do you optimize Python code performance?"],
        "javascript": ["Explain event loop and asynchronous programming in JavaScript.", "How do you handle state management in a React application?", "Describe closures and their practical uses."],
        "sql": ["How do you optimize slow database queries?", "Explain database normalization and when to denormalize.", "How do you handle database migrations in production?"],
        "docker": ["How do you secure Docker containers in production?", "Explain Docker networking and container communication.", "How do you optimize Docker image size?"],
        "aws": ["How do you design for high availability on AWS?", "Explain AWS security best practices.", "How do you optimize AWS costs?"],
        "api": ["How do you design RESTful APIs?", "Explain API versioning strategies.", "How do you handle API rate limiting?"],
        "testing": ["How do you approach testing in your development process?", "Explain the difference between unit and integration tests.", "How do you test asynchronous code?"]
    }
    
    for skill in req.skills:
        if skill in skill_questions:
            questions_pool.extend(skill_questions[skill][:2])
    
    if req.experience_level == "junior":
        questions_pool.extend(["What is your favorite programming language and why?", "How do you stay updated with technology trends?", "Describe your debugging process."])
    elif req.experience_level == "mid":
        questions_pool.extend(["How do you approach code reviews?", "Describe your experience with agile development.", "How do you handle technical debt?"])
    elif req.experience_level == "senior":
        questions_pool.extend(["How do you mentor junior developers?", "Describe your experience leading technical projects.", "How do you make architectural decisions?"])
    
    role_questions = {
        "software engineer": ["How do you ensure code quality?", "Describe your experience with version control.", "How do you handle production incidents?"],
        "data scientist": ["How do you approach feature engineering?", "Explain model validation techniques.", "How do you communicate technical findings to non-technical stakeholders?"],
        "devops engineer": ["How do you implement CI/CD pipelines?", "Describe your experience with infrastructure as code.", "How do you monitor system performance?"],
        "frontend developer": ["How do you optimize web application performance?", "Describe your experience with responsive design.", "How do you handle browser compatibility?"],
        "backend developer": ["How do you design scalable systems?", "Describe your experience with databases.", "How do you handle concurrent requests?"]
    }
    
    role_lower = req.role.lower() if req.role else ""
    for role, q_list in role_questions.items():
        if role in role_lower:
            questions_pool.extend(q_list[:2])
    
    questions_pool = list(set(questions_pool))
    selected = questions_pool[:5]
    questions = [InterviewQuestion(id=i+1, question=q) for i, q in enumerate(selected)]
    
    return QuestionGenerationResponse(questions=questions)


@app.post("/evaluate-answer", response_model=AnswerEvaluationResponse)
def evaluate_answer(req: AnswerEvaluationRequest) -> AnswerEvaluationResponse:
    if not req.answer or len(req.answer.strip()) == 0:
        raise HTTPException(status_code=400, detail="Answer cannot be empty")
    
    answer_lower = req.answer.lower()
    
    relevance = 2.0
    for skill in (req.resume_skills or []):
        if skill.lower() in answer_lower:
            relevance += 2.0
    
    word_count = len(req.answer.split())
    if word_count > 150:
        relevance += 3.5
    elif word_count > 100:
        relevance += 2.5
    elif word_count > 60:
        relevance += 1.5
    elif word_count < 20:
        relevance -= 1.0
    
    if re.search(r'\d+\%|\d+x|decreased|increased|improved', answer_lower):
        relevance += 1.5
    
    relevance = max(0, min(10.0, relevance))
    
    star_keywords = {
        "situation": ["situation", "context", "background", "team", "company", "project", "faced"],
        "task": ["task", "challenge", "problem", "goal", "asked", "responsibility", "needed"],
        "action": ["action", "i did", "i led", "i implemented", "i developed", "i wrote", "i created"],
        "result": ["result", "outcome", "impact", "improved", "achieved", "metrics", "delivered"]
    }
    
    detected_components = []
    for component, keywords in star_keywords.items():
        if any(kw in answer_lower for kw in keywords):
            detected_components.append(component)
    
    structure_star = len(detected_components) >= 3
    
    missing_points = []
    
    if not structure_star:
        missing = []
        for component, keywords in star_keywords.items():
            if not any(kw in answer_lower for kw in keywords):
                missing.append(component.upper())
        if missing:
            missing_points.append(f"Add missing STAR components: {', '.join(missing)}")
    
    if relevance < 4.0:
        missing_points.append("Mention more relevant technical skills or specific projects")
    
    if word_count < 60:
        missing_points.append("Provide more detail. Aim for 80+ words to show depth")
    
    if not re.search(r'\d+\%|\d+x|decreased|increased|improved', answer_lower):
        missing_points.append("Quantify impact with metrics (e.g., '40% faster', '2x improvement')")
    
    confidence = 45.0
    confidence += min(30.0, (word_count / 5))
    if structure_star:
        confidence += 20.0
    if any(kw in answer_lower for kw in ["we", "team", "collaborated", "led"]):
        confidence += 5.0
    if re.search(r'\d+\%|\d+x', answer_lower):
        confidence += 5.0
    
    confidence = max(0, min(100.0, confidence))
    
    improved = "**Situation:** Start with context: 'At [Company], I was part of a team where...' **Task:** Explain the challenge: 'We faced [specific problem]...' **Action:** Describe what YOU did (use 'I'): 'I led the effort to [action]...' **Result:** End with impact: 'This resulted in [metric], improving [outcome] by X%.' \n\nExample: 'At TechCorp, our API response times were slow. I optimized the database queries, added caching, and implemented connection pooling. This reduced P99 latency by 60% and improved user satisfaction scores by 25%.'"
    
    return AnswerEvaluationResponse(
        relevance=round(relevance, 1),
        structure_star=structure_star,
        missing_points=missing_points,
        improved_answer=improved,
        confidence=round(confidence, 1)
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "InterviewCoachAI FastAPI"}