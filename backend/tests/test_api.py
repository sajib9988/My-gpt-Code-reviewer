from fastapi.testclient import TestClient

from app.main import app


def test_registration_session_and_project_isolation() -> None:
    first = TestClient(app)
    response = first.post(
        "/api/v1/auth/register",
        json={"email": "first@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    assert first.get("/api/v1/auth/me").status_code == 200

    csrf_token = first.cookies.get("csrf_token")
    response = first.post(
        "/api/v1/projects",
        headers={"X-CSRF-Token": csrf_token},
        json={"name": "First Project"},
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    second = TestClient(app)
    response = second.post(
        "/api/v1/auth/register",
        json={"email": "second@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    assert second.get(f"/api/v1/projects/{project_id}").status_code == 404


def test_mutating_requests_require_csrf() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "csrf@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    response = client.post("/api/v1/projects", json={"name": "Blocked"})
    assert response.status_code == 403