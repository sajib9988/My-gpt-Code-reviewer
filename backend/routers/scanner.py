import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DatabaseSession

from app.db.session import get_db
from app.models.auth import User
from app.models.project import ProjectFile, RepositoryScan
from app.schemas.scanner import ProjectFileResponse, ScanResponse
from dependencies import get_current_user, require_csrf
from routers.github import get_connection, get_project, github_client, repository_parts
from services.scanner import detect_framework, project_file_from_tree

router = APIRouter(prefix="/projects", tags=["repository-scanner"])


@router.post("/{project_id}/scan", response_model=ScanResponse, dependencies=[Depends(require_csrf)])
def scan_project(
    project_id: str,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> RepositoryScan:
    project = get_project(project_id, user, database)
    connection = get_connection(user, database)
    scan = database.scalar(select(RepositoryScan).where(RepositoryScan.project_id == project.id))
    if not scan:
        scan = RepositoryScan(id=str(uuid.uuid4()), project_id=project.id, branch=project.branch)
        database.add(scan)
        database.flush()
    scan.status = "scanning"
    scan.error = None
    database.query(ProjectFile).filter(ProjectFile.scan_id == scan.id).delete()
    owner, repository = repository_parts(project.repository_url)
    client = github_client(connection)
    try:
        repository_info = client.repository(owner, repository)
        tree = client.tree(owner, repository, project.branch)
        languages = client.languages(owner, repository)
        items = [item for item in tree.get("tree", []) if item.get("type") == "blob"]
        database.add_all(project_file_from_tree(scan.id, item) for item in items[:10000])
        scan.status = "completed"
        scan.branch = project.branch
        scan.commit_sha = tree.get("sha") or repository_info.get("default_branch")
        scan.framework = detect_framework(item["path"] for item in items)
        scan.languages = languages
        scan.files_count = len(items)
        scan.completed_at = datetime.now(UTC)
        database.commit()
        database.refresh(scan)
        return scan
    except Exception as error:
        scan.status = "failed"
        scan.error = "Repository scan failed"
        database.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Repository scan failed") from error
    finally:
        client.close()


@router.get("/{project_id}/scan", response_model=ScanResponse)
def scan_status(
    project_id: str,
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> RepositoryScan:
    project = get_project(project_id, user, database)
    scan = database.scalar(select(RepositoryScan).where(RepositoryScan.project_id == project.id))
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project has not been scanned")
    return scan


@router.get("/{project_id}/files", response_model=list[ProjectFileResponse])
def indexed_files(
    project_id: str,
    path: str | None = Query(default=None, max_length=1000),
    user: User = Depends(get_current_user),
    database: DatabaseSession = Depends(get_db),
) -> list[ProjectFile]:
    project = get_project(project_id, user, database)
    scan = database.scalar(select(RepositoryScan).where(RepositoryScan.project_id == project.id))
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project has not been scanned")
    query = select(ProjectFile).where(ProjectFile.scan_id == scan.id)
    if path:
        query = query.where(ProjectFile.path.startswith(path))
    return list(database.scalars(query.order_by(ProjectFile.path)))