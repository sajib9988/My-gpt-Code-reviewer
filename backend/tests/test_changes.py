from fastapi.testclient import TestClient

from app.main import app


def test_change_approval_and_default_branch_protection() -> None:
    client = TestClient(app)
    assert client.post(
        "/api/v1/auth/register",
        json={"email": "changes@example.com", "password": "correct-horse-battery"},
    ).status_code == 201
    csrf = client.cookies.get("csrf_token")
    headers = {"X-CSRF-Token": csrf}
    project = client.post("/api/v1/projects", headers=headers, json={"name": "Changes"})
    project_id = project.json()["id"]

    change = client.post(
        f"/api/v1/projects/{project_id}/changes",
        headers=headers,
        json={"path": "src/app.py", "new_content": "print('updated')"},
    )
    assert change.status_code == 201
    change_id = change.json()["id"]
    assert change.json()["status"] == "pending"

    approved = client.post(f"/api/v1/projects/{project_id}/changes/{change_id}/approve", headers=headers)
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    commit = client.post(
        f"/api/v1/projects/{project_id}/changes/commit",
        headers=headers,
        json={"branch": "main", "message": "Do not bypass review"},
    )
    assert commit.status_code == 400