from fastapi.testclient import TestClient

from app.main import app
from services.scanner import detect_framework, language_for_path


def test_scanner_detects_common_project_shapes() -> None:
    assert detect_framework(["next.config.ts", "app/page.tsx"]) == "Next.js"
    assert detect_framework(["manage.py", "settings.py"]) == "Django"
    assert detect_framework(["package.json", "src/index.js"]) == "Node.js"
    assert language_for_path("src/main.py") == "Python"


def test_scan_requires_a_github_connection() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "scanner@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    csrf_token = client.cookies.get("csrf_token")
    response = client.post(
        "/api/v1/projects",
        headers={"X-CSRF-Token": csrf_token},
        json={"name": "Scanner Project", "repository_url": "https://github.com/acme/demo"},
    )
    assert response.status_code == 201
    project_id = response.json()["id"]
    response = client.post(
        f"/api/v1/projects/{project_id}/scan",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert response.status_code == 409