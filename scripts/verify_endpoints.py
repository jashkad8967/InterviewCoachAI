import json
import urllib.request

BASE = 'http://localhost:8000'

def post(path, payload):
    url = BASE + path
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, r.read().decode()

if __name__ == '__main__':
    try:
        s, h = post('/health', {})
    except Exception:
        print('Health check failed; try starting backend first')
    else:
        print('Health OK')

    # Sample flow: analyze -> generate -> evaluate
    resume = {'text': 'Jane Doe\nSoftware Engineer\nSkills: Python, SQL, Docker\n5+ years experience'}
    print('\nPOST /analyze-resume')
    print(post('/analyze-resume', resume))

    gen_req = {'skills': ['python', 'sql'], 'experience_level': 'mid', 'role': 'software engineer'}
    print('\nPOST /generate-questions')
    print(post('/generate-questions', gen_req))

    eval_req = {'question':'Tell me about a time','answer':'I fixed a bug and improved latency by 40%','resume_skills':['python'],'role':'software engineer'}
    print('\nPOST /evaluate-answer')
    print(post('/evaluate-answer', eval_req))
