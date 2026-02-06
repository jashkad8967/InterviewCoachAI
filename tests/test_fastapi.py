import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path so we can import
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "fastapi_ai"))

from main import app

client = TestClient(app)


# ============================================================================
# HEALTH CHECK
# ============================================================================

def test_health_check():
    """Verify service is running."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ============================================================================
# RESUME ANALYSIS TESTS
# ============================================================================

def test_analyze_resume_valid():
    """Test resume analysis with valid input."""
    response = client.post(
        "/analyze-resume",
        json={"text": "Senior Python Developer. 10+ years. Skills: Python, Django, PostgreSQL, AWS"}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Schema validation
    assert "skills" in data
    assert "experience_level" in data
    assert isinstance(data["skills"], list)
    assert isinstance(data["experience_level"], str)
    
    # Content validation
    assert "python" in data["skills"]
    assert data["experience_level"] == "senior"


def test_analyze_resume_empty_text():
    """Test resume analysis rejects empty text."""
    response = client.post("/analyze-resume", json={"text": ""})
    assert response.status_code == 422  # Pydantic validation


def test_analyze_resume_junior_level():
    """Test junior experience detection."""
    response = client.post(
        "/analyze-resume",
        json={"text": "Recent graduate. Java, JavaScript, HTML/CSS. Entry-level position."}
    )
    assert response.status_code == 200
    assert response.json()["experience_level"] == "junior"


def test_analyze_resume_mid_level():
    """Test mid-level experience detection."""
    response = client.post(
        "/analyze-resume",
        json={"text": "Software Engineer with 5 years. Go, Kubernetes, gRPC. Team lead experience."}
    )
    assert response.status_code == 200
    data = response.json()
    # "5 years" triggers mid-level (contains "5")
    assert data["experience_level"] in ["mid", "senior"]


def test_analyze_resume_no_skills():
    """Test resume with no recognized skills."""
    response = client.post(
        "/analyze-resume",
        json={"text": "Project manager with excellent communication skills."}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["skills"] == []  # Empty skills list


# ============================================================================
# QUESTION GENERATION TESTS
# ============================================================================

def test_generate_questions_swe_role():
    """Test SWE-specific questions are generated."""
    response = client.post(
        "/generate-questions",
        json={"role": "SWE", "experience_level": "mid", "skills": ["python", "docker"]}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Schema validation
    assert "questions" in data
    assert isinstance(data["questions"], list)
    assert len(data["questions"]) > 0
    assert len(data["questions"]) <= 10
    
    # Content validation: Check for SWE-relevant keywords
    question_text = " ".join([q["question"] for q in data["questions"]]).lower()
    assert any(word in question_text for word in ["optimize", "system", "design", "debug", "bug"])


def test_generate_questions_data_role():
    """Test Data-specific questions are generated."""
    response = client.post(
        "/generate-questions",
        json={"role": "Data Science", "experience_level": "mid", "skills": []}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check for Data-relevant keywords
    question_text = " ".join([q["question"] for q in data["questions"]]).lower()
    assert any(word in question_text for word in ["data", "pipeline", "model", "validation"])


def test_generate_questions_generic_role():
    """Test generic behavioral questions for unknown roles."""
    response = client.post(
        "/generate-questions",
        json={"role": "Project Manager", "experience_level": "mid", "skills": []}
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should have questions, not fail
    assert len(data["questions"]) > 0
    for q in data["questions"]:
        assert "id" in q
        assert "question" in q
        assert isinstance(q["id"], int)
        assert isinstance(q["question"], str)


def test_generate_questions_response_schema():
    """Verify response strictly matches schema."""
    response = client.post(
        "/generate-questions",
        json={"role": "SWE", "experience_level": "junior", "skills": []}
    )
    assert response.status_code == 200
    data = response.json()
    
    for question in data["questions"]:
        assert isinstance(question["id"], int)
        assert isinstance(question["question"], str)
        assert len(question["question"]) > 0


# ============================================================================
# ANSWER EVALUATION TESTS
# ============================================================================

def test_evaluate_answer_valid_star():
    """Test evaluation of a good STAR-structured answer."""
    response = client.post(
        "/evaluate-answer",
        json={
            "question": "Tell me about a time you optimized performance.",
            "answer": (
                "Situation: Our API was responding slowly to users. "
                "Task: I was asked to improve performance. "
                "Action: I implemented database query caching and connection pooling. "
                "Result: Response time decreased by 60%, improving user satisfaction scores by 25%."
            ),
            "resume_skills": ["python", "database"],
            "role": "SWE"
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Schema validation
    assert "relevance" in data
    assert "structure_star" in data
    assert "missing_points" in data
    assert "improved_answer" in data
    assert "confidence" in data
    
    # Type validation
    assert isinstance(data["relevance"], (int, float))
    assert isinstance(data["structure_star"], bool)
    assert isinstance(data["missing_points"], list)
    assert isinstance(data["improved_answer"], str)
    assert isinstance(data["confidence"], (int, float))
    
    # Value range validation
    assert 0 <= data["relevance"] <= 10
    assert 0 <= data["confidence"] <= 100
    
    # Content validation: Should detect STAR and have good score
    assert data["structure_star"] is True
    assert data["relevance"] >= 3.5  # With good content and skills


def test_evaluate_answer_empty():
    """Test evaluation rejects empty answer."""
    response = client.post(
        "/evaluate-answer",
        json={
            "question": "Tell me about yourself.",
            "answer": "",
            "resume_skills": []
        }
    )
    assert response.status_code == 422  # Pydantic validation


def test_evaluate_answer_short_answer():
    """Test short answer gets low relevance and suggestions."""
    response = client.post(
        "/evaluate-answer",
        json={
            "question": "Describe a challenge you overcame.",
            "answer": "Fixed a bug.",
            "resume_skills": [],
            "role": "SWE"
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Short answer should have low scores
    assert data["relevance"] < 5.0
    assert len(data["missing_points"]) > 0


def test_evaluate_answer_with_metrics():
    """Test answer with metrics gets bonus."""
    response = client.post(
        "/evaluate-answer",
        json={
            "question": "Tell about optimization work.",
            "answer": (
                "I optimized the API response time. "
                "The improvement was 45% faster and reduced latency by 2x."
            ),
            "resume_skills": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should detect metrics
    assert data["relevance"] > 1.0  # Base + word count + metrics


def test_evaluate_answer_with_skills():
    """Test answer matching resume skills gets bonus."""
    response = client.post(
        "/evaluate-answer",
        json={
            "question": "Describe a technical project.",
            "answer": "I built a Python backend using FastAPI and PostgreSQL for a real-time dashboard.",
            "resume_skills": ["python", "fastapi", "postgresql"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should reward skill mentions: 2 base + 2*3 skills + word count bonus
    assert data["relevance"] >= 2.0


def test_evaluate_answer_no_star():
    """Test answer without STAR structure."""
    response = client.post(
        "/evaluate-answer",
        json={
            "question": "Tell me about a time...",
            "answer": "I worked on many projects. It was fun and I learned a lot.",
            "resume_skills": []
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should detect missing STAR
    assert data["structure_star"] is False
    assert any("STAR" in point for point in data["missing_points"])


def test_evaluate_answer_complex_scenario():
    """Test comprehensive evaluation with all features."""
    response = client.post(
        "/evaluate-answer",
        json={
            "question": "Describe a time you led a technical initiative.",
            "answer": (
                "At my previous company, the Situation was that our microservices "
                "infrastructure was becoming difficult to manage. The Task was to design "
                "a Kubernetes migration strategy. My Action was to lead the effort: I "
                "created migration playbooks, worked with platform teams, and championed "
                "adoption across 12 services. The Result was a 70% reduction in deployment "
                "time and improved system reliability from 95% to 99.9% uptime. I also "
                "mentored 5 engineers on Kubernetes best practices."
            ),
            "resume_skills": ["kubernetes", "python", "microservices", "leadership"],
            "role": "SWE"
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Should score well: 2 base + 4*2 skills + word bonus + metrics + STAR
    assert data["relevance"] >= 4.0
    assert data["structure_star"] is True
    assert data["confidence"] >= 65.0


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================

def test_invalid_json():
    """Test invalid JSON is rejected."""
    response = client.post(
        "/analyze-resume",
        data="not valid json",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422  # Validation error


def test_missing_required_field():
    """Test missing required fields are caught."""
    response = client.post(
        "/generate-questions",
        json={"role": "SWE"}  # Missing experience_level
    )
    assert response.status_code == 422  # Validation error


def test_malformed_role():
    """Test robustness with unusual role input."""
    response = client.post(
        "/generate-questions",
        json={"role": "xyz123", "experience_level": "mid"}
    )
    assert response.status_code == 200
    # Should still return generic questions
    assert len(response.json()["questions"]) > 0


# ============================================================================
# INTEGRATION TESTS (End-to-End Flow)
# ============================================================================

def test_full_interview_flow():
    """Test complete interview flow: resume → questions → evaluation."""
    
    # Step 1: Analyze resume
    resume_res = client.post(
        "/analyze-resume",
        json={"text": "Senior SWE at Google. Python, Go, Kubernetes, AWS. 8+ years."}
    )
    assert resume_res.status_code == 200
    resume_data = resume_res.json()
    skills = resume_data["skills"]
    
    # Step 2: Generate questions
    question_res = client.post(
        "/generate-questions",
        json={
            "role": "SWE",
            "experience_level": resume_data["experience_level"],
            "skills": skills
        }
    )
    assert question_res.status_code == 200
    questions = question_res.json()["questions"]
    assert len(questions) > 0
    
    # Step 3: Evaluate answer to first question
    eval_res = client.post(
        "/evaluate-answer",
        json={
            "question": questions[0]["question"],
            "answer": (
                "Situation: Our infrastructure was struggling with scale. "
                "Task: I needed to redesign our deployment system. "
                "Action: I led migration to Kubernetes, built automated workflows. "
                "Result: 50% faster deployments, 99.99% uptime."
            ),
            "resume_skills": skills,
            "role": "SWE"
        }
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    
    # Verify evaluation is sensible
    assert eval_data["relevance"] > 0
    assert isinstance(eval_data["confidence"], float)

