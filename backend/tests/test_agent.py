import os

os.environ["DATABASE_URL"] = "sqlite:///./test_agent.db"

from fastapi.testclient import TestClient

from app.main import app


def test_conversation_task_run_and_sse_contract() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "agent@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    csrf = client.cookies.get("csrf_token")
    headers = {"X-CSRF-Token": csrf}

    project = client.post("/api/v1/projects", headers=headers, json={"name": "Agent Project"})
    assert project.status_code == 201
    project_id = project.json()["id"]

    conversation = client.post(
        f"/api/v1/projects/{project_id}/conversations",
        headers=headers,
        json={"title": "Auth refactor"},
    )
    assert conversation.status_code == 201
    conversation_id = conversation.json()["id"]
    message = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": "Review the authentication flow"},
    )
    assert message.status_code == 201

    task = client.post(
        f"/api/v1/projects/{project_id}/tasks",
        headers=headers,
        json={"title": "Review authentication", "priority": "high"},
    )
    assert task.status_code == 201
    run = client.post(
        f"/api/v1/projects/{project_id}/runs",
        headers=headers,
        json={"task_id": task.json()["id"]},
    )
    assert run.status_code == 200
    run_id = run.json()["id"]
    assert run.json()["provider"] == "ollama"

    events = client.get(f"/api/v1/runs/{run_id}/events")
    assert events.status_code == 200
    assert "Agent run queued" in events.text
