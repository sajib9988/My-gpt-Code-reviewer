import base64
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.auth import GitHubConnection, GitHubOAuthState, User
from app.models.project import Project
from app.schemas.github import (
    GitHubAuthUrlResponse,
    GitHubConnectionResponse,
    GitHubFileResponse,
    GitHubRepositoryResponse,
    GitHubSearchResponse,
)
from app.security import create_token, decrypt_secret, encrypt_secret, expires_in, hash_token
from dependencies import get_current_user, require_csrf
from services.github import GitHubAPIError, GitHubClient
from services.github_oauth import authorization_url, exchange_code

router = APIRouter(prefix="/github", tags=["github"])
settings = get_settings()
logger = logging.getLogger(__name__)


def require_github_config() -> None:
    if not settings.github_client_id or not settings.github_client_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub is not configured")


def get_connection(user: User, database: DatabaseSession) -> GitHubConnection:
    connection = database.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if not connection:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Connect GitHub first")
    return connection


def get_project(project_id: str, user: User, database: DatabaseSession) -> Project:
    project = database.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not project.repository_url:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project has no GitHub repository")
    return project


def repository_parts(repository_url: str) -> tuple[str, str]:
    parts = repository_url.rstrip("/").split("/")
    if len(parts) < 2 or parts[-3] not in {"github.com", "www.github.com"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported GitHub repository URL")
    return parts[-2], parts[-1].removesuffix(".git")


def github_client(connection: GitHubConnection) -> GitHubClient:
    return GitHubClient(
        decrypt_secret(connection.encrypted_access_token, settings.token_encryption_key, settings.secret_key)
    )


@router.post("/connect", response_model=GitHubAuthUrlResponse, dependencies=[Depends(require_csrf)])
def connect_github(user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> dict[str, str]:
    require_github_config()
    state = create_token()
    database.add(
        GitHubOAuthState(
            id=str(uuid.uuid4()),
            user_id=user.id,
            state_hash=hash_token(state),
            expires_at=expires_in(600),
        )
    )
    database.commit()
    return {"authorization_url": authorization_url(state)}


@router.get("/callback")
def github_callback(
    state: str,
    code: str,
    database: DatabaseSession = Depends(get_db),
) -> Response:
    oauth_state = database.scalar(
        select(GitHubOAuthState).where(
            GitHubOAuthState.state_hash == hash_token(state),
            GitHubOAuthState.expires_at > datetime.now(UTC),
        )
    )
    if not oauth_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")
    try:
        access_token, scopes = exchange_code(code)
        github_user = GitHubClient(access_token)
        profile = github_user.current_user()
        github_user.close()
    except GitHubAPIError as error:
        logger.warning("GitHub OAuth failed: %s", error)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub authorization failed") from error

    connection = database.scalar(
        select(GitHubConnection).where(GitHubConnection.user_id == oauth_state.user_id)
    )
    encrypted_token = encrypt_secret(access_token, settings.token_encryption_key, settings.secret_key)
    if connection:
        connection.github_user_id = str(profile["id"])
        connection.github_login = profile["login"]
        connection.encrypted_access_token = encrypted_token
        connection.scopes = scopes
    else:
        database.add(
            GitHubConnection(
                id=str(uuid.uuid4()),
                user_id=oauth_state.user_id,
                github_user_id=str(profile["id"]),
                github_login=profile["login"],
                encrypted_access_token=encrypted_token,
                scopes=scopes,
            )
        )
    database.delete(oauth_state)
    database.commit()
    return RedirectResponse(url=f"{settings.frontend_url}/?github=connected", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/connection", response_model=GitHubConnectionResponse)
def connection_status(user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> dict:
    connection = database.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if not connection:
        return {"connected": False, "login": None, "scopes": []}
    return {"connected": True, "login": connection.github_login, "scopes": connection.scopes.split(",")}


@router.delete("/connection", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def disconnect_github(user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> None:
    connection = database.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if connection:
        database.delete(connection)
        database.commit()


@router.get("/projects/{project_id}/repositories", response_model=list[GitHubRepositoryResponse])
def repositories(project_id: str, user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> list[dict]:
    get_project(project_id, user, database)
    connection = get_connection(user, database)
    client = github_client(connection)
    try:
        return client.repositories()
    except GitHubAPIError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub request failed") from error
    finally:
        client.close()


@router.get("/projects/{project_id}/file", response_model=GitHubFileResponse)
def read_file(
    project_id: str,
    path: str = Query(min_length=1, max_length=1000),
    branch: str | None = Query(default=None, max_length=255),
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> dict:
    project = get_project(project_id, user, database)
    owner, repository = repository_parts(project.repository_url)
    connection = get_connection(user, database)
    client = github_client(connection)
    try:
        payload = client.file(owner, repository, path, branch or project.branch)
        if payload.get("type") != "file" or "content" not in payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path is not a file")
        content = base64.b64decode(payload["content"].replace("\n", "")).decode("utf-8")
        return {"path": payload["path"], "content": content, "sha": payload["sha"], "size": payload["size"]}
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="File is not UTF-8 text") from error
    except GitHubAPIError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub request failed") from error
    finally:
        client.close()


@router.get("/projects/{project_id}/search", response_model=GitHubSearchResponse)
def search(
    project_id: str,
    query: str = Query(min_length=1, max_length=200),
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> dict:
    project = get_project(project_id, user, database)
    owner, repository = repository_parts(project.repository_url)
    connection = get_connection(user, database)
    client = github_client(connection)
    try:
        return client.search_code(query, owner, repository)
    except GitHubAPIError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub request failed") from error
    finally:
        client.close()
