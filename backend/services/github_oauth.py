from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from services.github import GitHubAPIError

settings = get_settings()


def authorization_url(state: str) -> str:
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_callback_url,
        "scope": settings.github_scopes,
        "state": state,
    }
    return f"https://github.com/login/oauth/authorize?{urlencode(params)}"


def exchange_code(code: str) -> tuple[str, str]:
    response = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
            "redirect_uri": settings.github_callback_url,
        },
        headers={"Accept": "application/json"},
        timeout=20.0,
    )
    if response.is_error:
        raise GitHubAPIError(response.status_code, "GitHub OAuth exchange failed")
    payload = response.json()
    if not payload.get("access_token"):
        raise GitHubAPIError(400, "GitHub did not return an access token")
    return payload["access_token"], payload.get("scope", "")
