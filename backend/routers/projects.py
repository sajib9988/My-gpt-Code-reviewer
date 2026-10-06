import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession
from routers.github import repository_parts
from app.db.session import get_db
from app.models.auth import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from dependencies import get_current_user, require_csrf

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_project(
    
        if payload.repository_url:
        repository_parts(payload.repository_url)
    payload: ProjectCreate,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> Project:
    project = Project(id=str(uuid.uuid4()), owner_id=user.id, **payload.model_dump())
    database.add(project)
    database.commit()
    database.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> list[Project]:
    return list(database.scalars(select(Project).where(Project.owner_id == user.id).order_by(Project.created_at.desc())))


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> Project:
    project = database.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def delete_project(project_id: str, user: User = Depends(get_current_user), database: DatabaseSession = Depends(get_db)) -> None:
    project = database.scalar(select(Project).where(Project.id == project_id, Project.owner_id == user.id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    database.delete(project)
    database.commit()
