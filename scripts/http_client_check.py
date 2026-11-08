"""External HTTP client check (standard library only).

Runs the five operations and the three provoked errors against a running server
and prints the status code of every response.

Usage:
    python manage.py seed_quiz
    python manage.py runserver
    python scripts/http_client_check.py [base_url] [username] [password]
"""
import base64
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"
USER = sys.argv[2] if len(sys.argv) > 2 else "demo"
PASSWORD = sys.argv[3] if len(sys.argv) > 3 else "demo12345"
AUTH = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()


def call(method, path, body=None, auth=True):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if auth:
        request.add_header("Authorization", AUTH)
    try:
        with urllib.request.urlopen(request) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    payload = json.loads(raw) if raw else None
    print(f"{method:<6} {path:<40} -> {status}")
    if status >= 400:
        print(f"       {json.dumps(payload, ensure_ascii=False)}")
    return status, payload


def question_body(exam_id, correct):
    return {
        "exam": exam_id,
        "text": "Which HTTP method creates a resource?",
        "points": 2,
        "choices": [{"text": f"Option {i}", "is_correct": i < correct} for i in range(4)],
    }


print("== Five operations ==")
_, exams = call("GET", "/exams/", auth=False)                                   # list
exam_id = exams["results"][0]["id"]
call("GET", f"/exams/{exam_id}/", auth=False)                                    # detail
_, created = call("POST", "/questions/", question_body(exam_id, 1))              # create
call("PATCH", f"/questions/{created['id']}/", {"points": 5})                     # partial update
call("DELETE", f"/questions/{created['id']}/")                                   # delete

print("\n== Provoked errors ==")
call("POST", "/exams/", {"description": "title is missing"})                     # missing field
call("POST", "/questions/", {**question_body(exam_id, 1), "points": "many"})     # wrong type
call("POST", "/questions/", question_body(exam_id, 0))                           # no correct choice
call("POST", "/questions/", question_body(exam_id, 2))                           # two correct choices
call("POST", "/exams/", {"title": "No credentials"}, auth=False)                 # no auth
call("GET", "/exams/9999/", auth=False)                                          # not found

print("\n== Filter, search, pagination ==")
call("GET", f"/questions/?exam={exam_id}", auth=False)
call("GET", "/questions/?search=django", auth=False)
call("GET", "/questions/?page=2", auth=False)
