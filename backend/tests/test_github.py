from fastapi.testclient import TestClient

from app.main import app
from app.security import decrypt_secret, encrypt_secret


def test_github_token_encryption_round_trip() -> None:
    encrypted = encrypt_secret("github-token", "", "development-secret")
    assert encrypted != "github-token"
    assert decrypt_secret(encrypted, "", "development-secret") == "github-token"


def test_github_connection_requires_oauth_configuration() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "github@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201
    assert client.get("/api/v1/github/connection").json() == {
        "connected": False,
        "login": None,
        "scopes": [],
    }

    csrf_token = client.cookies.get("csrf_token")
    response = client.post("/api/v1/github/connect", headers={"X-CSRF-Token": csrf_token})
    assert response.status_code == 503