import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.db.session import get_db
from app.models.agent import CodeChange
from app.models.auth import User
from app.models.project import Project
from app.schemas.changes import (
    CodeChangeCreate,
    CodeChangeResponse,
    CommitRequest,
    PullRequestRequest,
)
from dependencies import get_current_user, require_csrf
from routers.github import get_connection, get_project, github_client, repository_parts

router = APIRouter(prefix="/projects", tags=["code-changes"])


def owned_change(change_id: str, user: User, database: DatabaseSession) -> CodeChange:
    change = database.scalar(
        select(CodeChange).join(Project, Project.id == CodeChange.project_id).where(
            CodeChange.id == change_id, Project.owner_id == user.id
        )
    )
    if not change:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code change not found")
    return change


@router.post("/{project_id}/changes", response_model=CodeChangeResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_change(project_id: str, payload: CodeChangeCreate, user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> CodeChange:
    get_project(project_id, user, database)
    change = CodeChange(id=str(uuid.uuid4()), project_id=project_id, **payload.model_dump())
    database.add(change)
    database.commit()
    database.refresh(change)
    return change


@router.get("/{project_id}/changes", response_model=list[CodeChangeResponse])
def list_changes(project_id: str, user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> list[CodeChange]:
    get_project(project_id, user, database)
    return list(database.scalars(select(CodeChange).where(CodeChange.project_id == project_id).order_by(CodeChange.created_at.desc())))


@router.post("/{project_id}/changes/{change_id}/approve", response_model=CodeChangeResponse, dependencies=[Depends(require_csrf)])
def approve_change(project_id: str, change_id: str, user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> CodeChange:
    change = owned_change(change_id, user, database)
    if change.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code change not found")
    if change.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Code change is not pending")
    change.status = "approved"
    change.approved_at = datetime.now(UTC)
    database.commit()
    database.refresh(change)
    return change


@router.post("/{project_id}/changes/commit", response_model=list[CodeChangeResponse], dependencies=[Depends(require_csrf)])
def commit_changes(project_id: str, payload: CommitRequest, user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> list[CodeChange]:
    if payload.branch in {"main", "master"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Changes cannot be committed directly to the default branch")
    project = get_project(project_id, user, database)
    changes = list(database.scalars(select(CodeChange).where(CodeChange.project_id == project_id, CodeChange.status == "approved")))
    if not changes:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No approved changes")
    connection = get_connection(user, database)
    owner, repository = repository_parts(project.repository_url)
    client = github_client(connection)
    try:
        branch = client.branch(owner, repository, payload.branch)
        for change in changes:
            result = client.commit_file(owner, repository, change.path, payload.branch, change.new_content, payload.message)
            change.status = "committed"
            change.branch = payload.branch
            change.commit_sha = result.get("commit", {}).get("sha") or branch.get("commit", {}).get("sha")
        database.commit()
        return changes
    finally:
        client.close()


@router.post("/{project_id}/pull-requests", dependencies=[Depends(require_csrf)])
def create_pull_request(project_id: str, payload: PullRequestRequest, user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> dict:
    if payload.branch in {"main", "master"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pull requests require an agent branch")
    project = get_project(project_id, user, database)
    connection = get_connection(user, database)
    owner, repository = repository_parts(project.repository_url)
    client = github_client(connection)
    try:
        pull_request = client.create_pull_request(owner, repository, payload.title, payload.body, payload.branch, project.branch)
        return {"number": pull_request.get("number"), "url": pull_request.get("html_url"), "title": pull_request.get("title")}
    finally:
        client.close()