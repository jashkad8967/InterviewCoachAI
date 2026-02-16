// ============================================================================
// FRONTEND CONFIG
// ============================================================================

// Override API_BASE by setting window.API_BASE_OVERRIDE before loading this script
// or by adding ?api=https://your-backend-url to the URL query params
const queryParams = new URLSearchParams(window.location.search);
const queryApiBase = queryParams.get('api');

const API_BASE = window.API_BASE_OVERRIDE 
  ? window.API_BASE_OVERRIDE
  : queryApiBase
  ? queryApiBase
  : ['localhost', '127.0.0.1', '::1', ''].includes(window.location.hostname)
  ? 'http://localhost:8000'
  : 'https://interview-coach-ai-backend.onrender.com';

console.log(`[InterviewCoach] Using API base: ${API_BASE}`);

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

async function postJson(endpoint, body) {
  try {
    const url = `${API_BASE}${endpoint}`;
    console.log(`[API] POST ${endpoint}`, body);
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(`API Error ${res.status}: ${errorData.detail || res.statusText}`);
    }
    const data = await res.json();
    console.log(`[API] Response:`, data);
    return data;
  } catch (err) {
    console.error(`[API] Error:`, err.message);
    alert(`Error: ${err.message}`);
    throw err;
  }
}

async function processResume(text, role, exp, isFile = false) {
  try {
    let skills, experience;
    if (isFile) {
      const analysisData = await text;
      skills = analysisData.skills;
      experience = analysisData.experience_level;
    } else {
      const analysisRes = await postJson('/analyze-resume', { text });
      skills = analysisRes.skills;
      experience = analysisRes.experience_level;
    }

    console.log(`[UI] Extracted skills: ${skills.join(', ')}, level: ${experience}`);
    const qRes = await postJson('/generate-questions', {
      role,
      experience_level: exp || experience,
      skills
    });

    window.currentSession = {
      resumeText: isFile ? skills.join(', ') : text,
      skills, experience, role,
      questions: qRes.questions,
      evaluations: []
    };

    renderQuestions(qRes.questions);
    document.getElementById('resume-form').style.display = 'none';
    document.getElementById('questions').style.display = 'block';
  } catch (err) {
    console.error('[UI] Error:', err);
  }
}

// ============================================================================
// RESUME UPLOAD & ANALYSIS
// ============================================================================

function setupResumeForm() {
  const form = document.getElementById('resume-form');
  if (!form) return;

  const uploadBtn = document.getElementById('upload-btn');
  const fileInput = document.getElementById('resume-file');

  if (uploadBtn && fileInput) {
    uploadBtn.addEventListener('click', (e) => {
      e.preventDefault();
      fileInput.click();
    });

    fileInput.addEventListener('change', async (e) => {
      if (!e.target.files.length) return;
      const file = e.target.files[0];
      if (!['application/pdf', 'text/plain'].includes(file.type) && !file.name.match(/\.(pdf|txt)$/i)) {
        alert('Please upload a PDF or text file.');
        return;
      }

      const role = document.getElementById('role').value;
      const exp = document.getElementById('exp').value;
      const formData = new FormData();
      formData.append('file', file);

      try {
        console.log('[UI] Uploading file:', file.name);
        const uploadRes = await fetch(`${API_BASE}/upload-resume`, { method: 'POST', body: formData });
        if (!uploadRes.ok) {
          const errorData = await uploadRes.json().catch(() => ({}));
          throw new Error(`Upload failed: ${errorData.detail || uploadRes.statusText}`);
        }
        await processResume(await uploadRes.json(), role, exp, true);
      } catch (err) {
        console.error('[UI] File upload error:', err);
        alert(`Error: ${err.message}`);
      }
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = document.getElementById('resume-text').value;
    if (!text.trim()) {
      alert('Please upload a file or paste your resume text.');
      return;
    }
    await processResume(text, document.getElementById('role').value, document.getElementById('exp').value);
  });
}function renderQuestions(questions) {
  const container = document.getElementById('questions');
  container.innerHTML = '';

  const header = document.createElement('h2');
  header.textContent = `Interview Questions for ${window.currentSession.role}`;
  container.appendChild(header);

  questions.forEach((q) => {
    const div = document.createElement('div');
    div.className = 'question-box';

    const qnum = document.createElement('div');
    qnum.className = 'question-number';
    qnum.textContent = `Q${q.id}`;

    const qtext = document.createElement('p');
    qtext.className = 'question-text';
    qtext.innerHTML = `<strong>${q.question}</strong>`;

    const textarea = document.createElement('textarea');
    textarea.id = `answer-${q.id}`;
    textarea.className = 'answer-textarea';
    textarea.placeholder = 'Type your answer here... (aim for 80+ words)';
    textarea.rows = 6;

    const submitBtn = document.createElement('button');
    submitBtn.className = 'submit-btn';
    submitBtn.textContent = 'Submit Answer';
    submitBtn.addEventListener('click', () => {
      try { window.evaluateAnswer(q.id, q.question); } catch (err) { console.error('evaluate click error', err); }
    });

    const feedbackDiv = document.createElement('div');
    feedbackDiv.id = `feedback-${q.id}`;
    feedbackDiv.className = 'feedback-box';

    div.appendChild(qnum);
    div.appendChild(qtext);
    div.appendChild(textarea);
    div.appendChild(submitBtn);
    div.appendChild(feedbackDiv);

    container.appendChild(div);
  });

  const completeBtn = document.createElement('button');
  completeBtn.textContent = 'View Interview Summary';
  completeBtn.className = 'complete-btn';
  completeBtn.onclick = showSummary;
  container.appendChild(completeBtn);
}

// ============================================================================
// ANSWER EVALUATION
// ============================================================================

window.currentSession = {
  resumeText: '', skills: [], experience: '', role: '', questions: [], evaluations: []
};

window.evaluateAnswer = async function(questionId, question) {
  console.log(`[UI] evaluateAnswer clicked for Q${questionId}`);
  const answer = document.getElementById(`answer-${questionId}`).value;
  if (!answer.trim()) {
    alert('Please type an answer before submitting.');
    return;
  }

  try {
    console.log(`[UI] Evaluating answer for Q${questionId}...`);
    const evalRes = await postJson('/evaluate-answer', {
      question, answer,
      resume_skills: window.currentSession.skills,
      role: window.currentSession.role
    });

    window.currentSession.evaluations.push({ questionId, question, answer, evaluation: evalRes });
    const btn = document.querySelector(`#answer-${questionId}`).nextElementSibling;
    if (btn) { btn.disabled = true; btn.textContent = 'Submitted'; }

    const feedbackDiv = document.getElementById(`feedback-${questionId}`);
    feedbackDiv.innerHTML = renderFeedback(evalRes);
    feedbackDiv.style.display = 'block';
  } catch (err) {
    console.error('[UI] Evaluation error:', err);
  }
}

function renderFeedback(evalRes) {
  const starBadge = evalRes.structure_star 
    ? '<span class="badge badge-success">✓ STAR Detected</span>'
    : '<span class="badge badge-warning">✗ Missing STAR Structure</span>';

  const relevanceBadge = evalRes.relevance >= 7 ? 'badge-success' : evalRes.relevance >= 4 ? 'badge-warning' : 'badge-danger';

  return `
    <div class="feedback-header">
      <div class="score-row">
        <div class="score-item"><strong>Relevance:</strong><span class="badge ${relevanceBadge}">${evalRes.relevance}/10</span></div>
        <div class="score-item"><strong>Confidence:</strong><span class="badge badge-info">${evalRes.confidence.toFixed(0)}%</span></div>
      </div>
      <div class="star-badge">${starBadge}</div>
    </div>
    ${evalRes.missing_points.length > 0 ? `
      <div class="suggestions">
        <h4>Areas for Improvement:</h4>
        <ul>${evalRes.missing_points.map(p => `<li>${p}</li>`).join('')}</ul>
      </div>
    ` : `<div class="success-msg">Great answer! Keep practicing with different scenarios.</div>`}
    <div class="improved-answer">
      <h4>Stronger Answer Example:</h4>
      <blockquote>${evalRes.improved_answer}</blockquote>
    </div>
  `;
}

function showSummary() {
  const evals = window.currentSession.evaluations;
  const avgRelevance = (evals.reduce((sum, e) => sum + e.evaluation.relevance, 0) / evals.length).toFixed(1);
  const starCount = evals.filter(e => e.evaluation.structure_star).length;

  const summaryDiv = document.createElement('div');
  summaryDiv.className = 'summary-box';
  summaryDiv.innerHTML = `
    <h2>Interview Summary</h2>
    <p><strong>Role:</strong> ${window.currentSession.role}</p>
    <p><strong>Questions Answered:</strong> ${evals.length}/${window.currentSession.questions.length}</p>
    <p><strong>Average Relevance:</strong> ${avgRelevance}/10</p>
    <p><strong>STAR Structure Detected:</strong> ${starCount}/${evals.length}</p>
    <div class="tips">
      <h3>💡 Next Steps:</h3>
      <ul>
        <li>Review feedback for each answer</li>
        <li>Re-record answers using the improved examples</li>
        <li>Practice STAR method (Situation → Task → Action → Result)</li>
        <li>Quantify your achievements with metrics</li>
        <li>Take another mock interview to track progress</li>
      </ul>
    </div>
    <button class="reset-btn" onclick="location.reload()">Try Another Interview</button>
  `;

  document.getElementById('questions').appendChild(summaryDiv);
  document.querySelector('.complete-btn').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  console.log('[App] Initializing InterviewCoachAI frontend...');
  setupResumeForm();
});

